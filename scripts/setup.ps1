param([switch]$SkipModel)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Resolve-SupportedPython {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($v in @("3.13","3.12","3.11","3.10")) {
            & py "-$v" -c "import sys; raise SystemExit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) { return @{Exe="py"; Args=@("-$v")} }
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python -c "import sys; raise SystemExit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)"
        if ($LASTEXITCODE -eq 0) { return @{Exe="python"; Args=@()} }
    }
    throw "Python 3.10–3.13 is required for the verified Piper + Pedalboard setup. Install one of those versions and rerun SETUP_ONCE.bat."
}

$Resolved = Resolve-SupportedPython
$Py = $Resolved.Exe
$PyArgs = $Resolved.Args
Write-Host "Using $Py $($PyArgs -join ' ')"
if (-not (Test-Path ".venv")) { & $Py @PyArgs -m venv .venv }
$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
& $VenvPy -m pip install --upgrade pip
& $VenvPy -m pip install -r requirements.txt
if (-not $SkipModel) { & $VenvPy scripts\fetch_model.py }
Write-Host "Setup complete. Run: .\RUN_WORKBENCH.bat"
