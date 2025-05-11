@echo off
cls
@REM Echo Tested using Python 3.12 on Windows 11

echo Clearning Logs
del logs\*.log

SET DEBUG=True
IF EXIST "venv" GOTO Convert
echo Virtual environment not found. Installing ...
call install_venv.bat

:Convert
@REM call convert_ui.bat
cd resource
call resources.bat
cd .. 

:Run
ECHO Running application in portable mode with debug enabled
call "venv\Scripts\activate.bat"
python cybercraft.py --debug --portable

:End

