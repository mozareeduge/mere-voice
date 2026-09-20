param([switch]$SkipSetup, [switch]$DevVerify)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not $SkipSetup) {
    & "$Root\scripts\setup.ps1"
}
$Py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
$Args = @("scripts\local_release.py", "--prepare-real", "--export-smoke")
if ($DevVerify) { $Args += "--dev-verify" }
& $Py @Args
if ($LASTEXITCODE -ne 0) { throw "Local finalization did not reach real-voice engineering PASS. See evidence\local\local_release_report.md" }
Write-Host "Real Voice engineering preparation is complete. Run RUN_WORKBENCH.bat and perform the remaining listening/Windows audio gates."
