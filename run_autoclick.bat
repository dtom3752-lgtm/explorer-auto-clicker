@echo off
cd /d "%~dp0"
title Explorer Auto-Click

where python >nul 2>nul
if %errorlevel%==0 (set PY=python) else (
    where py >nul 2>nul
    if %errorlevel%==0 (set PY=py) else (
        echo Python is not installed.
        echo Download it from https://www.python.org/downloads/
        echo and tick "Add Python to PATH" during setup, then run this again.
        pause
        exit /b 1
    )
)

echo Installing requirements (first run only)...
%PY% -m pip install --quiet pywinauto psutil

echo.
echo Starting. Leave this window open. Press Ctrl+C to stop.
echo.
%PY% explorer_autoclick.py
pause
