#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Authors (see git history)
# SPDX-License-Identifier: MIT

import ctypes
import os
import shlex
import shutil
import subprocess
import sys


def _owns_console():
    """Return True if this process already owns a console.

    On Windows, console scripts run attached to a terminal (True), while
    gui-scripts are launched without a terminal (False). The latter must
    pass CREATE_NO_WINDOW when spawning a console child to avoid opening
    a new, empty terminal window.

    On non-Windows platforms there is no GUI/console executable distinction,
    so we always return True (the child is allowed to inherit our terminal).
    """
    if sys.platform != "win32":
        return True  # only Windows distinguishes console vs GUI executables
    return ctypes.windll.kernel32.GetConsoleWindow() != 0


def get_uvr_version():
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version('uvr')
    except PackageNotFoundError:
        return 'unknown'


def print_help():
    print(f"Version:            {get_uvr_version()}")
    print("Usage:               uvr [options] [--] script.py [script options]")
    print("                     uvr [options] [--] command [arguments]")
    print("                     uvr                       (start Python)")
    print("Help:                uvr -h | --help")
    print("Python selection:    active/project .venv, then system Python 3")
    print("System Python:       set UVR_SYSTEM_PYTHON to override the default")
    print("uv scripts:          PEP 723 metadata or --script/--gui-script")
    print("Offline mode:        set UV_OFFLINE=1 or pass --offline")


# Option '--' is separator.  When you use it, you're telling uvr to treat all arguments that come after it
#   as destined exclusively for your Python script, not for uvr or uv.
def resolve_argv():
    pre_opt = []
    run_script = None
    post_opt = []

    # The '--' argument explicitly separates `uvr`/`uv` options (pre-options)
    # from the script path and any arguments meant for the script (post-options).
    # Example: uvr <pre_opt> -- <script_path> <post_opt>
    # For instance, `uvr -a --b -- my_script.py --d` would pass `-a --b` to `uvr`/`uv`
    # and `my_script.py --d` to the script.

    if '--' in sys.argv:
        idx = sys.argv.index('--')
        pre_opt = sys.argv[1:idx]

    else:
        # Simple heuristic for pre-options:
        # Identifies options (starting with '-') at the beginning of the arguments.
        # The first argument found that doesn't start with '-' is assumed to be the script path.
        # Example: uvr -a -b script_name --arg1 --arg2
        # Here, pre_opt would be ['-a', '-b'], and 'script_name' is identified as the script.

        idx = 0
        for i in range(1, len(sys.argv)):
            if sys.argv[i].startswith('-'):
                idx = i
            else:
                break
        pre_opt = sys.argv[1:idx + 1]

    if idx + 1 >= len(sys.argv) or sys.argv[idx + 1].startswith('-'):
        return pre_opt, run_script, post_opt

    run_script = sys.argv[idx + 1]
    post_opt = sys.argv[idx + 2:]

    # prevent looping forever the same script not ending with .py or .pyw
    script_options = ('-s', '--script', '--gui-script')
    if (
        not run_script.endswith(('.py', '.pyw'))
        and not any(option in pre_opt for option in script_options)
        and os.path.isfile(run_script)
        and not _is_executable_program(run_script)
    ):
        pre_opt.append('--script')

    return pre_opt, run_script, post_opt


def _venv_python_at(directory):
    """Return the path to the Python interpreter of the .venv in ``directory``,
    or None if that directory has no .venv.

    Supports the Unix layout (`.venv/bin/python`) and the Windows layout
    (`.venv/Scripts/python.exe`).
    """
    candidates = [
        os.path.join(directory, '.venv', 'bin', 'python'),
        os.path.join(directory, '.venv', 'Scripts', 'python.exe'),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def _find_venv_python(start_dir):
    """Locate the project's .venv Python by walking upward from ``start_dir``.

    The search stops at the first directory that looks like a Python project
    root (contains ``pyproject.toml`` or ``uv.lock``) so we never escape the
    project and search system directories. An already-activated virtual
    environment (``VIRTUAL_ENV``) takes precedence.

    Returns the interpreter path, or None when no .venv was found.
    """
    venv_root = os.environ.get('VIRTUAL_ENV')
    if venv_root:
        # VIRTUAL_ENV already points at the .venv directory itself, so check it
        # directly instead of looking for a nested .venv inside it.
        candidates = [
            os.path.join(venv_root, 'bin', 'python'),
            os.path.join(venv_root, 'Scripts', 'python.exe'),
        ]
        for interpreter in candidates:
            if os.path.isfile(interpreter):
                return interpreter

    current = os.path.realpath(start_dir)
    if os.path.isfile(current):
        current = os.path.dirname(current)

    while True:
        interpreter = _venv_python_at(current)
        if interpreter:
            return interpreter

        # Stop at project-root markers so we don't climb into unrelated dirs.
        # Note: only Python/uv-specific markers are used here. A `.git` marker
        # would misfire when scripts live inside a foreign git repository
        # (e.g. via a symlink into someone else's repo), so it is intentionally
        # omitted. The filesystem root check below is the final safety net.
        for marker in ('pyproject.toml', 'uv.lock', 'poetry.lock'):
            if os.path.exists(os.path.join(current, marker)):
                return None

        parent = os.path.dirname(current)
        if parent == current:  # reached the filesystem root
            return None
        current = parent


def _find_project_root(start_dir):
    current = os.path.realpath(start_dir)
    if os.path.isfile(current):
        current = os.path.dirname(current)

    while True:
        for marker in ('pyproject.toml', 'uv.lock', 'poetry.lock'):
            if os.path.exists(os.path.join(current, marker)):
                return current

        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def _is_poetry_project(project_root):
    if not project_root:
        return False
    if os.path.isfile(os.path.join(project_root, 'poetry.lock')):
        return True

    pyproject = os.path.join(project_root, 'pyproject.toml')
    if not os.path.isfile(pyproject):
        return False
    with open(pyproject, encoding='utf-8') as project_file:
        return any(
            line.strip() == '[tool.poetry]' or
            (line.strip().startswith('[tool.poetry.') and line.strip().endswith(']'))
            for line in project_file
        )


def _venv_program(venv_python, program):
    if os.path.basename(program) != program:
        return None

    venv_root = os.path.dirname(os.path.dirname(venv_python))
    candidates = [
        os.path.join(venv_root, 'bin', program),
        os.path.join(venv_root, 'Scripts', program),
    ]
    if os.name == 'nt' and not os.path.splitext(program)[1]:
        candidates.extend(
            os.path.join(venv_root, 'Scripts', program + extension)
            for extension in ('.exe', '.bat', '.cmd')
        )

    for candidate in candidates:
        if os.path.isfile(candidate) and (os.name == 'nt' or os.access(candidate, os.X_OK)):
            return candidate
    return None


def _has_inline_script_metadata(script_path):
    """Return True when a script contains a PEP 723 metadata block."""
    try:
        with open(script_path, encoding='utf-8-sig') as script_file:
            in_metadata = False
            for line in script_file:
                marker = line.strip()
                if marker == '# /// script':
                    in_metadata = True
                elif in_metadata and marker == '# ///':
                    return True
    except (OSError, UnicodeError):
        return False
    return False


def _is_uvr_shebang(script_path):
    try:
        with open(script_path, encoding='utf-8-sig') as script_file:
            shebang = script_file.readline().lower()
    except (OSError, UnicodeError):
        return False
    return shebang.startswith('#!') and 'uvr' in shebang


def _manager_shebang_args(script_path):
    try:
        with open(script_path, encoding='utf-8-sig') as script_file:
            shebang = script_file.readline().strip()
    except (OSError, UnicodeError):
        return None

    if not shebang.startswith('#!'):
        return None
    try:
        parts = shlex.split(shebang[2:].strip())
        if not parts:
            return None
        if os.path.basename(parts[0]) == 'env':
            parts = parts[1:]
            if parts and parts[0] == '-S':
                parts = shlex.split(' '.join(parts[1:]))
        if not parts:
            return None
    except ValueError:
        return None

    command = os.path.basename(parts[0]).lower()
    if command.startswith('python') or command == 'uvr':
        return None
    return parts


def _is_executable_program(path):
    if not os.path.isfile(path):
        return False
    if os.name == 'nt':
        return os.path.splitext(path)[1].lower() in ('.exe', '.bat', '.cmd')
    return os.access(path, os.X_OK) and not (
        _has_inline_script_metadata(path) or _is_uvr_shebang(path)
    )


def _system_python():
    configured_python = os.environ.get('UVR_SYSTEM_PYTHON')
    if configured_python:
        return [configured_python]

    if os.name == 'nt':
        launcher = shutil.which('py')
        if launcher:
            return [launcher, '-3']
    elif os.path.isfile('/usr/bin/python3'):
        return ['/usr/bin/python3']

    raise ValueError(
        'System Python 3 was not found; set UVR_SYSTEM_PYTHON to its executable.'
    )


def _resolve_default_python_args(cwd=None):
    start_dir = cwd or os.getcwd()
    venv_python = _find_venv_python(start_dir)
    if venv_python:
        return [venv_python]

    project_root = _find_project_root(start_dir)
    if project_root:
        raise ValueError(
            f'Python project at {project_root!r} has no usable .venv; '
            'create the project environment before starting Python.'
        )
    return _system_python()


def _resolve_prog_args(run_target, pre_opt, post_opt, cwd=None):
    offline = _is_offline(pre_opt)
    script_options = ('-s', '--script', '--gui-script')
    explicitly_script = any(option in pre_opt for option in script_options)
    is_file = os.path.isfile(run_target)
    manager_shebang = _manager_shebang_args(run_target) if is_file else None
    if manager_shebang and not explicitly_script:
        manager_name = os.path.basename(manager_shebang[0]).lower()
        if not (offline and manager_name == 'uv'):
            return manager_shebang + [os.path.realpath(run_target)] + post_opt

    is_script = (
        explicitly_script
        or run_target.endswith(('.py', '.pyw'))
        or (is_file and not _is_executable_program(run_target))
    )
    if is_script:
        if is_file:
            run_target = os.path.realpath(run_target)
            start_dir = os.path.dirname(run_target)
        else:
            start_dir = cwd or os.getcwd()
    else:
        start_dir = cwd or os.getcwd()

    project_root = _find_project_root(start_dir)
    poetry_project = _is_poetry_project(project_root)
    venv_python = _find_venv_python(start_dir)

    if is_script:
        has_inline_metadata = is_file and _has_inline_script_metadata(run_target)
        if (explicitly_script or has_inline_metadata) and not offline:
            return ['uv', 'run'] + pre_opt + [run_target] + post_opt
        if venv_python:
            return [venv_python, run_target] + post_opt
        if poetry_project:
            raise ValueError(
                "Poetry project has no usable .venv; create it with Poetry before running this script."
            )
        if offline:
            raise ValueError(
                "Offline mode requires a usable project .venv; refusing to run uv."
            )
        if project_root:
            raise ValueError(
                f'Python project at {project_root!r} has no usable .venv; '
                'create the project environment before running this script.'
            )
        return _system_python() + [run_target] + post_opt

    if venv_python:
        program = _venv_program(venv_python, run_target)
        if program:
            return [program] + post_opt

    path_program = shutil.which(run_target)
    if path_program:
        return [path_program] + post_opt

    if offline:
        if venv_python:
            raise ValueError(
                f"Offline mode cannot find {run_target!r} in the selected .venv or PATH."
            )
        raise ValueError(
            "Offline mode requires a usable project .venv; refusing to run uv."
        )

    raise ValueError(f"Command {run_target!r} was not found in the selected .venv or PATH.")


def _is_offline(pre_opt):
    """Return True when uv offline mode is requested.

    Offline mode is triggered either by passing ``--offline`` among the
    `uvr`/`uv` pre-options or by setting ``UV_OFFLINE=1`` in the environment.
    """
    if os.environ.get('UV_OFFLINE') == '1':
        return True
    return '--offline' in pre_opt


def main():  # pragma: no cover
    if len(sys.argv) < 2:
        pre_opt, run_script, post_opt = [], None, []
    else:
        pre_opt, run_script, post_opt = resolve_argv()

    if '-h' in pre_opt or '--help' in pre_opt:
        print_help()
        sys.exit(0)

    if '-v' in pre_opt or '-vv' in pre_opt:
        print(f"DEBUG uvr {sys.argv=}", file=sys.stderr)
        print(f"DEBUG uvr {pre_opt=} {run_script=} {post_opt=}", file=sys.stderr)

        if '-vv' in pre_opt:  # exit after debug output
            sys.exit(0)

    try:
        if run_script is None:
            prog_args = _resolve_default_python_args()
        else:
            prog_args = _resolve_prog_args(run_script, pre_opt, post_opt)
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(1)

    if '-v' in pre_opt:
        print(f"DEBUG uv {prog_args=}", file=sys.stderr)


    # Remove extraneous output (junk) on Ctrl+C (SIGINT):
    try:
        kwargs = {}
        if not _owns_console():
            # We are the gui-script entry point (uvr-gui) on Windows, launched
            # without a console. Tell the child `uv` process not to create one.
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(prog_args, check=False, **kwargs)
    except KeyboardInterrupt:
        # Cleanly handle Ctrl+C (SIGINT): exit with code 130 (128 + 2),
        # where 128 is the base for fatal signals and 2 is the signal number for SIGINT.
        # This prevents unwanted traceback (unwanted output/noise) and signals to the shell
        # that the process was interrupted by the user.
        sys.exit(130)
    sys.exit(result.returncode)


if __name__ == "__main__":  # pragma: no cover
    main()
