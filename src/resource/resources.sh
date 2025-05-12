#!/bin/bash

# Configuration
QRC_FILE="resources.qrc"
PY_SCRIPT="generate_qrc.py"
RC_OUTPUT="resources_rc.py"

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Python is not found in PATH"
    exit 1
fi

# Check if PySide6 is available
if ! command -v pyside6-rcc &> /dev/null; then
    echo "PySide6 tools are not found in PATH"
    exit 1
fi

echo "Generating $QRC_FILE..."
python "$PY_SCRIPT"
if [ $? -ne 0 ]; then
    echo "Failed to generate QRC file"
    exit 1
fi

echo "Compiling $QRC_FILE to $RC_OUTPUT..."
pyside6-rcc "$QRC_FILE" -o "../$RC_OUTPUT"
if [ $? -ne 0 ]; then
    echo "Failed to compile QRC file"
    exit 1
fi

echo "Done!"
echo "Resource file generated: $QRC_FILE"
echo "Python module generated: $RC_OUTPUT"
