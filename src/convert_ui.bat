@echo off
cls
@REM Echo Tested using Python 3.12 on Windows 11

:Convert
echo Converting UI files to Python
call "venv\Scripts\activate.bat"
for /R .\ui %%i in (*.ui) do pyside6-uic "%%i"  --star-imports -o "%%~ni.py"


