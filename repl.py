#!/usr/bin/env python3
"""
Replace, Load, and Replay Postman collections through any proxy tool.

This script allows you to:
1. Load a Postman collection
2. Replace variables with values from an insertion point file
3. Send requests through a proxy
4. Save results

Basic Usage:
    python repl.py --collection collections/my_collection.json

Extract Variables:
    python repl.py --extract-keys
    python repl.py --collection collections/my_collection.json --extract-keys variables.json

Extract Collection Structure:
    python repl.py --collection collections/my_collection.json --import
    python repl.py --collection collections/my_collection.json --import my_api_dir

Encode Variables:
    python repl.py --encode-payloads variables.json
    python repl.py --encode-url "https://example.com"

List Configurations:
    python repl.py --list auth
    python repl.py --list proxies
    python repl.py --list collections
    python repl.py --list insertion_points workflows
    python repl.py --list auth proxies insertion_points workflows collections

Show Configuration Details:
    python repl.py --show auth apikey/api_key_example
    python repl.py --show workflows social_media_api
    python repl.py --show proxies default
    python repl.py --show insertion_points test_insertion_point

For more options, use --help
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any

# Import custom modules
from modules.logman import setup_logging, get_logger, ensure_log_directory, save_results_to_file

# Setup logging
logger = setup_logging()

# Import requests and urllib3 with error handling
try:
    import requests
    import urllib3
    from urllib3.exceptions import InsecureRequestWarning
    # Suppress only the InsecureRequestWarning
    urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    print("Warning: requests or urllib3 module not found. HTTP functionality will be limited.")
    requests = None
    urllib3 = None

# Import encoder module with error handling
try:
    from modules.encoder import Encoder
    encoder_available = True
except ImportError:
    print("Warning: encoder module not found. Variable encoding functionality will be limited.")
    encoder_available = False

# Import config_lister module with error handling
try:
    from modules.config import handle_list_command, handle_show_command
except ImportError:
    print("Warning: config module not found. List and show functionality will not be available.")
    
    def handle_list_command(list_type):
        """Fallback function if config module is not available."""
        print(f"Error: Cannot list {list_type}. The config module is not available.")
        print("Please make sure the modules/config.py file is in the same directory as repl.py.")
        
    def handle_show_command(config_type, config_name):
        """Fallback function if config module is not available."""
        print(f"Error: Cannot show {config_type}/{config_name}. The config module is not available.")
        print("Please make sure the modules/config.py file is in the same directory as repl.py.")

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COLLECTIONS_DIR = os.path.join(SCRIPT_DIR, "collections")
VARIABLES_DIR = os.path.join(SCRIPT_DIR, "variables")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
INSERTION_POINTS_DIR = os.path.join(SCRIPT_DIR, "insertion_points")
AUTH_DIR = os.path.join(SCRIPT_DIR, "auth")
PROXY_DIR = os.path.join(SCRIPT_DIR, "proxies")
LOGS_DIR = os.path.join(SCRIPT_DIR, "logs")

# Import functions from config module
from modules.config import (
    validate_json_file,
    load_proxy,
    save_proxy,
    check_proxy_connection,
    verify_proxy_with_request,
    select_proxy_file
)

# Import the encoder module
try:
    from modules.encoder import Encoder, process_insertion_point
except ImportError:
    process_insertion_point = None
    Encoder = None
    print("Warning: encoder module not found. Variable encoding will not be available.")

# Disable SSL warnings
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
    Extract all variables from a Postman collection.
    Returns a tuple of (variables, collection_id, collection_data).
    
    Args:
        collection_path: Path to the collection file
        
    Returns:
        Tuple[Set[str], Optional[str], Dict]: Tuple of (variables, collection_id, collection_data)
    """
    logger.debug(f"extract_variables_from_collection called with path: {collection_path}")
    
    # Validate the collection file
    is_valid, collection_data = validate_json_file(collection_path)
    
    if not is_valid or not collection_data:
        logger.error(f"Invalid collection file: {collection_path}")
        return set(), None, {}
    
    # Extract collection ID
    collection_id = None
    if "info" in collection_data and "_postman_id" in collection_data["info"]:
        collection_id = collection_data["info"]["_postman_id"]
    
    # Extract variables from the collection
    variables = set()
    
    def process_url(url):
        if isinstance(url, str):
            variables.update(extract_variables_from_text(url))
        elif isinstance(url, dict):
            # Handle URL object format
            for key, value in url.items():
                if isinstance(value, str):
                    variables.update(extract_variables_from_text(value))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            variables.update(extract_variables_from_text(item))
    
    def process_body(body):
        if not isinstance(body, dict):
            return
        
        # Check for raw body
        if "raw" in body and isinstance(body["raw"], str):
            variables.update(extract_variables_from_text(body["raw"]))
        
        # Check for urlencoded or form-data
        if "urlencoded" in body and isinstance(body["urlencoded"], list):
            for param in body["urlencoded"]:
                if isinstance(param, dict):
                    for key in ["key", "value"]:
                        if key in param and isinstance(param[key], str):
                            variables.update(extract_variables_from_text(param[key]))
        
        if "formdata" in body and isinstance(body["formdata"], list):
            for param in body["formdata"]:
                if isinstance(param, dict):
                    for key in ["key", "value"]:
                        if key in param and isinstance(param[key], str):
                            variables.update(extract_variables_from_text(param[key]))
    
    def process_headers(headers):
        if isinstance(headers, list):
            for header in headers:
                if isinstance(header, dict):
                    for key in ["key", "value"]:
                        if key in header and isinstance(header[key], str):
                            variables.update(extract_variables_from_text(header[key]))
    
    def process_request(request):
        if not isinstance(request, dict):
            return
        
        # Process URL
        if "url" in request:
            process_url(request["url"])
        
        # Process headers
        if "header" in request:
            process_headers(request["header"])
        
        # Process body
        if "body" in request:
            process_body(request["body"])
    
    def process_item(item):
        # Process request if present
        if "request" in item:
            process_request(item["request"])
        
        # Process nested items
        if "item" in item and isinstance(item["item"], list):
            for nested_item in item["item"]:
                process_item(nested_item)
    
    # Process all items in the collection
    if "item" in collection_data and isinstance(collection_data["item"], list):
        for item in collection_data["item"]:
            process_item(item)
    
    return variables, collection_id, collection_data

def generate_variables_template(collection_path: str, output_path: str) -> None:
    """
    Generate a template file with variables extracted from a collection.
    
    Args:
        collection_path: Path to the collection file
        output_path: Path to save the template file
    """
    logger.debug(f"generate_variables_template called with collection_path: {collection_path}, output_path: {output_path}")
    
    # Extract variables from the collection
    variables, collection_id, _ = extract_variables_from_collection(collection_path)
    
    if not variables:
        logger.warning("No variables found in the collection")
        print("No variables found in the collection.")
        return
    
    # Create insertion_points directory if it doesn't exist
    if not os.path.exists(VARIABLES_DIR):
        try:
            os.makedirs(VARIABLES_DIR)
            logger.debug(f"Created insertion_points directory at {VARIABLES_DIR}")
        except Exception as e:
            logger.error(f"Could not create insertion_points directory: {e}")
            print(f"Error: Could not create insertion_points directory: {e}")
            return
    
    # Create a template file with the variables
    insertion_point = {
        "name": f"Template for {os.path.basename(collection_path)}",
        "values": [],
        "_postman_variable_scope": "environment",
        "_postman_exported_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "_postman_exported_using": "Repl/Interactive",
        "_postman_collection_id": collection_id if collection_id else "",
    }
    
    # Add variables to the template
    for var in sorted(variables):
        insertion_point["values"].append({
            "key": var,
            "value": "",
            "type": "default",
            "enabled": True
        })
    
    # Save the template
    try:
        with open(output_path, 'w') as f:
            json.dump(insertion_point, f, indent=2)
        logger.info(f"Template saved to {output_path}")
        print(f"Template saved to {output_path}")
    except Exception as e:
        logger.error(f"Error saving template: {e}")
        print(f"Error: Could not save template: {e}")

def select_collection_file() -> str:
    """
    List all JSON collection files in the collections directory and allow the user to select one.
    Returns the path to the selected collection file.
    """
    logger.info("Listing available collection files")
    
    # Create collections directory if it doesn't exist
    if not os.path.exists(COLLECTIONS_DIR):
        try:
            os.makedirs(COLLECTIONS_DIR)
            logger.debug(f"Created collections directory at {COLLECTIONS_DIR}")
        except Exception as e:
            logger.error(f"Could not create collections directory: {e}")
            print(f"Error: Could not create collections directory: {e}")
            return ""
    
    # Get all JSON files in the collections directory
    collection_files = []
    try:
        for file in os.listdir(COLLECTIONS_DIR):
            if file.endswith('.json'):
                collection_files.append(file)
    except Exception as e:
        logger.error(f"Error listing collections directory: {e}")
        print(f"Error: Could not list collections directory: {e}")
        return ""
    
    # If no collection files found, prompt user to specify a path
    if not collection_files:
        logger.info("No collection files found in collections directory")
        print(f"No collection files found in {COLLECTIONS_DIR}")
        collection_path = input("Enter path to collection file: ")
        if not collection_path:
            logger.warning("No collection path provided")
            return ""
        return collection_path
    
    # If only one collection file found, use it without prompting
    if len(collection_files) == 1:
        collection_path = os.path.join(COLLECTIONS_DIR, collection_files[0])
        logger.info(f"Using collection file: {collection_files[0]}")
        print(f"Using collection file: {collection_files[0]}")
        return collection_path
    
    # Multiple collection files found, prompt user to select
    print("\nSelect collection file:")
    for i, file in enumerate(collection_files, 1):
        print(f"{i}. {file}")
    print("0. Enter a different path")
    
    while True:
        try:
            choice = input("\nSelect file (0-{0}): ".format(len(collection_files)))
            choice_num = int(choice)
            
            if choice_num == 0:
                collection_path = input("Enter path to collection file: ")
                if not collection_path:
                    logger.warning("No collection path provided")
                    continue
                return collection_path
            
            if 1 <= choice_num <= len(collection_files):
                collection_path = os.path.join(COLLECTIONS_DIR, collection_files[choice_num-1])
                logger.info(f"User selected collection file: {collection_files[choice_num-1]}")
                return collection_path
            
            print(f"Invalid choice. Enter a number between 0 and {len(collection_files)}.")
        except ValueError:
            print("Invalid input. Enter a number.")

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
    
    # If the path is empty, prompt the user to select a collection
    if not collection_path:
        return select_collection_file()
    
    # Check if the path is absolute
    if os.path.isabs(collection_path):
        if os.path.exists(collection_path):
            return collection_path
        else:
            logger.warning(f"Collection file not found at absolute path: {collection_path}")
    
    # Check if the file exists in the current directory
    if os.path.exists(collection_path):
        return os.path.abspath(collection_path)
    
    # Check if the file exists in the collections directory
    collections_path = os.path.join(COLLECTIONS_DIR, collection_path)
    if os.path.exists(collections_path):
        return collections_path
    
    # Check if the file exists in the collections directory with .json extension
    if not collection_path.endswith('.json'):
        collections_path_with_ext = os.path.join(COLLECTIONS_DIR, collection_path + '.json')
        if os.path.exists(collections_path_with_ext):
            return collections_path_with_ext
    
    logger.warning(f"Collection file not found: {collection_path}")
    return collection_path

def extract_collection_id(collection_path: str) -> Optional[str]:
    """
    Extract the collection ID from a Postman collection file.
    
    Args:
        collection_path: Path to the collection file
        
    Returns:
        Optional[str]: Collection ID if found, None otherwise
    """
    logger.debug(f"extract_collection_id called with path: {collection_path}")
    
    # Validate the collection file
    is_valid, collection_data = validate_json_file(collection_path)
    
    if not is_valid or not collection_data:
        logger.error(f"Invalid collection file: {collection_path}")
        return None
    
    # Extract collection ID
    if "info" in collection_data and "_postman_id" in collection_data["info"]:
        return collection_data["info"]["_postman_id"]
    
    return None

def encode_insertion_point_variables(insertion_point_path=None):
    """
    Apply encoding to variables in an insertion point file.
    
    Args:
        insertion_point_path (str, optional): Path to the insertion point file. If None, user will be prompted to select one.
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if encoder module is available
    if not encoder_available:
        logger.error("Encoder module not available. Cannot encode variables.")
        return False
    
    # Import the process_insertion_point function from modules.encoder
    try:
        from modules.encoder import process_insertion_point
    except ImportError:
        logger.error("Could not import process_insertion_point from modules.encoder")
        return False
    
    # If no path provided, prompt user to select one
    if insertion_point_path is None or insertion_point_path == 'select':
        # Check if insertion_points directory exists
        if not os.path.exists(VARIABLES_DIR):
            logger.error(f"Insertion points directory not found: {VARIABLES_DIR}")
            return False
            
        # List all JSON files in the insertion_points directory
        json_files = [f for f in os.listdir(VARIABLES_DIR) if f.endswith('.json')]
        
        if not json_files:
            logger.error(f"No JSON files found in {VARIABLES_DIR}")
            print(f"\nNo insertion point files found in {VARIABLES_DIR}")
            print("Create an insertion point file first using --extract-keys")
            return False
            
        print("\nSelect insertion point file:")
        for i, file in enumerate(json_files, 1):
            print(f"{i}. {file}")
            
        while True:
            try:
                choice = input("\nSelect file: ")
                choice_num = int(choice)
                if 1 <= choice_num <= len(json_files):
                    insertion_point_path = os.path.join(VARIABLES_DIR, json_files[choice_num-1])
                    break
                print(f"Invalid choice. Enter a number between 1 and {len(json_files)}.")
            except ValueError:
                print("Invalid input. Enter a number.")
    elif not os.path.exists(insertion_point_path):
        # Try looking in the insertion_points directory
        alt_path = os.path.join(VARIABLES_DIR, os.path.basename(insertion_point_path))
        if os.path.exists(alt_path):
            insertion_point_path = alt_path
        else:
            logger.error(f"File not found: {insertion_point_path}")
            return False
    
    # Validate insertion point file
    valid, insertion_point_data = validate_json_file(insertion_point_path)
    if not valid or not insertion_point_data:
        logger.error(f"Invalid insertion point file: {insertion_point_path}")
        return False
    
    # Make a copy of the original data
    modified_data = json.loads(json.dumps(insertion_point_data))
    
    # Get list of variables from the insertion point
    variables = []
    
    # Check if this is a Postman environment format (with values array)
    if "values" in modified_data and isinstance(modified_data["values"], list):
        for var in modified_data["values"]:
            if "key" in var and "value" in var and var.get("enabled", True):
                # Skip base_url as it should never be encoded
                if var["key"] == "base_url":
                    continue
                variables.append(var["key"])
    
    # Simple key-value format
    elif "variables" in modified_data and isinstance(modified_data["variables"], list):
        for var in modified_data["variables"]:
            if "key" in var and "value" in var:
                # Skip base_url as it should never be encoded
                if var["key"] == "base_url":
                    continue
                variables.append(var["key"])
    
    # No variables found
    if not variables:
        logger.error("No variables found in the insertion point file")
        return False
    
    # Keep encoding variables until the user is done
    variables_modified = 0
    
    while True:
        # Prompt user to select variables to encode
        print("\nSelect variables to encode:")
        print("0. All variables")
        
        # Find the longest variable name for formatting
        max_var_length = max([len(var) for var in variables]) if variables else 0
        format_str = "{{}}. {{:<{}}} {{}}".format(max_var_length + 2)
        
        # Display variables with their encoding status
        for i, var in enumerate(variables, 1):
            # Check if variable already has encoding
            encoding_info = ""
            if "values" in modified_data and isinstance(modified_data["values"], list):
                for v in modified_data["values"]:
                    if v.get("key") == var and "encoding" in v:
                        encoding_method = v.get("encoding", "")
                        iterations = v.get("encoding_iterations", 1)
                        encoding_info = f"[{encoding_method}"
                        if iterations > 1:
                            encoding_info += f" x{iterations}"
                        encoding_info += "]"
                        break
            elif "variables" in modified_data and isinstance(modified_data["variables"], list):
                for v in modified_data["variables"]:
                    if v.get("key") == var and "encoding" in v:
                        encoding_method = v.get("encoding", "")
                        iterations = v.get("encoding_iterations", 1)
                        encoding_info = f"[{encoding_method}"
                        if iterations > 1:
                            encoding_info += f" x{iterations}"
                        encoding_info += "]"
                        break
            
            print(format_str.format(i, var, encoding_info))
        
        print("q. Done - save and exit")
        
        choice = input("\nSelect variables (0 for all, numbers separated by commas, or q to finish): ")
        
        if choice.lower() == 'q':
            break
        
        selected_vars = None
        try:
            if choice == "0":
                # All variables
                selected_vars = variables
            else:
                # Parse comma-separated list
                indices = [int(x.strip()) for x in choice.split(",")]
                if all(1 <= idx <= len(variables) for idx in indices):
                    selected_vars = [variables[idx-1] for idx in indices]
                else:
                    print(f"Invalid choice. Enter numbers between 1 and {len(variables)}.")
                    continue
        except ValueError:
            print("Invalid input. Enter numbers separated by commas.")
            continue
        
        if not selected_vars:
            continue
        
        # Now prompt for encoding method for the selected variables
        print("\nSelect encoding method:")
        encoding_options = [
            "url",
            "double_url",
            "html",
            "xml",
            "unicode",
            "hex",
            "octal",
            "base64",
            "sql_char",
            "js_escape",
            "css_escape"
        ]
        
        for i, option in enumerate(encoding_options, 1):
            print(f"{i}. {option}")
        
        encoding_type = None
        while True:
            try:
                choice = input("\nSelect encoding: ")
                choice_num = int(choice)
                if 1 <= choice_num <= len(encoding_options):
                    encoding_type = encoding_options[choice_num-1]
                    break
                print(f"Invalid choice. Enter a number between 1 and {len(encoding_options)}.")
            except ValueError:
                print("Invalid input. Enter a number.")
        
        # Prompt for iterations
        iterations = 1
        while True:
            try:
                iterations_input = input("\nNumber of iterations [1]: ")
                if not iterations_input:
                    break
                iterations = int(iterations_input)
                if iterations > 0:
                    break
                print("Invalid value. Enter a positive number.")
            except ValueError:
                print("Invalid input. Enter a number.")
        
        # Process variables
        group_modified = 0
        encoded_vars = []
        
        # Check if this is a Postman environment format (with values array)
        if "values" in modified_data and isinstance(modified_data["values"], list):
            # Process each variable
            for i, var in enumerate(modified_data["values"]):
                if "key" in var and "value" in var and var.get("enabled", True):
                    # Skip if not in the selected list
                    if var["key"] not in selected_vars:
                        continue
                    
                    # Skip base_url as it should never be encoded
                    if var["key"] == "base_url":
                        print(f"  Skipping base_url as it must be preserved for targeting the correct endpoint")
                        continue
                    
                    # Add encoding information
                    modified_data["values"][i]["encoding"] = encoding_type
                    modified_data["values"][i]["encoding_iterations"] = iterations
                    group_modified += 1
                    encoded_vars.append(var["key"])
        
        # Simple key-value format
        elif "variables" in modified_data and isinstance(modified_data["variables"], list):
            # Process each variable
            for i, var in enumerate(modified_data["variables"]):
                if "key" in var and "value" in var:
                    # Skip if not in the selected list
                    if var["key"] not in selected_vars:
                        continue
                    
                    # Skip base_url as it should never be encoded
                    if var["key"] == "base_url":
                        print(f"  Skipping base_url as it must be preserved for targeting the correct endpoint")
                        continue
                    
                    # Add encoding information
                    modified_data["variables"][i]["encoding"] = encoding_type
                    modified_data["variables"][i]["encoding_iterations"] = iterations
                    group_modified += 1
                    encoded_vars.append(var["key"])
        
        variables_modified += group_modified
        
        # Show feedback with more details
        if group_modified > 0:
            iteration_str = f" x{iterations}" if iterations > 1 else ""
            print(f"\nAdded {encoding_type}{iteration_str} encoding to {group_modified} variables:")
            # Display in columns if there are many variables
            if group_modified > 5:
                # Calculate how many variables to show per line
                term_width = os.get_terminal_size().columns if hasattr(os, 'get_terminal_size') else 80
                max_var_length = max([len(var) for var in encoded_vars]) if encoded_vars else 0
                vars_per_line = max(1, term_width // (max_var_length + 4))
                
                for i, var in enumerate(encoded_vars):
                    print(f"  {var:<{max_var_length + 2}}", end="\n" if (i + 1) % vars_per_line == 0 else "")
                # Add a newline if the last line wasn't complete
                if len(encoded_vars) % vars_per_line != 0:
                    print()
            else:
                for var in encoded_vars:
                    print(f"  {var}")
        else:
            print("\nNo variables were modified.")
    
    if variables_modified == 0:
        logger.warning("No variables were modified")
        return False
    
    # Save the modified insertion point
    output_path = insertion_point_path
    if os.path.exists(output_path):
        # Create a backup
        backup_path = f"{output_path}.bak"
        try:
            with open(backup_path, 'w') as f:
                json.dump(insertion_point_data, f, indent=2)
            logger.info(f"Created backup of original file at {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    # Write the modified file
    try:
        with open(output_path, 'w') as f:
            json.dump(modified_data, f, indent=2)
        logger.info(f"Updated {variables_modified} variables with encoding in {output_path}")
        
        # Collect encoding statistics
        encoding_stats = {}
        if "values" in modified_data and isinstance(modified_data["values"], list):
            for var in modified_data["values"]:
                if "encoding" in var:
                    encoding_type = var["encoding"]
                    iterations = var.get("encoding_iterations", 1)
                    key = f"{encoding_type}" + (f" x{iterations}" if iterations > 1 else "")
                    encoding_stats[key] = encoding_stats.get(key, 0) + 1
        elif "variables" in modified_data and isinstance(modified_data["variables"], list):
            for var in modified_data["variables"]:
                if "encoding" in var:
                    encoding_type = var["encoding"]
                    iterations = var.get("encoding_iterations", 1)
                    key = f"{encoding_type}" + (f" x{iterations}" if iterations > 1 else "")
                    encoding_stats[key] = encoding_stats.get(key, 0) + 1
        
        # Show example of how to use the file
        print(f"\nSuccessfully updated {variables_modified} variables with encoding:")
        
        # Display encoding statistics
        if encoding_stats:
            for encoding, count in encoding_stats.items():
                print(f"  {count} variables with {encoding} encoding")
        
        print(f"\nTo use this file with a collection:")
        print(f"python3 repl.py --collection <collection.json> --insertion-point {os.path.basename(output_path)}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to save modified insertion point: {e}")
        return False

class Repl:
    """
    Main class for replacing, loading, and replaying Postman collections.
    """
    def __init__(self, collection_path: str, target_insertion_point: str = None, proxy_host: str = None, proxy_port: int = None,
                 verify_ssl: bool = False, auto_detect_proxy: bool = True,
                 verbose: bool = False, custom_headers: List[str] = None, auth_method: Dict = None):
        """
        Initialize the Repl class.
        
        Args:
            collection_path: Path to the Postman collection file
            target_insertion_point: Path to the insertion point file
            proxy_host: Proxy host
            proxy_port: Proxy port
            verify_ssl: Whether to verify SSL certificates
            auto_detect_proxy: Whether to auto-detect proxy
            verbose: Whether to enable verbose logging
            custom_headers: List of custom headers to add to all requests
            auth_method: Authentication method to use
        """
        # Import save_results_to_file here to avoid circular imports
        self.save_results_to_file = save_results_to_file
        
        # Initialize instance variables
        self.collection_path = collection_path
        self.target_insertion_point = target_insertion_point
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.verify_ssl = verify_ssl
        self.auto_detect_proxy = auto_detect_proxy
        self.verbose = verbose
        self.custom_headers = custom_headers or []
        self.auth_method = auth_method
        
        # Initialize other attributes
        self.collection = {}
        self.insertion_point = {}
        self.variables = {}
        self.results = {"requests": []}
        
        # Load collection and insertion point
        self.load_collection()
        if target_insertion_point:
            self.load_insertion_point()
    
    def load_collection(self) -> bool:
        """
        Load the Postman collection from the specified path.
        
        Returns:
            bool: True if the collection was loaded successfully, False otherwise
        """
        logger.info(f"Loading collection from {self.collection_path}")
        
        # Validate the collection file
        is_valid, json_data = validate_json_file(self.collection_path)
        
        if not is_valid or not json_data:
            logger.error(f"Invalid collection file: {self.collection_path}")
            return False
        
        # Check if this is a Postman collection
        if "info" not in json_data or "item" not in json_data:
            logger.error(f"Not a valid Postman collection: {self.collection_path}")
            return False
        
        # Store the collection
        self.collection = json_data
        
        # Extract collection name
        collection_name = self.collection.get("info", {}).get("name", "Unknown Collection")
        logger.info(f"Loaded collection: {collection_name}")
        
        return True
    
    def load_insertion_point(self) -> bool:
        """
        Load the insertion point from the specified path.
        
        Returns:
            bool: True if the insertion point was loaded successfully, False otherwise
        """
        logger.info(f"Loading insertion point from {self.target_insertion_point}")
        
        # Validate the insertion point file
        valid, insertion_point_data = validate_json_file(self.target_insertion_point)
        if not valid or not insertion_point_data:
            logger.error(f"Invalid insertion point file: {self.target_insertion_point}")
            return False
        
        # Store the insertion point
        self.insertion_point = insertion_point_data
        
        # Extract variables from the insertion point
        if "values" in self.insertion_point and isinstance(self.insertion_point["values"], list):
            for var in self.insertion_point["values"]:
                if "key" in var and "value" in var and var.get("enabled", True):
                    self.variables[var["key"]] = var["value"]
        
        # Also check for variables in the "variables" object format
        if "variables" in self.insertion_point and isinstance(self.insertion_point["variables"], dict):
            for key, value in self.insertion_point["variables"].items():
                self.variables[key] = value
        
        # Check if we have any variables
        if not self.variables:
            logger.warning("No variables found in the insertion point file")
        else:
            logger.info(f"Loaded {len(self.variables)} variables from insertion point")
        
        return True
    
    def replace_variables(self, text: str) -> str:
        """
        Replace variables in the text with values from the insertion point.
        
        Args:
            text: Text to replace variables in
            
        Returns:
            str: Text with variables replaced
        """
        if not text:
            return text
        
        # Define a whitelist of variables that should be preserved if not defined
        # These are typically variables that are meant to be replaced by the target system
        whitelist = ["base_url", "api_url", "host", "domain", "endpoint"]
        
        # Find all variables in the text
        all_vars = re.findall(r"{{([^{}]+)}}", text)
        
        # Replace variables in the format {{variable_name}}
        for var_name, var_value in self.variables.items():
            pattern = r"{{" + re.escape(var_name) + r"}}"
            text = re.sub(pattern, str(var_value), text)
        
        # Log warning for whitelisted variables that are used but not defined
        for var in all_vars:
            if var in whitelist and var not in self.variables and f"{{{{{var}}}}}" in text:
                logger.warning(f"Whitelisted variable '{var}' is used but not defined in the insertion point")
        
        return text
    
    def extract_requests_from_item(self, item: Dict, folder_name: str = "") -> List[Dict]:
        """
        Extract requests from a collection item.
        
        Args:
            item: Collection item
            folder_name: Folder name for the item
            
        Returns:
            List[Dict]: List of requests
        """
        requests = []
        
        # Check if this item has a request
        if "request" in item:
            request_data = {
                "name": item.get("name", "Unnamed Request"),
                "folder": folder_name,
                "request": item["request"]
            }
            requests.append(request_data)
        
        # Check if this item has nested items
        if "item" in item and isinstance(item["item"], list):
            new_folder_name = folder_name
            if folder_name and item.get("name"):
                new_folder_name = f"{folder_name}/{item['name']}"
            elif item.get("name"):
                new_folder_name = item["name"]
            
            for nested_item in item["item"]:
                requests.extend(self.extract_requests_from_item(nested_item, new_folder_name))
        
        return requests
    
    def extract_all_requests(self, collection: Dict) -> List[Dict]:
        """
        Extract all requests from a collection.
        
        Args:
            collection: Postman collection
            
        Returns:
            List[Dict]: List of requests
        """
        requests = []
        
        # Check if the collection has items
        if "item" in collection and isinstance(collection["item"], list):
            for item in collection["item"]:
                requests.extend(self.extract_requests_from_item(item))
        
        return requests
    
    def prepare_request(self, request_data: Dict) -> Dict:
        """
        Prepare a request for sending.
        
        Args:
            request_data: Request data
            
        Returns:
            Dict: Prepared request
        """
        # Extract request details
        request = request_data["request"]
        
        # Initialize prepared request
        prepared_request = {
            "name": request_data["name"],
            "folder": request_data.get("folder", ""),
            "method": request.get("method", "GET"),
            "url": "",
            "headers": {},
            "body": None,
            "auth": None
        }
        
        # Process URL
        if "url" in request:
            url = request["url"]
            if isinstance(url, str):
                prepared_request["url"] = self.replace_variables(url)
            elif isinstance(url, dict):
                # Handle URL object format
                host = url.get("host", [])
                if isinstance(host, list):
                    host = ".".join(host)
                elif isinstance(host, str):
                    host = host
                else:
                    host = ""
                
                path = url.get("path", [])
                if isinstance(path, list):
                    path = "/".join(path)
                elif isinstance(path, str):
                    path = path
                else:
                    path = ""
                
                protocol = url.get("protocol", "http")
                port = url.get("port", "")
                
                # Replace variables in URL components
                host = self.replace_variables(host)
                path = self.replace_variables(path)
                
                # Build URL
                full_url = f"{protocol}://{host}"
                if port:
                    full_url += f":{port}"
                if path:
                    if not path.startswith("/"):
                        full_url += "/"
                    full_url += path
                
                # Handle query parameters
                if "query" in url and isinstance(url["query"], list):
                    query_params = []
                    for param in url["query"]:
                        if isinstance(param, dict) and "key" in param:
                            key = self.replace_variables(param["key"])
                            value = ""
                            if "value" in param:
                                value = self.replace_variables(str(param["value"]))
                            query_params.append(f"{key}={value}")
                    
                    if query_params:
                        full_url += "?" + "&".join(query_params)
                
                prepared_request["url"] = full_url
        
        # Process headers
        if "header" in request and isinstance(request["header"], list):
            for header in request["header"]:
                if isinstance(header, dict) and "key" in header and "value" in header:
                    key = self.replace_variables(header["key"])
                    value = self.replace_variables(header["value"])
                    prepared_request["headers"][key] = value
        
        # Add custom headers
        for header in self.custom_headers:
            if ":" in header:
                key, value = header.split(":", 1)
                prepared_request["headers"][key.strip()] = value.strip()
        
        # Process body
        if "body" in request and isinstance(request["body"], dict):
            body = request["body"]
            mode = body.get("mode", "")
            
            if mode == "raw" and "raw" in body:
                prepared_request["body"] = self.replace_variables(body["raw"])
            elif mode == "urlencoded" and "urlencoded" in body and isinstance(body["urlencoded"], list):
                form_data = []
                for param in body["urlencoded"]:
                    if isinstance(param, dict) and "key" in param:
                        key = self.replace_variables(param["key"])
                        value = ""
                        if "value" in param:
                            value = self.replace_variables(str(param["value"]))
                        form_data.append(f"{key}={value}")
                
                prepared_request["body"] = "&".join(form_data)
                if "Content-Type" not in prepared_request["headers"]:
                    prepared_request["headers"]["Content-Type"] = "application/x-www-form-urlencoded"
            elif mode == "formdata" and "formdata" in body and isinstance(body["formdata"], list):
                # For simplicity, we'll just convert form data to a string representation
                form_data = []
                for param in body["formdata"]:
                    if isinstance(param, dict) and "key" in param:
                        key = self.replace_variables(param["key"])
                        value = ""
                        if "value" in param:
                            value = self.replace_variables(str(param["value"]))
                        form_data.append(f"{key}={value}")
                
                prepared_request["body"] = "&".join(form_data)
                if "Content-Type" not in prepared_request["headers"]:
                    prepared_request["headers"]["Content-Type"] = "multipart/form-data"
        
        # Process authentication
        if self.auth_method:
            prepared_request["auth"] = self.auth_method
        
        return prepared_request
    
    def send_request(self, prepared_request: Dict) -> Dict:
        """
        Send a request through the proxy.
        
        Args:
            prepared_request: Prepared request
            
        Returns:
            Dict: Response data
        """
        # Extract request details
        method = prepared_request["method"]
        url = prepared_request["url"]
        headers = prepared_request["headers"]
        body = prepared_request["body"]
        
        # Set up proxy
        proxies = None
        if self.proxy_host and self.proxy_port:
            proxy_url = f"http://{self.proxy_host}:{self.proxy_port}"
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
        
        # Set up authentication
        auth = None
        if "auth" in prepared_request and prepared_request["auth"]:
            auth_data = prepared_request["auth"]
            auth_type = auth_data.get("type")
            
            if auth_type == "basic":
                auth = requests.auth.HTTPBasicAuth(
                    auth_data.get("username", ""),
                    auth_data.get("password", "")
                )
            elif auth_type == "bearer":
                headers["Authorization"] = f"Bearer {auth_data.get('token', '')}"
            elif auth_type == "api_key":
                key = auth_data.get("key", "")
                location = auth_data.get("location", "header")
                name = auth_data.get("name", "X-API-Key")
                
                if location == "header":
                    headers[name] = key
                elif location == "query":
                    # Add to URL as query parameter
                    url_parts = list(urllib.parse.urlparse(url))
                    query = dict(urllib.parse.parse_qsl(url_parts[4]))
                    query.update({name: key})
                    url_parts[4] = urllib.parse.urlencode(query)
                    url = urllib.parse.urlunparse(url_parts)
        
        # Prepare the response data
        response_data = {
            "name": prepared_request["name"],
            "folder": prepared_request["folder"],
            "request": {
                "method": method,
                "url": url,
                "headers": headers,
                "body": body
            },
            "response": {
                "status_code": None,
                "headers": {},
                "body": None,
                "time": None
            },
            "success": False,
            "error": None
        }
        
        try:
            # Log the request
            logger.info(f"Sending {method} request to {url}")
            if self.verbose:
                logger.debug(f"Headers: {headers}")
                if body:
                    logger.debug(f"Body: {body}")
            
            # Send the request
            start_time = time.time()
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                proxies=proxies,
                verify=self.verify_ssl,
                auth=auth,
                timeout=30
            )
            end_time = time.time()
            
            # Process the response
            response_data["response"]["status_code"] = response.status_code
            response_data["response"]["headers"] = dict(response.headers)
            response_data["response"]["body"] = response.text
            response_data["response"]["time"] = end_time - start_time
            response_data["success"] = 200 <= response.status_code < 300
            
            # Log the response
            logger.info(f"Received response: {response.status_code}")
            if self.verbose:
                logger.debug(f"Response headers: {response.headers}")
                logger.debug(f"Response body: {response.text[:1000]}...")
            
        except Exception as e:
            # Handle request errors
            response_data["error"] = str(e)
            logger.error(f"Request error: {e}")
        
        return response_data
    
    def save_results(self) -> None:
        """
        Save the results to a file.
        """
        print(f"Saving results to {RESULTS_DIR} and {LOGS_DIR}")
        
        # Save to both results and logs directories
        self.save_results_to_file(
            self.results, 
            self.collection_path, 
            self.target_insertion_point, 
            (self.proxy_host, self.proxy_port), 
            RESULTS_DIR, 
            logger
        )
        
        # Also save to logs directory
        self.save_results_to_file(
            self.results, 
            self.collection_path, 
            self.target_insertion_point, 
            (self.proxy_host, self.proxy_port), 
            LOGS_DIR, 
            logger
        )
    
    def process_items(self, items, folder_name=""):
        """
        Process items in a collection.
        
        Args:
            items: Collection items
            folder_name: Folder name for the items
        """
        for item in items:
            # Check if this is a folder
            if "item" in item and isinstance(item["item"], list):
                new_folder_name = folder_name
                if folder_name and item.get("name"):
                    new_folder_name = f"{folder_name}/{item['name']}"
                elif item.get("name"):
                    new_folder_name = item["name"]
                
                self.process_items(item["item"], new_folder_name)
            # Check if this is a request
            elif "request" in item:
                request_data = {
                    "name": item.get("name", "Unnamed Request"),
                    "folder": folder_name,
                    "request": item["request"]
                }
                
                # Prepare and send the request
                prepared_request = self.prepare_request(request_data)
                response_data = self.send_request(prepared_request)
                
                # Add to results
                self.results["requests"].append(response_data)
    
    def process_collection(self) -> None:
        """
        Process the collection.
        """
        # Check if collection is loaded
        if not self.collection:
            logger.error("No collection loaded")
            return
        
        # Process items in the collection
        if "item" in self.collection and isinstance(self.collection["item"], list):
            self.process_items(self.collection["item"])
    
    def run(self) -> Dict:
        """
        Run the collection through the proxy.
        
        Returns:
            Dict: Results of the run
        """
        # Check proxy connection
        if self.proxy_host and self.proxy_port:
            if not self.check_proxy():
                logger.error(f"Could not connect to proxy at {self.proxy_host}:{self.proxy_port}")
                return self.results
        
        # Process the collection
        self.process_collection()
        
        # Save results
        self.save_results()
        
        return self.results
    
    def check_proxy(self) -> bool:
        """
        Check if the proxy is running.
        
        Returns:
            bool: True if the proxy is running, False otherwise
        """
        if not self.proxy_host or not self.proxy_port:
            return False
        
        # Check if proxy is running
        if not check_proxy_connection(self.proxy_host, self.proxy_port):
            logger.warning(f"Could not connect to proxy at {self.proxy_host}:{self.proxy_port}")
            
            if self.auto_detect_proxy:
                # Try to auto-detect proxy
                logger.info("Trying to auto-detect proxy...")
                
                # Common proxy ports
                # TODO: convert to global variable
                common_ports = [8080, 8081, 8082, 8888, 8889]
                
                # Try localhost first
                host = "localhost"
                for port in common_ports:
                    if port == self.proxy_port:
                        continue
                    
                    if check_proxy_connection(host, port):
                        logger.info(f"Found proxy at {host}:{port}")
                        
                        # Verify proxy with a test request
                        if verify_proxy_with_request(host, port):
                            logger.info(f"Verified proxy at {host}:{port}")
                            self.proxy_host = host
                            self.proxy_port = port
                            return True
                
                # Try 127.0.0.1
                host = "127.0.0.1"
                for port in common_ports:
                    if port == self.proxy_port:
                        continue
                    
                    if check_proxy_connection(host, port):
                        logger.info(f"Found proxy at {host}:{port}")
                        
                        # Verify proxy with a test request
                        if verify_proxy_with_request(host, port):
                            logger.info(f"Verified proxy at {host}:{port}")
                            self.proxy_host = host
                            self.proxy_port = port
                            return True
                
                logger.warning("Could not auto-detect proxy")
            
            return False
        
        # Verify proxy with a test request
        if verify_proxy_with_request(self.proxy_host, self.proxy_port):
            logger.info(f"Verified proxy at {self.proxy_host}:{self.proxy_port}")
            return True
        
        logger.warning(f"Could not verify proxy at {self.proxy_host}:{self.proxy_port}")
        return False

def main():
    """
    Main entry point for the script.
    """
    # Get the logger
    logger = get_logger('repl')
    
    # Create a custom formatter class for better help formatting
    class CustomHelpFormatter(argparse.HelpFormatter):
        def __init__(self, prog):
            super().__init__(prog, max_help_position=40, width=100)
        
        def _format_action_invocation(self, action):
            if not action.option_strings or action.nargs == 0:
                return super()._format_action_invocation(action)
            
            # Modified format for better readability
            return ', '.join(action.option_strings)
        
        def _format_usage(self, usage, actions, groups, prefix):
            # Create a simplified usage string
            simplified_usage = f"{prefix}%(prog)s [options]"
            return simplified_usage
    
    # Custom action for encoding options
    class EncodingAction(argparse.Action):
        def __init__(self, option_strings, dest, **kwargs):
            super().__init__(option_strings, dest, **kwargs)
        
        def __call__(self, parser, namespace, values, option_string=None):
            # Extract the encoding method from the option string
            method = option_string.replace('--encode-', '')
            setattr(namespace, self.dest, (method, values))
    
    # Parse command line arguments with improved formatting
    parser = argparse.ArgumentParser(
        description="Replace, Load, and Replay Postman collections through any proxy tool",
        formatter_class=CustomHelpFormatter,
        add_help=True
    )
    
    # Basic options
    basic_group = parser.add_argument_group("BASIC OPTIONS")
    basic_group.add_argument("--collection", nargs="?", 
                           help="Path to Postman collection file. Use without value to select interactively")
    basic_group.add_argument("--banner", action="store_true", 
                           help="Print the banner")
    
    # Configuration management options
    config_group = parser.add_argument_group("CONFIGURATION OPTIONS")
    config_group.add_argument("--list", nargs='+', choices=['auth', 'proxies', 'insertion_points', 'workflows', 'collections'],
                          help="List available configurations")
    config_group.add_argument("--show", nargs=2, metavar=('TYPE', 'NAME'),
                    help='Show details of a specific configuration. TYPE can be auth, proxies, insertion_points, or workflows')
    
    # Insertion Point options
    env_group = parser.add_argument_group("VARIABLE OPTIONS")
    env_group.add_argument("--insertion-point", 
                          help="Path to insertion_point file with variable values")
    env_group.add_argument("--extract-keys", nargs="?", const=True, metavar="OUTPUT_FILE",
                          help="Extract variables from collection. Use without value to print variables, or specify a file path to save template")
    env_group.add_argument("--import-collection", dest="import_collection", nargs="?", const=True, metavar="OUTPUT_DIR",
                          help="Import Postman collection and extract to a directory structure in the 'collections' folder. Use without value to use collection name as base directory, or specify a subdirectory name")
    
    # Encoding options - simplified and grouped
    encoding_group = parser.add_argument_group("ENCODING OPTIONS")
    encoding_group.add_argument("--encode-payloads", nargs="?", metavar="FILE",
                              help="Encode variables in an insertion point file. Use without value to select interactively")
    
    # Add a single help entry for all encoding methods
    encoding_group.add_argument("--encode-METHOD", metavar="VALUE", dest="encode_value",
                              help="Encode a string using METHOD (url, double-url, html, xml, unicode, hex, octal, base64, sql-char, js, css)")
    
    # Add the actual encoding options
    encoding_group.add_argument("--encode-url", metavar="VALUE", help=argparse.SUPPRESS)
    encoding_group.add_argument("--encode-double-url", metavar="VALUE", help=argparse.SUPPRESS)
    encoding_group.add_argument("--encode-html", metavar="VALUE", help=argparse.SUPPRESS)
    encoding_group.add_argument("--encode-xml", metavar="VALUE", help=argparse.SUPPRESS)
    encoding_group.add_argument("--encode-unicode", metavar="VALUE", help=argparse.SUPPRESS)
    encoding_group.add_argument("--encode-hex", metavar="VALUE", help=argparse.SUPPRESS)
    encoding_group.add_argument("--encode-octal", metavar="VALUE", help=argparse.SUPPRESS)
    encoding_group.add_argument("--encode-base64", metavar="VALUE", help=argparse.SUPPRESS)
    encoding_group.add_argument("--encode-sql-char", metavar="VALUE", help=argparse.SUPPRESS)
    encoding_group.add_argument("--encode-js", metavar="VALUE", help=argparse.SUPPRESS)
    encoding_group.add_argument("--encode-css", metavar="VALUE", help=argparse.SUPPRESS)
    
    # Proxy options
    proxy_group = parser.add_argument_group("PROXY OPTIONS")
    proxy_group.add_argument("--proxy", metavar="HOST:PORT", 
                           help="Proxy to use in format host:port")
    proxy_group.add_argument("--proxy-host", 
                           help="Proxy hostname")
    proxy_group.add_argument("--proxy-port", type=int, 
                           help="Proxy port")
    proxy_group.add_argument("--verify-ssl", action="store_true", 
                           help="Verify SSL certificates")
    proxy_group.add_argument("--no-verify-ssl", action="store_true", 
                           help="Do not verify SSL certificates")
    proxy_group.add_argument("--save-proxy", action="store_true", 
                           help="Save proxy settings for future use")
    proxy_group.add_argument("--proxy-profile", nargs="?",
                           help="Use a saved proxy profile. Use without value to select interactively")
    
    # Output options
    output_group = parser.add_argument_group("OUTPUT OPTIONS")
    output_group.add_argument("--output", metavar="DIR",
                             help="Specify custom output directory for results")
    output_group.add_argument("--verbose", action="store_true", 
                             help="Show verbose output")
    
    # Header options
    header_group = parser.add_argument_group("HEADER OPTIONS")
    header_group.add_argument("--header", action="append", metavar="KEY:VALUE",
                             help="Add custom header. Can be specified multiple times")
    
    # Authentication options
    auth_group = parser.add_argument_group("AUTHENTICATION OPTIONS")
    auth_group.add_argument("--auth", nargs="?", 
                          help="Use a saved auth profile. Use without value to select interactively")
    auth_group.add_argument("--auth-METHOD", metavar="PARAMS", dest="auth_method",
                          help="Set authentication with METHOD (basic, bearer, api-key)")
    
    # Hide the actual auth options from help but still make them available
    auth_group.add_argument("--auth-basic", nargs=2, metavar=("USERNAME", "PASSWORD"), help=argparse.SUPPRESS)
    auth_group.add_argument("--auth-bearer", metavar="TOKEN", help=argparse.SUPPRESS)
    auth_group.add_argument("--auth-api-key", nargs=2, metavar=("KEY", "LOCATION"), help=argparse.SUPPRESS)
    auth_group.add_argument("--auth-api-key-name", metavar="NAME", help=argparse.SUPPRESS)
    
    # Add a single help entry for OAuth options
    auth_group.add_argument("--auth-oauth-OPTIONS", dest="oauth_options",
                          help="OAuth authentication options (see documentation)")
    
    # Hide the actual OAuth options from help but still make them available
    auth_group.add_argument("--auth-oauth1", nargs=2, metavar=("CONSUMER_KEY", "CONSUMER_SECRET"), help=argparse.SUPPRESS)
    auth_group.add_argument("--auth-oauth1-token", nargs=2, metavar=("TOKEN", "TOKEN_SECRET"), help=argparse.SUPPRESS)
    auth_group.add_argument("--auth-oauth1-signature", metavar="METHOD", help=argparse.SUPPRESS)
    auth_group.add_argument("--auth-oauth2", nargs=2, metavar=("CLIENT_ID", "CLIENT_SECRET"), help=argparse.SUPPRESS)
    auth_group.add_argument("--auth-oauth2-token-url", metavar="URL", help=argparse.SUPPRESS)
    auth_group.add_argument("--auth-oauth2-refresh-url", metavar="URL", help=argparse.SUPPRESS)
    auth_group.add_argument("--auth-oauth2-grant", metavar="TYPE", help=argparse.SUPPRESS)
    auth_group.add_argument("--auth-oauth2-username", metavar="USERNAME", help=argparse.SUPPRESS)
    auth_group.add_argument("--auth-oauth2-password", metavar="PASSWORD", help=argparse.SUPPRESS)
    auth_group.add_argument("--auth-oauth2-scope", metavar="SCOPE", help=argparse.SUPPRESS)
    
    args = parser.parse_args()
    
    # Ensure all required directories exist
    for directory in [COLLECTIONS_DIR, VARIABLES_DIR, RESULTS_DIR, INSERTION_POINTS_DIR, AUTH_DIR, PROXY_DIR, LOGS_DIR]:
        ensure_log_directory(directory)
    
    # Update logging level based on verbose flag
    if args.verbose:
        # Re-setup logging with verbose flag
        logger = setup_logging(verbose=True)
    
    # Handle list argument if specified
    if args.list:
        for list_type in args.list:
            if list_type == 'collections':
                list_collections()
            else:
                handle_list_command(list_type)
            # Add a newline between different list types for better readability
            if list_type != args.list[-1]:
                print()
        return
    
    # Handle show argument if specified
    if args.show:
        config_type, config_name = args.show
        if config_type not in ['auth', 'proxies', 'insertion_points', 'workflows']:
            print(f"Error: Unknown configuration type '{config_type}'")
            print("Available configuration types: auth, proxies, insertion_points, workflows")
            return
        handle_show_command(config_type, config_name)
        return
    
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
    
    # Handle insertion point encoding
    if args.encode_payloads:
        if encode_insertion_point_variables(args.encode_payloads):
            return
        else:
            logger.error("Failed to encode insertion point variables")
            return
    
    # Handle extract keys without collection specified
    if args.extract_keys is not None and not args.collection:
        logger.error("No collection specified. Please provide a collection with --collection.")
        sys.exit(1)
    
    # Handle extract keys with collection specified
    if args.extract_keys is not None:
        # Import the extract module
        try:
            from modules.extract import extract_keys
        except ImportError:
            logger.error("Could not import extract module")
            sys.exit(1)
        
        collection_path = resolve_collection_path(args.collection)
        if not collection_path:
            logger.error(f"Could not resolve collection path: {args.collection}")
            sys.exit(1)
        
        logger.debug(f"Resolved collection path: {collection_path}")
        
        # Extract keys using the module
        output_path = args.extract_keys if args.extract_keys is not True else None
        success = extract_keys(collection_path, output_path)
        
        # Exit after extraction
        sys.exit(0 if success else 1)
    
    # Handle import without collection specified
    if args.import_collection is not None and not args.collection:
        logger.error("No collection specified. Please provide a collection with --collection when using --import-collection.")
        sys.exit(1)
    
    # Handle import with collection specified
    if args.import_collection is not None:
        # Import the importman module
        try:
            import importlib
            importman_module = importlib.import_module('modules.importman')
            extract_collection_to_structure = getattr(importman_module, 'extract_collection_to_structure')
        except ImportError:
            logger.error("Could not import the importman module. Import features will not be available.")
            sys.exit(1)
        except AttributeError:
            logger.error("The importman module does not contain the required function.")
            sys.exit(1)
        
        collection_path = resolve_collection_path(args.collection)
        if not collection_path:
            logger.error(f"Could not resolve collection path: {args.collection}")
            sys.exit(1)
        
        logger.debug(f"Resolved collection path: {collection_path}")
        
        # Extract collection to structure
        output_dir = args.import_collection if args.import_collection is not True else None
        
        # Ensure output is in the collections directory
        if output_dir is not None:
            # If output_dir is an absolute path, make it relative to collections
            if os.path.isabs(output_dir):
                output_dir = os.path.join('collections', os.path.basename(output_dir))
            else:
                output_dir = os.path.join('collections', output_dir)
        else:
            output_dir = 'collections'
            
        success = extract_collection_to_structure(collection_path, output_dir)
        
        # Exit after extraction
        sys.exit(0 if success else 1)
    
    print("DEBUG: Continuing to auth module")
    
    # Import auth module
    try:
        from modules.auth import auth_manager, BasicAuth, BearerToken, ApiKey, OAuth1, OAuth2
    except ImportError:
        logger.error("Failed to import authentication module. Authentication features will not be available.")
        auth_manager = None
    
    
    
    # Print banner if requested (independent of other options)
    if args.banner:
        # Use colored banner if terminal supports colors, otherwise use plain text
        print(BANNER)
        # If only the banner was requested, exit
        if not args.collection and not args.extract_keys:
            sys.exit(0)
    
    # Handle collection selection if --collection is provided without a value
    collection_path = None
    if args.collection is None:
        collection_path = select_collection_file()
    elif args.collection:
        collection_path = args.collection
    elif args.extract_keys is not None:
        # This case is now handled earlier in the code
        pass
    else:
        logger.error("No collection specified. Use --collection to specify a collection file.")
        print("Error: No collection specified. Use --collection to specify a collection file.")
        print("       Or run with --collection without a value to select from available collections.")
        sys.exit(1)
    
    # Resolve collection path
    collection_path = resolve_collection_path(collection_path)
    logger.debug(f"Resolved collection path: {collection_path}")
    
    # Handle authentication options
    
    # Initialize auth_manager
    try:
        from modules.auth import AuthManager
        auth_manager = AuthManager()
    except ImportError as e:
        logger.warning(f"Could not import AuthManager: {e}")
        auth_manager = None
    
    # Select authentication profile if requested
    if args.auth is None and auth_manager:
        # Interactive mode - prompt user to select an auth profile
        auth_methods = auth_manager.get_auth_methods()
        if auth_methods:
            print("\nAvailable authentication profiles:")
            for i, method in enumerate(auth_methods, 1):
                auth_obj = auth_manager.get_auth_method(method)
                auth_type = auth_obj.type if auth_obj else "unknown"
                print(f"  {i}. {method} ({auth_type})")
            
            while True:
                choice = input("\nSelect authentication profile (or 0 to skip): ")
                if choice == "0":
                    args.auth = "0"  # Set to "0" to indicate skipping
                    break
                
                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(auth_methods):
                        args.auth = auth_methods[choice_idx]
                        break
                    else:
                        print(f"Invalid choice. Please enter a number between 1 and {len(auth_methods)}, or 0 to skip.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
        else:
            print("\nNo authentication profiles found.")
    
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
    
    # Only handle proxy selection if we're not extracting keys
    # Handle proxy selection
    proxy_path = None
    if args.proxy is None:
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
    
    # Handle authentication options
    if args.auth and args.auth != "0":  # Skip if auth is "0"
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
    
    # We always log now, no need to check args.log
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    try:
        os.makedirs(logs_dir, exist_ok=True)
        logger.debug(f"Created logs directory: {logs_dir}")
    except Exception as e:
        logger.error(f"Could not create logs directory: {e}")
    
    # Generate log filename based on collection name
    collection_name = os.path.splitext(os.path.basename(collection_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(logs_dir, f"{collection_name}_{timestamp}.json")
    logger.info(f"Results will be logged to: {log_path}")
    
    # Run the converter
    result = converter.run()
    # Check if there were successful requests or if we're just extracting keys
    if args.extract_keys is not None or (
        "metadata" in result and 
        result["metadata"].get("successful_requests", 0) > 0
    ):
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
                
            # Always enable logging
            proxy_to_save["log"] = True
            
            if save_proxy(proxy_to_save):
                logger.info("Configuration saved successfully")
                if args.insertion_point:
                    logger.info(f"Target insertion_point '{args.insertion_point}' saved in proxy")
            else:
                logger.error("Failed to save proxy")

def list_collections():
    """
    List all available collection files.
    """
    logger.info("Listing available collection files")
    
    # Check if collections directory exists
    if not os.path.exists(COLLECTIONS_DIR):
        try:
            os.makedirs(COLLECTIONS_DIR)
            logger.debug(f"Created collections directory at {COLLECTIONS_DIR}")
        except Exception as e:
            logger.error(f"Could not create collections directory: {e}")
            return
    
    # Get all JSON files in the collections directory
    try:
        collection_files = [f for f in os.listdir(COLLECTIONS_DIR) if f.endswith('.json')]
    except Exception as e:
        logger.error(f"Could not list collections directory: {e}")
        return
    
    if not collection_files:
        print("No collection files found.")
        print(f"Place your Postman collection JSON files in the {COLLECTIONS_DIR} directory.")
        return
    
    # Print the list of collection files
    print(f"\nAvailable collection files ({len(collection_files)}):")
    for i, file in enumerate(sorted(collection_files), 1):
        print(f"  {i}. {file}")

def handle_list_command(list_type):
    """
    Handle the --list command based on the specified type.
    
    Args:
        list_type (str): Type of configuration to list
    """
    if list_type == 'collections':
        list_collections()
        return
        
    # Fallback function if config module is not available
    print(f"Error: Cannot list {list_type}. The config module is not available.")
    print("Please make sure the modules/config.py file is in the same directory as repl.py.")

if __name__ == "__main__":
    main() 