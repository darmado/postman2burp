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

# Check if Burp Suite is running
if ! nc -z localhost 8080 &>/dev/null; then
    echo "Warning: Burp Suite proxy doesn't seem to be running on localhost:8080"
    echo "Please make sure Burp Suite is running and the proxy is configured."
    read -p "Continue anyway? (y/n): " continue_anyway
    if [[ "$continue_anyway" != "y" && "$continue_anyway" != "Y" ]]; then
        echo "Aborted."
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
python postman2burp.py \
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