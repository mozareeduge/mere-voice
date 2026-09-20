@echo off
setlocal
set ROOT=%~dp0
if not exist "%ROOT%.venv\Scripts\python.exe" (
  echo .venv missing. Run SETUP_ONCE.bat first.
  exit /b 1
)
"%ROOT%.venv\Scripts\python.exe" "%ROOT%scripts\prepare_all.py"
if errorlevel 1 exit /b %errorlevel%
echo Mana/Piper dry assets and processed variants are ready.
