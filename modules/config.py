#!/usr/bin/env python3
"""
config.py - Configuration management module for Repl

This module provides functions for loading, saving, and managing proxy configurations
and other settings. It also includes functions for listing and showing configuration details.
"""

import os
import json
import time
import logging
import socket
import re
from typing import Dict, List, Optional, Tuple, Any, Set

# Try to import tabulate for better table formatting
try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False
    logger = logging.getLogger("repl.config")
    logger.warning("tabulate module not found. Tables will be displayed in simple format.")
    logger.warning("To install: pip install tabulate")

# Setup logging
logger = logging.getLogger("repl.config")

# Constants
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(SCRIPT_DIR, "config", "proxies")
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "default.json")
AUTH_DIR = os.path.join(SCRIPT_DIR, "config", "auth")
PROXY_DIR = os.path.join(SCRIPT_DIR, "config", "proxies")
INSERTION_POINTS_DIR = os.path.join(SCRIPT_DIR, "insertion_points")
COLLECTIONS_DIR = os.path.join(SCRIPT_DIR, "collections")

# Default configuration
DEFAULT_CONFIG = {
    "proxy_host": "localhost",
    "proxy_port": 8080,
    "verify_ssl": False,
    "target_insertion_point": "",
    "verbose": False
}


def validate_json_file(file_path: str) -> Tuple[bool, Optional[Dict]]:
    """
    Validate a JSON file and return its contents if valid.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Tuple[bool, Optional[Dict]]: A tuple containing a boolean indicating if the file is valid,
                                    and the parsed JSON data if valid, None otherwise
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return True, data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return False, None


def load_proxy(proxy_path: str = None) -> Dict:
    """
    Load proxy configuration from a JSON file.
    
    Args:
        proxy_path (str, optional): Path to the proxy configuration file. 
                                   If None, user will be prompted to select one.
        
    Returns:
        Dict: The loaded proxy configuration, or an empty dict if loading failed
    """
    logger.debug(f"load_proxy called with proxy_path: {proxy_path}")
    
    proxy = DEFAULT_CONFIG.copy()
    
    # If no specific proxy path was provided, prompt user to select one
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
                return {}
        
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


def save_proxy(proxy: Dict) -> bool:
    """
    Save proxy configuration to a JSON file.
    
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


def select_proxy_file() -> str:
    """
    List all proxy files in the config/proxies directory and allow the user to select one.
    
    Returns:
        str: Path to the selected proxy file
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
            import sys
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
    Verify proxy by sending a test request.
    
    Args:
        host: Proxy host
        port: Proxy port
        
    Returns:
        bool: True if the proxy is working, False otherwise
    """
    try:
        import requests
        
        # Configure proxy
        proxies = {
            'http': f'http://{host}:{port}',
            'https': f'http://{host}:{port}'
        }
        
        # Send a test request to a reliable endpoint
        response = requests.get('http://httpbin.org/get', proxies=proxies, timeout=5, verify=False)
        
        # Check if the request was successful
        if response.status_code == 200:
            logger.debug(f"Proxy verification successful at {host}:{port}")
            return True
        else:
            logger.debug(f"Proxy verification failed at {host}:{port} with status code {response.status_code}")
            return False
    except Exception as e:
        logger.debug(f"Error verifying proxy at {host}:{port}: {str(e)}")
        return False


def truncate_string(s: str, max_length: int = 30) -> str:
    """
    Truncate a string to a maximum length and add ellipsis if needed.
    
    Args:
        s: String to truncate
        max_length: Maximum length of the string
        
    Returns:
        str: Truncated string
    """
    if not s:
        return ""
    
    if len(s) <= max_length:
        return s
    
    return s[:max_length-3] + "..."

def format_table(headers: List[str], data: List[List[Any]]) -> str:
    """
    Format data as a table.
    
    Args:
        headers: List of column headers
        data: List of rows, where each row is a list of values
        
    Returns:
        str: Formatted table as a string
    """
    # Truncate long strings in data
    processed_data = []
    for row in data:
        processed_row = []
        for item in row:
            if isinstance(item, str):
                processed_row.append(truncate_string(item))
            else:
                processed_row.append(item)
        processed_data.append(processed_row)
    
    if TABULATE_AVAILABLE:
        return tabulate(processed_data, headers=headers, tablefmt="simple")
    else:
        # Simple ASCII table format if tabulate is not available
        result = []
        
        # Add header
        header_str = " | ".join(headers)
        result.append(header_str)
        result.append("-" * len(header_str))
        
        # Add rows
        for row in processed_data:
            row_str = " | ".join(str(item) for item in row)
            result.append(row_str)
            
        return "\n".join(result)


def list_auth_configurations() -> None:
    """List all available authentication configurations."""
    print("Available Authentication Configurations:")
    auth_dir = AUTH_DIR
    
    if not os.path.exists(auth_dir):
        print("  No authentication configurations found.")
        return
    
    # Find all JSON files recursively in the auth directory
    auth_files = []
    for root, _, files in os.walk(auth_dir):
        for file in files:
            if file.endswith('.json'):
                auth_files.append(os.path.join(root, file))
    
    if not auth_files:
        print("  No authentication configurations found.")
        return
    
    # Prepare data for table
    headers = ["Name", "Type", "Details"]
    data = []
    
    for auth_path in sorted(auth_files):
        # Get relative path from auth directory for display
        rel_path = os.path.relpath(auth_path, auth_dir)
        # Use the filename without extension as the name
        name = os.path.splitext(os.path.basename(auth_path))[0]
        # If in a subdirectory, include the directory in the name
        if os.path.dirname(rel_path):
            name = f"{os.path.dirname(rel_path)}/{name}"
        
        try:
            with open(auth_path, 'r') as f:
                auth_data = json.load(f)
                auth_type = auth_data.get('type', 'Unknown')
                
                # Extract details based on auth type
                details = ""
                if auth_type == "basic":
                    details = f"Username: {auth_data.get('username', 'N/A')}"
                elif auth_type == "bearer":
                    token = auth_data.get('token', '')
                    if token and len(token) > 10:
                        details = f"Token: {token[:5]}...{token[-5:]}"
                    else:
                        details = "Token: N/A"
                elif auth_type == "apikey":
                    details = f"Key: {auth_data.get('key', 'N/A')}, In: {auth_data.get('in', 'N/A')}"
                
                data.append([name, auth_type, details])
        except Exception as e:
            data.append([name, "Error", str(e)])
    
    print(format_table(headers, data))


def list_proxy_configurations() -> None:
    """List all available proxy configurations."""
    print("Available Proxy Configurations:")
    proxy_dir = PROXY_DIR
    
    if not os.path.exists(proxy_dir):
        print("  No proxy configurations found.")
        return
    
    # Find all JSON files recursively in the proxy directory
    proxy_files = []
    for root, _, files in os.walk(proxy_dir):
        for file in files:
            if file.endswith('.json'):
                proxy_files.append(os.path.join(root, file))
    
    if not proxy_files:
        print("  No proxy configurations found.")
        return
    
    # Prepare data for table
    headers = ["Name", "Host", "Port", "SSL Verify", "Additional Settings"]
    data = []
    
    for proxy_path in sorted(proxy_files):
        # Get relative path from proxy directory for display
        rel_path = os.path.relpath(proxy_path, proxy_dir)
        # Use the filename without extension as the name
        name = os.path.splitext(os.path.basename(proxy_path))[0]
        # If in a subdirectory, include the directory in the name
        if os.path.dirname(rel_path):
            name = f"{os.path.dirname(rel_path)}/{name}"
        
        try:
            with open(proxy_path, 'r') as f:
                proxy_data = json.load(f)
                host = proxy_data.get('proxy_host', 'Unknown')
                port = proxy_data.get('proxy_port', 'Unknown')
                verify_ssl = "Yes" if proxy_data.get('verify_ssl', False) else "No"
                
                # Check for additional settings
                additional = []
                if 'target_insertion_point' in proxy_data and proxy_data['target_insertion_point']:
                    additional.append(f"Insertion Point: {os.path.basename(proxy_data['target_insertion_point'])}")
                if 'verbose' in proxy_data and proxy_data['verbose']:
                    additional.append("Verbose Mode")
                
                additional_str = ", ".join(additional) if additional else "None"
                
                data.append([name, host, port, verify_ssl, additional_str])
        except Exception as e:
            data.append([name, "Error", "", "", str(e)])
    
    print(format_table(headers, data))


def list_insertion_points() -> None:
    """List all available insertion points."""
    print("Available Insertion Points:")
    insertion_dir = INSERTION_POINTS_DIR
    
    if not os.path.exists(insertion_dir):
        print("  No insertion points found.")
        return
    
    # Find all JSON files recursively in the insertion points directory
    insertion_files = []
    for root, _, files in os.walk(insertion_dir):
        for file in files:
            if file.endswith('.json'):
                insertion_files.append(os.path.join(root, file))
    
    if not insertion_files:
        print("  No insertion points found.")
        return
    
    # Prepare data for table
    headers = ["Name", "Variables", "Variable Names"]
    data = []
    
    for insertion_path in sorted(insertion_files):
        # Get relative path from insertion points directory for display
        rel_path = os.path.relpath(insertion_path, insertion_dir)
        # Use the filename without extension as the name
        name = os.path.splitext(os.path.basename(insertion_path))[0]
        # If in a subdirectory, include the directory in the name
        if os.path.dirname(rel_path):
            name = f"{os.path.dirname(rel_path)}/{name}"
        
        try:
            with open(insertion_path, 'r') as f:
                insertion_data = json.load(f)
                variables = insertion_data.get('variables', {})
                var_count = len(variables)
                
                # Get variable names (limit to first 3 for display)
                var_names = list(variables.keys())
                if var_names:
                    if len(var_names) > 3:
                        var_names_str = f"{', '.join(var_names[:3])}... (+{len(var_names) - 3} more)"
                    else:
                        var_names_str = ", ".join(var_names)
                else:
                    var_names_str = "None"
                
                data.append([name, var_count, var_names_str])
        except Exception as e:
            data.append([name, "Error", str(e)])
    
    print(format_table(headers, data))


def list_workflows() -> None:
    """List all available workflows."""
    print("Available Workflows:")
    collections_dir = COLLECTIONS_DIR
    
    if not os.path.exists(collections_dir):
        print("  No workflows found.")
        return
    
    # Find all JSON files recursively in the collections directory
    collection_files = []
    for root, _, files in os.walk(collections_dir):
        for file in files:
            if file.endswith('.json'):
                collection_files.append(os.path.join(root, file))
    
    if not collection_files:
        print("  No workflows found.")
        return
    
    # Prepare data for table
    headers = ["Name", "Collection Name", "Requests", "Description"]
    data = []
    
    for collection_path in sorted(collection_files):
        # Get relative path from collections directory for display
        rel_path = os.path.relpath(collection_path, collections_dir)
        # Use the filename without extension as the name
        name = os.path.splitext(os.path.basename(collection_path))[0]
        # If in a subdirectory, include the directory in the name
        if os.path.dirname(rel_path):
            name = f"{os.path.dirname(rel_path)}/{name}"
        
        try:
            with open(collection_path, 'r') as f:
                collection_data = json.load(f)
                info = collection_data.get('info', {})
                collection_name = info.get('name', 'Unknown')
                description = info.get('description', 'No description')
                
                # We'll truncate in the format_table function
                request_count = count_requests_in_collection(collection_data)
                
                data.append([name, collection_name, request_count, description])
        except Exception as e:
            data.append([name, "Error", "", str(e)])
    
    print(format_table(headers, data))


def count_requests_in_collection(collection_data: Dict[str, Any]) -> int:
    """
    Count the number of requests in a collection.
    
    Args:
        collection_data: The collection data as a dictionary
        
    Returns:
        int: The number of requests in the collection
    """
    count = 0
    items = collection_data.get('item', [])
    
    def count_items(items_list: List[Dict[str, Any]]) -> None:
        nonlocal count
        for item in items_list:
            if 'request' in item:
                count += 1
            if 'item' in item:
                count_items(item['item'])
    
    count_items(items)
    return count


def handle_list_command(list_type: str) -> None:
    """
    Handle the --list command based on the specified type.
    
    Args:
        list_type: The type of configuration to list
    """
    if list_type == 'auth':
        list_auth_configurations()
    elif list_type == 'proxies':
        list_proxy_configurations()
    elif list_type == 'insertion_points':
        list_insertion_points()
    elif list_type == 'workflows':
        list_workflows()
    else:
        print(f"Error: Unknown list type '{list_type}'")
        print("Available list types: auth, proxies, insertion_points, workflows")


def find_config_file(config_type: str, config_name: str) -> str:
    """
    Find a configuration file by type and name.
    
    Args:
        config_type: Type of configuration (auth, proxies, insertion_points, workflows)
        config_name: Name of the configuration
        
    Returns:
        str: Path to the configuration file, or empty string if not found
    """
    base_dir = ""
    if config_type == "auth":
        base_dir = AUTH_DIR
    elif config_type == "proxies":
        base_dir = PROXY_DIR
    elif config_type == "insertion_points":
        base_dir = INSERTION_POINTS_DIR
    elif config_type == "workflows":
        base_dir = COLLECTIONS_DIR
    else:
        logger.error(f"Unknown configuration type: {config_type}")
        return ""
    
    # Check if the config_name contains a directory path
    if "/" in config_name:
        # Try direct path first
        direct_path = os.path.join(base_dir, config_name + ".json")
        if os.path.isfile(direct_path):
            return direct_path
    
    # Search recursively
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.json'):
                # Check if the filename matches
                if os.path.splitext(file)[0] == config_name:
                    return os.path.join(root, file)
                
                # Check if the relative path matches
                rel_path = os.path.relpath(os.path.join(root, file), base_dir)
                rel_path_no_ext = os.path.splitext(rel_path)[0]
                if rel_path_no_ext == config_name:
                    return os.path.join(root, file)
    
    return ""


def show_auth_configuration(config_name: str) -> None:
    """
    Show details of an authentication configuration.
    
    Args:
        config_name: Name of the authentication configuration
    """
    config_path = find_config_file("auth", config_name)
    if not config_path:
        print(f"Error: Authentication configuration '{config_name}' not found.")
        return
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            # Print raw JSON with indentation for readability
            print(json.dumps(config_data, indent=2))
    except Exception as e:
        print(f"Error reading configuration file: {e}")


def show_proxy_configuration(config_name: str) -> None:
    """
    Show details of a proxy configuration.
    
    Args:
        config_name: Name of the proxy configuration
    """
    config_path = find_config_file("proxies", config_name)
    if not config_path:
        print(f"Error: Proxy configuration '{config_name}' not found.")
        return
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            # Print raw JSON with indentation for readability
            print(json.dumps(config_data, indent=2))
    except Exception as e:
        print(f"Error reading configuration file: {e}")


def show_insertion_point(config_name: str) -> None:
    """
    Show details of an insertion point.
    
    Args:
        config_name: Name of the insertion point
    """
    config_path = find_config_file("insertion_points", config_name)
    if not config_path:
        print(f"Error: Insertion point '{config_name}' not found.")
        return
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            # Print raw JSON with indentation for readability
            print(json.dumps(config_data, indent=2))
    except Exception as e:
        print(f"Error reading configuration file: {e}")


def show_workflow(config_name: str) -> None:
    """
    Show details of a workflow (collection).
    
    Args:
        config_name: Name of the workflow
    """
    config_path = find_config_file("workflows", config_name)
    if not config_path:
        print(f"Error: Workflow '{config_name}' not found.")
        return
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            # Print raw JSON with indentation for readability
            print(json.dumps(config_data, indent=2))
    except Exception as e:
        print(f"Error reading configuration file: {e}")


def handle_show_command(config_type: str, config_name: str) -> None:
    """
    Handle the --show command based on the specified type and name.
    
    Args:
        config_type: Type of configuration (auth, proxies, insertion_points, workflows)
        config_name: Name of the configuration
    """
    if config_type == 'auth':
        show_auth_configuration(config_name)
    elif config_type == 'proxies':
        show_proxy_configuration(config_name)
    elif config_type == 'insertion_points':
        show_insertion_point(config_name)
    elif config_type == 'workflows':
        show_workflow(config_name)
    else:
        print(f"Error: Unknown configuration type '{config_type}'")
        print("Available configuration types: auth, proxies, insertion_points, workflows")


if __name__ == "__main__":
    # Setup logging for standalone testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Example usage
    print("Testing config.py")
    
    # Load proxy
    proxy_config = load_proxy()
    print(f"Loaded proxy configuration: {proxy_config}")
    
    # Check proxy connection
    if 'proxy_host' in proxy_config and 'proxy_port' in proxy_config:
        host = proxy_config['proxy_host']
        port = proxy_config['proxy_port']
        
        print(f"Checking proxy connection to {host}:{port}...")
        if check_proxy_connection(host, port):
            print(f"Proxy is running at {host}:{port}")
        else:
            print(f"No proxy found at {host}:{port}")
    else:
        print("No proxy host/port specified in configuration")