#!/usr/bin/env python3
"""
Repl makes it easy to replace, load, and replay Postman collections through any proxy tool.

Usage:
    Basic Usage:
        python repl.py --collection <collection.json>
    
    Environment Variables:
        python repl.py --collection <collection.json> --insertion-point <environment.json>
    
    Proxy Settings:
        python repl.py --collection <collection.json> --proxy-host <host> --proxy-port <port>
    
    Log Options:
        python repl.py --collection <collection.json> --log --verbose
    
    Proxy & Behavior Configuration:
        python repl.py --collection <collection.json> --save-proxy
        
    Extract Variables:
        python repl.py --collection <collection.json> --extract-keys
        
    Encode Values:
        python repl.py --encode-url "param=value&other=value"
        python repl.py --encode-html "<script>alert(1)</script>"
        python repl.py --encode-double-url "param=value"
        python repl.py --encode-xml "<tag>content</tag>"
        python repl.py --encode-unicode "Café"
        python repl.py --encode-hex "ABC"
        python repl.py --encode-octal "ABC"
        python repl.py --encode-base64 "test string"
        python repl.py --encode-sql-char "ABC"
        python repl.py --encode-js "alert('test')"
        python repl.py --encode-css "#test"
    
    Encode Insertion Point Variables:
        python repl.py --encode-values <insertion_point.json>
        python repl.py --encode-values <insertion_point.json> --encoding html
        python repl.py --encode-values <insertion_point.json> --encoding url --variables "param1,param2"
    
    Authentication:
        python repl.py --collection <collection.json> --auth-basic <username:password>
        python repl.py --collection <collection.json> --auth-bearer <token>
        python repl.py --collection <collection.json> --auth-apikey <name:value:location>
        python repl.py --collection <collection.json> --auth-method <profile_name>
        python repl.py --list-auth
        python repl.py --create-auth
    
    Custom Headers:
        python repl.py --collection <collection.json> --header "X-API-Key:12345" --header "User-Agent:Repl"
    
    SSL Verification:
        python repl.py --collection <collection.json> --verify-ssl
        python repl.py --collection <collection.json> --no-verify-ssl


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

# Import the encoder module
from encoder import Encoder, process_insertion_point

# Configure logging
def configure_logging(log_level=logging.INFO):
    """
    Configure the logging system with the specified log level.
    
    Args:
        log_level: The logging level to use (default: logging.INFO)
        
    Returns:
        logger: Configured logger instance
    """
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Get and return the logger for the module
    return logging.getLogger(__name__)

# Initialize logger at module level
logger = configure_logging()

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
PROXIES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "proxies")
PROXY_FILE_PATH = os.path.join(PROXIES_DIR, "default.json")

# Path to variables templates directory
VARIABLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "insertion_points")

# ANSI color codes
COLOR_ORANGE = "\033[38;5;208m"  # Orange color
COLOR_RESET = "\033[0m"          # Reset to default

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
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "proxies")
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "default.json")

# Path to variables templates directory
VARIABLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "insertion_points")

# Function to check if terminal supports colors
def supports_colors():
    """Check if the terminal supports colors."""
    if not sys.stdout.isatty():
        return False
    
    # Check platform-specific color support
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or 'ANSICON' in os.environ)
    
    # isatty is not always implemented, so we fallback to supported_platform
    return supported_platform

BANNER_TEXT = """
                                                                                ████       
             ██████████                                                         ████       
          ████████████████                                                      ████       
        ███████████████████       ████████    ████████████    █████████████     ████       
       ███████        ██████      ████████  ███████████████   ███████████████   ████       
      ███  █  ███████  █  ███     █████     █████      █████  ████       ████   ████       
      ██  █  ████ ████  █  ██     █████     ████████████████  ████       ████   ████       
      █████  ████ ████  ██████    █████     ████████████████  ████       ████   ████       
      ██████  ███████   █████     █████     ████              ████       ████   ████       
       ██████    ██   ███████     █████     ████████████████  ███████████████   ████       
        ████           █████      █████     ████████████████  ███████████████   ████       
         ██              █                                    ████                         
                                                              ████                         
                                                              ████           

              Replace, Load, and Replay Postman Collections | Author: @daramdo
                      Version 1.0.0 | Apache License, Version 2.0
"""

# Define colored banner (will be used if terminal supports colors)
BANNER = f"{COLOR_ORANGE}{BANNER_TEXT}{COLOR_RESET}" if supports_colors() else BANNER_TEXT

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
    logger.debug(f"load_proxy called with proxy_path: {proxy_path}")
    
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
                logger.debug(f"Created config/proxies directory at {CONFIG_DIR}")
            except Exception as e:
                logger.warning(f"Could not create config/proxies directory: {e}")
                return False
        
        if os.path.exists(proxy_file_path):
            # Validate the JSON file before loading
            is_valid, parsed_proxy = validate_json_file(proxy_file_path)
            
            if is_valid and parsed_proxy:
                # Handle new proxy structure with nested 'proxy' object
                if 'proxy' in parsed_proxy:
                    proxy_config = parsed_proxy['proxy']
                    proxy['proxy_host'] = proxy_config.get('host', DEFAULT_CONFIG['proxy_host'])
                    proxy['proxy_port'] = proxy_config.get('port', DEFAULT_CONFIG['proxy_port'])
                    proxy['verify_ssl'] = proxy_config.get('verify_ssl', DEFAULT_CONFIG['verify_ssl'])
                    
                    # Store additional proxy-specific settings
                    if 'type' in proxy_config:
                        proxy['proxy_type'] = proxy_config['type']
                    if 'username' in proxy_config:
                        proxy['proxy_username'] = proxy_config['username']
                    if 'password' in proxy_config:
                        proxy['proxy_password'] = proxy_config['password']
                else:
                    # Handle legacy format - only copy proxy-specific settings
                    proxy_keys = ['proxy_host', 'proxy_port', 'verify_ssl', 'proxy_type', 'proxy_username', 'proxy_password']
                    for key in proxy_keys:
                        if key in parsed_proxy:
                            proxy[key] = parsed_proxy[key]
                
                # Add custom headers if present
                if 'headers' in parsed_proxy:
                    proxy['headers'] = parsed_proxy['headers']
                
                # Add description if present
                if 'description' in parsed_proxy:
                    proxy['description'] = parsed_proxy['description']
                
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
    except Exception as e:
        logger.error(f"Error loading proxy: {e}")
        # Return empty dictionary to ensure we rely only on command-line arguments
        return {}
        
    return proxy

def check_proxy_connection(host: str, port: int) -> bool:
    """
    Check if a proxy is running at the specified host and port.
    
    Args:
        host: Proxy host
        port: Proxy port
        
    Returns:
        bool: True if the proxy is running, False otherwise
    """
    try:
        # Try to resolve the hostname to an IP address
        ip_address = socket.gethostbyname(host)
        logger.debug(f"Resolved {host} to IP: {ip_address}")
        
        # Create a socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # 2 second timeout
        
        # Try to connect to the proxy
        result = sock.connect_ex((ip_address, port))
        sock.close()
        
        if result == 0:
            logger.debug(f"Proxy connection successful at {host}:{port}")
            return True
        else:
            logger.debug(f"Proxy connection failed at {host}:{port} with error code {result}")
            return False
    except Exception as e:
        logger.debug(f"Error checking proxy at {host}:{port}: {str(e)}")
        return False

def verify_proxy_with_request(host: str, port: int) -> bool:
    """
    Verify proxy connection by making a test request.
    
    Args:
        host: Proxy host
        port: Proxy port
        
    Returns:
        bool: True if the proxy is working, False otherwise
    """
    try:
        # Set up proxy
        proxy_url = f"http://{host}:{port}"
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        # Make a test request to a reliable endpoint
        logger.debug(f"Testing proxy with request to httpbin.org through {proxy_url}")
        response = requests.get(
            "http://httpbin.org/get",
            proxies=proxies,
            timeout=5,
            verify=False  # Disable SSL verification for the test
        )
        
        # Check if the response contains the proxy information
        response_json = response.json()
        origin = response_json.get("origin", "")
        
        logger.debug(f"Response from httpbin.org: status={response.status_code}, origin={origin}")
        
        # If the response contains the proxy information, the proxy is working
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Error verifying proxy with request: {str(e)}")
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
    
    # Create a simple target insertion_point with direct key-value pairs
    insertion_point = {
        "id": f"auto-generated-{int(time.time())}",
        "name": collection_data.get("info", {}).get("name", "Environment"),
        "values": [],
        "_postman_variable_scope": "environment",
        "_postman_exported_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "_postman_exported_using": "Repl/Interactive",
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
    print("- Target insertion_point values take precedence over collection variables")
    
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
                insertion_point["values"].append({
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
                insertion_point["values"].append({
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
    filename = f"{collection_id}_{int(time.time())}.json" if collection_id else f"insertion_point_{int(time.time())}.json"
    
    # Save to insertion_points directory
    output_path = os.path.join(VARIABLES_DIR, filename)
    
    try:
        # Save insertion_point
        with open(output_path, 'w') as f:
            json.dump(insertion_point, f, indent=2)
        
        # Print success message
        relative_path = os.path.relpath(output_path)
        collection_name = os.path.basename(collection_path)
        
        print(f"\n[✓] Successfully created target insertion_point with {variables_with_values} variables at {relative_path}")
        print(f"\nNext command to run:")
        print(f"python3 repl.py --collection \"{collection_name}\" --insertion-point\"{filename}\"")
        
        # Exit after creating the insertion_point
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Failed to save insertion_point: {e}")
        sys.exit(1)

def save_proxy(proxy: Dict) -> bool:
    """
    Save proxy to default.json file.
    
    Args:
        proxy: Configuration dictionary to save
        
    Returns:
        bool: True if the proxy was saved successfully, False otherwise
    """
    logger.debug(f"save_proxy called with proxy: {proxy}")
    
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
            "target_insertion_point": proxy.get("target_insertion_point", ""),
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
    List all proxy files in the config/proxies directory and allow the user to select one.
    Returns the path to the selected proxy file.
    """
    logger.info("Listing available proxy files")
    
    # Get all JSON files in the config/proxies directory
    proxy_profiles = []
    try:
        for file in os.listdir(CONFIG_DIR):
            if file.endswith('.json'):
                proxy_profiles.append(file)
    except Exception as e:
        logger.error(f"Error listing config/proxies directory: {e}")
        return CONFIG_FILE_PATH
    
    # If no proxy profiles found, return the default
    if not proxy_profiles:
        logger.info("No proxy profiles found, using default proxy")
        return CONFIG_FILE_PATH
    
    # If only one proxy file found, use it without prompting
    if len(proxy_profiles) == 1:
        proxy_path = os.path.join(CONFIG_DIR, proxy_profiles[0])
        logger.info(f"Using proxy file: {proxy_profiles[0]}")
        return proxy_path
    
    # Multiple proxy profiles found, always prompt user to select
    print("\nMultiple proxy proxy profiles found. Please select one:")
    for i, file in enumerate(proxy_profiles, 1):
        # Highlight the default proxy file
        if file == os.path.basename(CONFIG_FILE_PATH):
            print(f"  {i}. {file} (default)")
        else:
            print(f"  {i}. {file}")
    
    print("  n. Create a new proxy file")
    print("  q. Quit")
    
    while True:
        choice = input("\nEnter your choice (1-{0}/n/q): ".format(len(proxy_profiles)))
        
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
            if 0 <= choice_idx < len(proxy_profiles):
                selected_file = proxy_profiles[choice_idx]
                proxy_path = os.path.join(CONFIG_DIR, selected_file)
                logger.info(f"User selected proxy file: {selected_file}")
                return proxy_path
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(proxy_profiles)}, 'n', or 'q'.")
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

def extract_collection_id(collection_path: str) -> Optional[str]:
    """
    Extract the Postman collection ID from a collection file.
    
    Args:
        collection_path: Path to the collection file
        
    Returns:
        The collection ID if found, None otherwise
    """
    if not collection_path:
        return None
        
    try:
        with open(collection_path, 'r') as f:
            collection_data = json.load(f)
            if "info" in collection_data and "_postman_id" in collection_data["info"]:
                return collection_data["info"]["_postman_id"]
    except Exception as e:
        logger.debug(f"Could not extract collection ID: {e}")
    
    return None

class Repl:
    def __init__(self, collection_path: str, target_insertion_point: str = None, proxy_host: str = None, proxy_port: int = None,
                 verify_ssl: bool = False, auto_detect_proxy: bool = True,
                 verbose: bool = False, custom_headers: List[str] = None, auth_method: Dict = None):
        """
        Initialize the Repl converter.
        
        Args:
            collection_path: Path to the Postman collection JSON file
            target_insertion_point: Path to the Postman environment JSON file
            proxy_host: Proxy host
            proxy_port: Proxy port
            verify_ssl: Whether to verify SSL certificates
            auto_detect_proxy: Whether to auto-detect proxy settings
            verbose: Whether to enable verbose logging
            custom_headers: List of custom headers in format "Key:Value"
            auth_method: Label of the authentication method to use
        """
        self.collection_path = collection_path
        self.target_insertion_point = target_insertion_point
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.verify_ssl = verify_ssl
        self.auto_detect_proxy = auto_detect_proxy
        self.log_path = None
        self.verbose = verbose
        self.custom_headers = {}
        self.auth_method = auth_method
        
        # Process custom headers if provided
        if custom_headers:
            for header in custom_headers:
                if ":" in header:
                    key, value = header.split(":", 1)
                    self.custom_headers[key.strip()] = value.strip()
        
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
        
        # Store collection variables in a separate dictionary to avoid overriding target insertion_point variables
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
        
        # Only add collection variables if they don't exist in the environment (target insertion_point takes precedence)
        for key, value in collection_variables.items():
            if key not in self.environment:
                self.environment[key] = value
                if self.verbose:
                    self.logger.debug(f"Using collection variable: {key} = {value}")
            else:
                if self.verbose:
                    self.logger.debug(f"Ignoring collection variable '{key}' as it's already defined in target insertion_point")
        
        self.logger.info(f"Loaded collection: {self.collection_name} ({self.collection_id})")
        return True
    
    def load_insertion_point(self) -> bool:
        """Load variables from a target insertion_point file."""
        if not self.target_insertion_point:
            self.logger.debug("No target insertion_point specified")
            return True

        # First try the path as provided
        insertion_point_path = self.target_insertion_point
        
        # If the file doesn't exist, try looking in the insertion_points directory
        if not os.path.exists(insertion_point_path):
            insertion_points_dir_path = os.path.join(VARIABLES_DIR, os.path.basename(insertion_point_path))
            if os.path.exists(insertion_points_dir_path):
                self.logger.debug(f"Insertion Point not found at {insertion_point_path}, using {insertion_points_dir_path} instead")
                insertion_point_path = insertion_points_dir_path
            else:
                self.logger.warning(f"Insertion Point not found at {insertion_point_path} or in insertion_points directory")

        # Validate insertion_point file
        valid, insertion_point_data = validate_json_file(insertion_point_path)
        if not valid or not insertion_point_data:
            self.logger.error(f"Invalid insertion_point file: {self.target_insertion_point}")
            return False

        if self.verbose:
            self.logger.debug(f"Loading insertion_point: {insertion_point_path}")
            self.logger.debug(f"Insertion Point structure: {list(insertion_point_data.keys())}")
            
        # Process the insertion point to apply any encodings
        insertion_point_data = process_insertion_point(insertion_point_data)

        # Check if this is a Postman environment format (with values array)
        if "values" in insertion_point_data and isinstance(insertion_point_data["values"], list):
            self.logger.debug("Loading Postman environment format insertion_point")
            for var in insertion_point_data["values"]:
                if "key" in var and "value" in var and var.get("enabled", True):
                    key = var["key"]
                    value = var["value"]
                    self.environment[key] = value
                    if self.verbose:
                        self.logger.debug(f"Loaded variable from insertion_point: {key}")
        else:
            # Load variables from insertion_point - simple key-value structure
            self.logger.debug("Loading simple key-value format insertion_point")
            for key, value in insertion_point_data.items():
                # Skip metadata fields
                if key in ["id", "collection_id", "created_at", "name", "description"]:
                    continue
                    
                # Add to environment dictionary
                self.environment[key] = value
                if self.verbose:
                    self.logger.debug(f"Loaded variable from insertion_point: {key}")

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
        
        # Add custom headers if any
        if self.custom_headers:
            self.logger.debug(f"Adding {len(self.custom_headers)} custom headers")
            for key, value in self.custom_headers.items():
                headers[key] = self.replace_variables(value)
                self.logger.debug(f"Added custom header: {key}")
        
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
        
        # Add custom headers from proxy configuration if available
        if hasattr(self, 'proxy_config') and 'headers' in self.proxy_config:
            for header_name, header_value in self.proxy_config['headers'].items():
                # Only add if not already set in the request
                if header_name not in headers:
                    headers[header_name] = header_value
                    self.logger.debug(f"Added proxy header: {header_name}: {header_value}")
        
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
        
        # Parse URL query parameters
        params = {}
        cookies = {}
        
        # Parse URL query parameters
        url_parts = url.split('?', 1)
        if len(url_parts) > 1:
            query_string = url_parts[1]
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
        
        # Get authentication object if configured
        auth = None
        if hasattr(self, 'auth_method') and self.auth_method:
            try:
                # Import auth module here to avoid circular imports
                from modules.auth import auth_manager
                
                # Handle dictionary format for direct auth methods
                if isinstance(self.auth_method, dict):
                    auth_type = self.auth_method.get('type')
                    
                    if auth_type == 'basic':
                        username = self.auth_method.get('username', '')
                        password = self.auth_method.get('password', '')
                        auth = requests.auth.HTTPBasicAuth(username, password)
                        self.logger.info(f"Applied Basic Authentication for user: {username}")
                    
                    elif auth_type == 'bearer':
                        token = self.auth_method.get('token', '')
                        headers['Authorization'] = f"Bearer {token}"
                        self.logger.info("Applied Bearer Token Authentication")
                    
                    elif auth_type == 'api_key':
                        key = self.auth_method.get('key', '')
                        location = self.auth_method.get('location', 'header')
                        name = self.auth_method.get('name', 'X-API-Key')
                        
                        if location.lower() == 'header':
                            headers[name] = key
                        elif location.lower() == 'query':
                            params[name] = key
                        elif location.lower() == 'cookie':
                            cookies[name] = key
                        
                        self.logger.info(f"Applied API Key Authentication ({location})")
                    
                    elif auth_type == 'profile':
                        profile = self.auth_method.get('profile')
                        if auth_manager.get_auth_method(profile):
                            auth_manager.set_active_method(profile)
                            auth = auth_manager.get_auth()
                            if not auth:
                                headers, params, cookies = auth_manager.apply_auth(headers, params, cookies)
                            self.logger.info(f"Applied authentication profile: {profile}")
                        else:
                            self.logger.warning(f"Authentication profile not found: {profile}")
                
                # Legacy string format for profile names
                elif isinstance(self.auth_method, str) and auth_manager.get_auth_method(self.auth_method):
                    auth_manager.set_active_method(self.auth_method)
                    
                    # Get the auth object for requests
                    auth = auth_manager.get_auth()
                    
                    # If auth object is not available, apply auth manually
                    if not auth:
                        headers, params, cookies = auth_manager.apply_auth(headers, params, cookies)
                    
                    self.logger.info(f"Applied authentication method: {self.auth_method}")
                else:
                    self.logger.warning(f"Authentication method not recognized: {self.auth_method}")
            except Exception as e:
                self.logger.error(f"Error applying authentication: {str(e)}")
                self.logger.debug(f"Authentication error details:", exc_info=True)
        
        # Rebuild URL with updated query parameters
        if params:
            query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
            url = f"{url_parts[0]}?{query_string}" if len(url_parts) > 1 else f"{url}?{query_string}"
        
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
            
            # Log authentication details
            if auth:
                self.logger.debug(f"Using authentication object: {type(auth).__name__}")
            elif 'Authorization' in headers:
                self.logger.debug(f"Using Authorization header: {headers['Authorization'][:10]}...")
            
            # Send request (using session's proxy settings)
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                cookies=cookies,
                auth=auth,
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
                    "description": f"Results of scanning {self.collection.get('info', {}).get('name', 'Unknown Collection')} with repl",
                    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                    "_exporter_id": "repl"
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
                        "target_insertion_point": self.target_insertion_point,
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
        
        # Load insertion_point
        if not self.load_insertion_point():
            return {"success": False, "message": "Failed to load insertion_point"}
        
        # Print all variables for reference
        print("\n=== Available Variables ===")
        print("Target Insertion Point Variables (these take precedence):")
        if self.environment:
            for key, value in sorted(self.environment.items()):
                # Mask sensitive values
                if "token" in key.lower() or "key" in key.lower() or "secret" in key.lower() or "password" in key.lower():
                    print(f"  {key} = ******** (will be used)")
                else:
                    print(f"  {key} = {value} (will be used)")
        else:
            print("  No target insertion_point variables found")
        
        # Print collection variables
        print("\nCollection Variables (used only if not in target insertion_point):")
        if "variable" in self.collection and self.collection["variable"]:
            for var in sorted(self.collection["variable"], key=lambda x: x.get("key", "")):
                if "key" in var and "value" in var:
                    key = var["key"]
                    value = var["value"]
                    # Check if this variable is overridden by target insertion_point
                    is_overridden = key in self.environment
                    status = "(overridden by target insertion_point)" if is_overridden else "(will be used)"
                    
                    # Mask sensitive values
                    if "token" in key.lower() or "key" in key.lower() or "secret" in key.lower() or "password" in key.lower():
                        print(f"  {key} = ******** {status}")
                    else:
                        print(f"  {key} = {value} {status}")
        else:
            print("  No collection variables found")
        
        print("\nNote: Target insertion_point variables take precedence over collection variables.")
        print("To override a collection variable, add it to your target insertion_point.")
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
                insertion_point_arg = f"--insertion-point'{os.path.basename(self.target_insertion_point)}'" if self.target_insertion_point else ""
                
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
    """
    # Parse command line arguments first to check for proxy option
    parser = argparse.ArgumentParser(description="Replace, Load, and Replay Postman collections through any proxy tool")
    parser.add_argument("--collection", nargs="?", const="select", help="Path to Postman collection JSON file (supports Postman 2.1 schema). Specify no path to select interactively.")
    
    # Insertion Point options
    env_group = parser.add_argument_group("INSERTION POINT OPTIONS")
    env_group.add_argument("--insertion-point", help="Path to insertion_point JSON file with values to replace variables in the collection")
    env_group.add_argument("--extract-keys", nargs="?", const="interactive", metavar="OUTPUT_FILE",
                          help="Extract variables from collection. Specify no file to enter interactive mode. Specify 'print' to display variables. Specify a filename to save template.")
    
    # Authentication options
    auth_group = parser.add_argument_group("AUTHENTICATION OPTIONS")
    auth_group.add_argument("--auth", nargs="?", const="select", help="Use a saved authentication profile. Specify no value to select interactively.")
    auth_group.add_argument("--list-auth", action="store_true", help="List all saved authentication profiles")
    auth_group.add_argument("--create-auth", action="store_true", help="Create a new authentication profile interactively")
    auth_group.add_argument("--auth-basic", nargs=2, metavar=("USERNAME", "PASSWORD"), help="Use Basic Authentication with the specified username and password")
    auth_group.add_argument("--auth-bearer", help="Use Bearer Token Authentication with the specified token")
    auth_group.add_argument("--auth-api-key", nargs=2, metavar=("KEY", "LOCATION"), help="Use API Key Authentication with the specified key and location (header, query, or cookie)")
    auth_group.add_argument("--auth-api-key-name", help="Name of the API Key header/parameter/cookie (default: X-API-Key)")
    
    # OAuth1 arguments
    auth_group.add_argument("--auth-oauth1", nargs=2, metavar=("CONSUMER_KEY", "CONSUMER_SECRET"), help="Use OAuth1 Authentication with the specified consumer key and secret")
    auth_group.add_argument("--auth-oauth1-token", nargs=2, metavar=("TOKEN", "TOKEN_SECRET"), help="OAuth1 token and token secret (required for OAuth1)")
    auth_group.add_argument("--auth-oauth1-signature", help="OAuth1 signature method (default: HMAC-SHA1)")
    
    # OAuth2 arguments
    auth_group.add_argument("--auth-oauth2", nargs=2, metavar=("CLIENT_ID", "CLIENT_SECRET"), help="Use OAuth2 Authentication with the specified client ID and secret")
    auth_group.add_argument("--auth-oauth2-token-url", help="OAuth2 token endpoint URL (required for OAuth2)")
    auth_group.add_argument("--auth-oauth2-refresh-url", help="OAuth2 refresh token endpoint URL")
    auth_group.add_argument("--auth-oauth2-grant", choices=["client_credentials", "password", "refresh_token"], default="client_credentials", help="OAuth2 grant type (default: client_credentials)")
    auth_group.add_argument("--auth-oauth2-username", help="Username for OAuth2 password grant")
    auth_group.add_argument("--auth-oauth2-password", help="Password for OAuth2 password grant")
    auth_group.add_argument("--auth-oauth2-scope", help="Space-separated list of OAuth2 scopes")
    
    # Proxy options
    proxy_group = parser.add_argument_group("PROXY OPTIONS")
    proxy_group.add_argument("--proxy", help="Proxy in host:port format")
    proxy_group.add_argument("--proxy-host", help="Proxy host")
    proxy_group.add_argument("--proxy-port", type=int, help="Proxy port")
    proxy_group.add_argument("--verify-ssl", action="store_true", help="Verify SSL certificates")
    
    # Output options
    output_group = parser.add_argument_group("OUTPUT OPTIONS")
    output_group.add_argument("--log", action="store_true", help="Enable logging to file (saves detailed request results to logs directory)")
    output_group.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    output_group.add_argument("--save-proxy", action="store_true", help="Save current settings as default proxy")
    
    # Proxy insertion_point options
    proxy_group = parser.add_argument_group("PROXY INSERTION POINTS")
    proxy_group.add_argument("--proxy-profile", nargs="?", const="select", 
                             help="Use specific proxy insertion_point or select from available insertion_points if no file specified. Omit to select when multiple insertion_points exist.")
    
    # Custom header options
    header_group = parser.add_argument_group("CUSTOM HEADERS")
    header_group.add_argument("--header", action="append", 
                             help="Add custom header in format 'Key:Value'. Can be specified multiple times. "
                                  "These headers will be added to all requests and will override any existing headers with the same name."
                                  " Example: --header 'X-API-Key:12345' --header 'User-Agent:Repl'")

    print_banner = parser.add_argument("--banner", action="store_true", help="Print the banner")
    
    # Add encoding command-line options
    parser.add_argument('--encode-url', type=str, help='URL encode a string')
    parser.add_argument('--encode-double-url', type=str, help='Double URL encode a string')
    parser.add_argument('--encode-html', type=str, help='HTML encode a string')
    parser.add_argument('--encode-xml', type=str, help='XML encode a string')
    parser.add_argument('--encode-unicode', type=str, help='Unicode escape a string')
    parser.add_argument('--encode-hex', type=str, help='Hex escape a string')
    parser.add_argument('--encode-octal', type=str, help='Octal escape a string')
    parser.add_argument('--encode-base64', type=str, help='Base64 encode a string')
    parser.add_argument('--encode-sql-char', type=str, help='SQL CHAR() encode a string')
    parser.add_argument('--encode-js', type=str, help='JavaScript escape a string')
    parser.add_argument('--encode-css', type=str, help='CSS escape a string')
    
    args = parser.parse_args()
    
    # Handle encoding commands if any are specified
    encoding_args = {
        'url': args.encode_url,
        'double_url': args.encode_double_url,
        'html': args.encode_html,
        'xml': args.encode_xml,
        'unicode': args.encode_unicode,
        'hex': args.encode_hex,
        'octal': args.encode_octal,
        'base64': args.encode_base64,
        'sql_char': args.encode_sql_char,
        'js_escape': args.encode_js,
        'css_escape': args.encode_css
    }
    
    # Check if any encoding option was specified
    for encoding_type, value in encoding_args.items():
        if value:
            try:
                encoded = Encoder.encode(value, encoding_type)
                print(f"Original: {value}")
                print(f"Encoded ({encoding_type}): {encoded}")
                return
            except Exception as e:
                logger.error(f"Encoding error: {e}")
                return
    
    # Continue with normal execution if no encoding was requested
    # Configure logging
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_date_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format=log_format, datefmt=log_date_format)
    logger = logging.getLogger(__name__)
    
    # Import auth module
    try:
        from modules.auth import auth_manager, BasicAuth, BearerToken, ApiKey, OAuth1, OAuth2
    except ImportError:
        logger.error("Failed to import authentication module. Authentication features will not be available.")
        auth_manager = None
    
    # List authentication profiles if requested (independent of other options)
    if args.list_auth and auth_manager:
        auth_methods = auth_manager.get_auth_methods()
        if auth_methods:
            print("\nAvailable authentication profiles:")
            for i, method in enumerate(auth_methods, 1):
                auth_obj = auth_manager.get_auth_method(method)
                auth_type = auth_obj.type if auth_obj else "unknown"
                print(f"  {i}. {method} ({auth_type})")
        else:
            print("\nNo authentication profiles found.")
            print("Create one with --create-auth or use direct authentication options.")
        sys.exit(0)
    
    # Create authentication profile if requested (independent of other options)
    if args.create_auth and auth_manager:
        print("\nCreate a new authentication profile:")
        print("1. Basic Authentication")
        print("2. Bearer Token (Fixed)")
        print("3. Bearer Token (Dynamic)")
        print("4. API Key / Custom Token (Fixed)")
        print("5. API Key / Custom Token (Dynamic)")
        
        while True:
            choice = input("\nSelect authentication type (1-5): ")
            if choice in ["1", "2", "3", "4", "5"]:
                break
            print("Invalid choice. Please enter a number between 1 and 5.")
        
        # Get collection ID if available
        collection_id = None
        if args.collection:
            collection_path = resolve_collection_path(args.collection)
            collection_id = extract_collection_id(collection_path)
        
        # Suggest a label based on collection ID if available
        suggested_label = ""
        if collection_id:
            auth_type_suffix = {
                "1": "basic",
                "2": "bearer",
                "3": "bearer_dynamic",
                "4": "apikey",
                "5": "apikey_dynamic"
            }
            suggested_label = f"{collection_id}_{auth_type_suffix[choice]}"
            label = input(f"Enter a unique label for this authentication profile [{suggested_label}]: ")
            if not label:
                label = suggested_label
        else:
            label = input("Enter a unique label for this authentication profile: ")
        
        if choice == "1":  # Basic Authentication
            username = input("Enter username: ")
            password = input("Enter password: ")
            auth_manager.create_basic_auth(label, username, password)
            print(f"Basic Authentication profile '{label}' created successfully.")
        
        elif choice == "2":  # Bearer Token (Fixed)
            token = input("Enter Bearer token: ")
            auth_manager.create_bearer_token(label, token)
            print(f"Bearer Token profile '{label}' created successfully.")
        
        elif choice == "3":  # Bearer Token (Dynamic)
            token_url = input("Enter token URL: ")
            auth_manager.create_bearer_token(label, None, True, token_url)
            print(f"Dynamic Bearer Token profile '{label}' created successfully.")
        
        elif choice == "4":  # API Key (Fixed)
            key = input("Enter API key: ")
            print("\nSelect API key location:")
            print("1. Header")
            print("2. Query Parameter")
            print("3. Cookie")
            
            while True:
                location_choice = input("\nSelect location (1-3): ")
                if location_choice in ["1", "2", "3"]:
                    break
                print("Invalid choice. Please enter a number between 1 and 3.")
            
            location_map = {"1": "header", "2": "query", "3": "cookie"}
            location = location_map[location_choice]
            
            param_name = input(f"Enter {location} parameter name [X-API-Key]: ")
            if not param_name:
                param_name = "X-API-Key"
            
            auth_manager.create_api_key(label, key, location, param_name)
            print(f"API Key profile '{label}' created successfully.")
        
        elif choice == "5":  # API Key (Dynamic)
            key_url = input("Enter API key URL: ")
            print("\nSelect API key location:")
            print("1. Header")
            print("2. Query Parameter")
            print("3. Cookie")
            
            while True:
                location_choice = input("\nSelect location (1-3): ")
                if location_choice in ["1", "2", "3"]:
                    break
                print("Invalid choice. Please enter a number between 1 and 3.")
            
            location_map = {"1": "header", "2": "query", "3": "cookie"}
            location = location_map[location_choice]
            
            param_name = input(f"Enter {location} parameter name [X-API-Key]: ")
            if not param_name:
                param_name = "X-API-Key"
            
            auth_manager.create_api_key_dynamic(label, key_url, location, param_name)
            print(f"Dynamic API Key profile '{label}' created successfully.")
        
        sys.exit(0)
    
    # Print banner if requested (independent of other options)
    if args.banner:
        # Use colored banner if terminal supports colors, otherwise use plain text
        print(BANNER)
        # If only the banner was requested, exit
        if not args.collection and not args.extract_keys:
            sys.exit(0)
    
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
    
    # Handle authentication options
    
    # Import auth module
    try:
        from modules.auth import auth_manager, BasicAuth, BearerToken, ApiKey, OAuth1, OAuth2
    except ImportError:
        logger.error("Failed to import authentication module. Authentication features will not be available.")
        auth_manager = None
    
    # Select authentication profile if requested
    if args.auth == "select" and auth_manager:
        auth_methods = auth_manager.get_auth_methods()
        if auth_methods:
            print("\nSelect an authentication profile:")
            for i, method in enumerate(auth_methods, 1):
                auth_obj = auth_manager.get_auth_method(method)
                auth_type = auth_obj.type if auth_obj else "unknown"
                print(f"  {i}. {method} ({auth_type})")
            
            while True:
                choice = input("\nEnter profile number (or 'q' to quit): ")
                if choice.lower() == 'q':
                    sys.exit(0)
                
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(auth_methods):
                        auth_method = auth_methods[index]
                        break
                    else:
                        print("Invalid choice. Please enter a valid number.")
                except ValueError:
                    print("Invalid input. Please enter a number or 'q'.")
        else:
            print("\nNo authentication profiles found.")
            print("Create one with --create-auth or use direct authentication options.")
            sys.exit(1)
    elif args.auth and auth_manager:
        # Use specified profile
        if auth_manager.get_auth_method(args.auth):
            auth_method = args.auth
        else:
            logger.error(f"Authentication profile not found: {args.auth}")
            print(f"Error: Authentication profile not found: {args.auth}")
            print("Use --list-auth to see available profiles or --create-auth to create a new one.")
            sys.exit(1)
    
    # Handle direct authentication options
    if args.auth_basic and auth_manager:
        username, password = args.auth_basic
        
        # Get collection ID if available
        collection_id = extract_collection_id(collection_path)
        
        # Use collection ID in the label if available
        if collection_id:
            temp_label = f"{collection_id}_basic"
        else:
            temp_label = f"temp_basic_{int(time.time())}"
            
        auth_manager.create_basic_auth(temp_label, username, password)
        auth_method = temp_label
    
    if args.auth_bearer and auth_manager:
        # Get collection ID if available
        collection_id = extract_collection_id(collection_path)
        
        # Use collection ID in the label if available
        if collection_id:
            temp_label = f"{collection_id}_bearer"
        else:
            temp_label = f"temp_bearer_{int(time.time())}"
            
        auth_manager.create_bearer_token(temp_label, args.auth_bearer)
        auth_method = temp_label
    
    if args.auth_api_key and auth_manager:
        key, location = args.auth_api_key
        if location.lower() not in ["header", "query", "cookie"]:
            logger.error(f"Invalid API key location: {location}. Must be 'header', 'query', or 'cookie'.")
            print(f"Error: Invalid API key location: {location}. Must be 'header', 'query', or 'cookie'.")
            sys.exit(1)
        
        # Get collection ID if available
        collection_id = extract_collection_id(collection_path)
        
        param_name = args.auth_api_key_name or "X-API-Key"
        
        # Use collection ID in the label if available
        if collection_id:
            temp_label = f"{collection_id}_apikey_{location.lower()}"
        else:
            temp_label = f"temp_apikey_{int(time.time())}"
            
        auth_manager.create_api_key(temp_label, key, location.lower(), param_name)
        auth_method = temp_label
    
    # Extract variables from collection if requested - do this before proxy selection
    # since we don't need a proxy for extraction
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
            print(f"python3 repl.py --collection {os.path.basename(collection_path)} --extract-keys variables_template.json")
            print("\nOr use interactive mode to create a insertion_point with values:")
            print(f"python3 repl.py --collection {os.path.basename(collection_path)} --extract-keys")
            # Exit after printing variables
            sys.exit(0)
        else:
            # Generate template file
            generate_variables_template(collection_path, args.extract_keys)
            # Exit after generating template
            sys.exit(0)
    
    # Only handle proxy selection if we're not extracting keys
    # Handle proxy selection
    proxy_path = None
    if args.proxy == "select":
        proxy_path = select_proxy_file()
    elif args.proxy:
        proxy_path = args.proxy
    else:
        # Check if multiple proxy files exist
        try:
            proxy_profiles = [f for f in os.listdir(CONFIG_DIR) if f.endswith('.json')]
            if len(proxy_profiles) > 1:
                logger.info("Multiple proxy profiles found, prompting user to select")
                proxy_path = select_proxy_file()
            elif len(proxy_profiles) == 1:
                proxy_path = os.path.join(CONFIG_DIR, proxy_profiles[0])
                logger.info(f"Using the only available proxy file: {proxy_profiles[0]}")
            else:
                logger.info("No proxy profiles found, using default proxy")
        except Exception as e:
            logger.warning(f"Error listing proxies directory: {e}")
            logger.info("Using default proxy")
    
    # Load proxy
    proxy = load_proxy(proxy_path)
    
    # Parse proxy settings - prioritize command line arguments over proxy
    # If proxy is empty (due to malformed proxy file), use DEFAULT_CONFIG values only if no command line args
    proxy_host = args.proxy_host or proxy.get("proxy_host") or DEFAULT_CONFIG["proxy_host"]
    proxy_port = args.proxy_port or proxy.get("proxy_port") or DEFAULT_CONFIG["proxy_port"]
    
    # Get target insertion_point from args or proxy
    target_insertion_point = args.insertion_point or proxy.get("target_insertion_point")
    if target_insertion_point and not args.insertion_point:
        logger.info(f"Using target insertion_point from proxy: {target_insertion_point}")
    
    if args.proxy:
        try:
            proxy_parts = args.proxy.split(":")
            proxy_host = proxy_parts[0]
            proxy_port = int(proxy_parts[1])
        except (IndexError, ValueError):
            logger.error("Invalid proxy format. Use host:port")
            return
    
    # Initialize auth_method
    auth_method = None
    if args.auth:
        auth_method = {"type": "profile", "profile": args.auth}
    elif args.auth_basic:
        auth_method = {"type": "basic", "username": args.auth_basic[0], "password": args.auth_basic[1]}
    elif args.auth_bearer:
        auth_method = {"type": "bearer", "token": args.auth_bearer}
    elif args.auth_api_key:
        key_name = args.auth_api_key_name or "X-API-Key"
        auth_method = {"type": "api_key", "key": args.auth_api_key[0], "location": args.auth_api_key[1], "name": key_name}
    
    # Create the converter
    converter = Repl(
        collection_path=collection_path,
        target_insertion_point=target_insertion_point,
        proxy_host=proxy_host,
        proxy_port=proxy_port,
        verify_ssl=args.verify_ssl or proxy.get("verify_ssl", False),
        auto_detect_proxy=True,  # Always enable auto-detection
        verbose=args.verbose or proxy.get("verbose", False),
        custom_headers=args.header,
        auth_method=auth_method
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
            
            # Save target_insertion_point if provided
            if args.insertion_point:
                proxy_to_save["target_insertion_point"] = args.insertion_point
                
            # Save collection_path if provided
            if collection_path:
                proxy_to_save["collection_path"] = os.path.basename(collection_path)
                
            # Save log option if enabled
            if args.log:
                proxy_to_save["log"] = True
            
            if save_proxy(proxy_to_save):
                logger.info("Configuration saved successfully")
                if args.insertion_point:
                    logger.info(f"Target insertion_point '{args.insertion_point}' saved in proxy")
            else:
                logger.error("Failed to save proxy")

if __name__ == "__main__":
    main() 