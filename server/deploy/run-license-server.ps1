# Run Vietlott license & delivery server (Windows, for Cloudflare Tunnel / local behind HTTPS proxy).
# Usage (from repo root or this folder):
#   $env:ADMIN_TOKEN = "<strong-random-secret>"
#   powershell -ExecutionPolicy Bypass -File .\server\deploy\run-license-server.ps1
#
# Optional env vars (see server/.env.example): LICENSE_DB_PATH, LICENSE_SERVER_HOST, LICENSE_SERVER_PORT
# Do NOT hardcode secrets here. Do NOT commit .env or licenses.db.

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
Set-Location $RepoRoot

$HostAddr = if ($env:LICENSE_SERVER_HOST) { $env:LICENSE_SERVER_HOST } else { "127.0.0.1" }
$Port = if ($env:LICENSE_SERVER_PORT) { $env:LICENSE_SERVER_PORT } else { "8787" }
$DbPath = if ($env:LICENSE_DB_PATH) { $env:LICENSE_DB_PATH } else { (Join-Path $RepoRoot "server\licenses.db") }

if (-not $env:ADMIN_TOKEN) {
    Write-Warning "ADMIN_TOKEN is not set. Admin API/CLI over HTTP will be unauthorized; set a strong secret for production."
}

Write-Host "[run-license-server] repo=$RepoRoot host=$HostAddr port=$Port db=$DbPath"
Write-Host "[run-license-server] health (local): http://$HostAddr`:$Port/healthz"

# Ensure DB initialized (safe to run repeatedly)
python server\license_server.py init-db --db "$DbPath" | Out-Host

# Serve (foreground). For 24/7 run via Task Scheduler/NSSM and keep machine on.
python server\license_server.py serve --host $HostAddr --port $Port --db "$DbPath"
