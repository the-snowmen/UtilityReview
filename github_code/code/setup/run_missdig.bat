@echo off
setlocal enabledelayedexpansion

REM ──────────────────────────────────────────────────────────────
REM 0) Jump to the repo root (one level above this Setup folder)
cd /d "%~dp0\.."

REM ──────────────────────────────────────────────────────────────
REM 1) Point at changeme.txt in Setup\
set "CFG_PATH=%~dp0changeme.txt"
if not exist "%CFG_PATH%" (
    echo ERROR: Configuration file not found: %CFG_PATH%
    echo Please put changeme.txt in the Setup folder.
    pause
    exit /b 1
)
echo Using config: %CFG_PATH%

REM ──────────────────────────────────────────────────────────────
REM 2) Read key=value pairs from that file
for /f "usebackq tokens=1,* delims==" %%A in ("%CFG_PATH%") do (
    set "rawKey=%%A"
    set "firstChar=!rawKey:~0,1!"
    if NOT "!firstChar!"=="[" if NOT "!firstChar!"=="#" (
        set "key=!rawKey: =!"
        set "rawVal=%%B"
        for /f "tokens=* delims= " %%V in ("!rawVal!") do (
            set "!key!=%%V"
        )
    )
)

REM ──────────────────────────────────────────────────────────────
REM 3) Choose python: prefer .venv, else use PythonExe
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else if defined PythonExe (
    if exist "%PythonExe%" (
        set "PYTHON=%PythonExe%"
    ) else (
        echo ERROR: PythonExe is set to "%PythonExe%", but that file does not exist.
        pause
        exit /b 1
    )
) else (
    echo ERROR: No .venv/python.exe and PythonExe not set!
    pause
    exit /b 1
)

REM ──────────────────────────────────────────────────────────────
REM 4) Ensure UTF-8 mode
set PYTHONUTF8=1

REM ──────────────────────────────────────────────────────────────
REM 5a) Copy the config into the repo root so main.py will pick it up
copy /Y "%CFG_PATH%" "%CD%\changeme.txt" >nul

REM ──────────────────────────────────────────────────────────────
REM 5b) Launch the configured script
if defined ScriptPath (
    echo Launching: %PYTHON% "%ScriptPath%"
    "%PYTHON%" "%ScriptPath%"
) else (
    echo ERROR: ScriptPath not defined in changeme.txt!
    pause
    exit /b 1
)

pause
