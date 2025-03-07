#!/bin/bash
# test_repl.sh - Simple test script for repl.py
# Tests non-interactive argument combinations to verify functionality

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to run a test and check exit code
test_command() {
    local description="$1"
    local command="$2"
    
    echo -e "\n${YELLOW}Testing: ${description}${NC}"
    echo "Command: $command"
    
    # Run the command and capture output
    local output
    output=$(eval "$command" 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}[PASS]${NC} Exit code: $exit_code"
        return 0
    else
        echo -e "${RED}[FAIL]${NC} Exit code: $exit_code"
        echo -e "${RED}Error output:${NC}"
        echo "$output"
        return 1
    fi
}

# Create test collection if needed
setup_test_files() {
    # Create collections directory if it doesn't exist
    if [ ! -d "collections" ]; then
        mkdir -p collections
    fi
    
    # Create a simple test collection
    cat > collections/test_collection.json << EOF
{
    "info": {
        "_postman_id": "test-id",
        "name": "Test Collection",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "Test Request",
            "request": {
                "method": "GET",
                "url": "https://example.com/api/{{endpoint}}",
                "header": [
                    {
                        "key": "Authorization",
                        "value": "Bearer {{token}}"
                    }
                ]
            }
        }
    ]
}
EOF

    # Create insertion points directory if it doesn't exist
    if [ ! -d "insertion_points" ]; then
        mkdir -p insertion_points
    fi
    
    # Create a simple insertion point file
    cat > insertion_points/test_insertion_point.json << EOF
{
    "name": "Test Insertion Point",
    "values": [
        {
            "key": "endpoint",
            "value": "test",
            "type": "default",
            "enabled": true
        },
        {
            "key": "token",
            "value": "test-token",
            "type": "default",
            "enabled": true
        }
    ]
}
EOF
}

# Run tests
run_tests() {
    local failed=0
    
    # Test 1: Help command
    test_command "Help command" "python3 repl.py --help"
    [ $? -ne 0 ] && failed=$((failed+1))
    
    # Test 2: Banner display
    test_command "Banner display" "python3 repl.py --banner"
    [ $? -ne 0 ] && failed=$((failed+1))
    
    # Test 3: URL encoding
    test_command "URL encoding" "python3 repl.py --encode-url 'test string'"
    [ $? -ne 0 ] && failed=$((failed+1))
    
    # Test 4: HTML encoding
    test_command "HTML encoding" "python3 repl.py --encode-html '<script>alert(1)</script>'"
    [ $? -ne 0 ] && failed=$((failed+1))
    
    # Test 5: Extract keys (print mode)
    test_command "Extract keys (print mode)" "python3 repl.py --extract-keys print --collection collections/test_collection.json"
    [ $? -ne 0 ] && failed=$((failed+1))
    
    # Test 6: Collection with insertion point
    test_command "Collection with insertion point" "python3 repl.py --collection collections/test_collection.json --insertion-point insertion_points/test_insertion_point.json --no-verify-ssl"
    [ $? -ne 0 ] && failed=$((failed+1))
    
    return $failed
}

# Main execution
echo -e "${YELLOW}Setting up test files...${NC}"
setup_test_files

echo -e "${YELLOW}Running tests...${NC}"
run_tests
failed=$?

# Print summary
if [ $failed -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}$failed tests failed!${NC}"
    exit 1
fi 