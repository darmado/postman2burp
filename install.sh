#!/bin/bash

# Repl Installation Script
# This script automates the installation and setup of Repl

set -e

echo "🚀 Installing Repl..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git and try again."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.6+ and try again."
    exit 1
fi

# Clone the repository
echo "📦 Cloning repository..."
git clone https://github.com/darmado/repl.git
cd repl

# Create virtual environment and install dependencies
echo "🔧 Setting up virtual environment and installing dependencies..."
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p collections
mkdir -p profiles
mkdir -p proxies
mkdir -p logs

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
echo "🔑 Making scripts executable..."
chmod +x repl.py

echo "✅ Installation complete!"
echo ""
echo "📋 Quick Usage Guide:"
echo "1. Place your Postman collection JSON files in the 'collections' directory"
echo "2. Place your target profiles in the 'profiles' directory"
echo "3. Configure proxy settings in the 'proxies' directory"
echo ""
echo "📚 For more information, visit: https://github.com/darmado/repl/wiki" 