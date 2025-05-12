#!/bin/bash
clear

echo "Tested using Python 3.12 on macOS"
echo "Checking for PIP upgrade on system"
python3 -m pip install --upgrade pip

if [ ! -d "venv" ]; then
    echo "Creating virtual environment"
    python3 -m venv "venv"
else
    echo "Virtual environment already exists."
fi

echo "continuing"
source venv/bin/activate

echo "Checking for PIP upgrade in virtual environment"
python -m pip install --upgrade pip

echo "Installing requirements.txt"
python -m pip install -r requirements.txt

echo "Installing pyinstaller"
python -m pip install pyinstaller

echo "Upgrading setup tools"
pip install --upgrade setuptools
