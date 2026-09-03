# Usefull Instructions for Windows

These instructions assume you're using **Chocolatey** as your package manager, **git for Windows**, the **MSYS2** Unix-like subsystem with the **UCRT64** environment, and **uv** for Python package management.

**MSYS2** is a building tool for native Windows applications using GNU tools, replacing previous MSYS, MinGW, and Clang environments.

- **Chocolatey (choco)** - Package manager
    - Use homepage how to install: [https://community.chocolatey.org/](https://community.chocolatey.org/)

    - **Note:** Always use **Admin PowerShell** to install packages with `choco`.

- **Multi Commander**
    - Homepage: [https://multicommander.com/](https://multicommander.com/)
    - To install: `choco install multicommander`

- **VS Code**
    - Homepage: [https://code.visualstudio.com](https://code.visualstudio.com)
    - To install: `choco install vscode`

- **uv** - Python package and project manager
    - Homepage: [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv)
    - To install: `choco install uv`

- **uvr** - Run scripts in a virtual environment
    - Homepage: [https://github.com/Oorteo/uvr](https://github.com/Oorteo/uvr)
    - To install: `uv tool install uvr`

- **Git**
    - Homepage: [https://gitforwindows.org](https://gitforwindows.org)
    - To install: `choco install git`
    - **Note:** It's best to avoid the Git client provided by MSYS2 due to its ongoing integration challenges with Windows.

- **MSYS2**
    - Homepage: [https://www.msys2.org/](https://www.msys2.org/)
    - To install: `choco install msys2` (This will install it to `C:\tools\msys64` by default.)
    - To uninstall: `choco uninstall msys2`
        - **Be careful when linking or creating a junction to your directories within the MSYS2 subsystem**, as uninstalling MSYS2 may recursively delete them.

---

### UCRT64 Environment Setup

- Create a directory `C:\MyScripts` for your Windows scripts.
- **Create a symlink** from `C:\Users\%USERNAME%\Documents\inkstitch_git\my_dir\bin\msys2\ucrt.bat` to `C:\MyScripts\ucrt.bat`.
    - From an **Admin CMD** prompt: `mklink "C:\MyScripts\ucrt.bat" "C:\Users\%USERNAME%\Documents\inkstitch_git\my_dir\bin\msys2\ucrt.bat"`
    - Alternatively, use **Multi Commander**: `Tools` -\> `File Links` -\> `Create Links` -\> `Symlink`.
- Update your registry using the file `bin/msys2/ucrt.reg` from your Ink/Stitch directory.
- Optionally you can also symlink `pw.bat` as alias for **Powershell**.
- Optionally enable UCRT64 bash in VS Code editor ( see `bin/msys2/vscode_setting.md`)

---

### Set Up PATHs

- **Windows PATH** (for `cmd.exe` and `PowerShell`):
    - Edit your system's `PATH` environment variable to include these directories:
        - `C:\MyScripts` (for `ucrt.bat`, `pw.bat`)
        - `C:\ProgramData\chocolatey\bin` (for `choco`, `uv`)
        - `C:\Program Files\Git\cmd` (for `git`)
        - `C:\Users\%USERNAME%\.local\bin` (for `uvr`)
        - `C:\tools\msys64\usr\bin` (for `bash`, `make`, etc.)

- **MSYS2 Subsystem PATH** (`C:\tools\msys64\home\$USER\.bashrc`):
    - Add these lines to your `.bashrc` file:
        ```bash
        export PATH="/c/Program Files/Git/cmd:$PATH"
        export PATH="/c/ProgramData/chocolatey/bin:$PATH"
        export PATH="/c/Users/$USER/.local/bin:$PATH"
        ```
        **Note:** Be aware that uninstalling MSYS2 will remove any custom configurations in bashrc.

---

### Install `make` within MSYS2

- Activate the **UCRT64** environment by running `ucrt`.
- Check if `UCRT64` is active: `echo $MSYSTEM` should output `UCRT64`.
- Install **`make`** within `msys2` using Pacman:
    - `pacman -S make`
- **Note:** For better compatibility and security, it's recommended to avoid old or unmaintained Windows versions of make.

---

### VS Code with the MSYS2 UCRT terminal

- `C:\Users\%USERNAME%\AppData\Roaming\Code\User\settings.json`
- Add the following configuration:

```json
{
    "terminal.integrated.profiles.windows": {
        "MSYS2 UCRT": {
            "path": "ucrt.bat"
        }
    }
}
```

---

### Periodically Update Subsystems

- **Chocolatey packages:**
    - Run **Admin PowerShell**.
    - `choco upgrade all -y`

- **MSYS2 packages:**
    - Run `ucrt`.
    - `pacman -Syu` (**Note:** The order `-Syu` is important for proper synchronization and upgrade.)

- **`uv` tools:**
    - Run `cmd.exe`.
    - `uv tool upgrade --all`

---
