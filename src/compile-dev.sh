#!/bin/bash
# https://yash7.medium.com/how-to-turn-your-python-script-into-an-executable-file-d64edb13c2d4
# https://coderslegacy.com/pyinstaller-virtual-environment-with-venv/

clear

# Function to determine the correct Python command
get_python_cmd() {
    # Check if python is Python 3.12+
    if command -v python &>/dev/null; then
        PYTHON_VERSION=$(python --version 2>&1)
        if [[ $PYTHON_VERSION =~ Python\ 3\.([0-9]+) ]] && [ "${BASH_REMATCH[1]}" -ge "12" ]; then
            echo "python"
            return 0
        fi
    fi
    
    # Check if python3 is Python 3.12+
    if command -v python3 &>/dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        if [[ $PYTHON_VERSION =~ Python\ 3\.([0-9]+) ]] && [ "${BASH_REMATCH[1]}" -ge "12" ]; then
            echo "python3"
            return 0
        fi
    fi
    
    # Neither python nor python3 is 3.12+
    echo "none"
    return 1
}

# Get the correct Python command
PYTHON_CMD=$(get_python_cmd)
if [ "$PYTHON_CMD" == "none" ]; then
    echo "Error: Python 3.12 or newer is required but not found."
    echo "Please install Python 3.12 or newer and try again."
    exit 1
fi

echo "Using Python command: $PYTHON_CMD ($(${PYTHON_CMD} --version 2>&1))"
echo "Tested using Python 3.12 on macOS"
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
