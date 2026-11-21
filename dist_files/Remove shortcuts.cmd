@echo off
REM Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
REM SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)
REM
REM Toglie i collegamenti fatti da "Create shortcuts.cmd" (menu Start e desktop). Il programma resta: per toglierlo,
REM cancella poi questa cartella; le impostazioni sono in %USERPROFILE%\.myEasyMP3toIPhone.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0_internal\shortcuts.ps1" -Action Remove %*
echo.
pause
