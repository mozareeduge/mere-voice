@echo off
if not exist ".venv-pocket\Scripts\python.exe" (echo Pocket environment missing. Run the drop-in installer first.& exit /b 2)
.venv-pocket\Scripts\python.exe scripts\prepare_pocket.py
