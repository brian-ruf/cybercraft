@REM @echo off
REM https://yash7.medium.com/how-to-turn-your-python-script-into-an-executable-file-d64edb13c2d4
REM https://coderslegacy.com/pyinstaller-virtual-environment-with-venv/
REM 
cls

IF EXIST "venv" GOTO Compile
echo Virtual environment not found. Installing ...
call install_venv.bat

:Compile
call .\venv\Scripts\activate.bat

cd resource
call resources.bat
cd .. 

REM Use --noconsole to hide the console window
REM Use --onefile to create a single executable file
REM Use --clean to remove temporary files
REM Use --log-level INFO to show the log level
REM Use --add-data to include additional files or directories
REM Use --icon to specify the icon for the executable
REM --add-data=support\*:support ^
ECHO Compiling application
pyinstaller --onefile --clean --log-level INFO  ^
            --name=CyberCraft ^
            --console ^
            --icon=resource\img\favicon.ico ^
            cybercraft.py  

:Run    
if ERRORLEVEL 0 (
    cd dist
    cybercraft.exe --portable --debug
    cd ..
)


:End
