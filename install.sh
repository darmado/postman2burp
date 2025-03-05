#!/usr/bin/env sh
# Repl Installation Script
# Automate the installation and setup of Repl
# Supports direct installation or execution via curl
# 
#

# Error handling function
error_exit() {
    echo "[x] Error: $1" >&2
    exit 1
}

# Set up trap to catch errors
trap 'error_exit "An unexpected error occurred. Installation failed."' ERR

# Banner
echo "[+] Installing Repl..."

# Check if script has execute permissions
if [ ! -x "$0" ] && [ -t 0 ]; then
    echo "[!] Warning: This script does not have execute permissions."
    echo "[!] Consider running: chmod +x $0"
fi

# Check for required tools
# Check if git is installed
if ! command -v git >/dev/null 2>&1; then
    error_exit "[x] Git is not installed. Please install git and try again."
fi

# Check if Python is installed
if ! command -v python3 >/dev/null 2>&1; then
    error_exit "[x] Python 3 is not installed. Please install Python 3.6+ and try again."
fi

# Check if pip is available
if ! command -v pip3 >/dev/null 2>&1 && ! python3 -m pip --version >/dev/null 2>&1; then
    error_exit "[x] pip is not installed. Please install pip and try again."
fi

# Check if current directory is writable
if [ ! -w "$(pwd)" ]; then
    error_exit "[x] Current directory is not writable. Please run from a directory with write permissions."
fi
# Set installation directory
INSTALL_DIR="$(pwd)/repl"

# Clone the repository
echo "[+] Cloning repository..."
if [ -d "$INSTALL_DIR" ]; then
    echo "[!] Directory 'repl' already exists."
    printf "[?] Do you want to overwrite it? (y/N): "
    read -r response
    if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
        error_exit "[x] Installation canceled by user."
    fi
    rm -rf "$INSTALL_DIR" || error_exit "[x] Failed to remove existing directory."
fi

if ! git clone https://github.com/darmado/repl.git; then
    error_exit "[x] Failed to clone repository. Please check your internet connection and try again."
fi

# Change to the repl directory
if ! cd repl; then
    error_exit "[x] Failed to change directory to 'repl'. Installation failed."
fi

# Store the repo path for later use
REPO_PATH="$(pwd)"
echo "[+] Successfully changed to repository directory: $REPO_PATH"

# Create virtual environment and install dependencies
echo "[+] Setting up virtual environment and installing dependencies..."
if ! python3 -m venv venv; then
    error_exit "[x] Failed to create virtual environment. Please ensure python3-venv is installed."
fi

# Make source command compatible with all shells
# Try to detect the current shell and use appropriate command
ACTIVATE_SCRIPT="./venv/bin/activate"
if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    error_exit "[x] Virtual environment activation script not found."
fi

# Source/activate the virtual environment based on shell
if [ -n "$BASH_VERSION" ] || [ -n "$ZSH_VERSION" ]; then
    # For bash and zsh
    . "$ACTIVATE_SCRIPT" || error_exit "[x] Failed to activate virtual environment."
else
    # For sh and others
    . "$ACTIVATE_SCRIPT" || error_exit "[x] Failed to activate virtual environment."
fi

# Install required packages
if ! pip install --upgrade pip; then
    error_exit "[x] Failed to upgrade pip. Please check your internet connection."
fi

if [ ! -f "requirements.txt" ]; then
    error_exit "requirements.txt not found. The repository might be incomplete."
fi

if ! pip install -r requirements.txt; then
    error_exit "[x] Failed to install required packages. Please check your internet connection."
fi

# Create necessary directories
echo "\U0001F4C1 Creating necessary directories..."
DIRECTORIES="collections profiles proxies logs"
for dir in $DIRECTORIES; do
    if [ -d "$dir" ]; then
        echo "Directory '$dir' already exists."
    else
        if ! mkdir -p "$dir"; then
            error_exit "[x] Failed to create directory '$dir'. Please check permissions."
        fi
    fi
done

# Create sample profile file if it doesn't exist
if [ ! -f "profiles/sample_profile.json" ]; then
    echo "[+] Creating sample profile file..."
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
    echo "[+] Creating default proxy configuration..."
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
echo "Making scripts executable..."
if [ -f "repl.py" ]; then
    if ! chmod +x repl.py; then
        error_exit "[x] Failed to make repl.py executable. Please check permissions."
    fi
else
    error_exit "repl.py not found. The repository might be incomplete."
fi

echo "[+] Installation complete!"
echo ""
echo "[+] Quick Usage Guide:"
echo "1. Place your Postman collection JSON files in the 'collections' directory"
echo "2. Place your target profiles in the 'profiles' directory"
echo "3. Configure proxy settings in the 'proxies' directory"
echo ""
echo "For more information, visit: https://github.com/darmado/repl/wiki"
echo ""
echo "[+] Current status:"
echo "  - Repository installed at: $REPO_PATH"
echo "  - Virtual environment is activated for this session"
echo ""
echo "[+] You can now run repl directly with:"
echo "  ./repl.py [options]"
echo ""
echo "[+] For future sessions, activate the virtual environment from the repository directory:"
echo "  cd $REPO_PATH"
echo "  source venv/bin/activate  # For bash/zsh"
echo "  . venv/bin/activate       # For sh"
echo ""
echo "[+] To test if the installation was successful, run:"
echo "  ./repl.py --help"
echo ""

# Create a convenience script for activating the environment
cat > "$REPO_PATH/activate_repl.sh" << EOF
#!/usr/bin/env sh
# Convenience script to activate the Repl environment
cd "$REPO_PATH" && . venv/bin/activate
echo "[+] Repl environment activated. You can now run ./repl.py"
EOF

chmod +x "$REPO_PATH/activate_repl.sh"
echo "[+] Created convenience script: $REPO_PATH/activate_repl.sh"
echo "    In the future, you can run: source $REPO_PATH/activate_repl.sh"
echo ""
trap - ERR
exit 0
