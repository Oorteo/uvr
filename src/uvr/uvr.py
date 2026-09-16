#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Authors (see git history)
# SPDX-License-Identifier: MIT

import ctypes
import os
import sys
import subprocess


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
    print("Shebang usage:      #!/usr/bin/env -S uvr [options] [--]")
    print(
        "Command line usage: uvr [options] [--] script.py [script options]"
    )
    print(
        "Debug usage:        uvr -v [options] [--] script.py [script options]"
    )
    print("Offline mode:       set UV_OFFLINE=1 to run the script with the")
    print("                    project's .venv Python directly (no uv run).")


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
    if not (run_script.endswith('.py') or run_script.endswith('.pyw')):
        if '-s' not in pre_opt and '--script' not in pre_opt and '--gui-script' not in pre_opt:
            if os.path.isfile(run_script):  # check if the script is a valid file
                pre_opt.append('--script')  # if it is a file, we assume it is a python script

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
        for marker in ('pyproject.toml', 'uv.lock'):
            if os.path.exists(os.path.join(current, marker)):
                return None

        parent = os.path.dirname(current)
        if parent == current:  # reached the filesystem root
            return None
        current = parent


def _is_offline():
    """Return True when uv offline mode is requested via UV_OFFLINE."""
    return os.environ.get('UV_OFFLINE') == '1'


def main():  # pragma: no cover
    if len(sys.argv) < 2:
        print_help()

        sys.exit(1)

    pre_opt, run_script, post_opt = resolve_argv()

    if '-v' in pre_opt or '-vv' in pre_opt:
        print(f"DEBUG uvr {sys.argv=}", file=sys.stderr)
        print(f"DEBUG uvr {pre_opt=} {run_script=} {post_opt=}", file=sys.stderr)

        if '-vv' in pre_opt:  # exit after debug output
            sys.exit(0)

    if run_script is None:
        print("No script provided", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(run_script):    # fall back to uv run
        prog_args = ['uv', 'run'] + pre_opt + [
            run_script
        ] + post_opt
    else:
        run_script = os.path.realpath(run_script)
        run_script_dir = os.path.dirname(run_script)
        venv_python = _find_venv_python(run_script_dir) if _is_offline() else None

        if venv_python:
            if '-v' in pre_opt:
                print(f"DEBUG uvr offline mode: using {venv_python}", file=sys.stderr)
            prog_args = [venv_python, run_script] + post_opt
        else:
            prog_args = ['uv', 'run'] + pre_opt + [
                '--project', run_script_dir, run_script
            ] + post_opt

    if '-v' in pre_opt:
        print(f"DEBUG uv {prog_args=}", file=sys.stderr)


    # Remove extraneous output (junk) on Ctrl+C (SIGINT):
    try:
        kwargs = {}
        if not _owns_console():
            # We are the gui-script entry point (uvr-gui) on Windows, launched
            # without a console. Tell the child `uv` process not to create one.
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(prog_args, **kwargs)
    except KeyboardInterrupt:
        # Cleanly handle Ctrl+C (SIGINT): exit with code 130 (128 + 2),
        # where 128 is the base for fatal signals and 2 is the signal number for SIGINT.
        # This prevents unwanted traceback (unwanted output/noise) and signals to the shell
        # that the process was interrupted by the user.
        sys.exit(130)
    sys.exit(result.returncode)


if __name__ == "__main__":  # pragma: no cover
    main()
