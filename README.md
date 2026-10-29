# Streamlined Script Execution with `uvr`

[`uv`](https://github.com/astral-sh/uv.git) is a Python package manager and script runner. `uvr` selects an interpreter for Python scripts and resolves commands from a project's `.venv` or `PATH`. It delegates to `uv` when a script requests uv-managed execution, such as with PEP 723 inline metadata or a uv shebang.

Call `uvr` with a script or command:

```bash
uvr [options] [--] script.py [script arguments]
uvr [options] [--] command [arguments]
```

## Decision Rules

Rules are applied in this order:

1. `uvr -h` and `uvr --help` print help and exit successfully.
2. With no target, `uvr` starts Python. It uses a usable active `VIRTUAL_ENV`, then a project `.venv`. If the current directory is inside a project but that project has no usable `.venv`, it reports an error. Outside a project it starts system Python 3.
3. `uvr --script` or `uvr --gui-script` explicitly requests uv-managed script execution.
4. Otherwise, a script with a non-Python manager in its shebang is handed to that manager. Examples include `uv run --script`, `poetry run python`, and `conda run -n my-env python`. A shebang naming `uvr` itself is not recursively invoked.
5. A script containing PEP 723 inline script metadata is run by `uv`, so its declared dependencies and Python requirement are honored. This takes precedence over a discovered project `.venv`.
6. Other Python scripts use the active `VIRTUAL_ENV`, then the nearest project `.venv`. Project roots are detected by `pyproject.toml`, `uv.lock`, or `poetry.lock`. If a project root has no usable `.venv`, `uvr` reports an error rather than silently selecting a different Python.
7. A Python script outside a project and without an active venv uses system Python 3. Set `UVR_SYSTEM_PYTHON` to select its executable explicitly. The default is `/usr/bin/python3` on Unix-like systems and `py -3` on Windows.
8. For commands, `uvr` checks the selected venv's `bin` or `Scripts` directory first, then searches `PATH`. It does not use `uv run` as a command fallback.

The active `VIRTUAL_ENV` takes precedence over a project `.venv`. `uvr` does not install or synchronize dependencies in either environment.

## Python Packages

`UVR_SYSTEM_PYTHON` selects an interpreter; it does not install packages. Install packages into an isolated project `.venv` when possible. Packages can also be installed into a separately managed Python installation, but mixing dependencies into an OS-managed Python may conflict with the operating system's package manager.

## Installation

Prerequisite: `uv` must be installed and available on your `PATH`.

To install `uvr`, use the following command:

```bash
uv tool install uvr
```

To upgrade `uvr`, use the following command:

```bash
uv tool upgrade uvr
```

## Windows Console Modes

Two entry points are installed:

- `uvr` — console application. Use from a terminal or for scripts that need a command-line window.
- `uvr-gui` — GUI application. Use for scripts started by double-click or for GUI-only programs that must not open a console window.

On Linux and macOS both commands behave the same.

## Usage

Examples of running scripts and commands with `uvr`:

1.  **Using `uv run --project <project_path> <script_path>`:**
    - This command explicitly tells `uv` to run the specified Python script within the context of the project located at `<project_path>`.
    - This is useful when your script relies on dependencies defined within a specific project directory but is executed from elsewhere.
    - Example:

        ```bash
        uv run --project /path/to/project [options] /path/to/project/script.py [script_options]
        ```

2.  **Using `uvr script.py`:**
    - `uvr` selects the interpreter based on the decision rules above.
    - Example:

        ```bash
        uvr [options] [--] script.py [script_options]
        ```

    - For ambiguity and edge cases, use `--` (see the section _General Rule for Using the `--` Separator_).

3.  **Shebang Usage:**
    - Example:

        ```python
        #!/usr/bin/env -S uvr [options] [--]
        # Your Python code here...
        ```

    - **Note on `-S` flag**: The `-S` flag allows passing multiple arguments to the interpreter. It is optional if your `env` implementation supports it (most modern systems do). However:
        - **Without `-S`**: You can only use `#!/usr/bin/env uvr` without additional options or parameters
        - **With `-S`**: You can pass options like `#!/usr/bin/env -S uvr --with dep1 --`
        - Some older or minimal Unix-like systems may not support the `-S` flag in `env`

    - If you pass script arguments, use `--` to separate `uvr/uv` options from script arguments.

4.  **Scripts without `.py` or `.pyw` extension:**
    - For extensionless script files, `uvr` uses `--script` when needed to preserve script execution. A shebang naming another manager is handed to that manager.

    - Example: For a `foo` script:

        ```python
        #!/usr/bin/env -S uvr [options] [--]
        # Your Python code here...
        ```

        This is treated as a Python script. Use an explicit manager shebang, such as `#!/usr/bin/env -S uv run --script`, when the script must use that manager.

    - Or, to be more explicit, you can include the `--script` flag directly in the shebang:

        ```python
        #!/usr/bin/env -S uvr --script
        ```

    - Commands such as `uvr black .` or `uvr pytest` are resolved from the selected venv and then `PATH`; they are not treated as Python scripts.

5.  **Debug usage:**
    - Example:
        ```bash
        uvr -v [options] [--] script.py [script_options]
        uvr -vv [options] [--] script.py [script_options]
        ```

6.  **Offline mode:**
                - When `UV_OFFLINE=1` is set or `--offline` is passed among the `uvr`
                    pre-options, `uvr` does not invoke uv for script dependency resolution.
                - Python scripts run directly from the selected venv. A script that needs
                    uv-managed metadata but has no usable venv fails rather than resolving
                    or downloading dependencies.
                - Commands are still resolved from the selected venv and then `PATH`.
    - Examples:
        ```bash
        UV_OFFLINE=1 uvr script.py
        uvr --offline script.py
        uvr --offline -- script.py --some-script-arg
        uvr --offline pytest -q
        ```

## General Rule for Using the `--` Separator

The `--` argument functions as a standard command-line delimiter. It separates options intended for `uvr` (and, for uv-managed scripts, uv) from arguments intended for the target script or command.

Arguments appearing before `--` are processed by `uvr`. Arguments appearing after `--` are passed directly to the invoked script or command.

This explicit separation is crucial for:

- **Preventing Ambiguity**: `uvr` employs a basic heuristic to identify the script path (the first non-hyphenated argument). This can lead to misinterpretation if the script itself accepts options that resemble `uvr/uv` arguments.

- **Ensuring Precise Argument Passing**: By using `--`, users guarantee that all subsequent arguments are correctly delivered to their script, bypassing `uvr's` argument parsing logic.

**Recommendation**: Utilize the `--` separator whenever precise control over argument distribution between `uvr/uv` and the target script is required.

## Ctrl+C (SIGINT) Handling

`uvr` handles `KeyboardInterrupt` to provide clean CLI behavior when interrupted with `Ctrl+C`.

- It suppresses Python traceback noise (unwanted junk output) on user interruption.
- It exits with status code `130`, following the common Unix convention: `128 + 2` (`SIGINT` is signal number `2`).
- This keeps output clean while still signaling to the parent shell/process that execution was interrupted.

Platform note:

- On Linux and macOS, `130` matches the common signal-derived convention (`128 + SIGINT 2`).
- On Windows, `130` is used intentionally as a consistent, cross-platform interruption code for `uvr`.

## Security Notes

`uvr` is a command runner, not a sandbox. It executes the script or command you pass to it, directly or through the manager selected by the script's shebang.

Main risks:

- Running untrusted scripts can execute arbitrary code.
- Untrusted dependency sources can introduce supply-chain risk.
- Running as root/Administrator increases impact if something goes wrong.
- A compromised `PATH` could resolve a malicious `uv` binary.

Recommended protections:

- Run only trusted scripts and trusted dependency sources.
- Do not run `uvr` as root/Administrator unless strictly required.
- In CI, pin dependencies and use a lockfile where possible.
- Prefer explicit script paths for automation (`script.py`) over ambiguous invocations.
- Keep build/runtime environments isolated (virtual environments, containers, CI runners).
- Ensure your `PATH` resolves to the expected `uv` executable.

Scope note:

- `uvr` is not a sandbox. It is a command runner helper and should be used with standard secure development practices.
