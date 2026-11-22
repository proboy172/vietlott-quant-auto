# Backup license DB (private). Run manually or via Task Scheduler daily.
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\server\deploy\backup-licenses.ps1
# Optional env: LICENSE_DB_PATH, VIETLOTT_BACKUP_DIR (default: <repo>\backups\licenses)
# Keep the backup directory PRIVATE; never commit it.

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Resolve-Path (Join-Path $ScriptDir '..\..')
$DbPath    = if ($env:LICENSE_DB_PATH) { $env:LICENSE_DB_PATH } else { Join-Path $RepoRoot 'server\licenses.db' }
$BackupDir = if ($env:VIETLOTT_BACKUP_DIR) { $env:VIETLOTT_BACKUP_DIR } else { Join-Path $RepoRoot 'backups\licenses' }
$Keep      = 14

if (-not (Test-Path $DbPath)) { throw "DB not found: $DbPath" }
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$stamp = (Get-Date).ToString('yyyyMMdd-HHmmss')
$dest  = Join-Path $BackupDir $stamp
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$files = @($DbPath, "$DbPath-wal", "$DbPath-shm") | Where-Object { Test-Path $_ }
foreach ($f in $files) { Copy-Item -LiteralPath $f -Destination (Join-Path $dest (Split-Path -Leaf $f)) -Force }
$hashes = Get-ChildItem $dest -File | Get-FileHash -Algorithm SHA256 | ForEach-Object { "$($_.Hash)  $($_.Path)" }
Set-Content -Path (Join-Path $dest 'SHA256SUMS.txt') -Value $hashes -Encoding utf8

Write-Host "[backup] $($files.Count) file(s) -> $dest"

# Retention: keep newest $Keep folders
Get-ChildItem $BackupDir -Directory | Sort-Object Name -Descending |
  Select-Object -Skip $Keep | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force; Write-Host "[backup] removed old: $($_.Name)" }
