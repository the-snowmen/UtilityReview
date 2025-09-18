@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ──────────────────────────────────────────────────────────────
REM 0) Jump to the repo root (one level above this Setup folder)
cd /d "%~dp0\.."

REM ──────────────────────────────────────────────────────────────
REM 1) Point at config.json in Setup\  (txt -> json swap, minimal change)
set "CFG_PATH=%~dp0config.json"
if not exist "%CFG_PATH%" (
    echo ERROR: Configuration file not found: %CFG_PATH%
    echo Please put config.json in the Setup folder.
    pause
    exit /b 1
)
echo Using config: %CFG_PATH%

REM ──────────────────────────────────────────────────────────────
REM 2) Read needed values from JSON (replaces the old changeme.txt key=value loop)
REM    We only extract the two things the launcher needs:
REM      - PATHS.PythonExe  -> %PYTHON% and %PYTHONEXE% (both, to be safe)
REM      - PATHS.ScriptPath -> %ScriptPath%
REM    (PowerShell property names are case-insensitive.)
for /f "usebackq delims=" %%A in (`
  powershell -NoProfile -Command ^
    "$cfg = Get-Content -Raw '%CFG_PATH%' | ConvertFrom-Json;" ^
    "$py  = $cfg.PATHS.PythonExe; if(-not $py -or $py -eq ''){ $py = 'python' };" ^
    "$sp  = $cfg.PATHS.ScriptPath; if(-not $sp -or $sp -eq ''){ $sp = 'main.py' };" ^
    "[Console]::WriteLine('PYTHON=' + $py);" ^
    "[Console]::WriteLine('PYTHONEXE=' + $py);" ^
    "[Console]::WriteLine('ScriptPath=' + $sp);"
`) do (
  for /f "tokens=1,* delims==" %%K in ("%%A") do (
    set "%%K=%%L"
  )
)

REM strip any accidental quotes coming from JSON so paths with spaces still work
set "PYTHON=%PYTHON:"=%"
set "PYTHONEXE=%PYTHONEXE:"=%"
set "ScriptPath=%ScriptPath:"=%"

REM ──────────────────────────────────────────────────────────────
REM 3) Launch the configured script (unchanged behavior)
echo Launching: "%PYTHON%" "%ScriptPath%"
"%PYTHON%" "%ScriptPath%"
set "EC=%ERRORLEVEL%"

if not "%EC%"=="0" (
  echo.
  echo The script exited with errorlevel %EC%.
)

echo.
pause
