# EXAMPLE: Register a Windows Scheduled Task to run the license server at startup (24/7, Option A).
# REVIEW and edit paths/token handling before use. Run in an elevated PowerShell if required.
# Do NOT store real ADMIN_TOKEN in this file or commit secrets. Prefer setting a machine/user env var securely.
#
# After running, verify:
#   - Task runs:  Get-ScheduledTask -TaskName "VietlottLicenseServer"
#   - Local health: http://127.0.0.1:8787/healthz
#   - Tunnel up:    https://aivietlott.jbai.vn/healthz (when cloudflared service/tunnel is running)
#
# Also ensure cloudflared tunnel runs as a service/task (see docs/DEPLOY_AIVIETLOTT_CLOUDFLARE_TUNNEL.md).

$TaskName   = "VietlottLicenseServer"
$RepoRoot   = "D:\Du An Code\vietlott-quant-auto"
$PythonExe  = "C:\Python314\python.exe"  # adjust to your python path (`where.exe python`)
$ListenHost = "127.0.0.1"
$ListenPort = "8787"
$DbPath     = "$RepoRoot\server\licenses.db"

# IMPORTANT: set ADMIN_TOKEN securely (e.g. system/user env var) instead of embedding it here.
# $env:ADMIN_TOKEN must be available to the task's runtime if you rely on it.

$Arguments = "server\license_server.py serve --host $ListenHost --port $ListenPort --db `"$DbPath`""
$Action    = New-ScheduledTaskAction -Execute $PythonExe -Argument $Arguments -WorkingDirectory $RepoRoot
$Trigger   = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel LeastPrivilege
$Settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force

Write-Host "Registered task '$TaskName'. Ensure ADMIN_TOKEN is set for the task context and cloudflared is running."
