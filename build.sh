#!/bin/bash
# build.sh - Compile Postman2Burp into binary executables

# Ensure we're in the project root
cd "$(dirname "$0")"

# Create build directory
mkdir -p build

# Install required packages
pip install pyinstaller

# Build for current platform
echo "Building for $(uname -s)..."
pyinstaller --onefile --clean --name=postman2burp postman2burp.py

# Copy additional files
mkdir -p dist/collections dist/profiles dist/config
cp -r README.md LICENSE dist/

echo "Build complete! Executable is in the dist directory."
echo "Usage: ./dist/postman2burp --collection your_collection.json" 