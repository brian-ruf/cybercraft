@echo off
cls
@REM Echo Tested using Python 3.12 on Windows 11


SET DEBUG=False
IF EXIST "venv" GOTO Run
echo Virtual environment not found. Installing ...
call install_venv.bat



:Run
ECHO Running application
call "venv\Scripts\activate.bat"
python metaschema_parser.py %*
:End

