#!/usr/bin/env sh
# Repl Installation Script
# Automate the installation and setup of Repl
# Supports direct installation or execution via curl
# Usage:
#   Local:  sh install.sh [--branch=BRANCH_NAME] [--no-color]
#   Remote: curl -L https://github.com/darmado/repl/raw/main/install.sh | sh -s -- [--branch=BRANCH_NAME] [--no-color]
#
# Options:
#   --branch=BRANCH_NAME  Specify which branch to install (default: main)
#   --no-color            Disable colored output


# Global variables
TOOL_NAME="repl"
BRANCH_DEV="dev"
BRANCH_MAIN="main"
BRANCH_TO_INSTALL="$BRANCH_MAIN"  # Default to main branch
USE_COLORS=true  # Default to using colors
REPO_MAIN_URL="https://github.com/darmado/repl.git"
REPO_WIKI_URL="https://github.com/darmado/repl/wiki"
VENV_DIR="venv"
VENV_ACTIVATE_PATH="./venv/bin/activate"
PYTHON_REQ="requirements.txt"
REPL="repl.py"
DIRECTORIES="collections insertion_points config/proxies logs img"
SAMPLE_PROFILE_PATH="insertion_points/sample_profile.json"
DEFAULT_PROXY_PATH="config/proxies/default.json"
ASCII_LOGO_PATH="img/repl_logo_ascii.txt"

# Define basic ASCII color codes
COLOR_RESET="\033[0m"
COLOR_RED="\033[31m"
COLOR_GREEN="\033[32m"
COLOR_YELLOW="\033[33m"
COLOR_BLUE="\033[34m"
COLOR_MAGENTA="\033[35m"
COLOR_CYAN="\033[36m"

# Check if terminal supports colors
supports_colors() {
    if [ "$USE_COLORS" = false ]; then
        return 1  # User explicitly disabled colors
    elif [ -t 1 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
        return 0  # Terminal supports colors
    else
        return 1  # Terminal doesn't support colors
    fi
}

# Define colored symbols (with fallback for terminals that don't support colors)
if supports_colors; then
    SYMBOL_SUCCESS="${COLOR_GREEN}[✓]${COLOR_RESET}"
    SYMBOL_ERROR="${COLOR_RED}[x]${COLOR_RESET}"
    SYMBOL_INFO="${COLOR_BLUE}[+]${COLOR_RESET}"
    SYMBOL_WARNING="${COLOR_YELLOW}[!]${COLOR_RESET}"
    SYMBOL_QUESTION="${COLOR_CYAN}[?]${COLOR_RESET}"
else
    SYMBOL_SUCCESS="[✓]"
    SYMBOL_ERROR="[x]"
    SYMBOL_INFO="[+]"
    SYMBOL_WARNING="[!]"
    SYMBOL_QUESTION="[?]"
fi

# Set up trap to catch errors
trap 'error_exit "An unexpected error occurred. Installation failed."' ERR


# Detect if script is being piped (remote installation)
is_piped() {
    [ ! -t 0 ]
}

# Error handling function
error_exit() {
    echo "$SYMBOL_ERROR $COLOR_RED$1$COLOR_RESET" >&2
    exit 1
}

# Check if a branch exists in the repository
check_branch_exists() {
    local branch="$1"
    if git ls-remote --heads "$REPO_MAIN_URL" "$branch" | grep -q "$branch"; then
        return 0  # Branch exists
    else
        return 1  # Branch doesn't exist
    fi
}

# Parse command line arguments
parse_args() {
    # When script is piped via curl, the first argument is "--"
    # Skip it to properly parse the actual arguments
    if [ "$1" = "--" ]; then
        shift
    fi
    
    for arg in "$@"; do
        case $arg in
            --branch=*)
                BRANCH_TO_INSTALL="${arg#*=}"
                echo "$SYMBOL_INFO Using branch: $BRANCH_TO_INSTALL"
                ;;
            --no-color)
                USE_COLORS=false
                # Redefine symbols without colors
                SYMBOL_SUCCESS="[✓]"
                SYMBOL_ERROR="[x]"
                SYMBOL_INFO="[+]"
                SYMBOL_WARNING="[!]"
                SYMBOL_QUESTION="[?]"
                echo "[+] Colors disabled."
                ;;
            --help)
                echo "Usage: sh install.sh [--branch=BRANCH_NAME] [--no-color]"
                echo "       curl -L https://github.com/darmado/repl/raw/main/install.sh | sh -s -- [--branch=BRANCH_NAME] [--no-color]"
                echo "Options:"
                echo "  --branch=BRANCH_NAME  Specify which branch to install (default: main)"
                echo "  --no-color            Disable colored output"
                echo "  --help                Show this help message"
                exit 0
                ;;
            *)
                echo "$SYMBOL_WARNING Unknown option: $arg"
                echo "Use --help for usage information."
                ;;
        esac
    done
}

# Verify all prerequisites before proceeding with installation
verify_prerequisites() {
    echo "$SYMBOL_INFO Verifying prerequisites..."
    
    # Check if script has execute permissions when run locally
    if [ ! -x "$0" ] && [ ! $(is_piped) ] && [ -t 0 ]; then
        echo "$SYMBOL_WARNING Warning: This script does not have execute permissions."
        echo "$SYMBOL_WARNING Consider running: chmod +x $0"
    fi
    
    # Check if git is installed
    if ! command -v git >/dev/null 2>&1; then
        error_exit "Git is not installed. Please install git and try again."
    fi
    echo "$SYMBOL_SUCCESS Git is installed."
    
    # Check if Python is installed and version is 3.6+
    if ! command -v python3 >/dev/null 2>&1; then
        error_exit "Python 3 is not installed. Please install Python 3.6+ and try again."
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 6 ]); then
        error_exit "Python version must be 3.6 or higher. Current version: $PYTHON_VERSION"
    fi
    echo "$SYMBOL_SUCCESS Python $PYTHON_VERSION is installed."
    
    # Check if pip is available
    if ! command -v pip3 >/dev/null 2>&1 && ! python3 -m pip --version >/dev/null 2>&1; then
        error_exit "pip is not installed. Please install pip and try again."
    fi
    echo "$SYMBOL_SUCCESS pip is installed."
    
    # Check if venv module is available
    if ! python3 -c "import venv" >/dev/null 2>&1; then
        error_exit "Python venv module is not installed. Please install python3-venv and try again."
    fi
    echo "$SYMBOL_SUCCESS Python venv module is available."
    
    # Check for required Python modules
    echo "$SYMBOL_INFO Checking for required Python modules..."
    if ! python3 -c "import urllib3" >/dev/null 2>&1; then
        echo "$SYMBOL_WARNING Warning: urllib3 module is not installed. It will be installed during setup."
    fi
    
    # Check if current directory is writable
    if [ ! -w "$(pwd)" ]; then
        error_exit "Current directory is not writable. Please run from a directory with write permissions."
    fi
    echo "$SYMBOL_SUCCESS Current directory is writable."
    
    # Check internet connectivity by pinging GitHub
    if ! ping -c 1 github.com >/dev/null 2>&1; then
        echo "$SYMBOL_WARNING Warning: Unable to ping github.com. Check your internet connection."
        # Try an alternative check using curl
        if ! curl -s --head https://github.com >/dev/null 2>&1; then
            error_exit "No internet connection detected. Please check your network and try again."
        fi
    fi
    echo "$SYMBOL_SUCCESS Internet connection is available."
    
    # Check disk space (need at least 100MB free)
    if command -v df >/dev/null 2>&1; then
        FREE_SPACE=$(df -k . | awk 'NR==2 {print $4}')
        if [ "$FREE_SPACE" -lt 102400 ]; then  # 100MB in KB
            error_exit "Insufficient disk space. At least 100MB of free space is required."
        fi
        echo "$SYMBOL_SUCCESS Sufficient disk space available."
    fi
    
    echo "$SYMBOL_SUCCESS All prerequisites verified successfully."
}

# Parse command line arguments
parse_args "$@"

verify_prerequisites

echo "$SYMBOL_INFO Installing $TOOL_NAME from branch: $BRANCH_TO_INSTALL..."

# Verify branch exists
echo "$SYMBOL_INFO Verifying branch: $BRANCH_TO_INSTALL..."
if ! check_branch_exists "$BRANCH_TO_INSTALL"; then
    echo "$SYMBOL_ERROR Branch '$BRANCH_TO_INSTALL' does not exist in the repository."
    echo "$SYMBOL_ERROR Available branches:"
    git ls-remote --heads "$REPO_MAIN_URL" | awk -F'/' '{print "    - " $NF}'
    
    echo "$SYMBOL_ERROR Falling back to main branch..."
    BRANCH_TO_INSTALL="$BRANCH_MAIN"
fi

# Set installation directory
INSTALL_DIR="$(pwd)/$TOOL_NAME"

# Clone the repository
echo "$SYMBOL_INFO Cloning repository (branch: $BRANCH_TO_INSTALL)..."
if [ -d "$INSTALL_DIR" ]; then
    echo "$SYMBOL_ERROR Directory '$TOOL_NAME' already exists."
    printf "$SYMBOL_QUESTION Do you want to overwrite it? (y/N): "
    read -r response
    if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
        error_exit "$SYMBOL_ERROR Installation canceled by user."
    fi
    rm -rf "$INSTALL_DIR" || error_exit "$SYMBOL_ERROR Failed to remove existing directory."
fi

if ! git clone -b "$BRANCH_TO_INSTALL" "$REPO_MAIN_URL"; then
    error_exit "$SYMBOL_ERROR Failed to clone repository. Please check your internet connection and try again."
fi

# Change to the repl directory
if ! cd "$TOOL_NAME"; then
    error_exit "$SYMBOL_ERROR Failed to change directory to '$TOOL_NAME'. Installation failed."
fi

# Store the repo path for later use
REPO_PATH="$(pwd)"
echo "$SYMBOL_SUCCESS Successfully changed to repository directory: $REPO_PATH"

# Create virtual environment and install dependencies
echo "$SYMBOL_INFO Setting up virtual environment and installing dependencies..."
if ! python3 -m venv "$VENV_DIR"; then
    error_exit "$SYMBOL_ERROR Failed to create virtual environment. Please ensure python3-venv is installed."
fi

# Make source command compatible with all shells
# Try to detect the current shell and use appropriate command
if [ ! -f "$VENV_ACTIVATE_PATH" ]; then
    error_exit "$SYMBOL_ERROR Virtual environment activation script not found."
fi

# Source/activate the virtual environment based on shell
if [ -n "$BASH_VERSION" ] || [ -n "$ZSH_VERSION" ]; then
    # For bash and zsh
    . "$VENV_ACTIVATE_PATH" || error_exit "$SYMBOL_ERROR Failed to activate virtual environment."
else
    # For sh and others
    . "$VENV_ACTIVATE_PATH" || error_exit "$SYMBOL_ERROR Failed to activate virtual environment."
fi

# Install required packages
if ! pip install --upgrade pip; then
    error_exit "$SYMBOL_ERROR Failed to upgrade pip. Please check your internet connection."
fi

if [ ! -f "$PYTHON_REQ" ]; then
    echo "$SYMBOL_WARNING Warning: $PYTHON_REQ not found. Creating a basic requirements file..."
    cat > "$PYTHON_REQ" << EOF
urllib3>=2.0.0
requests>=2.28.0
colorama>=0.4.4
EOF
    echo "$SYMBOL_SUCCESS Created basic $PYTHON_REQ file with essential dependencies."
fi

if ! pip install -r "$PYTHON_REQ"; then
    error_exit "$SYMBOL_ERROR Failed to install required packages. Please check your internet connection."
fi

# Check for missing directories that should be part of the repository
echo "$SYMBOL_INFO Checking for missing directories..."
MISSING_DIRS=""
for dir in $DIRECTORIES; do
    if [ ! -d "$dir" ]; then
        if [ -z "$MISSING_DIRS" ]; then
            MISSING_DIRS="$dir"
        else
            MISSING_DIRS="$MISSING_DIRS, $dir"
        fi
    fi
done

# Only create directories if any are missing
if [ -n "$MISSING_DIRS" ]; then
    echo "$SYMBOL_ERROR Creating missing directories: $MISSING_DIRS"
    for dir in $DIRECTORIES; do
        if [ ! -d "$dir" ]; then
            if ! mkdir -p "$dir"; then
                error_exit "$SYMBOL_ERROR Failed to create directory '$dir'. Please check permissions."
            fi
            echo "$SYMBOL_SUCCESS Created directory: $dir"
        fi
    done
fi


# Create sample profile file if it doesn't exist
if [ ! -f "$SAMPLE_PROFILE_PATH" ]; then
    echo "$SYMBOL_INFO Creating sample profile file..."
    cat > "$SAMPLE_PROFILE_PATH" << EOF
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
if [ ! -f "$DEFAULT_PROXY_PATH" ]; then
    echo "$SYMBOL_INFO Creating default proxy configuration..."
    cat > "$DEFAULT_PROXY_PATH" << EOF
{
  "proxy_host": "localhost",
  "proxy_port": 8080,
  "verify_ssl": false,
  "verbose": false
}
EOF
fi

# Make the main script executable
echo "$SYMBOL_INFO Making scripts executable..."
if [ -f "$REPL" ]; then
    if ! chmod +x "$REPL"; then
        error_exit "$SYMBOL_ERROR Failed to make $REPL executable. Please check permissions."
    fi
else
    error_exit "$REPL not found. The repository might be incomplete."
fi

# Create a simple activation script
echo "$SYMBOL_INFO Creating activation script..."
cat > "$REPO_PATH/activate" << EOF
#!/usr/bin/env sh
# Simple script to activate the virtual environment

# Get the directory of this script
SCRIPT_DIR="\$(cd "\$(dirname "\$0")" && pwd)"

# Source the virtual environment activation script
. "\$SCRIPT_DIR/$VENV_DIR/bin/activate"

echo "$SYMBOL_SUCCESS Virtual environment activated for $TOOL_NAME."
echo "$SYMBOL_INFO You can now run: python3 $REPL"
EOF

chmod +x "$REPO_PATH/activate"
echo "$SYMBOL_SUCCESS Created activation script: $REPO_PATH/activate"

echo "$SYMBOL_SUCCESS Installation complete!"
echo ""
echo "$SYMBOL_INFO Quick Usage Guide:"
echo "1. Place your Postman collection JSON files in the 'collections' directory"
echo "2. Place your target insertion_points in the 'insertion_points' directory"
echo "3. Configure proxy settings in the 'proxies' directory"
echo ""
echo "For more information, visit: $REPO_WIKI_URL"
echo ""
echo "$SYMBOL_INFO Current status:"
echo "  - Repository installed at: $REPO_PATH"
echo "  - Virtual environment is activated for this session"
echo ""
echo "    For development, you can run: source ./activate"
echo ""

# Run the help command to show usage
echo "$SYMBOL_INFO Showing help information..."
cd "$REPO_PATH" && python3 ./$REPL --banner || {
    echo "$SYMBOL_ERROR Failed to run the help command. This is likely because of a Python module issue."
    echo "$SYMBOL_WARNING To use $TOOL_NAME, try: python3 ./$REPL"
}

# Print final instructions
echo ""
echo "$SYMBOL_SUCCESS Installation complete! You are now in the $TOOL_NAME directory."
echo "$SYMBOL_INFO To use $TOOL_NAME:"
echo "    1. Always activate the virtual environment first: source ./activate"
echo "    2. Then run the tool: python3 ./$REPL [options]"
echo ""
echo "$SYMBOL_INFO For more information, visit: $REPO_WIKI_URL"

# Deactivate the trap before exiting to prevent error messages
trap - ERR

# Stay in the repository directory
# Note: The script will exit in the repository directory since we cd'd there earlier
exit 0
