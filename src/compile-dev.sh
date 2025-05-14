#!/bin/bash
# https://yash7.medium.com/how-to-turn-your-python-script-into-an-executable-file-d64edb13c2d4
# https://coderslegacy.com/pyinstaller-virtual-environment-with-venv/

clear

echo "Activating virtual environment"

if [ -d "venv" ]; then
    echo "Virtual environment found."
else
    echo "Virtual environment not found. Installing ..."
    bash install_venv.sh
fi

source venv/bin/activate

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
