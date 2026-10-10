@echo off
title hunter3eye
cd /d "%~dp0"
echo ==============================================
echo  hunter3eye
echo ==============================================
echo folder: %CD%
echo.
where py >nul 2>nul
if errorlevel 1 goto nopy
echo [*] python:
py --version
echo.
echo [*] launching hunter3eye ...
py run.py
echo ==============================================
echo hunter3eye exited. press any key to close.
pause
goto end
:nopy
echo [!] python not found. install python 3.11+ from python.org
pause
:end
