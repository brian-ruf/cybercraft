#!/bin/bash
# https://yash7.medium.com/how-to-turn-your-python-script-into-an-executable-file-d64edb13c2d4
# https://coderslegacy.com/pyinstaller-virtual-environment-with-venv/

clear

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
            --strip \
            --exclude-module \
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
