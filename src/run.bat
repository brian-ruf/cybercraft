@echo off
cls
@REM Echo Tested using Python 3.12 on Windows 11


SET DEBUG=False
IF EXIST "venv" GOTO Resource
echo Virtual environment not found. Installing ...
call install_venv.bat

:Resource
cd resource
call resources.bat
cd .. 

:Run
ECHO Running application
call "venv\Scripts\activate.bat"
python cybercraft.py %*
:End

