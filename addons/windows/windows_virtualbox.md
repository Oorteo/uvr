

# Install the C++ Build Tools

In PowerShell running as Administrator, install Visual Studio Build Tools first, then the C++ workload:

```
choco install visualstudio2022buildtools -y
choco install visualstudio2022-workload-vctools -y --package-parameters "--includeRecommended"
```

Alternatively, run the installer directly:
`C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe`

After installation, open **Developer PowerShell for VS 2022** (or **Developer Command Prompt**) from the Start menu. The `cl` compiler command is available in that shell.


# OpenSSH Server

A Windows virtual machine in VirtualBox is a convenient way to test native Windows locking behavior. An SSH server is not required to run the tests, but it lets you launch them from the Linux host.

In VirtualBox, set Adapter 1 to **NAT** for internet access and Adapter 2 to **Host-only Adapter** so the Linux host can connect to the VM. Enable DHCP for the host-only network.
In Windows, install Visual Studio Build Tools with the C++ build tools to test against the native Windows C runtime (CRT).
In PowerShell running as Administrator, install and start the built-in OpenSSH Server:

```
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Set-Service sshd -StartupType Automatic
Start-Service sshd
Get-NetFirewallRule -Name OpenSSH-Server-In-TCP
```


# Add an SSH public key

scp ~/.ssh/id_ed25519.pub user@192.168.x.x:~/tmp_key.pub

For a regular Windows user, run these commands in PowerShell to add the key to that user's `authorized_keys` file:

```
if (!(Test-Path "$HOME\.ssh")) { New-Item -ItemType Directory -Force -Path "$HOME\.ssh" }
Get-Content "$HOME\tmp_key.pub" | Add-Content "$HOME\.ssh\authorized_keys"
Remove-Item "$HOME\tmp_key.pub"
```

**If the Windows account belongs to the local Administrators group**, OpenSSH uses a different key file: `C:\ProgramData\ssh\administrators_authorized_keys`. Add the public key to that file instead of the user's `authorized_keys` file. The file must also have appropriate permissions for the Administrators group and `SYSTEM`.

