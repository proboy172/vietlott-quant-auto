# Quick health check for all public endpoints used by the product.
# Usage: powershell -ExecutionPolicy Bypass -File .\server\deploy\health-check.ps1
# Optional: -Json to print JSON (for monitoring).

param([switch]$Json)

$ErrorActionPreference = 'Continue'
$results = @()

function Check-Url($name, $url, $expect) {
  try {
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
    $ok = ($r.StatusCode -eq 200) -and (-not $expect -or $r.Content -match $expect)
    $script:results += [pscustomobject]@{ name=$name; url=$url; ok=$ok; status=$r.StatusCode; detail=($r.Content.Substring(0,[Math]::Min(80,$r.Content.Length)) -replace '\s+',' ') }
  } catch {
    $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
    $script:results += [pscustomobject]@{ name=$name; url=$url; ok=$false; status=$code; detail=$_.Exception.Message }
  }
}

Check-Url 'license-local'   'http://127.0.0.1:8787/healthz'        '"ok"\s*:\s*true'
Check-Url 'license-public'  'https://aivietlott.jbai.vn/healthz'   '"ok"\s*:\s*true'
Check-Url 'landing-public'  'https://landing.jbai.vn/'             'Vietlott Auto Flow'
Check-Url 'landing-local'   'http://127.0.0.1:8090/index.html'     'Vietlott Auto Flow'

if ($Json) {
  $results | ConvertTo-Json -Depth 4
} else {
  $results | Format-Table -AutoSize | Out-String | Write-Host
}

$failed = @($results | Where-Object { -not $_.ok })
if ($failed.Count) {
  Write-Host "FAIL: $($failed.Count)/$($results.Count) checks failed. If all fail, restart tasks: Start-ScheduledTask -TaskName VietlottLicenseServer,VietlottCloudflaredTunnel; or run the Startup .bat."
  exit 1
}
Write-Host "OK: all $($results.Count) checks passed."
exit 0
