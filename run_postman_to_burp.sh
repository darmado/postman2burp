#!/bin/bash
# Example script to run the Postman2Burp tool with virtual environment

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

# Set variables
COLLECTION_FILE="./real_world_postman_collection.json"
ENVIRONMENT_FILE="./real_world_environment.json"
OUTPUT_FILE="./burp_results.json"

# Check if files exist
if [ ! -f "$COLLECTION_FILE" ]; then
    echo "Error: Collection file not found: $COLLECTION_FILE"
    deactivate
    exit 1
fi

if [ ! -f "$ENVIRONMENT_FILE" ]; then
    echo "Error: Environment file not found: $ENVIRONMENT_FILE"
    deactivate
    exit 1
fi

# Run the script
echo "Running Postman2Burp tool..."
$PYTHON_CMD postman2burp.py \
    --collection "$COLLECTION_FILE" \
    --environment "$ENVIRONMENT_FILE" \
    --output "$OUTPUT_FILE" \
    --verbose

# Check if the script ran successfully
if [ $? -eq 0 ]; then
    echo "Success! All requests have been sent through Burp Suite."
    echo "Results saved to: $OUTPUT_FILE"
    echo ""
    echo "Next steps:"
    echo "1. Check Burp Suite's HTTP history to see all captured requests"
    echo "2. Review the results file for any failed requests"
    echo "3. Configure Burp Suite's scanner to analyze the captured endpoints"
else
    echo "Error: The script encountered an issue. Please check the output above."
fi

# Deactivate virtual environment
deactivate
