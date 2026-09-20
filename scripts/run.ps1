$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$Py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
$env:VOICE_PORT = if ($env:VOICE_PORT) { $env:VOICE_PORT } else { "8765" }
$proc = Start-Process -FilePath $Py -ArgumentList "app.py" -WorkingDirectory $Root -PassThru -NoNewWindow
try {
  Start-Sleep -Milliseconds 700
  Start-Process "http://127.0.0.1:$env:VOICE_PORT/"
  Write-Host "Voice Temporal Workbench running at http://127.0.0.1:$env:VOICE_PORT/"
  Write-Host "Close this window or press Ctrl+C to stop."
  Wait-Process -Id $proc.Id
} finally {
  if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }
}
