@echo off
REM Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
REM SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)
REM
REM Mette myEasyMP3toIPhone nel menu Start e, se vuoi, sul desktop; prima sblocca i file di questa cartella (Windows marca
REM quelli di uno zip scaricato da internet). Dopo aver spostato questa cartella, eseguilo di nuovo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0_internal\shortcuts.ps1" -Action Create %*
echo.
pause
