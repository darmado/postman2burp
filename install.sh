#!/usr/bin/env sh
# Repl Installation Script
# Automate the installation and setup of Repl

# Error handling function
error_exit() {
    echo "❌ Error: $1" >&2
    exit 1
}

# Set up trap to catch errors
trap 'error_exit "An unexpected error occurred. Installation failed."' ERR

# Banner
echo "\U0001F680 Installing Repl..."

# Check if script has execute permissions
if [ ! -x "$0" ] && [ -t 0 ]; then
    echo "⚠️  Warning: This script does not have execute permissions."
    echo "   Consider running: chmod +x $0"
fi

# Check for required tools
# Check if git is installed
if ! command -v git >/dev/null 2>&1; then
    error_exit "Git is not installed. Please install git and try again."
fi

# Check if Python is installed
if ! command -v python3 >/dev/null 2>&1; then
    error_exit "Python 3 is not installed. Please install Python 3.6+ and try again."
fi

# Check if pip is available
if ! command -v pip3 >/dev/null 2>&1 && ! python3 -m pip --version >/dev/null 2>&1; then
    error_exit "pip is not installed. Please install pip and try again."
fi

# Check if current directory is writable
if [ ! -w "$(pwd)" ]; then
    error_exit "Current directory is not writable. Please run from a directory with write permissions."
fi
# Set installation directory
INSTALL_DIR="$(pwd)/repl"

# Clone the repository
echo "\U0001F4E6 Cloning repository..."
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Directory 'repl' already exists."
    printf "Do you want to overwrite it? (y/N): "
    read -r response
    if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
        error_exit "Installation canceled by user."
    fi
    rm -rf "$INSTALL_DIR" || error_exit "Failed to remove existing directory."
fi

if ! git clone https://github.com/darmado/repl.git; then
    error_exit "Failed to clone repository. Please check your internet connection and try again."
fi

# Change to the repl directory
if ! cd repl; then
    error_exit "Failed to change directory to 'repl'. Installation failed."
fi

# Create virtual environment and install dependencies
echo "\U0001F527 Setting up virtual environment and installing dependencies..."
if ! python3 -m venv venv; then
    error_exit "Failed to create virtual environment. Please ensure python3-venv is installed."
fi

# Make source command compatible with all shells
# Try to detect the current shell and use appropriate command
ACTIVATE_SCRIPT="./venv/bin/activate"
if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    error_exit "Virtual environment activation script not found."
fi

# Source/activate the virtual environment based on shell
if [ -n "$BASH_VERSION" ] || [ -n "$ZSH_VERSION" ]; then
    # For bash and zsh
    . "$ACTIVATE_SCRIPT" || error_exit "Failed to activate virtual environment."
else
    # For sh and others
    . "$ACTIVATE_SCRIPT" || error_exit "Failed to activate virtual environment."
fi

# Install required packages
if ! pip install --upgrade pip; then
    error_exit "Failed to upgrade pip. Please check your internet connection."
fi

if [ ! -f "requirements.txt" ]; then
    error_exit "requirements.txt not found. The repository might be incomplete."
fi

if ! pip install -r requirements.txt; then
    error_exit "Failed to install required packages. Please check your internet connection."
fi

# Create necessary directories
echo "\U0001F4C1 Creating necessary directories..."
DIRECTORIES="collections profiles proxies logs"
for dir in $DIRECTORIES; do
    if [ -d "$dir" ]; then
        echo "Directory '$dir' already exists."
    else
        if ! mkdir -p "$dir"; then
            error_exit "Failed to create directory '$dir'. Please check permissions."
        fi
    fi
done

# Create sample profile file if it doesn't exist
if [ ! -f "profiles/sample_profile.json" ]; then
    echo "📝 Creating sample profile file..."
    cat > profiles/sample_profile.json << EOF
{
  "name": "Sample Profile",
  "values": [
    {
      "key": "base_url",
      "value": "https://api.example.com",
      "enabled": true,
      "description": "Base URL for the API"
    },
    {
      "key": "api_key",
      "value": "your_api_key_here",
      "enabled": true,
      "description": "API key for authentication"
    }
  ]
}
EOF
fi

# Create sample proxy configuration if it doesn't exist
if [ ! -f "proxies/default.json" ]; then
    echo "📝 Creating default proxy configuration..."
    cat > proxies/default.json << EOF
{
  "proxy_host": "localhost",
  "proxy_port": 8080,
  "verify_ssl": false,
  "verbose": false
}
EOF
fi

# Make the main script executable
echo "\U0001F511 Making scripts executable..."
if [ -f "repl.py" ]; then
    if ! chmod +x repl.py; then
        error_exit "Failed to make repl.py executable. Please check permissions."
    fi
else
    error_exit "repl.py not found. The repository might be incomplete."
fi

echo "✅ Installation complete!"
echo ""
echo "📋 Quick Usage Guide:"
echo "1. Place your Postman collection JSON files in the 'collections' directory"
echo "2. Place your target profiles in the 'profiles' directory"
echo "3. Configure proxy settings in the 'proxies' directory"
echo ""
echo "\U0001F4DA For more information, visit: https://github.com/darmado/repl/wiki"
echo ""
echo "To start using Repl, activate the virtual environment:"
echo "  - For bash/zsh: source venv/bin/activate"
echo "  - For sh: . venv/bin/activate"
echo ""
# Reset trap before exiting successfully
trap - ERR
exit 0
