#!/bin/bash
# Script to run the Postman2Burp tool with virtual environment

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Setting it up first..."
    ./setup_venv.sh
    if [ $? -ne 0 ]; then
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

while [[ $# -gt 0 ]]; do
    case $1 in
        --collection)
            COLLECTION_FILE="collections/$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT_FILE="environments/$2"
            shift 2
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./run_postman_to_burp.sh --collection COLLECTION_FILE [--environment ENVIRONMENT_FILE] [--verbose]"
            deactivate
            exit 1
            ;;
    esac
done

# Check if collection file is provided
if [ -z "$COLLECTION_FILE" ]; then
    echo "Error: Collection file is required"
    echo "Usage: ./run_postman_to_burp.sh --collection COLLECTION_FILE [--environment ENVIRONMENT_FILE] [--verbose]"
    deactivate
    exit 1
fi

# Check if files exist
if [ ! -f "$COLLECTION_FILE" ]; then
    echo "Error: Collection file not found: $COLLECTION_FILE"
    deactivate
    exit 1
fi

if [ ! -z "$ENVIRONMENT_FILE" ] && [ ! -f "$ENVIRONMENT_FILE" ]; then
    echo "Error: Environment file not found: $ENVIRONMENT_FILE"
    deactivate
    exit 1
fi

# Build command
CMD="$PYTHON_CMD postman2burp.py --collection \"$COLLECTION_FILE\" $VERBOSE"
if [ ! -z "$ENVIRONMENT_FILE" ]; then
    CMD="$CMD --environment \"$ENVIRONMENT_FILE\""
fi

# Run the script
echo "Running Postman2Burp tool..."
eval $CMD

# Check if the script ran successfully
if [ $? -eq 0 ]; then
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
