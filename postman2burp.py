#!/usr/bin/env python3
"""
Postman2Burp - Loads a Postman collection and sends requests through Burp Suite proxy.

Postman2Burp is a tool that reads a Postman collection JSON file and sends all the requests
through Burp Suite proxy. 

Usage:
    Basic Usage:
        python postman2burp.py --collection <collection.json>
    
    Environment Variables:
        python postman2burp.py --collection <collection.json> --target-profile <environment.json>
    
    Proxy Settings:
        python postman2burp.py --collection <collection.json> --proxy-host <host> --proxy-port <port>
    
    Log Options:
        python postman2burp.py --collection <collection.json> --log --verbose
    
    Proxy & Behavior Configuration:
        python postman2burp.py --collection <collection.json> --save-proxy
        
    Extract Variables:
        # Interactive mode - prompts for values for each variable
        python postman2burp.py --collection <collection.json> --extract-keys
        
        # Print all variables in the collection
        python postman2burp.py --collection <collection.json> --extract-keys print
        
        # Generate a template environment file with all variables
        python postman2burp.py --collection <collection.json> --extract-keys <output_file.json>

Requirements:
    - requests
    - argparse
    - json
    - urllib3
"""

import argparse
import json
import logging
import os
import sys
import urllib3
import socket
import re
from typing import Dict, List, Optional, Any, Tuple, Set, Union
import requests
import time
import datetime
import uuid
import urllib.parse

#  the select_collection_file function

# Disable SSL warnings when using proxy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
VERSION = "1.0.0"
DEFAULT_CONFIG = {
    "proxy_host": "localhost",
    "proxy_port": 8080,
    "verify_ssl": False,
    "verbose": False
}

# Path to collections directory
COLLECTIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "collections")

# Path to proxy file
PROXIES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxies")
PROXY_FILE_PATH = os.path.join(PROXIES_DIR, "default.json")

# Path to variables templates directory
VARIABLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")

# Always check common proxies first
# Common proxy proxys to check
COMMON_PROXIES = [
    # Burp Suite default
    {"host": "localhost", "port": 8080},
    {"host": "127.0.0.1", "port": 8080},
    # OWASP ZAP default
    {"host": "localhost", "port": 8090},
    {"host": "127.0.0.1", "port": 8090},
    # Mitmproxy default
    {"host": "localhost", "port": 8081},
    {"host": "127.0.0.1", "port": 8081},
    # Charles Proxy default
    {"host": "localhost", "port": 8888},
    {"host": "127.0.0.1", "port": 8888},
    # Fiddler default
    {"host": "localhost", "port": 8888},
    {"host": "127.0.0.1", "port": 8888}
]

# Path to proxy file
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxies")
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "default.json")

# Path to variables templates directory
VARIABLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")

def validate_json_file(file_path: str) -> Tuple[bool, Optional[Dict]]:
    """
    Validate a JSON file to ensure it's properly formatted.
    Returns a tuple of (is_valid, parsed_json).
    If the file is invalid, parsed_json will be None.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Tuple[bool, Optional[Dict]]: Tuple of (is_valid, parsed_json)
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"validate_json_file called with path: {file_path}")
    
    # Ensure we have an absolute path
    abs_path = os.path.abspath(file_path)
    logger.debug(f"Absolute path: {abs_path}")
    logger.debug(f"File exists: {os.path.exists(abs_path)}")
    logger.debug(f"Is file: {os.path.isfile(abs_path) if os.path.exists(abs_path) else 'N/A'}")
    logger.debug(f"Collections dir: {COLLECTIONS_DIR}")
    logger.debug(f"Current working directory: {os.getcwd()}")
    
    try:
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}")
        
        if not os.path.isfile(abs_path):
            raise IsADirectoryError(f"Path is a directory, not a file: {abs_path}")
        
        with open(abs_path, 'r') as f:
            data = json.load(f)
        logger.debug(f"Successfully loaded JSON from {abs_path}")
        return True, data
    except FileNotFoundError as e:
        logger.warning(f"Error reading file {os.path.basename(file_path)}: {e}")
        return False, None
    except IsADirectoryError as e:
        logger.warning(f"Error reading file {os.path.basename(file_path)}: {e}")
        return False, None
    except json.JSONDecodeError as e:
        logger.warning(f"Error parsing JSON in {os.path.basename(file_path)}: {e}")
        return False, None
    except Exception as e:
        logger.warning(f"Error reading file {os.path.basename(file_path)}: {e}")
        return False, None

def load_proxy(proxy_path: str = None) -> Dict:
    """
    Load proxy from default.json file if it exists,
    otherwise return default proxy.
    If the proxy file exists but is malformed, return an empty dictionary
    to ensure we rely only on command-line arguments.
    """
    logger = logging.getLogger(__name__)
    proxy = DEFAULT_CONFIG.copy()
    
    # If no specific proxy path was provided, prompt user to select one if multiple exist
    if not proxy_path:
        proxy_path = select_proxy_file()
    
    # Use the provided proxy path or the selected one
    proxy_file_path = proxy_path
    
    try:
        # Create proxy directory if it doesn't exist
        if not os.path.exists(CONFIG_DIR):
            try:
                os.makedirs(CONFIG_DIR)
                logger.debug(f"Created proxies directory at {CONFIG_DIR}")
            except Exception as e:
                logger.warning(f"Could not create proxies directory: {e}")
        
        if os.path.exists(proxy_file_path):
            # Validate the JSON file before loading
            is_valid, parsed_proxy = validate_json_file(proxy_file_path)
            
            if is_valid and parsed_proxy:
                proxy.update(parsed_proxy)
                # Get just the directory name and filename instead of full path
                proxy_dir = os.path.basename(os.path.dirname(proxy_file_path))
                proxy_file = os.path.basename(proxy_file_path)
                logger.info(f"Loaded proxy from {proxy_dir}/{proxy_file}")
            else:
                logger.warning(f"Proxy file {os.path.basename(proxy_file_path)} is malformed, using default settings")
                # Return empty dictionary to ensure we rely only on command-line arguments
                return {}
        else:
            logger.info(f"No proxy file found at {os.path.basename(proxy_file_path)}, using default settings")
            # Auto-generate proxy file with default settings if using the default path
            if proxy_file_path == CONFIG_FILE_PATH:
                try:
                    with open(CONFIG_FILE_PATH, 'w') as f:
                        json.dump(DEFAULT_CONFIG, f, indent=4)
                    logger.info(f"Generated default proxy file: {os.path.basename(CONFIG_FILE_PATH)}")
                except Exception as e:
                    logger.warning(f"Could not create default proxy file: {e}")
    except Exception as e:
        logger.warning(f"Error loading proxy file: {e}. Using default settings.")
        # Return empty dictionary to ensure we rely only on command-line arguments
        return {}
    
    return proxy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_proxy_connection(host: str, port: int) -> bool:
    """
    Check if the proxy is running and accessible.
    Returns True if proxy is running, False otherwise.
    """
    try:
        # Resolve hostname to IP if needed
        try:
            # Try to resolve the hostname to handle cases where 'localhost' or other hostnames are used
            ip_address = socket.gethostbyname(host)
            logger.debug(f"Resolved {host} to IP: {ip_address}")
        except socket.gaierror:
            # If hostname resolution fails, use the original host (might be an IP already)
            logger.warning(f"Could not resolve hostname {host}, using as-is")
            ip_address = host
            
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip_address, port))
        sock.close()
        
        if result == 0:
            logger.info(f"Proxy connection successful at {host}:{port}")
            return True
        else:
            logger.debug(f"No proxy detected at {host}:{port}")
            return False
    except Exception as e:
        logger.debug(f"Error checking proxy at {host}:{port}: {str(e)}")
        return False

def verify_proxy_with_request(host: str, port: int) -> bool:
    """
    Verify proxy by making a test request through it.
    Returns True if the proxy works, False otherwise.
    """
    try:
        proxies = {
            "http": f"http://{host}:{port}",
            "https": f"http://{host}:{port}"
        }
        
        # Use a reliable test endpoint
        test_url = "https://httpbin.org/get"
        
        logger.debug(f"Testing proxy with request to {test_url}")
        logger.debug(f"Using proxy settings: {proxies}")
        
        # Create a new session for this test to avoid any proxy issues
        test_session = requests.Session()
        test_session.proxies.update(proxies)
        test_session.verify = False
        
        # Add a custom header to help identify if the request went through the proxy
        headers = {
            "X-Proxy-Test": "postman2burp-proxy-test"
        }
        
        response = test_session.get(
            test_url, 
            headers=headers,
            timeout=5
        )
        
        # Check if the response contains our custom header in the returned data
        # httpbin.org/get returns all headers in the response JSON
        try:
            response_json = response.json()
            headers_in_response = response_json.get('headers', {})
            if 'X-Proxy-Test' in headers_in_response:
                logger.debug("Found our test header in the response, proxy is working")
            else:
                logger.warning("Test header not found in response, proxy might not be working correctly")
        except:
            logger.warning("Could not parse response JSON to verify headers")
        
        if response.status_code == 200:
            logger.info(f"Proxy test request successful through {host}:{port}")
            return True
        else:
            logger.warning(f"Proxy test request failed with status code {response.status_code}")
            return False
    except requests.exceptions.ProxyError as e:
        logger.warning(f"Proxy error during test: {str(e)}")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"Connection error during proxy test: {str(e)}")
        return False
    except requests.exceptions.Timeout as e:
        logger.warning(f"Timeout during proxy test: {str(e)}")
        return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request error during proxy test: {str(e)}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error during proxy test: {str(e)}")
        return False

def extract_variables_from_text(text: str) -> Set[str]:
    """
    Extract all variables in the format {{variable_name}} from the given text.
    Returns a set of variable names without the curly braces.
    """
    if not text:
        return set()
    
    # Match {{variable}} pattern, but not {{{variable}}} (triple braces)
    pattern = r'{{([^{}]+)}}'
    matches = re.findall(pattern, text)
    
    # Filter out any matches that start with $ (these are usually Postman's built-in variables)
    return {match for match in matches if not match.startswith('$')}

def extract_variables_from_collection(collection_path: str) -> Tuple[Set[str], Optional[str], Dict]:
    """
    Extract all variables used in a Postman collection.
    Returns a tuple of (set of variable names, collection_id, collection_data).
    """
    logger.info(f"Extracting variables from collection: {collection_path}")
    
    try:
        with open(collection_path, 'r') as f:
            collection = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load collection: {e}")
        sys.exit(1)
    
    variables = set()
    collection_id = None
    
    # Try to extract the Postman collection ID
    if "info" in collection and "_postman_id" in collection["info"]:
        collection_id = collection["info"]["_postman_id"]
        logger.debug(f"Found Postman collection ID: {collection_id}")
    
    # Extract collection-level variables first
    if "variable" in collection:
        for var in collection["variable"]:
            if "key" in var:
                variables.add(var["key"])
                logger.debug(f"Found collection variable: {var['key']}")
    
    def process_url(url):
        if isinstance(url, dict):
            if "raw" in url:
                variables.update(extract_variables_from_text(url["raw"]))
            if "host" in url:
                for part in url["host"]:
                    variables.update(extract_variables_from_text(part))
            if "path" in url:
                for part in url["path"]:
                    variables.update(extract_variables_from_text(part))
            if "query" in url:
                for query in url["query"]:
                    if "key" in query:
                        variables.update(extract_variables_from_text(query["key"]))
                    if "value" in query:
                        variables.update(extract_variables_from_text(query["value"]))
        else:
            variables.update(extract_variables_from_text(url))
    
    def process_body(body):
        if not body:
            return
            
        mode = body.get("mode")
        if mode == "raw":
            variables.update(extract_variables_from_text(body.get("raw", "")))
        elif mode == "urlencoded":
            for param in body.get("urlencoded", []):
                if "key" in param:
                    variables.update(extract_variables_from_text(param["key"]))
                if "value" in param:
                    variables.update(extract_variables_from_text(param["value"]))
        elif mode == "formdata":
            for param in body.get("formdata", []):
                if "key" in param:
                    variables.update(extract_variables_from_text(param["key"]))
                if "value" in param:
                    variables.update(extract_variables_from_text(param["value"]))
    
    def process_headers(headers):
        for header in headers:
            if "key" in header:
                variables.update(extract_variables_from_text(header["key"]))
            if "value" in header:
                variables.update(extract_variables_from_text(header["value"]))
    
    def process_request(request):
        if "url" in request:
            process_url(request["url"])
        if "method" in request:
            variables.update(extract_variables_from_text(request["method"]))
        if "header" in request:
            process_headers(request["header"])
        if "body" in request:
            process_body(request["body"])
    
    def process_item(item):
        if "name" in item:
            variables.update(extract_variables_from_text(item["name"]))
        if "request" in item:
            process_request(item["request"])
        if "item" in item:
            for sub_item in item["item"]:
                process_item(sub_item)
    
    # Process all items
    if "item" in collection:
        for item in collection["item"]:
            process_item(item)
    
    logger.info(f"Found {len(variables)} unique variables in collection")
    return variables, collection_id, collection

def generate_variables_template(collection_path: str, output_path: str) -> None:
    """Generate a template file with all variables from a collection."""
    # Extract variables from collection
    variables, collection_id, collection_data = extract_variables_from_collection(collection_path)
    
    if not variables:
        logger.warning("No variables found in collection")
        return
    
    # Create a simple target profile with direct key-value pairs
    profile = {
        "id": f"auto-generated-{int(time.time())}",
        "name": collection_data.get("info", {}).get("name", "Environment"),
        "values": [],
        "_postman_variable_scope": "environment",
        "_postman_exported_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "_postman_exported_using": "Postman2Burp/Interactive",
        "_postman_collection_id": collection_id if collection_id else "",
        "_exporter_id": "12345678",
        "description": f"Environment for: {collection_data.get('info', {}).get('name', 'Unknown Collection')}"
    }
    
    # Separate collection-level variables from other variables
    collection_variables = []
    collection_variable_values = {}
    
    if "variable" in collection_data:
        for var in collection_data.get("variable", []):
            if "key" in var:
                collection_variables.append(var["key"])
                if "value" in var:
                    collection_variable_values[var["key"]] = var["value"]
            
    other_vars = [v for v in variables if v not in collection_variables]
    
    # Count variables with values
    variables_with_values = 0
    
    # Print information about found variables
    print(f"\n=== Variables Found in Collection ===")
    print(f"Collection-level variables ({len(collection_variables)}):")
    for var in sorted(collection_variables):
        value = collection_variable_values.get(var, "")
        value_display = "********" if any(sensitive in var.lower() for sensitive in ["token", "key", "secret", "password"]) else value
        print(f"  - {var} = {value_display}")
    
    print(f"\nOther variables ({len(other_vars)}):")
    for var in sorted(other_vars):
        print(f"  - {var}")
    
    print("\n=== Enter Values for Variables ===")
    print("- Press Enter to use the original value or skip")
    print("- Variables with empty values will use collection defaults if available")
    print("- Target profile values take precedence over collection variables")
    
    # First prompt for collection-level variables
    if collection_variables:
        print("\nCollection-level variables:")
        for var in sorted(collection_variables):
            # Get original value if available
            original_value = collection_variable_values.get(var, "")
            
            # Mask sensitive values in display
            display_value = "********" if any(sensitive in var.lower() for sensitive in ["token", "key", "secret", "password"]) else original_value
            
            # Prompt for value
            if original_value:
                value = input(f"{var} [original: {display_value}]: ").strip()
                if not value:  # Use original value if user just presses Enter
                    value = original_value
            else:
                value = input(f"{var}: ").strip()
            
            if value.strip():  # Only add if value is not empty
                profile["values"].append({
                    "key": var,
                    "value": value,
                    "type": "string",
                    "enabled": True
                })
                variables_with_values += 1
    
    # Then prompt for other variables
    if other_vars:
        print("\nOther variables:")
        for var in sorted(other_vars):
            value = input(f"{var}: ").strip()
            
            if value.strip():  # Only add if value is not empty
                profile["values"].append({
                    "key": var,
                    "value": value,
                    "type": "default",
                    "enabled": True
                })
                variables_with_values += 1
    
    # If no variables have values, ask if user wants to continue
    if variables_with_values == 0:
        print("\nNo values provided. Do you want to:")
        print("1. Create an empty template anyway")
        print("2. Cancel and exit")
        choice = input("Enter choice (1/2): ")
        if choice != "1":
            print("Operation cancelled.")
            return
    
    # Automatically generate filename based on collection ID
    filename = f"{collection_id}_{int(time.time())}.json" if collection_id else f"profile_{int(time.time())}.json"
    
    # Save to profiles directory
    output_path = os.path.join(VARIABLES_DIR, filename)
    
    try:
        # Save profile
        with open(output_path, 'w') as f:
            json.dump(profile, f, indent=2)
        
        # Print success message
        relative_path = os.path.relpath(output_path)
        collection_name = os.path.basename(collection_path)
        
        print(f"\n[✓] Successfully created target profile with {variables_with_values} variables at {relative_path}")
        print(f"\nNext command to run:")
        print(f"python3 postman2burp.py --collection \"{collection_name}\" --target-profile \"{filename}\"")
        
        # Exit after creating the profile
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Failed to save profile: {e}")
        sys.exit(1)

def save_proxy(proxy: Dict) -> bool:
    """
    Save proxy to default.json file.
    
    Args:
        proxy: Configuration dictionary to save
        
    Returns:
        bool: True if the proxy was saved successfully, False otherwise
    """
    logger = logging.getLogger(__name__)
    try:
        # Create proxy directory if it doesn't exist
        if not os.path.exists(CONFIG_DIR):
            try:
                os.makedirs(CONFIG_DIR)
                logger.debug(f"Created proxies directory at {CONFIG_DIR}")
            except Exception as e:
                logger.warning(f"Could not create proxies directory: {e}")
                return False

        # Ensure each argument is saved as a separate JSON item
        formatted_proxy = {
            "proxy_host": proxy.get("proxy_host", "localhost"),
            "proxy_port": proxy.get("proxy_port", 8080),
            "verify_ssl": proxy.get("verify_ssl", False),
            "target_profile": proxy.get("target_profile", ""),
            "verbose": proxy.get("verbose", False)
        }
        
        # Add any additional proxy items
        for key, value in proxy.items():
            if key not in formatted_proxy and value is not None:
                formatted_proxy[key] = value
        
        with open(CONFIG_FILE_PATH, 'w') as f:
            json.dump(formatted_proxy, f, indent=4)
        logger.info(f"Configuration saved to {os.path.basename(CONFIG_DIR)}/{os.path.basename(CONFIG_FILE_PATH)}")
        return True
    except Exception as e:
        logger.error(f"Failed to save proxy: {e}")
        return False

def select_collection_file() -> str:
    """
    List all JSON collection files in the collections directory and allow the user to select one.
    Returns the path to the selected collection file.
    """
    logger = logging.getLogger(__name__)
    logger.info("Listing available collection files")
    
    # Define collections directory
    COLLECTIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "collections")
    
    # Create collections directory if it doesn't exist
    if not os.path.exists(COLLECTIONS_DIR):
        os.makedirs(COLLECTIONS_DIR)
        logger.info(f"Created collections directory: {COLLECTIONS_DIR}")
    
    try:
        # List all JSON files in the collections directory
        collection_files = [f for f in os.listdir(COLLECTIONS_DIR) if f.endswith('.json')]
    except Exception as e:
        logger.error(f"Error listing collections directory: {e}")
        return ""
    
    if not collection_files:
        logger.warning("No collection files found in collections directory")
        print("No collection files found in the collections directory.")
        print("Please specify a collection file path:")
        collection_path = input("> ").strip()
        return collection_path
    
    # If only one collection file is found, use it
    if len(collection_files) == 1:
        collection_path = os.path.join(COLLECTIONS_DIR, collection_files[0])
        logger.info(f"Using the only available collection file: {collection_files[0]}")
        print(f"Using collection file: {collection_files[0]}")
        return collection_path
    
    # If multiple collection files are found, let the user select one
    print("\nAvailable collection files:")
    for i, file in enumerate(collection_files, 1):
        print(f"{i}. {file}")
    
    print("\nSelect a collection file (or enter a path to a different file):")
    choice = input("> ").strip()
    
    # Check if the input is a number (selecting from the list)
    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(collection_files):
            selected_file = collection_files[choice_idx]
            collection_path = os.path.join(COLLECTIONS_DIR, selected_file)
            logger.info(f"User selected collection file: {selected_file}")
            return collection_path
    except ValueError:
        # Not a number, treat as a file path
        pass
    
    # If we get here, the input was not a valid number, treat it as a file path
    if os.path.exists(choice):
        logger.info(f"User provided custom collection path: {choice}")
        return choice
    else:
        logger.warning(f"File not found: {choice}")
        print(f"File not found: {choice}")
        print("Please enter a valid file path:")
        collection_path = input("> ").strip()
        return collection_path

def select_proxy_file() -> str:
    """
    List all proxy files in the proxies directory and allow the user to select one.
    Returns the path to the selected proxy file.
    """
    logger = logging.getLogger(__name__)
    
    # Get all JSON files in the proxies directory
    proxy_files = []
    try:
        for file in os.listdir(CONFIG_DIR):
            if file.endswith('.json'):
                proxy_files.append(file)
    except Exception as e:
        logger.error(f"Error listing proxies directory: {e}")
        return CONFIG_FILE_PATH
    
    # If no proxy files found, return the default
    if not proxy_files:
        logger.info("No proxy files found, using default proxy")
        return CONFIG_FILE_PATH
    
    # If only one proxy file found, use it without prompting
    if len(proxy_files) == 1:
        proxy_path = os.path.join(CONFIG_DIR, proxy_files[0])
        logger.info(f"Using proxy file: {proxy_files[0]}")
        return proxy_path
    
    # Multiple proxy files found, always prompt user to select
    print("\nMultiple proxy proxy files found. Please select one:")
    for i, file in enumerate(proxy_files, 1):
        # Highlight the default proxy file
        if file == os.path.basename(CONFIG_FILE_PATH):
            print(f"  {i}. {file} (default)")
        else:
            print(f"  {i}. {file}")
    
    print("  n. Create a new proxy file")
    print("  q. Quit")
    
    while True:
        choice = input("\nEnter your choice (1-{0}/n/q): ".format(len(proxy_files)))
        
        if choice.lower() == 'q':
            print("Exiting...")
            sys.exit(0)
        elif choice.lower() == 'n':
            # Create a new proxy file with default settings
            timestamp = int(time.time())
            new_proxy_file = f"proxy_{timestamp}.json"
            new_proxy_path = os.path.join(CONFIG_DIR, new_proxy_file)
            
            try:
                with open(new_proxy_path, 'w') as f:
                    json.dump(DEFAULT_CONFIG, f, indent=4)
                logger.info(f"Created new proxy file: {new_proxy_file}")
                print(f"\nCreated new proxy file: {new_proxy_file}")
                return new_proxy_path
            except Exception as e:
                logger.error(f"Failed to create new proxy file: {e}")
                print(f"Error: Failed to create new proxy file: {e}")
                # Fall back to default
                return CONFIG_FILE_PATH
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(proxy_files):
                selected_file = proxy_files[choice_idx]
                proxy_path = os.path.join(CONFIG_DIR, selected_file)
                logger.info(f"User selected proxy file: {selected_file}")
                return proxy_path
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(proxy_files)}, 'n', or 'q'.")
        except ValueError:
            print("Invalid input. Please enter a number, 'n', or 'q'.")

def resolve_collection_path(collection_path: str) -> str:
    """
    Resolve the collection path. If the path is not absolute and the file doesn't exist,
    check if it exists in the collections directory.
    
    Args:
        collection_path: Path to the collection file
        
    Returns:
        str: Resolved path to the collection file
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"resolve_collection_path called with: {collection_path}")
    logger.debug(f"Current working directory: {os.getcwd()}")
    logger.debug(f"Collections directory: {COLLECTIONS_DIR}")
    
    # If the path is absolute and the file exists, return it as is
    if os.path.isabs(collection_path) and os.path.exists(collection_path):
        logger.debug(f"Path is absolute and file exists: {collection_path}")
        return collection_path
    
    # If the file exists in the current directory, return it
    if os.path.exists(collection_path):
        logger.debug(f"File exists in current directory: {collection_path}")
        return collection_path
    
    # Check if the file exists in the collections directory
    basename = os.path.basename(collection_path)
    collections_path = os.path.join(COLLECTIONS_DIR, basename)
    
    logger.debug(f"Checking if collection exists in collections directory: {collections_path}")
    
    if os.path.exists(collections_path) and os.path.isfile(collections_path):
        logger.info(f"Found collection file in collections directory: {basename}")
        return collections_path
    
    # Create collections directory if it doesn't exist
    if not os.path.exists(COLLECTIONS_DIR):
        try:
            os.makedirs(COLLECTIONS_DIR)
            logger.debug(f"Created collections directory at {COLLECTIONS_DIR}")
        except Exception as e:
            logger.warning(f"Could not create collections directory: {e}")
    
    # If the file doesn't exist in the collections directory, return the original path
    logger.warning(f"Collection file not found in collections directory: {basename}")
    return collection_path

class PostmanToBurp:
    def __init__(self, collection_path: str, target_profile: str = None, proxy_host: str = None, proxy_port: int = None,
                 verify_ssl: bool = False, auto_detect_proxy: bool = True,
                 verbose: bool = False):
        """
        Initialize the PostmanToBurp converter.
        
        Args:
            collection_path: Path to the Postman collection JSON file
            target_profile: Path to the Postman environment JSON file
            proxy_host: Proxy host
            proxy_port: Proxy port
            verify_ssl: Whether to verify SSL certificates
            auto_detect_proxy: Whether to auto-detect proxy settings
            verbose: Whether to enable verbose logging
        """
        self.collection_path = collection_path
        self.target_profile = target_profile
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.verify_ssl = verify_ssl
        self.auto_detect_proxy = auto_detect_proxy
        self.log_path = None
        self.verbose = verbose
        
        self.collection = None
        self.environment = {}
        self.results = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "requests": []
        }
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        
        # Configure session
        self.session = requests.Session()
        self.session.verify = verify_ssl

    def load_collection(self) -> bool:
        """Load the Postman collection from the specified file."""
        # Validate the collection file
        is_valid, json_data = validate_json_file(self.collection_path)
        if not is_valid:
            self.logger.error(f"Failed to load collection: {self.collection_path}")
            return False
        
        self.collection = json_data
        self.collection_id = self.collection.get("info", {}).get("_postman_id", "unknown")
        self.collection_name = self.collection.get("info", {}).get("name", "Unknown Collection")
        
        # Store collection variables in a separate dictionary to avoid overriding target profile variables
        collection_variables = {}
        
        # Extract collection variables
        if "variable" in self.collection:
            for var in self.collection["variable"]:
                if "key" in var and "value" in var:
                    var_key = var["key"]
                    var_value = var["value"]
                    collection_variables[var_key] = var_value
                    if self.verbose:
                        # Mask sensitive values in logs
                        if "token" in var_key.lower() or "key" in var_key.lower() or "secret" in var_key.lower() or "password" in var_key.lower():
                            self.logger.debug(f"Loaded collection variable: {var_key} = ********")
                        else:
                            self.logger.debug(f"Loaded collection variable: {var_key} = {var_value}")
        
        # Only add collection variables if they don't exist in the environment (target profile takes precedence)
        for key, value in collection_variables.items():
            if key not in self.environment:
                self.environment[key] = value
                if self.verbose:
                    self.logger.debug(f"Using collection variable: {key} = {value}")
            else:
                if self.verbose:
                    self.logger.debug(f"Ignoring collection variable '{key}' as it's already defined in target profile")
        
        self.logger.info(f"Loaded collection: {self.collection_name} ({self.collection_id})")
        return True
    
    def load_profile(self) -> bool:
        """Load variables from a target profile file."""
        if not self.target_profile:
            self.logger.debug("No target profile specified")
            return True

        # First try the path as provided
        profile_path = self.target_profile
        
        # If the file doesn't exist, try looking in the profiles directory
        if not os.path.exists(profile_path):
            profiles_dir_path = os.path.join(VARIABLES_DIR, os.path.basename(profile_path))
            if os.path.exists(profiles_dir_path):
                self.logger.debug(f"Profile not found at {profile_path}, using {profiles_dir_path} instead")
                profile_path = profiles_dir_path
            else:
                self.logger.warning(f"Profile not found at {profile_path} or in profiles directory")

        # Validate profile file
        valid, profile_data = validate_json_file(profile_path)
        if not valid or not profile_data:
            self.logger.error(f"Invalid profile file: {self.target_profile}")
            return False

        if self.verbose:
            self.logger.debug(f"Loading profile: {profile_path}")
            self.logger.debug(f"Profile structure: {list(profile_data.keys())}")

        # Check if this is a Postman environment format (with values array)
        if "values" in profile_data and isinstance(profile_data["values"], list):
            self.logger.debug("Loading Postman environment format profile")
            for var in profile_data["values"]:
                if "key" in var and "value" in var and var.get("enabled", True):
                    key = var["key"]
                    value = var["value"]
                    self.environment[key] = value
                    if self.verbose:
                        self.logger.debug(f"Loaded variable from profile: {key}")
        else:
            # Load variables from profile - simple key-value structure
            self.logger.debug("Loading simple key-value format profile")
            for key, value in profile_data.items():
                # Skip metadata fields
                if key in ["id", "collection_id", "created_at", "name", "description"]:
                    continue
                    
                # Add to environment dictionary
                self.environment[key] = value
                if self.verbose:
                    self.logger.debug(f"Loaded variable from profile: {key}")

        # Check if base_url is in environment
        if "base_url" not in self.environment:
            self.logger.warning("base_url not found in environment")
            
        if self.verbose:
            self.logger.debug(f"Loaded {len(self.environment)} variables")
            for key, value in self.environment.items():
                # Mask sensitive values in logs
                if "token" in key.lower() or "key" in key.lower() or "secret" in key.lower() or "password" in key.lower():
                    self.logger.debug(f"Variable: {key}=********")
                else:
                    self.logger.debug(f"Variable: {key}={value}")

        return True

    def replace_variables(self, text: str) -> str:
        """Replace Postman variables in the given text."""
        if not text:
            return text
        
        original_text = text
        
        # First try environment variables, then collection variables
        for key, value in self.environment.items():
            if value is not None:
                # Check if the variable is in the text before replacing
                if f"{{{{${key}}}}}" in text or f"{{{{{key}}}}}" in text:
                    self.logger.debug(f"Replacing variable {key} with value {value}")
                
                text = text.replace(f"{{{{${key}}}}}", str(value))
                text = text.replace(f"{{{{{key}}}}}", str(value))
        
        # Log if any replacements were made
        if original_text != text and self.verbose:
            self.logger.debug(f"Variable replacement: '{original_text}' -> '{text}'")
                
        return text

    def extract_requests_from_item(self, item: Dict, folder_name: str = "") -> List[Dict]:
        """Recursively extract requests from a Postman collection item."""
        requests = []
        
        # If this item has a request, it's an endpoint
        if "request" in item:
            request_data = {
                "name": item.get("name", "Unnamed Request"),
                "folder": folder_name,
                "request": item["request"]
            }
            requests.append(request_data)
            
        # If this item has items, it's a folder - process recursively
        if "item" in item:
            new_folder = folder_name
            if folder_name and item.get("name"):
                new_folder = f"{folder_name} / {item['name']}"
            elif item.get("name"):
                new_folder = item["name"]
                
            for sub_item in item["item"]:
                requests.extend(self.extract_requests_from_item(sub_item, new_folder))
                
        return requests

    def extract_all_requests(self, collection: Dict) -> List[Dict]:
        """Extract all requests from the Postman collection."""
        requests = []
        
        # Handle collection variables if present
        if "variable" in collection:
            for var in collection["variable"]:
                self.environment[var["key"]] = var["value"]
                
        # Extract requests from items
        if "item" in collection:
            for item in collection["item"]:
                requests.extend(self.extract_requests_from_item(item))
                
        return requests

    def prepare_request(self, request_data: Dict) -> Dict:
        """
        Prepare a request for sending.
        
        Args:
            request_data: The request data from the collection
            
        Returns:
            Dict: The prepared request data
        """
        # Extract request details
        name = request_data.get("name", "Unnamed Request")
        folder = request_data.get("folder", "")
        request = request_data.get("request", {})
        
        # Get base_url from environment if available
        base_url = self.environment.get("base_url", "")
        if base_url:
            self.logger.debug(f"Using base_url from environment: {base_url}")
            # Check if base_url has protocol, add https:// if not
            if not base_url.startswith("http://") and not base_url.startswith("https://"):
                base_url = f"https://{base_url}"
                self.logger.debug(f"Added protocol to base_url: {base_url}")
        else:
            self.logger.debug("No base_url found in environment")
            
        # Debug log the request URL structure
        if self.verbose:
            if isinstance(request.get("url"), dict):
                self.logger.debug(f"URL structure: {list(request.get('url', {}).keys())}")
                if "host" in request.get("url", {}):
                    self.logger.debug(f"URL host: {request.get('url', {}).get('host', [])}")
                if "raw" in request.get("url", {}):
                    self.logger.debug(f"URL raw: {request.get('url', {}).get('raw', '')}")
        
        # Extract URL
        url = ""
        if isinstance(request.get("url"), str):
            url = self.replace_variables(request.get("url", ""))
            self.logger.debug(f"URL is a string: {url}")
        elif isinstance(request.get("url"), dict):
            url_obj = request.get("url", {})
            
            # Check if there's a raw URL field and use it if available
            if "raw" in url_obj:
                raw_url = url_obj["raw"]
                self.logger.debug(f"Raw URL before variable replacement: {raw_url}")
                url = self.replace_variables(raw_url)
                self.logger.debug(f"Raw URL after variable replacement: {url}")
            else:
                # Build URL from components
                protocol = url_obj.get("protocol", "https")
                host = url_obj.get("host", [])
                if isinstance(host, list):
                    host = ".".join(host)
                self.logger.debug(f"Host before variable replacement: {host}")
                host = self.replace_variables(host)
                self.logger.debug(f"Host after variable replacement: {host}")
                
                path = url_obj.get("path", [])
                if isinstance(path, list):
                    path = "/".join(path)
                self.logger.debug(f"Path before variable replacement: {path}")
                path = self.replace_variables(path)
                self.logger.debug(f"Path after variable replacement: {path}")
                
                # Add query parameters
                query_params = []
                for param in url_obj.get("query", []):
                    if param.get("disabled", False):
                        continue
                    key = self.replace_variables(param.get("key", ""))
                    value = self.replace_variables(param.get("value", ""))
                    query_params.append(f"{key}={value}")
                
                query_string = ""
                if query_params:
                    query_string = "?" + "&".join(query_params)
                
                # Remove leading slash from path to avoid overriding the base_url domain
                if path.startswith("/"):
                    path = path[1:]
                    
                url = f"{protocol}://{host}/{path}{query_string}"
                self.logger.debug(f"Constructed URL: {url}")
        
        # Fix double protocol issue (https://https://example.com)
        if url.startswith("http://http://") or url.startswith("https://https://"):
            self.logger.debug(f"Fixing double protocol in URL: {url}")
            url = url.replace("http://http://", "http://").replace("https://https://", "https://")
        
        # Apply base_url if available and the URL doesn't already have a host
        if base_url and not (url.startswith("http://") or url.startswith("https://")):
            # Remove trailing slash from base_url if present
            if base_url.endswith("/"):
                base_url = base_url[:-1]
            
            # Add leading slash to URL if not present
            if not url.startswith("/"):
                url = "/" + url
                
            url = f"{base_url}{url}"
            self.logger.debug(f"Applied base_url to URL: {url}")
        
        # Extract method
        method = request.get("method", "GET")
        
        # Extract headers
        headers = {}
        for header in request.get("header", []):
            if header.get("disabled", False):
                continue
            key = self.replace_variables(header.get("key", ""))
            value = self.replace_variables(header.get("value", ""))
            headers[key] = value
        
        # Prepare request data
        prepared_request = {
            "name": name,
            "folder": folder,
            "method": method,
            "url": url,
            "headers": headers
        }
        
        # Extract body
        if "body" in request and request["body"]:
            body_mode = request["body"].get("mode", "")
            
            if body_mode == "raw":
                raw_body = request["body"].get("raw", "")
                # Replace variables in the raw body
                raw_body = self.replace_variables(raw_body)
                # Clean up the raw body by stripping extra whitespace
                raw_body = raw_body.strip()
                prepared_request["body"] = raw_body
                
            elif body_mode == "urlencoded":
                form_data = {}
                for param in request["body"].get("urlencoded", []):
                    if "disabled" in param and param["disabled"]:
                        continue
                    form_data[param["key"]] = self.replace_variables(param["value"])
                prepared_request["body"] = form_data
                
            elif body_mode == "formdata":
                form_data = {}
                for param in request["body"].get("formdata", []):
                    if "disabled" in param and param["disabled"]:
                        continue
                    if param["type"] == "text":
                        form_data[param["key"]] = self.replace_variables(param["value"])
                prepared_request["body"] = form_data
        
        return prepared_request

    def send_request(self, prepared_request: Dict) -> Dict:
        """
        Send a request to the specified URL through the proxy.
        
        Args:
            prepared_request: The prepared request data
            
        Returns:
            Dict: The response data
        """
        url = prepared_request.get("url", "")
        method = prepared_request.get("method", "GET")
        headers = prepared_request.get("headers", {})
        body = prepared_request.get("body", None)
        name = prepared_request.get("name", "Unnamed Request")
        folder = prepared_request.get("folder", "")
        
        self.logger.info(f"Sending request: {name} ({method} {url})")
        
        # Debug log for proxy settings - enhanced logging
        if self.session.proxies:
            self.logger.info(f"Using proxy: {self.session.proxies}")
            # Double-check that proxies are still set in the session
            if not self.session.proxies.get('http') and not self.session.proxies.get('https'):
                self.logger.warning("Proxy settings appear to be empty. Resetting proxy proxy.")
                if self.proxy_host and self.proxy_port:
                    self.session.proxies.update({
                        "http": f"http://{self.proxy_host}:{self.proxy_port}",
                        "https": f"http://{self.proxy_host}:{self.proxy_port}"
                    })
                    self.logger.info(f"Restored proxy settings: {self.session.proxies}")
        else:
            self.logger.warning("No proxy proxyured in session. Requests will be sent directly.")
            # Try to restore proxy settings if they were previously proxyured
            if self.proxy_host and self.proxy_port:
                self.logger.info(f"Attempting to restore proxy settings for {self.proxy_host}:{self.proxy_port}")
                self.session.proxies.update({
                    "http": f"http://{self.proxy_host}:{self.proxy_port}",
                    "https": f"http://{self.proxy_host}:{self.proxy_port}"
                })
        
        # Prepare response data
        response_data = {
            "name": name,
            "folder": folder,
            "method": method,
            "url": url,
            "headers": headers,
            "body": body,
            "request_details": prepared_request,
            "success": False
        }
        
        try:
            start_time = time.time()
            
            # Log the full request details for debugging
            self.logger.debug(f"Request details: URL={url}, Method={method}, Headers={headers}, Body={body}")
            self.logger.debug(f"Session proxy settings: {self.session.proxies}")
            
            # Send request (using session's proxy settings)
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                timeout=30,
                allow_redirects=True
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Clean up the response body by stripping extra whitespace
            try:
                response_body = response.text.strip()
            except:
                response_body = ""
            
            # Update response data
            response_data.update({
                "status_code": response.status_code,
                "response_time": response_time,
                "response_size": len(response.content),
                "response_headers": dict(response.headers),
                "response_body": response_body,
                "success": 200 <= response.status_code < 400
            })
            
            self.logger.info(f"Response: {response.status_code} ({round(response_time * 1000)}ms)")
            
            # Log if the request was likely proxied or not
            proxy_header = response.headers.get('Via') or response.headers.get('X-Forwarded-For')
            if proxy_header:
                self.logger.info(f"Request appears to have been proxied (Via header: {proxy_header})")
            else:
                self.logger.warning("No proxy headers detected in response. Request may not have gone through proxy.")
            
        except requests.exceptions.ProxyError as e:
            self.logger.error(f"Proxy error: {e}")
            response_data.update({
                "error": f"Proxy error: {str(e)}"
            })
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            response_data.update({
                "error": str(e)
            })
        
        return response_data

    def save_results(self) -> None:
        """Save results to a log file."""
        if not self.log_path:
            self.logger.warning("No log path specified, results will not be saved")
            return
            
        try:
            # Create a Postman Collection v2.1.0 format
            collection_data = {
                "info": {
                    "name": self.collection.get("info", {}).get("name", "Unknown Collection"),
                    "_postman_id": self.collection.get("info", {}).get("_postman_id", ""),
                    "description": f"Results of scanning {self.collection.get('info', {}).get('name', 'Unknown Collection')} with postman2burp",
                    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                    "_exporter_id": "postman2burp"
                },
                "item": []
            }
            
            # Group requests by folder
            folders = {}
            for request in self.results["requests"]:
                folder_name = request.get("folder", "")
                if folder_name not in folders:
                    folders[folder_name] = []
                folders[folder_name].append(request)
            
            # Create items for each folder
            for folder_name, requests in folders.items():
                folder_item = {
                    "name": folder_name,
                    "item": []
                }
                
                # Add each request to the folder
                for request in requests:
                    # Format headers for Postman schema
                    header_array = []
                    for key, value in request.get("headers", {}).items():
                        header_array.append({
                            "key": key,
                            "value": value,
                            "type": "text"
                        })
                    
                    # Create request item
                    request_item = {
                        "name": request.get("name", "Unnamed Request"),
                        "request": {
                            "method": request.get("method", "GET"),
                            "header": header_array,
                            "url": {
                                "raw": request.get("url", ""),
                                "protocol": request.get("url", "").split("://")[0] if "://" in request.get("url", "") else "",
                                "host": request.get("url", "").split("://")[1].split("/")[0].split(".") if "://" in request.get("url", "") else [],
                                "path": request.get("url", "").split("://")[1].split("/")[1:] if "://" in request.get("url", "") and "/" in request.get("url", "").split("://")[1] else []
                            }
                        },
                        "response": []
                    }
                    
                    # Add body if present
                    if request.get("body"):
                        if isinstance(request.get("body"), dict):
                            request_item["request"]["body"] = {
                                "mode": "raw",
                                "raw": json.dumps(request.get("body")),
                                "options": {
                                    "raw": {
                                        "language": "json"
                                    }
                                }
                            }
                        else:
                            request_item["request"]["body"] = {
                                "mode": "raw",
                                "raw": request.get("body", ""),
                                "options": {
                                    "raw": {
                                        "language": "json"
                                    }
                                }
                            }
                    
                    # Add response
                    response_headers = []
                    for key, value in request.get("response_headers", {}).items():
                        response_headers.append({
                            "key": key,
                            "value": value
                        })
                    
                    response_item = {
                        "name": f"Response {request.get('status_code', 0)}",
                        "originalRequest": request_item["request"],
                        "status": request.get("status_code", 0),
                        "code": request.get("status_code", 0),
                        "_postman_previewlanguage": "html",
                        "header": response_headers,
                        "cookie": [],
                        "body": request.get("response_body", "")
                    }
                    
                    request_item["response"].append(response_item)
                    folder_item["item"].append(request_item)
                
                collection_data["item"].append(folder_item)
            
            # Add metadata as a variable
            collection_data["variable"] = [
                {
                    "key": "metadata",
                    "value": json.dumps({
                        "collection_name": self.collection.get("info", {}).get("name", "Unknown Collection"),
                        "collection_id": self.collection.get("info", {}).get("_postman_id", ""),
                        "collection_path": self.collection_path,
                        "target_profile": self.target_profile,
                        "proxy": f"{self.proxy_host}:{self.proxy_port}" if self.proxy_host and self.proxy_port else "None",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "total_requests": len(self.results["requests"]),
                        "successful_requests": sum(1 for r in self.results["requests"] if r.get("success", False)),
                        "failed_requests": sum(1 for r in self.results["requests"] if not r.get("success", False))
                    })
                }
            ]
            
            # Create directory if it doesn't exist
            log_dir = os.path.dirname(self.log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                self.logger.debug(f"Created log directory: {log_dir}")
            
            with open(self.log_path, 'w') as f:
                json.dump(collection_data, f, indent=2)
            self.logger.info(f"Results saved to {self.log_path}")
            
            # Print a summary of the results
            print(f"\n=== Results Summary ===")
            print(f"Total requests: {len(self.results['requests'])}")
            print(f"Successful requests: {sum(1 for r in self.results['requests'] if r.get('success', False))}")
            print(f"Failed requests: {sum(1 for r in self.results['requests'] if not r.get('success', False))}")
            print(f"Results saved to: {self.log_path}")
            print("=====================\n")
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
            self.logger.debug(f"Exception details:", exc_info=True)

    def process_items(self, items, folder_name=""):
        """Process a list of items from the collection."""
        total_items = len(items)
        self.logger.info(f"Processing {total_items} items in folder: {folder_name or 'root'}")
        
        for i, item in enumerate(items):
            # If item has sub-items, process them recursively
            if "item" in item:
                sub_folder = item.get("name", "")
                new_folder = f"{folder_name}/{sub_folder}" if folder_name else sub_folder
                self.logger.debug(f"Processing folder: {new_folder} ({len(item['item'])} items)")
                self.process_items(item["item"], new_folder)
            # Otherwise, process the request
            elif "request" in item:
                request_name = item.get("name", f"Request {i+1}")
                self.logger.info(f"Processing request [{i+1}/{total_items}]: {request_name}")
                
                # Extract request data
                request_data = {
                    "name": request_name,
                    "folder": folder_name,
                    "request": item["request"]
                }
                
                # Prepare and send the request
                prepared_request = self.prepare_request(request_data)
                
                # Log the prepared request details
                method = prepared_request.get("method", "GET")
                url = prepared_request.get("url", "")
                self.logger.info(f"Prepared request: {method} {url}")
                
                # Try the request with retries
                max_retries = 3
                retry_count = 0
                result = None
                
                while retry_count < max_retries:
                    # Verify proxy settings before sending
                    if self.proxy_host and self.proxy_port:
                        if not self.session.proxies or not (self.session.proxies.get('http') or self.session.proxies.get('https')):
                            self.logger.warning("Proxy settings missing from session. Restoring...")
                            self.session.proxies.update({
                                "http": f"http://{self.proxy_host}:{self.proxy_port}",
                                "https": f"http://{self.proxy_host}:{self.proxy_port}"
                            })
                    
                    # Send the request
                    result = self.send_request(prepared_request)
                    
                    # Check if successful or if there's no error
                    if result.get("success", False) or "error" not in result:
                        break
                    
                    retry_count += 1
                    if retry_count < max_retries:
                        retry_delay = 2 ** retry_count  # Exponential backoff
                        self.logger.warning(f"Request failed: {result.get('error')}. Retrying in {retry_delay}s... (Attempt {retry_count+1}/{max_retries})")
                        time.sleep(retry_delay)
                
                if retry_count > 0 and not result.get("success", False):
                    self.logger.error(f"Request failed after {retry_count} retries: {result.get('error')}")
                
                # Log the result summary
                status = result.get("status_code", "Error")
                success = "✓" if result.get("success", False) else "✗"
                self.logger.info(f"Request result [{success}]: {request_name} - Status: {status}")
                
                self.results["requests"].append(result)

    def process_collection(self) -> None:
        """Process the collection and send requests to Burp."""
        self.logger.info(f"Processing collection: {self.collection.get('info', {}).get('name', 'Unknown')}")
        
        # Process all items
        self.process_items(self.collection.get("item", []))
        
        # Save results if output file is specified
        if self.log_path:
            self.save_results()
                
        # Print summary
        self.results["total"] = len(self.results["requests"])
        self.results["success"] = sum(1 for r in self.results["requests"] if r.get("success", False))
        self.results["failed"] = self.results["total"] - self.results["success"]
        self.logger.info(f"Summary: {self.results['success']}/{self.results['total']} requests successful")

    def run(self) -> Dict:
        """Run the converter."""
        self.logger.info(f"Starting conversion of {os.path.basename(self.collection_path)}")
        
        # Load collection
        if not self.load_collection():
            return {"success": False, "message": "Failed to load collection"}
        
        # Load profile
        if not self.load_profile():
            return {"success": False, "message": "Failed to load profile"}
        
        # Print all variables for reference
        print("\n=== Available Variables ===")
        print("Target Profile Variables (these take precedence):")
        if self.environment:
            for key, value in sorted(self.environment.items()):
                # Mask sensitive values
                if "token" in key.lower() or "key" in key.lower() or "secret" in key.lower() or "password" in key.lower():
                    print(f"  {key} = ******** (will be used)")
                else:
                    print(f"  {key} = {value} (will be used)")
        else:
            print("  No target profile variables found")
        
        # Print collection variables
        print("\nCollection Variables (used only if not in target profile):")
        if "variable" in self.collection and self.collection["variable"]:
            for var in sorted(self.collection["variable"], key=lambda x: x.get("key", "")):
                if "key" in var and "value" in var:
                    key = var["key"]
                    value = var["value"]
                    # Check if this variable is overridden by target profile
                    is_overridden = key in self.environment
                    status = "(overridden by target profile)" if is_overridden else "(will be used)"
                    
                    # Mask sensitive values
                    if "token" in key.lower() or "key" in key.lower() or "secret" in key.lower() or "password" in key.lower():
                        print(f"  {key} = ******** {status}")
                    else:
                        print(f"  {key} = {value} {status}")
        else:
            print("  No collection variables found")
        
        print("\nNote: Target profile variables take precedence over collection variables.")
        print("To override a collection variable, add it to your target profile.")
        print("===========================\n")
        
        # Check proxy connection
        if not self.check_proxy():
            return {"success": False, "message": "Failed to connect to proxy"}
            
        # Process collection
        self.process_collection()
        
        # Save results
        if self.log_path:
            self.save_results()
            
        return self.results

    def check_proxy(self) -> bool:
        """
        Check if the proxy is running and accessible.
        If user-specified proxy is not available, detect other running proxies
        and allow the user to interactively select one.
        
        Returns:
            bool: True if proxy is available, False otherwise
        """
        # Set up proxy URLs
        if self.proxy_host and self.proxy_port:
            # User explicitly provided proxy settings
            self.proxies = {
                "http": f"http://{self.proxy_host}:{self.proxy_port}",
                "https": f"http://{self.proxy_host}:{self.proxy_port}"
            }
            self.logger.debug(f"Using user-specified proxy: {self.proxies}")
            
            # Set the proxy in the session
            self.session.proxies.update(self.proxies)
                
            # Check if the specified proxy is running
            if not check_proxy_connection(self.proxy_host, self.proxy_port):
                self.logger.error(f"Specified proxy not running at {self.proxy_host}:{self.proxy_port}")
                
                # Find available proxies but don't automatically switch
                self.logger.info("Checking for other available proxies...")
                available_proxies = []
                
                for proxy in COMMON_PROXIES:
                    host, port = proxy["host"], proxy["port"]
                    # Skip the proxy that was already checked and failed
                    if host == self.proxy_host and port == self.proxy_port:
                        continue
                        
                    if check_proxy_connection(host, port):
                        available_proxies.append((host, port))
                
                # Wrap filenames in single quotes to handle spaces
                collection_name = f"'{os.path.basename(self.collection_path)}'" if ' ' in os.path.basename(self.collection_path) else os.path.basename(self.collection_path)
                profile_arg = f"--target-profile '{os.path.basename(self.target_profile)}'" if self.target_profile else ""
                
                print(f"\nSpecified proxy at {self.proxy_host}:{self.proxy_port} is not running.")
                
                if available_proxies:
                    print("\nAvailable proxies detected:")
                    for i, (host, port) in enumerate(available_proxies, 1):
                        print(f"  {i}. {host}:{port}")
                    
                    print("\nSelect an option:")
                    print("  1-{0}. Use one of the available proxies".format(len(available_proxies)))
                    print("  q. Quit")
                    
                    while True:
                        choice = input("\nEnter your choice (1-{0}/q): ".format(len(available_proxies)))
                        
                        if choice.lower() == 'q':
                            print("Exiting...")
                            sys.exit(0)
                        
                        try:
                            choice_idx = int(choice) - 1
                            if 0 <= choice_idx < len(available_proxies):
                                # User selected a valid proxy
                                self.proxy_host, self.proxy_port = available_proxies[choice_idx]
                                self.proxies = {
                                    "http": f"http://{self.proxy_host}:{self.proxy_port}",
                                    "https": f"http://{self.proxy_host}:{self.proxy_port}"
                                }
                                
                                # Update session proxies
                                self.session.proxies.update(self.proxies)
                                
                                print(f"\nUsing proxy: {self.proxy_host}:{self.proxy_port}")
                                self.logger.info(f"User selected proxy: {self.proxy_host}:{self.proxy_port}")
                                
                                # Verify the proxy with a test request
                                if verify_proxy_with_request(self.proxy_host, self.proxy_port):
                                    self.logger.info("Selected proxy verification successful")
                                    return True
                                else:
                                    self.logger.warning("Selected proxy failed verification, but will try to use it anyway")
                                    return True
                            else:
                                print(f"Invalid choice. Please enter a number between 1 and {len(available_proxies)}.")
                        except ValueError:
                            print("Invalid input. Please enter a number or 'q' to quit.")
                else:
                    print("\nNo other proxies were detected on common ports.")
                    print("Please start a proxy server (Burp Suite, ZAP, etc.) and try again.")
                    print("Common proxy ports checked: " + ", ".join(str(proxy["port"]) for proxy in COMMON_PROXIES[:4]))
                    
                    print("\nOptions:")
                    print("  1. Start a proxy server and try again")
                    print("  q. Quit")
                    
                    while True:
                        choice = input("\nEnter your choice (1/q): ")
                        
                        if choice.lower() == 'q':
                            print("Exiting...")
                            sys.exit(0)
                        elif choice == '1':
                            print("Please start a proxy server and run the command again.")
                            sys.exit(0)
                        else:
                            print("Invalid choice. Please enter 1 or q.")
            else:
                # Proxy connection successful
                self.logger.info(f"Proxy connection successful at {self.proxy_host}:{self.proxy_port}")
                
                # Verify the proxy with a test request for extra confidence
                if verify_proxy_with_request(self.proxy_host, self.proxy_port):
                    self.logger.info("Proxy verification successful with test request")
                else:
                    self.logger.warning("Proxy socket connection successful but test request failed. Continuing anyway.")
                
                return True
        else:
            # No proxy explicitly specified
            self.proxies = {}
            
            # Try to find running proxies
            self.logger.info("Auto-detecting proxy...")
            available_proxies = []
            
            for proxy in COMMON_PROXIES:
                host, port = proxy["host"], proxy["port"]
                if check_proxy_connection(host, port):
                    available_proxies.append((host, port))
            
            if available_proxies:
                if len(available_proxies) == 1:
                    # Only one proxy available, use it automatically
                    self.proxy_host, self.proxy_port = available_proxies[0]
                    self.proxies = {
                        "http": f"http://{self.proxy_host}:{self.proxy_port}",
                        "https": f"http://{self.proxy_host}:{self.proxy_port}"
                    }
                    self.logger.info(f"Auto-detected proxy at {self.proxy_host}:{self.proxy_port}")
                    
                    # Set the proxy in the session
                    self.session.proxies.update(self.proxies)
                    
                    print(f"\nUsing auto-detected proxy: {self.proxy_host}:{self.proxy_port}")
                    
                    # Verify the proxy with a test request
                    if verify_proxy_with_request(self.proxy_host, self.proxy_port):
                        self.logger.info("Auto-detected proxy verification successful")
                        return True
                    else:
                        self.logger.warning("Auto-detected proxy failed verification, but will try to use it anyway")
                        return True
                else:
                    # Multiple proxies available, let user choose
                    print("\nMultiple proxies detected. Please select one:")
                    for i, (host, port) in enumerate(available_proxies, 1):
                        print(f"  {i}. {host}:{port}")
                    
                    print("  q. Quit")
                    
                    while True:
                        choice = input("\nEnter your choice (1-{0}/q): ".format(len(available_proxies)))
                        
                        if choice.lower() == 'q':
                            print("Exiting...")
                            sys.exit(0)
                        
                        try:
                            choice_idx = int(choice) - 1
                            if 0 <= choice_idx < len(available_proxies):
                                # User selected a valid proxy
                                self.proxy_host, self.proxy_port = available_proxies[choice_idx]
                                self.proxies = {
                                    "http": f"http://{self.proxy_host}:{self.proxy_port}",
                                    "https": f"http://{self.proxy_host}:{self.proxy_port}"
                                }
                                
                                # Update session proxies
                                self.session.proxies.update(self.proxies)
                                
                                print(f"\nUsing proxy: {self.proxy_host}:{self.proxy_port}")
                                self.logger.info(f"User selected proxy: {self.proxy_host}:{self.proxy_port}")
                                
                                # Verify the proxy with a test request
                                if verify_proxy_with_request(self.proxy_host, self.proxy_port):
                                    self.logger.info("Selected proxy verification successful")
                                    return True
                                else:
                                    self.logger.warning("Selected proxy failed verification, but will try to use it anyway")
                                    return True
                            else:
                                print(f"Invalid choice. Please enter a number between 1 and {len(available_proxies)}.")
                        except ValueError:
                            print("Invalid input. Please enter a number or 'q' to quit.")
            else:
                self.logger.error("No proxy detected on any common ports")
                print("\nNo proxy was detected running on any common ports.")
                print("Please start a proxy server (Burp Suite, ZAP, etc.) and try again.")
                print("Common proxy ports checked: " + ", ".join(str(proxy["port"]) for proxy in COMMON_PROXIES[:4]))
                
                print("\nOptions:")
                print("  1. Start a proxy server and try again")
                print("  q. Quit")
                
                while True:
                    choice = input("\nEnter your choice (1/q): ")
                    
                    if choice.lower() == 'q':
                        print("Exiting...")
                        sys.exit(0)
                    elif choice == '1':
                        print("Please start a proxy server and run the command again.")
                        sys.exit(0)
                    else:
                        print("Invalid choice. Please enter 1 or q.")
        
        # This line should never be reached, but just in case
        return False
            
def main():
    """
    Main entry point for the script.
    Parses command line arguments, loads proxy, and runs the Postman to Burp conversion.
    """
    # Parse command line arguments first to check for proxy option
    parser = argparse.ArgumentParser(description="Convert Postman collections to Burp Suite requests")
    parser.add_argument("--collection", nargs="?", const="select", help="Path to Postman collection JSON file. If no path is provided, you will be prompted to select a collection.")
    
    # Environment options
    env_group = parser.add_argument_group("Environment Options")
    env_group.add_argument("--target-profile", help="Path to Postman environment JSON file")
    env_group.add_argument("--extract-keys", nargs="?", const="interactive", metavar="OUTPUT_FILE",
                          help="Extract all variables from collection. If no file is specified, enters interactive mode to create a profile. Otherwise, saves to template file.")
    
    # Proxy options
    proxy_group = parser.add_argument_group("Proxy Options")
    proxy_group.add_argument("--proxy", help="Proxy in host:port format")
    proxy_group.add_argument("--proxy-host", help="Proxy host")
    proxy_group.add_argument("--proxy-port", type=int, help="Proxy port")
    proxy_group.add_argument("--verify-ssl", action="store_true", help="Verify SSL certificates")
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument("--log", action="store_true", help="Enable logging to file (saves detailed request results to logs directory)")
    output_group.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    output_group.add_argument("--save-proxy", action="store_true", help="Save current settings as default proxy")
    
    # Proxy options
    proxy_group = parser.add_argument_group("Configuration Options")
    proxy_group.add_argument("-profile", nargs="?", const="select", 
                             help="Use a specific proxy file or select from available proxys if no file specified. "
                                  "If omitted, you will be prompted to select a proxy when multiple are available.")
    
    args = parser.parse_args()
    
    # Configure logging
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_date_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format=log_format, datefmt=log_date_format)
    logger = logging.getLogger(__name__)
    
    # Handle proxy selection
    proxy_path = None
    if args.proxy == "select":
        proxy_path = select_proxy_file()
    elif args.proxy:
        proxy_path = args.proxy
    else:
        # Check if multiple proxy files exist
        try:
            proxy_files = [f for f in os.listdir(CONFIG_DIR) if f.endswith('.json')]
            if len(proxy_files) > 1:
                logger.info("Multiple proxy files found, prompting user to select")
                proxy_path = select_proxy_file()
            elif len(proxy_files) == 1:
                proxy_path = os.path.join(CONFIG_DIR, proxy_files[0])
                logger.info(f"Using the only available proxy file: {proxy_files[0]}")
            else:
                logger.info("No proxy files found, using default proxy")
        except Exception as e:
            logger.warning(f"Error listing proxies directory: {e}")
            logger.info("Using default proxy")
    
    # Load proxy
    proxy = load_proxy(proxy_path)
    
    # Handle collection selection if --collection is provided without a value
    collection_path = None
    if args.collection == "select":
        collection_path = select_collection_file()
    elif args.collection:
        collection_path = args.collection
    else:
        logger.error("No collection specified. Use --collection to specify a collection file.")
        print("Error: No collection specified. Use --collection to specify a collection file.")
        print("       Or run with --collection without a value to select from available collections.")
        sys.exit(1)
    
    # Resolve collection path
    collection_path = resolve_collection_path(collection_path)
    logger.debug(f"Resolved collection path: {collection_path}")
    
    # Extract variables from collection if requested
    if args.extract_keys is not None:
        variables, collection_id, collection_data = extract_variables_from_collection(collection_path)
        
        if args.extract_keys == "interactive":
            # Interactive mode - prompt for values
            generate_variables_template(collection_path, "interactive")
            # Exit after interactive mode
            sys.exit(0)
        elif args.extract_keys == "print":
            # Print the list of keys
            print(f"\nFound {len(variables)} variables in collection {os.path.basename(collection_path)}:")
            for var in sorted(variables):
                print(f"  - {var}")
            print("\nTo create a template file with these variables:")
            print(f"python3 postman2burp.py --collection {os.path.basename(collection_path)} --extract-keys variables_template.json")
            print("\nOr use interactive mode to create a profile with values:")
            print(f"python3 postman2burp.py --collection {os.path.basename(collection_path)} --extract-keys")
            # Exit after printing variables
            sys.exit(0)
        else:
            # Generate template file
            generate_variables_template(collection_path, args.extract_keys)
            # Exit after generating template
            sys.exit(0)
    
    # Parse proxy settings - prioritize command line arguments over proxy
    # If proxy is empty (due to malformed proxy file), use DEFAULT_CONFIG values only if no command line args
    proxy_host = args.proxy_host or proxy.get("proxy_host") or DEFAULT_CONFIG["proxy_host"]
    proxy_port = args.proxy_port or proxy.get("proxy_port") or DEFAULT_CONFIG["proxy_port"]
    
    # Get target profile from args or proxy
    target_profile = args.target_profile or proxy.get("target_profile")
    if target_profile and not args.target_profile:
        logger.info(f"Using target profile from proxy: {target_profile}")
    
    if args.proxy:
        try:
            proxy_parts = args.proxy.split(":")
            proxy_host = proxy_parts[0]
            proxy_port = int(proxy_parts[1])
        except (IndexError, ValueError):
            logger.error("Invalid proxy format. Use host:port")
            return
    
    # Create the converter
    converter = PostmanToBurp(
        collection_path=collection_path,
        target_profile=target_profile,
        proxy_host=proxy_host,
        proxy_port=proxy_port,
        verify_ssl=args.verify_ssl or proxy.get("verify_ssl", False),
        auto_detect_proxy=True,  # Always enable auto-detection
        verbose=args.verbose or proxy.get("verbose", False)
    )
    
    # Set up logging to file if requested
    if args.log or proxy.get("log", False):
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        try:
            os.makedirs(logs_dir, exist_ok=True)
            logger.debug(f"Created logs directory: {logs_dir}")
        except Exception as e:
            logger.warning(f"Could not create logs directory: {e}")
        
        # Generate log filename based on collection name and timestamp
        collection_name = os.path.splitext(os.path.basename(collection_path))[0]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(logs_dir, f"{collection_name}_{timestamp}.json")
        
        converter.log_path = log_path
        logger.info(f"Results will be logged to: {log_path}")
    
    # Run the converter
    result = converter.run()
    if result["success"]:
        # Save proxy if requested
        if args.save_proxy:
            proxy_to_save = {
                "proxy_host": converter.proxy_host,
                "proxy_port": converter.proxy_port,
                "verify_ssl": args.verify_ssl,
                "verbose": args.verbose
            }
            
            # Save target_profile if provided
            if args.target_profile:
                proxy_to_save["target_profile"] = args.target_profile
                
            # Save collection_path if provided
            if collection_path:
                proxy_to_save["collection_path"] = os.path.basename(collection_path)
                
            # Save log option if enabled
            if args.log:
                proxy_to_save["log"] = True
            
            if save_proxy(proxy_to_save):
                logger.info("Configuration saved successfully")
                if args.target_profile:
                    logger.info(f"Target profile '{args.target_profile}' saved in proxy")
            else:
                logger.error("Failed to save proxy")

if __name__ == "__main__":
    main() 