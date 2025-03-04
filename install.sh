#!/bin/bash

# Postman2Burp Installation Script
# This script automates the installation and setup of Postman2Burp

set -e

echo "🚀 Installing Postman2Burp..."

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
git clone https://github.com/darmado/postman2burp.git
cd postman2burp

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
mkdir -p environments
mkdir -p logs

# Create sample environment file if it doesn't exist
if [ ! -f "environments/sample.json" ]; then
    echo "📝 Creating sample environment file..."
    cat > environments/sample.json << EOF
{
  "name": "Sample Environment",
  "values": [
    {
      "key": "base_url",
      "value": "https://api.example.com",
      "enabled": true
    },
    {
      "key": "api_key",
      "value": "your_api_key_here",
      "enabled": true
    }
  ]
}
EOF
fi

# Make scripts executable
echo "🔑 Making scripts executable..."
chmod +x setup_venv.sh

# Create run_postman_to_burp.sh script
echo "📝 Creating run script..."
cat > run_postman_to_burp.sh << EOF
#!/bin/bash
# Script to run the Postman2Burp tool with virtual environment

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Setting it up first..."
    ./setup_venv.sh
    if [ \$? -ne 0 ]; then
        echo "Failed to set up virtual environment. Please check the errors above."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Determine which python command to use
PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo "Error: Neither python nor python3 is available. Please install Python."
        deactivate
        exit 1
    fi
fi

# Parse command line arguments
COLLECTION_FILE=""
ENVIRONMENT_FILE=""
VERBOSE=""

while [[ \$# -gt 0 ]]; do
    case \$1 in
        --collection)
            COLLECTION_FILE="collections/\$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT_FILE="environments/\$2"
            shift 2
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        *)
            echo "Unknown option: \$1"
            echo "Usage: ./run_postman_to_burp.sh --collection COLLECTION_FILE [--environment ENVIRONMENT_FILE] [--verbose]"
            deactivate
            exit 1
            ;;
    esac
done

# Check if collection file is provided
if [ -z "\$COLLECTION_FILE" ]; then
    echo "Error: Collection file is required"
    echo "Usage: ./run_postman_to_burp.sh --collection COLLECTION_FILE [--environment ENVIRONMENT_FILE] [--verbose]"
    deactivate
    exit 1
fi

# Check if files exist
if [ ! -f "\$COLLECTION_FILE" ]; then
    echo "Error: Collection file not found: \$COLLECTION_FILE"
    deactivate
    exit 1
fi

if [ ! -z "\$ENVIRONMENT_FILE" ] && [ ! -f "\$ENVIRONMENT_FILE" ]; then
    echo "Error: Environment file not found: \$ENVIRONMENT_FILE"
    deactivate
    exit 1
fi

# Build command
CMD="\$PYTHON_CMD postman2burp.py --collection \"\$COLLECTION_FILE\" \$VERBOSE"
if [ ! -z "\$ENVIRONMENT_FILE" ]; then
    CMD="\$CMD --environment \"\$ENVIRONMENT_FILE\""
fi

# Run the script
echo "Running Postman2Burp tool..."
eval \$CMD

# Check if the script ran successfully
if [ \$? -eq 0 ]; then
    echo "✅ Success! All requests have been sent through Burp Suite."
    echo "📊 Results saved to logs directory"
    echo ""
    echo "📋 Next steps:"
    echo "1. Check Burp Suite's HTTP history to see all captured requests"
    echo "2. Review the log files for any failed requests"
    echo "3. Configure Burp Suite's scanner to analyze the captured endpoints"
else
    echo "❌ Error: The script encountered an issue. Please check the output above."
fi

# Deactivate virtual environment
deactivate
EOF

# Make the run script executable
chmod +x run_postman_to_burp.sh

echo "✅ Installation complete!"
echo ""
echo "📋 Quick Usage Guide:"
echo "1. Place your Postman collection JSON files in the 'collections' directory"
echo "2. Place your environment files in the 'environments' directory (optional)"
echo "3. Run the tool with: ./run_postman_to_burp.sh --collection \"your_collection.json\" [--environment \"your_environment.json\"] [--verbose]"
echo ""
echo "📚 For more information, visit: https://github.com/darmado/postman2burp/wiki" 