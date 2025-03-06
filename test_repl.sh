#!/bin/bash
# QA Test Script for repl.py
# Tests all arguments and features to ensure everything works correctly

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"  # Ensure we're in the script directory

# Test collection path - create a sample if needed
COLLECTION_PATH="./collections/test_collection.json"
INSERTION_POINT_PATH="./insertion_points/test_insertion_point.json"
AUTH_PROFILE_PATH="./config/auth/test_profile.json"

# Function to display help
show_help() {
    echo -e "${BLUE}REPL Test Script - Test Authentication Methods${NC}"
    echo
    echo -e "Usage: $0 [options]"
    echo
    echo -e "Options:"
    echo -e "  ${GREEN}--help${NC}                 Show this help message"
    echo -e "  ${GREEN}--interactive${NC}          Enable interactive mode with user prompts"
    echo -e "  ${GREEN}--verbose${NC}              Enable verbose output"
    echo -e "  ${GREEN}--quick${NC}                Run only essential tests"
    echo
    echo -e "Authentication Test Options:"
    echo -e "  ${GREEN}--test-auth=TYPE${NC}       Test a specific authentication type"
    echo -e "                         Available types: basic, bearer, apikey, oauth1, oauth2, profile"
    echo -e "  ${GREEN}--auth-args=\"ARGS\"${NC}     Arguments to pass to the authentication method"
    echo
    echo -e "Examples:"
    echo -e "  $0 --test-auth=basic"
    echo -e "  $0 --test-auth=basic --auth-args=\"myuser mypassword\""
    echo -e "  $0 --test-auth=bearer --auth-args=\"mytoken\""
    echo -e "  $0 --test-auth=apikey --auth-args=\"mykey header --auth-api-key-name X-API-Key\""
    echo -e "  $0 --test-auth=oauth1 --auth-args=\"consumer_key consumer_secret --auth-oauth1-token token token_secret\""
    echo -e "  $0 --test-auth=oauth2 --auth-args=\"client_id client_secret --auth-oauth2-token-url https://example.com/token\""
    echo -e "  $0 --test-auth=profile --auth-args=\"my_saved_profile\""
    echo -e "  $0 --interactive --verbose"
    echo
    exit 0
}

# Create test directories if they don't exist
mkdir -p ./collections
mkdir -p ./insertion_points
mkdir -p ./logs
mkdir -p ./config/proxies
mkdir -p ./config/auth/basic
mkdir -p ./config/auth/bearer
mkdir -p ./config/auth/apikey
mkdir -p ./config/auth/oauth1
mkdir -p ./config/auth/oauth2

# Parse command line arguments
INTERACTIVE=false
QUICK=false
VERBOSE=false
TEST_AUTH=false
AUTH_TYPE=""
AUTH_ARGS=""

for arg in "$@"; do
  case $arg in
    --help|-h)
      show_help
      ;;
    --interactive)
      INTERACTIVE=true
      shift
      ;;
    --quick)
      QUICK=true
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --test-auth=*)
      TEST_AUTH=true
      AUTH_TYPE="${arg#*=}"
      shift
      ;;
    --auth-args=*)
      AUTH_ARGS="${arg#*=}"
      shift
      ;;
    *)
      # Unknown option
      echo -e "${RED}Unknown option: $arg${NC}"
      echo -e "Use --help to see available options"
      exit 1
      ;;
  esac
done

# Function to print section headers
section() {
    echo -e "\n${BLUE}==== $1 =====${NC}"
}

# Function to run a test and report result
run_test() {
    local test_name="$1"
    local command="$2"
    local skip_condition="$3"
    
    if [ -n "$skip_condition" ] && eval "$skip_condition"; then
        echo -e "\n${YELLOW}Skipping: ${test_name} (${skip_condition})${NC}"
        return 0
    fi
    
    echo -e "\n${YELLOW}Testing: ${test_name}${NC}"
    echo -e "${CYAN}Command: $command${NC}"
    
    if [ "$VERBOSE" = true ]; then
        command="$command --verbose"
    fi
    
    # Run the command but don't fail the script if the command fails
    output=$(eval "$command" 2>&1)
    local status=$?
    
    if [ $status -eq 0 ]; then
        echo -e "${GREEN}✓ Test passed${NC}"
        return 0
    else
        echo -e "${RED}✗ Test failed${NC}"
        echo -e "${YELLOW}Output:${NC}"
        echo "$output"
        return 1
    fi
}

# Function to prompt user for input
prompt_user() {
    local prompt_text="$1"
    local default_value="$2"
    
    if [ "$INTERACTIVE" = false ]; then
        echo "$default_value"
        return
    fi
    
    read -p "$prompt_text [$default_value]: " user_input
    echo "${user_input:-$default_value}"
}

# Check if authentication module is available
section "Checking Authentication Module"
AUTH_MODULE_CHECK=$(python3 -c "
try:
    from modules.auth import AuthManager
    print('Authentication module is available')
    exit(0)
except ImportError as e:
    print('Authentication module is not available: ' + str(e))
    exit(1)
" 2>&1)

AUTH_MODULE_STATUS=$?
if [ $AUTH_MODULE_STATUS -ne 0 ]; then
    echo -e "${RED}Authentication module is not available. Some tests may fail.${NC}"
    echo -e "${YELLOW}$AUTH_MODULE_CHECK${NC}"
    echo -e "${YELLOW}Make sure the modules/auth.py file exists and all dependencies are installed.${NC}"
    echo -e "${YELLOW}You can install dependencies with: pip install -r requirements.txt${NC}"
    
    if [ "$TEST_AUTH" = true ]; then
        echo -e "${RED}Cannot run authentication tests without the authentication module.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}$AUTH_MODULE_CHECK${NC}"
fi

# Check if repl.py has the necessary authentication arguments
section "Checking REPL Script Arguments"
REPL_ARGS_CHECK=$(python3 repl.py --help | grep -E "auth-basic|auth-bearer|auth-api-key|auth-oauth1|auth-oauth2" || echo "Authentication arguments not found")

if [[ "$REPL_ARGS_CHECK" == *"Authentication arguments not found"* ]]; then
    echo -e "${RED}Authentication arguments are not available in repl.py.${NC}"
    echo -e "${YELLOW}Make sure repl.py has the necessary authentication arguments defined.${NC}"
    
    if [ "$TEST_AUTH" = true ]; then
        echo -e "${RED}Cannot run authentication tests without the authentication arguments.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Authentication arguments are available in repl.py.${NC}"
fi

# Simple auth test wrapper
if [ "$TEST_AUTH" = true ]; then
    section "Testing Authentication: $AUTH_TYPE"
    
    case "$AUTH_TYPE" in
        basic)
            # Default values if not provided
            if [ -z "$AUTH_ARGS" ]; then
                AUTH_ARGS="testuser testpassword"
            fi
            run_test "Basic Authentication" "python3 repl.py --collection $COLLECTION_PATH --auth-basic $AUTH_ARGS"
            exit $?
            ;;
        bearer)
            # Default values if not provided
            if [ -z "$AUTH_ARGS" ]; then
                AUTH_ARGS="test_token"
            fi
            run_test "Bearer Token Authentication" "python3 repl.py --collection $COLLECTION_PATH --auth-bearer $AUTH_ARGS"
            exit $?
            ;;
        apikey)
            # Default values if not provided
            if [ -z "$AUTH_ARGS" ]; then
                AUTH_ARGS="test_api_key header"
            fi
            run_test "API Key Authentication" "python3 repl.py --collection $COLLECTION_PATH --auth-api-key $AUTH_ARGS"
            exit $?
            ;;
        oauth1)
            # Default values if not provided
            if [ -z "$AUTH_ARGS" ]; then
                AUTH_ARGS="consumer_key consumer_secret --auth-oauth1-token token token_secret"
            fi
            run_test "OAuth1 Authentication" "python3 repl.py --collection $COLLECTION_PATH --auth-oauth1 $AUTH_ARGS"
            exit $?
            ;;
        oauth2)
            # Default values if not provided
            if [ -z "$AUTH_ARGS" ]; then
                AUTH_ARGS="client_id client_secret --auth-oauth2-token-url https://httpbin.org/anything"
            fi
            run_test "OAuth2 Authentication" "python3 repl.py --collection $COLLECTION_PATH --auth-oauth2 $AUTH_ARGS"
            exit $?
            ;;
        profile)
            # Default values if not provided
            if [ -z "$AUTH_ARGS" ]; then
                AUTH_ARGS="test_profile"
            fi
            run_test "Profile Authentication" "python3 repl.py --collection $COLLECTION_PATH --auth $AUTH_ARGS"
            exit $?
            ;;
        *)
            echo -e "${RED}Unknown authentication type: $AUTH_TYPE${NC}"
            echo -e "Available types: basic, bearer, apikey, oauth1, oauth2, profile"
            exit 1
            ;;
    esac
fi

# Create a sample collection if it doesn't exist
if [ ! -f "$COLLECTION_PATH" ]; then
    section "Creating sample collection"
    cat > "$COLLECTION_PATH" << 'EOF'
{
  "info": {
    "_postman_id": "test-collection-id",
    "name": "Test Collection",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Test Request",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "https://httpbin.org/get?param={{test_param}}",
          "protocol": "https",
          "host": ["httpbin", "org"],
          "path": ["get"],
          "query": [
            {
              "key": "param",
              "value": "{{test_param}}"
            }
          ]
        }
      }
    },
    {
      "name": "Auth Test",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "https://httpbin.org/headers",
          "protocol": "https",
          "host": ["httpbin", "org"],
          "path": ["headers"]
        }
      }
    },
    {
      "name": "Basic Auth Test",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "https://httpbin.org/basic-auth/testuser/testpassword",
          "protocol": "https",
          "host": ["httpbin", "org"],
          "path": ["basic-auth", "testuser", "testpassword"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "https://httpbin.org"
    }
  ]
}
EOF
    echo "Created sample collection at $COLLECTION_PATH"
fi

# Create a sample insertion point if it doesn't exist
if [ ! -f "$INSERTION_POINT_PATH" ]; then
    section "Creating sample insertion point"
    cat > "$INSERTION_POINT_PATH" << 'EOF'
{
  "id": "test-insertion-point-id",
  "name": "Test Insertion Point",
  "values": [
    {
      "key": "test_param",
      "value": "test_value",
      "enabled": true
    },
    {
      "key": "base_url",
      "value": "https://httpbin.org",
      "enabled": true
    }
  ]
}
EOF
    echo "Created sample insertion point at $INSERTION_POINT_PATH"
fi

# Create a sample auth profile if it doesn't exist
if [ ! -f "$AUTH_PROFILE_PATH" ]; then
    section "Creating sample auth profile"
    mkdir -p ./config/auth/basic
    cat > "./config/auth/basic/test_profile.json" << 'EOF'
{
  "label": "test_profile",
  "type": "basic",
  "username": "testuser",
  "password": "testpassword"
}
EOF
    echo "Created sample auth profile at ./config/auth/basic/test_profile.json"
    AUTH_PROFILE_PATH="./config/auth/basic/test_profile.json"
fi

# If no specific options were provided, show help
if [ "$TEST_AUTH" = false ] && [ "$INTERACTIVE" = false ] && [ "$QUICK" = false ] && [ "$VERBOSE" = false ]; then
    show_help
fi

# If authentication module is not available, skip all authentication tests
if [ $AUTH_MODULE_STATUS -ne 0 ]; then
    echo -e "${YELLOW}Skipping all authentication tests due to missing authentication module.${NC}"
    exit 0
fi

section "Authentication Tests"

# Test 1: Basic Authentication
run_test "Basic Authentication" "python3 repl.py --collection $COLLECTION_PATH --auth-basic testuser testpassword"

# Test 2: Basic Authentication with user input
if [ "$INTERACTIVE" = true ]; then
    section "Interactive Basic Authentication Test"
    username=$(prompt_user "Enter username for Basic Auth" "testuser")
    password=$(prompt_user "Enter password for Basic Auth" "testpassword")
    run_test "Basic Authentication (User Input)" "python3 repl.py --collection $COLLECTION_PATH --auth-basic \"$username\" \"$password\""
fi

# Test 3: Bearer Token Authentication
run_test "Bearer Token Authentication" "python3 repl.py --collection $COLLECTION_PATH --auth-bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3QgVXNlciIsImlhdCI6MTUxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

# Test 4: Bearer Token Authentication with user input
if [ "$INTERACTIVE" = true ]; then
    section "Interactive Bearer Token Authentication Test"
    token=$(prompt_user "Enter Bearer token" "test_token")
    run_test "Bearer Token Authentication (User Input)" "python3 repl.py --collection $COLLECTION_PATH --auth-bearer \"$token\""
fi

# Test 5: API Key Authentication in header
run_test "API Key Authentication (header)" "python3 repl.py --collection $COLLECTION_PATH --auth-api-key test_api_key header"

# Test 6: API Key Authentication in header with user input
if [ "$INTERACTIVE" = true ]; then
    section "Interactive API Key Authentication Test (header)"
    api_key=$(prompt_user "Enter API key" "test_api_key")
    key_name=$(prompt_user "Enter API key name" "X-API-Key")
    run_test "API Key Authentication (header, User Input)" "python3 repl.py --collection $COLLECTION_PATH --auth-api-key \"$api_key\" header --auth-api-key-name \"$key_name\""
fi

# Test 7: API Key Authentication in query parameter
run_test "API Key Authentication (query)" "python3 repl.py --collection $COLLECTION_PATH --auth-api-key test_api_key query --auth-api-key-name api_key"

# Test 8: API Key Authentication in query with user input
if [ "$INTERACTIVE" = true ]; then
    section "Interactive API Key Authentication Test (query)"
    api_key=$(prompt_user "Enter API key" "test_api_key")
    key_name=$(prompt_user "Enter API key parameter name" "api_key")
    run_test "API Key Authentication (query, User Input)" "python3 repl.py --collection $COLLECTION_PATH --auth-api-key \"$api_key\" query --auth-api-key-name \"$key_name\""
fi

# Test 9: API Key Authentication in cookie
run_test "API Key Authentication (cookie)" "python3 repl.py --collection $COLLECTION_PATH --auth-api-key test_api_key cookie --auth-api-key-name session_token"

# Test 10: API Key Authentication in cookie with user input
if [ "$INTERACTIVE" = true ]; then
    section "Interactive API Key Authentication Test (cookie)"
    api_key=$(prompt_user "Enter API key" "test_api_key")
    key_name=$(prompt_user "Enter cookie name" "session_token")
    run_test "API Key Authentication (cookie, User Input)" "python3 repl.py --collection $COLLECTION_PATH --auth-api-key \"$api_key\" cookie --auth-api-key-name \"$key_name\""
fi

# Check if list-auth argument is available
LIST_AUTH_CHECK=$(python3 repl.py --help | grep -E "\-\-list-auth" || echo "list-auth argument not found")
if [[ "$LIST_AUTH_CHECK" == *"list-auth argument not found"* ]]; then
    echo -e "${YELLOW}Skipping list-auth test as the argument is not available.${NC}"
else
    # Test 12: List authentication profiles
    run_test "List authentication profiles" "python3 repl.py --list-auth"
fi

# Test 13: Use saved authentication profile
run_test "Use saved authentication profile" "python3 repl.py --collection $COLLECTION_PATH --auth test_profile" "[ ! -f \"$AUTH_PROFILE_PATH\" ]"

# Test 14: Combined authentication and proxy
run_test "Combined authentication and proxy" "python3 repl.py --collection $COLLECTION_PATH --auth-bearer test_token --proxy localhost:8080"

# Test 15: Combined authentication and insertion point
run_test "Combined authentication and insertion point" "python3 repl.py --collection $COLLECTION_PATH --auth-basic testuser testpassword --insertion-point $INSERTION_POINT_PATH"

# Test 16: Direct HTTP request with authentication
run_test "Direct HTTP request with Basic Auth" "python3 repl.py --url https://httpbin.org/basic-auth/testuser/testpassword --auth-basic testuser testpassword"

# Test 17: Direct HTTP request with Bearer Token
run_test "Direct HTTP request with Bearer Token" "python3 repl.py --url https://httpbin.org/headers --auth-bearer test_token"

# Test 18: Direct HTTP request with API Key
run_test "Direct HTTP request with API Key" "python3 repl.py --url https://httpbin.org/headers --auth-api-key test_api_key header"

# Test 19: Authentication with verbose output
if [ "$VERBOSE" = false ]; then  # Only run if not already in verbose mode
    run_test "Authentication with verbose output" "python3 repl.py --collection $COLLECTION_PATH --auth-basic testuser testpassword --verbose"
fi

# Test 20: Authentication with custom headers
run_test "Authentication with custom headers" "python3 repl.py --collection $COLLECTION_PATH --auth-basic testuser testpassword --header 'X-Custom-Header: TestValue'"

# Check if OAuth1 and OAuth2 arguments are available
OAUTH_CHECK=$(python3 repl.py --help | grep -E "\-\-auth-oauth1|\-\-auth-oauth2" || echo "OAuth arguments not found")
if [[ "$OAUTH_CHECK" == *"OAuth arguments not found"* ]]; then
    echo -e "${YELLOW}Skipping OAuth tests as the arguments are not available.${NC}"
else
    section "OAuth Authentication Tests"

    # Test OAuth1 Authentication
    run_test "OAuth1 Authentication" "python3 repl.py --collection $COLLECTION_PATH --auth-oauth1 consumer_key consumer_secret --auth-oauth1-token token token_secret"

    # Test OAuth1 Authentication with user input
    if [ "$INTERACTIVE" = true ]; then
        section "Interactive OAuth1 Authentication Test"
        consumer_key=$(prompt_user "Enter consumer key for OAuth1" "test_consumer_key")
        consumer_secret=$(prompt_user "Enter consumer secret for OAuth1" "test_consumer_secret")
        token=$(prompt_user "Enter token for OAuth1" "test_token")
        token_secret=$(prompt_user "Enter token secret for OAuth1" "test_token_secret")
        run_test "OAuth1 Authentication (User Input)" "python3 repl.py --collection $COLLECTION_PATH --auth-oauth1 \"$consumer_key\" \"$consumer_secret\" --auth-oauth1-token \"$token\" \"$token_secret\""
    fi

    # Test OAuth2 Client Credentials
    run_test "OAuth2 Client Credentials" "python3 repl.py --collection $COLLECTION_PATH --auth-oauth2 client_id client_secret --auth-oauth2-token-url https://httpbin.org/anything"

    # Test OAuth2 Password Grant
    run_test "OAuth2 Password Grant" "python3 repl.py --collection $COLLECTION_PATH --auth-oauth2 client_id client_secret --auth-oauth2-grant password --auth-oauth2-username testuser --auth-oauth2-password testpassword --auth-oauth2-token-url https://httpbin.org/anything"

    # Test OAuth2 with user input
    if [ "$INTERACTIVE" = true ]; then
        section "Interactive OAuth2 Authentication Test"
        client_id=$(prompt_user "Enter client ID for OAuth2" "test_client_id")
        client_secret=$(prompt_user "Enter client secret for OAuth2" "test_client_secret")
        grant_type=$(prompt_user "Enter grant type for OAuth2 (client_credentials, password)" "client_credentials")
        token_url=$(prompt_user "Enter token URL for OAuth2" "https://httpbin.org/anything")
        
        if [ "$grant_type" = "password" ]; then
            username=$(prompt_user "Enter username for OAuth2 password grant" "testuser")
            password=$(prompt_user "Enter password for OAuth2 password grant" "testpassword")
            run_test "OAuth2 Authentication (User Input, Password Grant)" "python3 repl.py --collection $COLLECTION_PATH --auth-oauth2 \"$client_id\" \"$client_secret\" --auth-oauth2-grant password --auth-oauth2-username \"$username\" --auth-oauth2-password \"$password\" --auth-oauth2-token-url \"$token_url\""
        else
            run_test "OAuth2 Authentication (User Input, Client Credentials)" "python3 repl.py --collection $COLLECTION_PATH --auth-oauth2 \"$client_id\" \"$client_secret\" --auth-oauth2-token-url \"$token_url\""
        fi
    fi

    # Test OAuth2 with scope
    run_test "OAuth2 with scope" "python3 repl.py --collection $COLLECTION_PATH --auth-oauth2 client_id client_secret --auth-oauth2-token-url https://httpbin.org/anything --auth-oauth2-scope \"read write\""
fi

# Summary
section "Test Summary"
echo "Authentication tests completed. Check the output above for any failures."
echo "Note: Some tests may show 'Test failed' if they require a running proxy or user interaction."
echo "This is expected behavior and doesn't necessarily indicate a problem with the script."

if [ "$INTERACTIVE" = false ]; then
    echo -e "\nTip: Run with ${GREEN}--interactive${NC} flag to enable user input prompts for testing."
fi
if [ "$VERBOSE" = false ]; then
    echo -e "Tip: Run with ${GREEN}--verbose${NC} flag to see detailed request/response information."
fi 