@echo off
setlocal
cd /d "%~dp0"
set PY=python
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe
%PY% scripts\local_release.py --export-smoke
if errorlevel 1 pause
