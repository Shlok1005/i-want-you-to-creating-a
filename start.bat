@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 server.py %*
  exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python server.py %*
  exit /b %ERRORLEVEL%
)

where python3 >nul 2>nul
if %ERRORLEVEL%==0 (
  python3 server.py %*
  exit /b %ERRORLEVEL%
)

echo.
echo Python 3 was not found on this PC.
echo.
echo Install Python from https://www.python.org/downloads/
echo During setup, check "Add python.exe to PATH".
echo Then open a NEW PowerShell window and run:
echo   py server.py
echo.
echo If Windows opens the Microsoft Store for python/python3, disable those
echo App execution aliases:
echo   Settings ^> Apps ^> Advanced app settings ^> App execution aliases
echo.
exit /b 1
