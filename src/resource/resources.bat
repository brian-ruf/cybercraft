@echo off
setlocal

:: Configuration
set QRC_FILE=resources.qrc
set PY_SCRIPT=generate_qrc.py
set RC_OUTPUT=resources_rc.py

:: Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not found in PATH
    exit /b 1
)

:: Check if PySide6 is available
where pyside6-rcc >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo PySide6 tools are not found in PATH
    exit /b 1
)

echo Generating %QRC_FILE%...
python %PY_SCRIPT%
if %ERRORLEVEL% neq 0 (
    echo Failed to generate QRC file
    exit /b 1
)

echo Compiling %QRC_FILE% to %RC_OUTPUT%...
pyside6-rcc %QRC_FILE% -o ../%RC_OUTPUT%
if %ERRORLEVEL% neq 0 (
    echo Failed to compile QRC file
    exit /b 1
)

echo Done!
echo Resource file generated: %QRC_FILE%
echo Python module generated: %RC_OUTPUT%

endlocal
