#!/bin/bash
# Setup script for creating a Python virtual environment for Repl

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

# Install required packages directly
echo "Installing required packages..."
python -m pip install requests urllib3 python-dotenv

# Verify installation
echo "Verifying installation..."
if python -c "import requests, urllib3, dotenv" 2>/dev/null; then
    echo "All required packages are installed successfully."
else
    echo "Error: Failed to import required packages. Please check the installation."
    exit 1
fi

echo ""
echo "Setup complete! Virtual environment is ready."
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run the script with the virtual environment:"
echo "  source venv/bin/activate"
echo "  python repl.py --collection example_postman_collection.json"
echo ""
echo "To deactivate the virtual environment when finished:"
echo "  deactivate"
