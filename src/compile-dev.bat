@echo off
REM https://yash7.medium.com/how-to-turn-your-python-script-into-an-executable-file-d64edb13c2d4
REM https://coderslegacy.com/pyinstaller-virtual-environment-with-venv/
REM 
cls
Echo Tested using Python 3.12 on Windows 11
echo Activating virtual environment
call venv\Scripts\activate.bat

IF EXIST "venv" GOTO Compile
echo Virtual environment not found. Installing ...
call install_venv.bat

@REM :Convert
@REM call convert_ui.bat
cd resource
call resources.bat
cd .. 

:Compile
echo Compiling
SET DEBUG_CC=True
ECHO Compiling application
pyinstaller --onefile --clean --log-level DEBUG ^
            --name=CyberCraft ^
            --strip ^
            --exclude-module ^
            --console ^
            --icon=resource\img\favicon.ico ^
            cybercraft.py

:Run
echo Executing
if ERRORLEVEL 0 (
    @REM ren dist\cybercraft.exe CyberCraft.exe
    cd dist
    cybercraft.exe --portable --debug
    cd ..
)


:End
