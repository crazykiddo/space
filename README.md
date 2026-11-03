## Space
A simple script to get a quick overview of space available on all your local and remote devices.

## Requirements
- python
- ssh

## Install/setup
1. Install python (min. 3.14)
2. Prepare external PCs if needed
3. Adjust space.json with correct information
4. Profit!


### Windows 10/11 client
After reinstalling Windows, PC2 needs its SSH server enabled again. Your script connects to the hostname PC2 on port 22 as HOSTUSER; hosttype does not change how it connects.

On PC2, open PowerShell as Administrator and install/start OpenSSH Server:

```
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Set-Service sshd -StartupType Automatic
Start-Service sshd
```

Make sure inbound SSH is allowed. The installer often creates this rule; enable it if present, or create it if not:

```
$rule = Get-NetFirewallRule -Name OpenSSH-Server-In-TCP -ErrorAction SilentlyContinue
if ($rule) {
    Set-NetFirewallRule -Name OpenSSH-Server-In-TCP -Enabled True
} else {
    New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH SSH Server' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
}
```
Check that PC1 is still a Windows account on PC2 and use its account password, not a Windows Hello PIN. Reinstalling may have changed the account name or password, so update those values in the PC2 entry if needed.

From the computer running this script, test the connection:
```
Test-NetConnection PC2 -Port 22
ssh PC2USER@PC2
```


If PC2 does not resolve, use PC2's IP address for the test and update "hostname" in the script, or configure name resolution so PC2 points to it.

One separate possibility: after SSH connects, the script relies on wmic to read Windows disk space. If that command is unavailable on the reinstalled system, SSH can work while disk reporting fails.

The file includes plaintext passwords. Treat them as exposed and change them, especially if reused elsewhere.

### SSH on client/host

If PC2 was reinstalled, its SSH host key was likely regenerated. First, verify the new fingerprint directly on PC2 in PowerShell:

```
ssh-keygen -lf C:\ProgramData\ssh\ssh_host_ed25519_key.pub
```

Confirm it matches SHA256:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX. If it does, on the computer where you run SSH, remove the old entry and reconnect:

```
ssh-keygen -R PC2
ssh PC2USER@PC2
```

Accept the new key only if the fingerprint shown on reconnect matches the one you verified. ssh-keygen -R updates the relevant entry in known_hosts; you don’t need to edit line 8 manually.