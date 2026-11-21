@echo off
REM Avvio dai sorgenti, per lo sviluppo. La versione installata si avvia dal menu Start (Create shortcuts.cmd).
cd /d "%~dp0"
if not exist .venv\Scripts\pythonw.exe (
    echo Prima installazione: creo l'ambiente Python...
    python -m venv .venv
    .venv\Scripts\python -m pip install -r requirements.txt
)
start "" .venv\Scripts\pythonw.exe main.py
