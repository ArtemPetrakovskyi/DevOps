param([Parameter(Mandatory = $true)][string]$Url)
# Двічі на секунду опитує застосунок і друкує код відповіді, версію та ім'я пода.
# Запускайте в окремому терміналі під час rolling update.
# Використання:  .\scripts\watch-availability.ps1 http://127.0.0.1:PORT
while ($true) {
  try {
    $r = Invoke-WebRequest -Uri "$Url/info" -UseBasicParsing -TimeoutSec 2
    $msg = "[HTTP $($r.StatusCode)] $($r.Content.Trim())"
  } catch {
    $msg = "[FAILED] $($_.Exception.Message)"
  }
  Write-Host "$(Get-Date -Format HH:mm:ss) $msg"
  Start-Sleep -Milliseconds 500
}
