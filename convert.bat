@echo off
cd /d "%~dp0"

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PY=py -3"
) else (
  set "PY=python"
)

%PY% --version >nul 2>&1
if not %ERRORLEVEL%==0 (
  echo Python 3 is not installed.
  echo Download it from https://www.python.org/downloads/
  echo During setup, turn on "Add python.exe to PATH", then run this again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Setting up. The first time can take a minute.
  %PY% -m venv .venv
  if not %ERRORLEVEL%==0 (
    echo Setup failed.
    pause
    exit /b 1
  )
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  echo.
)

".venv\Scripts\python.exe" -u -m musicconverter %*
echo.
pause
