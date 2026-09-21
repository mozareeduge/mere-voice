@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set PY=.venv\Scripts\python.exe) else (set PY=python)
%PY% bench\prepare_bench.py
start "" "http://127.0.0.1:8766/"
%PY% bench\serve_bench.py
