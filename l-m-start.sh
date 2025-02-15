#!/bin/bash

VENV_NAME="myenv"
REQUIREMENTS="pip flask requests python-magic"

# Check if the virtual environment folder exists
if [ -d "$VENV_NAME" ]; then
    echo "Virtual environment '$VENV_NAME' already exists. Activating..."
    source "$VENV_NAME/bin/activate"
else
    echo "Creating virtual environment '$VENV_NAME'..."
    python3 -m venv "$VENV_NAME"
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Please ensure Python 3 is installed."
        exit 1
    fi
    echo "Activating virtual environment..."
    source "$VENV_NAME/bin/activate"
    echo "Installing required packages: $REQUIREMENTS..."
    pip install $REQUIREMENTS
    if [ $? -ne 0 ]; then
        echo "Failed to install packages."
        exit 1
    fi
    echo "Virtual environment created and packages installed successfully."
fi

echo "Virtual environment is now active. Use 'deactivate_env.sh' to deactivate."
