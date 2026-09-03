# Useful Instructions for Windows

These instructions assume you're using **Chocolatey** as your package manager, **git for Windows**, the **MSYS2** Unix-like subsystem with the **UCRT64** environment, and **uv** for Python package management.

## Quick Navigation

- [Prerequisites](#prerequisites)
- [UCRT64 Environment Setup](#ucrt64-environment-setup)
- [Set Up PATHs](#set-up-paths)
- [Install `make` within MSYS2](#install-make-within-msys2)
- [Creating symlinks in Windows](#creating-symlinks-in-windows)
- [VS Code with the MSYS2 UCRT terminal](#vs-code-with-the-msys2-ucrt-terminal)
- [Periodically Update Subsystems](#periodically-update-subsystems)

---

## Prerequisites

**MSYS2** is a building tool for native Windows applications using GNU tools, replacing previous MSYS, MinGW, and Clang environments.

- **Chocolatey (choco)** - Package manager
    - Installation instructions: [https://community.chocolatey.org/](https://community.chocolatey.org/)

    > **Note:** Always use **Admin PowerShell** to install packages with `choco`.

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

    > **Note:** It's best to avoid the Git client provided by MSYS2 due to its ongoing integration challenges with Windows.

- **MSYS2**
    - Homepage: [https://www.msys2.org/](https://www.msys2.org/)
    - To install: `choco install msys2` (This will install it to `C:\tools\msys64` by default.)
    - To uninstall: `choco uninstall msys2`

    > **Warning:** Be careful when linking or creating a junction to your directories within the MSYS2 subsystem, as uninstalling MSYS2 may recursively delete them.

---

## UCRT64 Environment Setup

- Create a directory `C:\MyScripts` for your Windows scripts.
- Download or copy the following files from the [uvr GitHub repository](https://github.com/Oorteo/uvr) into `C:\MyScripts` (or into a directory of your choice that is on your `PATH`):
    - `addons/windows/msys2/ucrt.bat`
    - `addons/windows/msys2/pw.bat`
    - `addons/windows/msys2/ucrt.reg`
- Apply the registry settings by double-clicking `ucrt.reg` or by running:
    ```cmd
    regedit /s "C:\MyScripts\ucrt.reg"
    ```
- Optionally create a symlink for `ucrt.bat` (or `pw.bat`) so you can keep the originals in the `uvr` repository and only reference them from `C:\MyScripts`.
    - See [Creating symlinks in Windows](#creating-symlinks-in-windows) below.

---

## Set Up PATHs

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

        > **Note:** Be aware that uninstalling MSYS2 will remove any custom configurations in `.bashrc`.

---

## Install `make` within MSYS2

- Activate the **UCRT64** environment by running `ucrt`.
- Check if `UCRT64` is active: `echo $MSYSTEM` should output `UCRT64`.
- Install **`make`** within `msys2` using Pacman:
    - `pacman -S make`

    > **Note:** For better compatibility and security, it's recommended to avoid old or unmaintained Windows versions of make.

---

## Creating symlinks in Windows

A symlink lets you keep the original file in one location (for example, your local `uvr` repository clone) while exposing it from another directory such as `C:\MyScripts`. This way you do not have to copy the file after every update.

#### From PowerShell (as Administrator)

```powershell
New-Item -ItemType SymbolicLink `
    -Path "C:\MyScripts\ucrt.bat" `
    -Target "C:\Users\$env:USERNAME\Documents\uvr_git\addons\windows\msys2\ucrt.bat"
```

Replace the `-Target` path with the actual location of your `uvr` repository clone.

#### From an Admin `CMD` prompt

```cmd
mklink "C:\MyScripts\ucrt.bat" "C:\Users\%USERNAME%\Documents\uvr_git\addons\windows\msys2\ucrt.bat"
```

#### Using Multi Commander

1. Select the source file, for example `uvr_git\addons\windows\msys2\ucrt.bat`.
2. Go to `Tools` -> `File Links` -> `Create Links` -> `Symlink`.
3. Choose `C:\MyScripts` as the destination.

> **Warning:** Be careful when linking or creating junctions inside the MSYS2 subsystem, because uninstalling MSYS2 may recursively delete them.

---

## VS Code with the MSYS2 UCRT terminal

To use the `ucrt.bat` launcher directly from VS Code, add a terminal profile to your user settings.

- Open `C:\Users\%USERNAME%\AppData\Roaming\Code\User\settings.json`.
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

> **Note:** `ucrt.bat` must be on your Windows `PATH` (for example, in `C:\MyScripts`).

---

## Periodically Update Subsystems

- **Chocolatey packages:**
    - Run **Admin PowerShell**.
    - `choco upgrade all -y`

- **MSYS2 packages:**
    - Run `ucrt`.
    - `pacman -Syu`

    > **Note:** The order `-Syu` is important for proper synchronization and upgrade.

- **`uv` tools:**
    - Run `cmd.exe`.
    - `uv tool upgrade --all`

---
