

# Simple Script Execution with uvr

[`uv`](https://github.com/astral-sh/uv.git) is a fast, modern Python package installer and resolver, designed as a drop-in replacement for pip and pip-compile.

Unfortunately, [`uv`](https://github.com/astral-sh/uv.git)
prioritizes virtual environments within the current directory. This makes it cumbersome to execute scripts located elsewhere, requiring the use of the `--project` flag.

This script offers a streamlined workaround for running Python scripts via `uv`, allowing you to use `uvr [options] script.py` instead of `uv run [options] --project <script_path> script.py`."

Its primary value lies in its simplicity and immediate usability, providing a *quick fix* for a pressing pain point.


## Installation

To install `uvr`, use the following command:

```bash
uv tool install uvr
```

or

```bash
uv tool install --from git+https://github.com/karnigen/uvr uvr
```


To upgrade `uvr`, use the following command:

```bash
uv tool upgrade uvr
```



## Usage

Several ways to run your Python scripts with `uv`:

1.  **Using `uv run --project <script_path> script.py`:**

    * This command explicitly tells `uv` to run the specified Python script (`script.py`) within the context of the project located at `<script_path>`.
    * This is useful when your script relies on dependencies defined within a specific project directory.
    * Example:

        ```bash
        uv run [options] --project /path/to/project run_script.py [script_options]
        ```

2.  **Using `uvr script.py`:**

    * This is a more direct way to execute your Python script (`run_script.py`) using `uvr`.
    * `uvr` automatically determines the project directory based on the script path, effectively mimicking the `--project` flag's behavior.
    * Example:

        ```bash
        uvr [options] [--] run_script.py [script_options]
        ```
    * Always use `--` if the automatic script identification fails or could be ambiguous.


3.  **Shebang Usage:**

    * Example:

        ```python
        #!/usr/bin/env -S uvr [options] [--]

        # Your Python code here...
        ```

    * **Note on `-S` flag**: The `-S` flag allows passing multiple arguments to the interpreter. It is optional if your `env` implementation supports it (most modern systems do). However:
        - **Without `-S`**: You can only use `#!/usr/bin/env uvr` without additional options or parameters
        - **With `-S`**: You can pass options like `#!/usr/bin/env -S uvr --with dep1 --`
        - Some older or minimal Unix-like systems may not support the `-S` flag in `env`

    * Always use `--` if the automatic script identification fails or could be ambiguous.

4. **Scripts without `.py` or `.pyw` extension:**
    * Automatic `--script` option is added if not already present (`--script` or `--gui-script`) in options.
    * Otherwise, `uv` might loop indefinitely.

    * Example: For a `foo` script:

        ```python
            #!/usr/bin/env -S uvr [options] [--]
            # Your Python code here...
        ```

        This will be executed as `uv run [options] --script ...` if `[options]` do not already contain `--script` or `--gui-script`.

    * Or, to be more explicit, you can include the `--script`  flag directly in the shebang:

        ```python
        #!/usr/bin/env -S uvr --script
        ```

        (Use `#!/usr/bin/env uvr` if `-S` is not supported, but then you cannot pass additional options)

    * **Important Exception for Non-Files**: If the identified `script_path` (the argument immediately following options or `--`) does not point to an actual file on disk, `uvr` will not automatically add the `--script` or `--gui-script` option. This behavior ensures `uvr` can correctly pass through commands that are executables within the virtual environment (e.g., `uvr black .`, `uvr pytest`), rather than a Python script file.


5.  **Debug usage:**
    * Example:
        ```bash
        uvr -v [options] [--] run_script.py [script_options]
        uvr -vv [options] [--] run_script.py [script_options]
        ```


## General Rule for Using the `--` Separator
The `--` argument functions as a standard command-line delimiter. It explicitly separates options intended for `uvr` (and its underlying `uv` process) from arguments specifically designated for the Python script being executed.

Arguments appearing before the `--` are processed by `uvr` (`uv`). Arguments appearing after the `--` are passed directly to the invoked Python script.

This explicit separation is crucial for:

* **Preventing Ambiguity**: `uvr` employs a basic heuristic to identify the script path (the first non-hyphenated argument). This can lead to misinterpretation if the script itself accepts options that resemble `uvr/uv` arguments.

* **Ensuring Precise Argument Passing**: By using `--`, users guarantee that all subsequent arguments are correctly delivered to their script, bypassing `uvr's` argument parsing logic.

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

`uvr` is a convenience wrapper around `uv run`. It does not add privileges by itself, but it will execute the script/command you pass to it.

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

