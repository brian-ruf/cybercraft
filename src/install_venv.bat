@echo off
cls

Echo Tested using Python 3.12 on Windows 11
@REM REM Set-ExecutionPolicy Unrestricted -Scope Process
@REM REM winget install -e --id Python.Python.3.12
ECHO Checking for PIP upgrade on system
python.exe -m pip install --upgrade pip
IF NOT EXIST "venv" (
    ECHO Creating virtual environment
    python -m venv "venv"
) ELSE (
    ECHO Virtual envirionment already exists.
)
echo continuing
call "venv\Scripts\activate.bat"
ECHO Checking for PIP upgrade in virtual environment
python.exe -m pip install --upgrade pip
ECHO Installing requirements.txt
python -m pip install -r requirements.txt

@REM ECHO Installing pyinstaller
python -m pip install pyinstaller

@REM ECHO Upgrading setup tools
pip install --upgrade setuptools

@REM REM python -m pip install json2html python-dotenv requests markupsafe psutil 

