#!/bin/bash
# https://yash7.medium.com/how-to-turn-your-python-script-into-an-executable-file-d64edb13c2d4
# https://coderslegacy.com/pyinstaller-virtual-environment-with-venv/

clear
echo "Tested using Python 3.12 on macOS"
echo "Activating virtual environment"
source venv/bin/activate

if [ -d "venv" ]; then
    echo "Virtual environment found."
else
    echo "Virtual environment not found. Installing ..."
    bash install_venv.sh
fi

# Resource compilation
cd resource
bash resources.sh
cd ..

echo "Compiling"
export DEBUG_CC=True
echo "Compiling application"
pyinstaller --onefile --clean --log-level DEBUG \
            --name=CyberCraft \
            --console \
            --icon=resource/img/favicon.ico \
            cybercraft.py

echo "Executing"
if [ $? -eq 0 ]; then
    cd dist
    ./CyberCraft --portable --debug
    cd ..
fi
