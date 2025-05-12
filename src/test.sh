#!/bin/bash
clear

echo "Clearing Logs"
rm -f appdata/logs/*.log

export DEBUG=True

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

echo "Running application in portable mode with debug enabled"
source venv/bin/activate
python cybercraft.py --debug --portable %@
