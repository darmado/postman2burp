#!/bin/bash
# Setup script for creating a Python virtual environment

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment directory if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        echo "Make sure python3-venv is installed."
        echo "On Ubuntu/Debian: sudo apt-get install python3-venv"
        echo "On macOS: pip3 install virtualenv"
        exit 1
    fi
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Ensure pip is up to date
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing packages from requirements.txt..."
    python -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install packages from requirements.txt."
        exit 1
    fi
    echo "All packages from requirements.txt installed successfully."
else
    echo "No requirements.txt found. No packages installed."
fi

echo ""
echo "Setup complete! Virtual environment is ready."
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate the virtual environment when finished:"
echo "  deactivate"
