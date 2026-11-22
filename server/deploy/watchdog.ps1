# Watchdog: keep license server, landing static server and Cloudflare Tunnel alive.
# Launched (hidden) from Startup .bat at logon. No admin rights required.
# Checks every 60s and starts only missing components.

$ErrorActionPreference = 'SilentlyContinue'
$RepoRoot = "D:\Du An Code\vietlott-quant-auto"
$Py = "C:\Python314\python.exe"
$Cf = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
$CfCfg = Join-Path $env:USERPROFILE ".cloudflared\config.yml"

function Test-Port($port) {
  return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

function Start-Proc($file, $argsLine, $workDir) {
  try { Start-Process -FilePath $file -ArgumentList $argsLine -WorkingDirectory $workDir -WindowStyle Hidden | Out-Null } catch {}
}

while ($true) {
  if (-not (Test-Port 8787)) {
    Start-Proc $Py "server\license_server.py serve --host 127.0.0.1 --port 8787" $RepoRoot
  }
  if (-not (Test-Port 8090)) {
    Start-Proc $Py "-m http.server 8090 --bind 127.0.0.1 --directory `"$RepoRoot\landing`"" $RepoRoot
  }
  $cfAlive = Get-CimInstance Win32_Process -Filter "Name='cloudflared.exe'" |
    Where-Object { $_.CommandLine -like "*run aivietlott*" }
  if (-not $cfAlive) {
    Start-Proc $Cf "tunnel --config `"$CfCfg`" run aivietlott" $RepoRoot
  }
  Start-Sleep -Seconds 60
}
