#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Authors (see git history)
# SPDX-License-Identifier: MIT

import ctypes
import os
import sys
import subprocess


def _has_console():
    """Return True if the current process has an associated console window.

    On Windows, gui-scripts do not get a console; calling a console child process
    from a GUI parent would otherwise open a new, empty terminal window.
    """
    if sys.platform != "win32":
        return True
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
        if '--script' not in pre_opt and '--gui-script' not in pre_opt:
            if os.path.isfile(run_script):  # check if the script is a valid file
                pre_opt.append('--script')  # if it is a file, we assume it is a python script

    return pre_opt, run_script, post_opt


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
        prog_args = ['uv', 'run'] + pre_opt + [
            '--project', run_script_dir, run_script
        ] + post_opt

    if '-v' in pre_opt:
        print(f"DEBUG uv {prog_args=}", file=sys.stderr)


    # Remove extraneous output (junk) on Ctrl+C (SIGINT):
    try:
        kwargs = {}
        if not _has_console():
            # Running as a Windows gui-script: prevent a new empty console window
            # from appearing when the child `uv` process starts.
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
