#!/bin/bash
clear

export DEBUG=False

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

echo "Running application"
source venv/bin/activate
python cybercraft.py %@
