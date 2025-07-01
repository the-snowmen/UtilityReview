@echo off
cd /d "%~dp0\.."

REM ── Detect Python Executable ────────────────────────────────
set "PY_CMD=python"
where python >nul 2>&1 || (
    echo python.exe not found, trying py.exe...
    set "PY_CMD=py"
)

REM ── Create venv at project root ─────────────────────────────
%PY_CMD% -m venv .venv

REM ── Activate venv ───────────────────────────────────────────
call .venv\Scripts\activate.bat

REM ── Upgrade pip ─────────────────────────────────────────────
%PY_CMD% -m pip install --upgrade pip

REM ── Install dependencies ────────────────────────────────────
if exist "Setup\requirements.txt" (
    %PY_CMD% -m pip install -r "Setup\requirements.txt"
) else (
    echo Setup\requirements.txt not found – skipping
)

echo.
echo Virtual environment ready. To activate later:
echo     .venv\Scripts\activate.bat
pause
