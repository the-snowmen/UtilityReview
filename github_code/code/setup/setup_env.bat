@echo off
cd /d "%~dp0\.."

REM 1) Create venv at project root
python -m venv .venv

REM 2) Activate
call .venv\Scripts\activate.bat

REM 3) Upgrade pip
python -m pip install --upgrade pip

REM 4) Install dependencies
if exist "Setup\requirements.txt" (
    pip install -r "Setup\requirements.txt"
) else (
    echo Setup\requirements.txt not found – skipping
)

echo.
echo Virtual environment ready. To activate later:
echo     .venv\Scripts\activate.bat
pause
