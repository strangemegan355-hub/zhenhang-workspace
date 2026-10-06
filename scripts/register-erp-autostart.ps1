# Add ShengTai ERP to current user's Windows Startup folder (no admin required).

$ErrorActionPreference = "Stop"

# Derived from this script's own location, as start-erp.ps1 does: a hardcoded checkout path makes the
# script unusable anywhere else, and it would fail its own guard with "Missing script".
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Script = Join-Path $Root "scripts\start-erp.ps1"
$StartupDir = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "ShengTai ERP.lnk"

if (-not (Test-Path $Script)) {
    Write-Error "Missing script: $Script"
    exit 1
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Script`""
$shortcut.WorkingDirectory = $Root
$shortcut.Description = "Auto-start ShengTai ERP (http://localhost:3000)"
$shortcut.Save()

Write-Host "Added startup shortcut:"
Write-Host "  $ShortcutPath"
Write-Host "ERP will start automatically after each Windows logon."
