#!/bin/bash
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
echo "Checking for PIP upgrade on system"
${PYTHON_CMD} -m pip install --upgrade pip

if [ ! -d "venv" ]; then
    echo "Creating virtual environment"
    ${PYTHON_CMD} -m venv "venv"
else
    echo "Virtual environment already exists."
fi

echo "continuing"
source venv/bin/activate

echo "Checking for PIP upgrade in virtual environment"
${PYTHON_CMD} -m pip install --upgrade pip

echo "Installing requirements.txt"
${PYTHON_CMD} -m pip install -r requirements.txt

echo "Installing pyinstaller"
${PYTHON_CMD} -m pip install pyinstaller

echo "Upgrading setup tools"
${PYTHON_CMD} -m pip install --upgrade setuptools
