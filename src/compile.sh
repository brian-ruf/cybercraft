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

if [ -d "venv" ]; then
    echo "Virtual environment found."
else
    echo "Virtual environment not found. Installing ..."
    bash install_venv.sh
fi

source venv/bin/activate

cd resource
bash resources.sh
cd ..

# Use --noconsole to hide the console window
# Use --onefile to create a single executable file
# Use --clean to remove temporary files
# Use --log-level INFO to show the log level
# Use --add-data to include additional files or directories
# Use --icon to specify the icon for the executable
# --add-data=support/*:support \
echo "Compiling application"
pyinstaller --onefile --clean --log-level INFO \
            --name=CyberCraft \
            --console \
            --icon=resource/img/favicon.ico \
            cybercraft.py

if [ $? -eq 0 ]; then
    echo "Compilation successful."
    echo "Executable file created in the dist directory."
    echo "You can run the application by executing the following command:"
    echo "./dist/CyberCraft"
else
    echo "Compilation failed."
    exit 1
fi
