"""
Key Extractor Module

This module provides functionality to extract variables from Postman collections
and generate template files for insertion points.
"""

import os
import json
import re
import logging
import shutil
import time
from typing import Dict, List, Set, Tuple, Optional

# Configure logger
logger = logging.getLogger('repl.importman')

# Constants
# HOME_DIR depends on the location of the script (Hacky) 
HOME_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(HOME_DIR, "config")
COLLECTIONS_DIR = os.path.join(HOME_DIR, "collections")

def extract_variables_from_text(text: str) -> Set[str]:
    """
    Extract variables from text using regex pattern {{variable}}.
    
    Args:
        text (str): Text to extract variables from
        
    Returns:
        Set[str]: Set of variable names
    """
    if not text:
        return set()
    
    # Pattern to match {{variable}}
    pattern = r'{{([^{}]+)}}'
    matches = re.findall(pattern, text)
    
    # Return unique variable names
    return set(matches)

def extract_variables_from_collection(collection_path: str) -> Tuple[Set[str], Optional[str], Dict]:
    """
    Extract variables from a Postman collection.
    
    Args:
        collection_path (str): Path to the collection file
        
    Returns:
        Tuple[Set[str], Optional[str], Dict]: Set of variable names, collection ID, and collection data
    """
    logger.debug(f"Extracting variables from collection: {collection_path}")
    
    # Load collection file
    try:
        with open(collection_path, 'r') as f:
            collection_data = json.load(f)
    except Exception as e:
        logger.error(f"Could not load collection file: {e}")
        return set(), None, {}
    
    # Extract collection ID
    collection_id = None
    if "info" in collection_data and "_postman_id" in collection_data["info"]:
        collection_id = collection_data["info"]["_postman_id"]
    
    # Initialize variables set
    variables = set()
    
    # Process URL
    def process_url(url):
        if isinstance(url, str):
            variables.update(extract_variables_from_text(url))
        elif isinstance(url, dict):
            for key, value in url.items():
                if key == "raw":
                    variables.update(extract_variables_from_text(value))
                elif key == "host" or key == "path" or key == "query":
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, str):
                                variables.update(extract_variables_from_text(item))
                            elif isinstance(item, dict) and "value" in item:
                                variables.update(extract_variables_from_text(item["value"]))
    
    # Process body
    def process_body(body):
        if not body:
            return
        
        if isinstance(body, dict):
            if "raw" in body:
                variables.update(extract_variables_from_text(body["raw"]))
            if "formdata" in body and isinstance(body["formdata"], list):
                for item in body["formdata"]:
                    if isinstance(item, dict) and "value" in item:
                        variables.update(extract_variables_from_text(item["value"]))
    
    # Process headers
    def process_headers(headers):
        if isinstance(headers, list):
            for header in headers:
                if isinstance(header, dict) and "value" in header:
                    variables.update(extract_variables_from_text(header["value"]))
    
    # Process request
    def process_request(request):
        if not request:
            return
        
        if isinstance(request, dict):
            # Process URL
            if "url" in request:
                process_url(request["url"])
            
            # Process headers
            if "header" in request:
                process_headers(request["header"])
            
            # Process body
            if "body" in request:
                process_body(request["body"])
    
    # Process item
    def process_item(item):
        # Process request if present
        if "request" in item:
            process_request(item["request"])
        
        # Process nested items
        if "item" in item and isinstance(item["item"], list):
            for nested_item in item["item"]:
                process_item(nested_item)
    
    # Process collection items
    if "item" in collection_data and isinstance(collection_data["item"], list):
        for item in collection_data["item"]:
            process_item(item)
    
    # Process collection variables
    if "variable" in collection_data and isinstance(collection_data["variable"], list):
        for var in collection_data["variable"]:
            if isinstance(var, dict) and "key" in var:
                variables.add(var["key"])
    
    logger.debug(f"Found {len(variables)} variables in collection")
    return variables, collection_id, collection_data

def generate_variables_template(collection_path: str, output_path: str) -> bool:
    """
    Generate a variables template file from a collection.
    
    Args:
        collection_path (str): Path to the collection file
        output_path (str): Path to save the template file
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.debug(f"Generating variables template from {collection_path} to {output_path}")
    
    # Extract variables from collection
    variables, collection_id, _ = extract_variables_from_collection(collection_path)
    
    if not variables:
        logger.warning("No variables found in collection")
        return False
    
    # Create template structure
    template = {
        "variables": []
    }
    
    # Add variables to template
    for var in sorted(variables):
        template["variables"].append({
            "key": var,
            "value": "",
            "description": f"Value for {var}"
        })
    
    # Save template to file
    try:
        with open(output_path, 'w') as f:
            json.dump(template, f, indent=2)
        logger.info(f"Variables template saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Could not save template file: {e}")
        return False

def print_variables(collection_path: str) -> bool:
    """
    Print variables found in a collection.
    
    Args:
        collection_path (str): Path to the collection file
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Extract variables from collection
    variables, _, _ = extract_variables_from_collection(collection_path)
    
    if not variables:
        logger.warning("No variables found in collection")
        return False
    
    # Print variables
    print(f"\nFound {len(variables)} variables in collection {os.path.basename(collection_path)}:")
    for var in sorted(variables):
        print(var)
    
    print("\nTo create a template file with these variables, run:")
    print(f"python repl.py --collection {collection_path} --extract-keys variables.json")
    
    return True

def extract_keys(collection_path: str, output_path: str = None) -> bool:
    """
    Extract keys from a collection and either print them or save to a file.
    
    Args:
        collection_path (str): Path to the collection file
        output_path (str, optional): Path to save the template file. If None, print variables.
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.debug(f"Extracting keys from {collection_path}")
    
    if not os.path.exists(collection_path):
        logger.error(f"Collection file not found: {collection_path}")
        return False
    
    if output_path == "print" or output_path is None:
        return print_variables(collection_path)
    else:
        return generate_variables_template(collection_path, output_path)

def create_directory_structure(collection_path: str, output_dir: str = None) -> bool:
    """
    Create directory structure from a Postman collection.
    
    Args:
        collection_path: Path to the collection file
        output_dir: Output directory (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Creating directory structure from collection: {collection_path}")
    
    # Load the collection
    try:
        with open(collection_path, 'r') as f:
            collection_data = json.load(f)
    except Exception as e:
        logger.error(f"Could not load collection: {e}")
        return False
    
    # Check if it's a valid collection
    if "info" not in collection_data or "item" not in collection_data:
        logger.error("Invalid collection format")
        return False
    
    # Get collection name and ID
    collection_name = collection_data["info"].get("name", "Unknown Collection")
    collection_id = collection_data["info"].get("_postman_id", "")
    
    # Create output directory if not provided
    if not output_dir:
        # Sanitize collection name for directory
        sanitized_name = re.sub(r'[^\w\-\.]', '_', collection_name)
        if collection_id:
            sanitized_name = f"{sanitized_name}_{collection_id}"
        output_dir = os.path.join(COLLECTIONS_DIR, sanitized_name)
    
    # Check if the directory already exists
    if os.path.exists(output_dir):
        logger.info(f"Directory already exists: {output_dir}")
        print(f"Collection directory already exists: {output_dir}")
        
        # Prompt user for action
        while True:
            choice = input("Do you want to replace the existing collection, create a new one, or quit? (replace/new/q): ").lower()
            if choice == "replace":
                # Remove the existing directory
                try:
                    shutil.rmtree(output_dir)
                    logger.info(f"Removed existing directory: {output_dir}")
                    print(f"Removed existing directory: {output_dir}")
                    
                    # Create the directory again
                    os.makedirs(output_dir)
                    logger.debug(f"Created directory: {output_dir}")
                except Exception as e:
                    logger.error(f"Could not replace directory: {e}")
                    print(f"Error: Could not replace directory: {e}")
                    return False
                break
            elif choice == "new":
                # Create a new directory with incremental suffix
                # Find existing directories with the same base name
                base_dir = output_dir
                suffix = 1
                
                # Check for existing directories with incremental suffixes
                parent_dir = os.path.dirname(output_dir)
                base_name = os.path.basename(output_dir)
                existing_dirs = [d for d in os.listdir(parent_dir) if os.path.join(parent_dir, d).startswith(output_dir)]
                
                # Find the highest suffix
                for dir_name in existing_dirs:
                    if dir_name == base_name:
                        continue
                    
                    # Check if the directory has a suffix pattern like .001, .002, etc.
                    match = re.search(r'\.(\d{3})$', dir_name)
                    if match:
                        current_suffix = int(match.group(1))
                        if current_suffix >= suffix:
                            suffix = current_suffix + 1
                
                # Format the new suffix as a 3-digit number with leading zeros
                new_suffix = f".{suffix:03d}"
                output_dir = f"{base_dir}{new_suffix}"
                try:
                    os.makedirs(output_dir)
                    logger.debug(f"Created new directory: {output_dir}")
                    print(f"Created new directory: {output_dir}")
                except Exception as e:
                    logger.error(f"Could not create new directory: {e}")
                    print(f"Error: Could not create new directory: {e}")
                    return False
                break
            elif choice == "q":
                logger.info("User chose to quit the import process")
                print("Import process cancelled by user")
                return False
            else:
                print("Invalid choice. Please enter 'replace', 'new', or 'q'.")
    else:
        # Create the output directory if it doesn't exist
        try:
            os.makedirs(output_dir)
            logger.debug(f"Created directory: {output_dir}")
        except Exception as e:
            logger.error(f"Could not create directory: {e}")
            return False
    
    # Save the original collection file to the root of the output directory
    try:
        with open(os.path.join(output_dir, "collection.json"), 'w') as f:
            json.dump(collection_data, f, indent=2)
        logger.debug(f"Saved collection to: {os.path.join(output_dir, 'collection.json')}")
    except Exception as e:
        logger.error(f"Could not save collection: {e}")
    
    # Process items recursively
    def process_items(items, current_path):
        for item in items:
            # Skip if no name
            if "name" not in item:
                continue
            
            # Get item name and sanitize it for use as a directory name
            item_name = item["name"]
            dir_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in item_name)
            
            # Create the full path
            item_path = os.path.join(current_path, dir_name)
            
            # If it has subitems, process them recursively
            if "item" in item and isinstance(item["item"], list):
                # Create the directory if it doesn't exist
                if not os.path.exists(item_path):
                    try:
                        os.makedirs(item_path)
                        logger.debug(f"Created directory: {item_path}")
                    except Exception as e:
                        logger.error(f"Could not create directory: {e}")
                        continue
                
                # Process subitems
                process_items(item["item"], item_path)
            
            # If it has a request, save it
            if "request" in item:
                # Create the directory if it doesn't exist and it's not already created
                if not os.path.exists(item_path):
                    try:
                        os.makedirs(item_path)
                        logger.debug(f"Created directory: {item_path}")
                    except Exception as e:
                        logger.error(f"Could not create directory: {e}")
                        continue
                
                # Save the request to a file
                request_file = os.path.join(item_path, "request.json")
                try:
                    with open(request_file, 'w') as f:
                        json.dump(item["request"], f, indent=2)
                    logger.debug(f"Saved request to: {request_file}")
                except Exception as e:
                    logger.error(f"Could not save request: {e}")
    
    # Start processing from the root items
    process_items(collection_data["item"], output_dir)
    
    logger.info(f"Directory structure created at: {output_dir}")
    print(f"Directory structure created at: {output_dir}")
    
    return True

def import_collection_to_structure(collection_path: str, output_dir: str = None) -> bool:
    """
    Import a collection to a directory structure.
    
    Args:
        collection_path: Path to the collection file
        output_dir: Directory to create the structure in. If None, use the collection name.
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Importing collection to structure: {collection_path}")
    
    # Track if the collection is from the queue
    from_queue = False
    original_path = collection_path
    
    # If collection_path doesn't have a path separator and doesn't exist,
    # check if it's in the .queue directory
    if not os.path.exists(collection_path) and os.path.basename(collection_path) == collection_path:
        queue_dir = os.path.join(COLLECTIONS_DIR, ".queue")
        queue_collection = os.path.join(queue_dir, collection_path)
        if os.path.exists(queue_collection):
            logger.info(f"Found collection in queue directory: {queue_collection}")
            collection_path = queue_collection
            from_queue = True
    
    # Create the directory structure
    structure_success = create_directory_structure(collection_path, output_dir)
    
    # Import authentication methods
    print("\nAnalyzing collection for authentication methods...")
    auth_success = import_auth_from_collection(collection_path)
    
    # If successful and the collection was from the queue, remove it from the queue
    if structure_success and from_queue:
        try:
            os.remove(collection_path)
            logger.info(f"Removed collection from queue: {collection_path}")
            print(f"Removed collection from queue: {os.path.basename(collection_path)}")
        except Exception as e:
            logger.warning(f"Could not remove collection from queue: {e}")
            print(f"Warning: Could not remove collection from queue: {e}")
    
    if structure_success:
        logger.info("Collection imported to directory structure successfully")
    else:
        logger.error("Failed to import collection to directory structure")
    
    return structure_success

def identify_auth_in_collection(collection_data: Dict) -> List[Dict]:
    """
    Identify authentication methods used in a collection.
    
    Args:
        collection_data: The collection data
        
    Returns:
        List[Dict]: List of identified authentication methods with their details
    """
    logger.info("Identifying authentication methods in collection")
    
    auth_methods = []
    collection_name = collection_data.get("info", {}).get("name", "Unknown")
    # Use _postman_id from the info object
    collection_id = collection_data.get("info", {}).get("_postman_id", "")
    
    # Sanitize collection name for directory structure
    sanitized_collection_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in collection_name)
    
    # Function to recursively process items
    def process_items(items, parent_name=""):
        for item in items:
            if "name" not in item:
                continue
                
            item_name = item["name"]
            full_name = f"{parent_name}_{item_name}" if parent_name else item_name
            sanitized_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in full_name)
            
            # Process request if present
            if "request" in item:
                process_request(item, sanitized_name)
            
            # Process subitems recursively
            if "item" in item and isinstance(item["item"], list):
                process_items(item["item"], sanitized_name)
    
    # Function to process a request and identify auth
    def process_request(item, item_name):
        request = item["request"]
        
        # Capture request method and URL for context
        method = request.get("method", "")
        url_info = {}
        
        if "url" in request:
            url_obj = request["url"]
            if isinstance(url_obj, dict):
                # Handle object format
                raw_url = url_obj.get("raw", "")
                host = url_obj.get("host", [])
                if isinstance(host, list):
                    host = ".".join(host)
                path = url_obj.get("path", [])
                if isinstance(path, list):
                    path = "/".join(path)
                
                url_info = {
                    "raw": raw_url,
                    "host": host,
                    "path": path
                }
            else:
                # Handle string format
                url_info = {"raw": str(url_obj)}
        
        # Check for auth in the request
        if "auth" in request:
            auth_type = request["auth"]["type"]
            
            if auth_type == "basic":
                # Extract basic auth details
                username = ""
                password = ""
                for param in request["auth"].get("basic", []):
                    if param.get("key") == "username":
                        username = param.get("value", "")
                    elif param.get("key") == "password":
                        password = param.get("value", "")
                
                if username or password:
                    auth_methods.append({
                        "type": "basic",
                        "label": f"{collection_name} - {item_name} Basic Auth",
                        "name": f"{sanitized_collection_name}_{item_name}_basic",
                        "username": username,
                        "password": password,
                        "collection_id": collection_id,
                        "enabled": True,
                        "method": method,
                        "url": url_info,
                        "request_name": item.get("name", ""),
                        "request_description": item.get("description", "")
                    })
            
            elif auth_type == "bearer":
                # Extract bearer token
                token = ""
                for param in request["auth"].get("bearer", []):
                    if param.get("key") == "token":
                        token = param.get("value", "")
                
                # Check if token is a variable (dynamic token)
                is_dynamic = False
                if token and (token.startswith("{{") and token.endswith("}}")):
                    is_dynamic = True
                
                auth_data = {
                    "type": "bearer",
                    "label": f"{collection_name} - {item_name} Bearer Token",
                    "name": f"{sanitized_collection_name}_{item_name}_bearer",
                    "token": token,
                    "is_dynamic": is_dynamic,
                    "collection_id": collection_id,
                    "enabled": True,
                    "method": method,
                    "url": url_info,
                    "request_name": item.get("name", ""),
                    "request_description": item.get("description", "")
                }
                
                # If dynamic, add dynamic token fields
                if is_dynamic:
                    # Look for a pre-request script that might set the token
                    pre_request_script = ""
                    if "event" in item:
                        for event in item.get("event", []):
                            if event.get("listen") == "prerequest":
                                pre_request_script = event.get("script", {}).get("exec", [])
                                if isinstance(pre_request_script, list):
                                    pre_request_script = "\n".join(pre_request_script)
                    
                    # Try to extract auth URL and method from pre-request script
                    auth_url = ""
                    auth_method = "POST"
                    auth_headers = {"Content-Type": "application/json"}
                    auth_body = "{}"
                    token_location = "data.access_token"
                    
                    # Look for pm.sendRequest in the pre-request script
                    if "pm.sendRequest" in pre_request_script:
                        # Very basic extraction - in a real implementation, this would be more sophisticated
                        url_match = re.search(r'pm\.sendRequest\([\'"]([^\'"]*)[\'"]\s*,', pre_request_script)
                        if url_match:
                            auth_url = url_match.group(1)
                        
                        # Try to extract method
                        method_match = re.search(r'method:\s*[\'"]([^\'"]*)[\'"]', pre_request_script)
                        if method_match:
                            auth_method = method_match.group(1)
                        
                        # Try to extract body
                        body_match = re.search(r'body:\s*[\'"]([^\'"]*)[\'"]', pre_request_script)
                        if body_match:
                            auth_body = body_match.group(1)
                        
                        # Try to extract token location
                        token_match = re.search(r'pm\.environment\.set\([\'"]([^\'"]*)[\'"],\s*([^\)]*)\)', pre_request_script)
                        if token_match and token_match.group(1) == token[2:-2]:  # Remove {{ and }}
                            token_location = token_match.group(2)
                    
                    # Add dynamic token fields
                    auth_data.update({
                        "token": None,
                        "is_dynamic": True,
                        "auth_url": auth_url or "https://api.example.com/auth/token",
                        "auth_method": auth_method,
                        "auth_headers": auth_headers,
                        "auth_body": auth_body,
                        "token_refresh_interval": 3600,
                        "token_location": token_location,
                        "variable_name": token[2:-2]  # Remove {{ and }}
                    })
                
                auth_methods.append(auth_data)
            
            elif auth_type == "apikey":
                # Extract API key details
                key = ""
                value = ""
                in_location = "header"
                
                for param in request["auth"].get("apikey", []):
                    if param.get("key") == "key":
                        key = param.get("value", "")
                    elif param.get("key") == "value":
                        value = param.get("value", "")
                    elif param.get("key") == "auth_loc":
                        in_location = param.get("value", "")  # Preserve original case
                
                if key and value:
                    auth_methods.append({
                        "type": "apikey",
                        "label": f"{collection_name} - {item_name} API Key",
                        "name": f"{sanitized_collection_name}_{item_name}_apikey",
                        "key": key,
                        "value": value,
                        "auth_loc": in_location,
                        "collection_id": collection_id,
                        "enabled": True,
                        "method": method,
                        "url": url_info,
                        "request_name": item.get("name", ""),
                        "request_description": item.get("description", "")
                    })
        
        # Check for auth in headers
        elif "header" in request:
            for header in request.get("header", []):
                header_key = header.get("key", "")
                header_value = header.get("value", "")
                
                # Check for Authorization header (case-insensitive comparison but preserve original case)
                if header_key.lower() == "authorization":
                    if header_value.startswith("Bearer "):
                        token = header_value[7:]  # Remove "Bearer " prefix
                        
                        # Check if token is a variable (dynamic token)
                        is_dynamic = False
                        if token and (token.startswith("{{") and token.endswith("}}")):
                            is_dynamic = True
                        
                        auth_data = {
                            "type": "bearer",
                            "label": f"{collection_name} - {item_name} Bearer Token (Header)",
                            "name": f"{sanitized_collection_name}_{item_name}_bearer_header",
                            "token": token,
                            "is_dynamic": is_dynamic,
                            "collection_id": collection_id,
                            "enabled": True,
                            "auth_loc": "header",  # Explicitly note it's in the header
                            "method": method,
                            "url": url_info,
                            "request_name": item.get("name", ""),
                            "request_description": item.get("description", "")
                        }
                        
                        # If dynamic, add dynamic token fields
                        if is_dynamic:
                            # Look for a pre-request script that might set the token
                            pre_request_script = ""
                            if "event" in item:
                                for event in item.get("event", []):
                                    if event.get("listen") == "prerequest":
                                        pre_request_script = event.get("script", {}).get("exec", [])
                                        if isinstance(pre_request_script, list):
                                            pre_request_script = "\n".join(pre_request_script)
                            
                            # Add dynamic token fields
                            auth_data.update({
                                "token": None,
                                "is_dynamic": True,
                                "auth_url": "https://api.example.com/auth/token",
                                "auth_method": "POST",
                                "auth_headers": {"Content-Type": "application/json"},
                                "auth_body": "{}",
                                "token_refresh_interval": 3600,
                                "token_location": "data.access_token",
                                "variable_name": token[2:-2]  # Remove {{ and }}
                            })
                        
                        auth_methods.append(auth_data)
                    elif header_value.startswith("Basic "):
                        # We don't decode Basic auth from headers as it's base64 encoded
                        # and might contain sensitive information
                        auth_methods.append({
                            "type": "basic",
                            "label": f"{collection_name} - {item_name} Basic Auth (Header)",
                            "name": f"{sanitized_collection_name}_{item_name}_basic_header",
                            "username": "{{username}}",
                            "password": "{{password}}",
                            "collection_id": collection_id,
                            "enabled": False,
                            "needs_config": True,
                            "auth_loc": "header",  # Explicitly note it's in the header
                            "method": method,
                            "url": url_info,
                            "request_name": item.get("name", ""),
                            "request_description": item.get("description", "")
                        })
                
                # Check for common API key headers (case-insensitive comparison but preserve original case)
                elif header_key.lower() in ["x-api-key", "api-key", "apikey"]:
                    # Check if value is a variable
                    is_dynamic = False
                    if header_value and (header_value.startswith("{{") and header_value.endswith("}}")):
                        is_dynamic = True
                        
                    auth_methods.append({
                        "type": "apikey",
                        "label": f"{collection_name} - {item_name} API Key (Header)",
                        "name": f"{sanitized_collection_name}_{item_name}_apikey_header",
                        "key": header_key,  # Preserve original case
                        "value": header_value,
                        "auth_loc": "header",
                        "collection_id": collection_id,
                        "enabled": True,
                        "method": method,
                        "url": url_info,
                        "request_name": item.get("name", ""),
                        "request_description": item.get("description", "")
                    })
        
        # Check for auth in URL params
        if "url" in request:
            url_obj = request["url"]
            
            # Check for query parameters
            if "query" in url_obj:
                for param in url_obj.get("query", []):
                    param_key = param.get("key", "")
                    param_value = param.get("value", "")
                    
                    # Check for common API key parameters
                    if param_key.lower() in ["api_key", "apikey", "key", "token"]:
                        auth_methods.append({
                            "type": "apikey",
                            "label": f"{collection_name} - {item_name} API Key (URL)",
                            "name": f"{sanitized_collection_name}_{item_name}_apikey_url",
                            "key": param_key,  # Preserve original case
                            "value": param_value,
                            "auth_loc": "query",
                            "collection_id": collection_id,
                            "enabled": True,
                            "method": method,
                            "url": url_info,
                            "request_name": item.get("name", ""),
                            "request_description": item.get("description", "")
                        })
        
        # Check for auth in body
        if "body" in request:
            body = request["body"]
            
            # Only check raw JSON bodies
            if body.get("mode") == "raw" and "raw" in body:
                raw_body = body.get("raw", "")
                
                # Try to parse as JSON
                try:
                    body_json = json.loads(raw_body)
                    
                    # Check for common auth fields in body
                    for key in ["api_key", "apikey", "key", "token", "access_token"]:
                        if key in body_json:
                            auth_methods.append({
                                "type": "apikey",
                                "label": f"{collection_name} - {item_name} API Key (Body)",
                                "name": f"{sanitized_collection_name}_{item_name}_apikey_body",
                                "key": key,
                                "value": body_json[key],
                                "auth_loc": "body",
                                "collection_id": collection_id,
                                "enabled": True,
                                "method": method,
                                "url": url_info,
                                "request_name": item.get("name", ""),
                                "request_description": item.get("description", "")
                            })
                except:
                    # Not JSON or invalid JSON, skip
                    pass
    
    # Start processing from root items
    if "item" in collection_data:
        process_items(collection_data["item"])
    
    # Remove duplicates based on type and name
    unique_auth_methods = []
    seen = set()
    
    for auth in auth_methods:
        key = (auth["type"], auth["name"])
        if key not in seen:
            seen.add(key)
            unique_auth_methods.append(auth)
    
    return unique_auth_methods

def import_auth_from_collection(collection_path: str) -> bool:
    """
    Import authentication methods from a Postman collection.
    
    Args:
        collection_path: Path to the collection file
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Importing authentication methods from collection: {collection_path}")
    
    # Load the collection
    try:
        with open(collection_path, 'r') as f:
            collection_data = json.load(f)
    except Exception as e:
        logger.error(f"Could not load collection: {e}")
        return False
    
    # Check if it's a valid collection
    if "info" not in collection_data:
        logger.error("Invalid collection format")
        return False
    
    # Get collection name and ID for directory structure
    collection_name = collection_data["info"].get("name", "Unknown Collection")
    collection_id = collection_data["info"].get("_postman_id", "")
    
    # Sanitize collection name for directory
    sanitized_collection_name = re.sub(r'[^\w\-\.]', '_', collection_name)
    if collection_id:
        sanitized_collection_name = f"{sanitized_collection_name}_{collection_id}"
    
    # HOME_DIR is the root directory of the project
    HOME_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # CONFIG_DIR is the config directory inside the project
    CONFIG_DIR = os.path.join(HOME_DIR, "config")
    
    # Collection config directory
    collection_config_dir = os.path.join(CONFIG_DIR, sanitized_collection_name)
    # Auth directory inside the collection config directory
    auth_dir = os.path.join(collection_config_dir, "auth")
    
    # Check if directory already exists
    if os.path.exists(collection_config_dir):
        logger.info(f"Collection config directory already exists: {collection_config_dir}")
        print(f"Collection config directory already exists: {collection_config_dir}")
        
        while True:
            choice = input("Do you want to replace the existing directory or create a new one? (replace/new): ").lower()
            if choice == "replace":
                # Continue with existing directory
                break
            elif choice == "new":
                # Create a new directory with incremental suffix
                # Find existing directories with the same base name
                base_dir = collection_config_dir
                suffix = 1
                
                # Check for existing directories with incremental suffixes
                parent_dir = os.path.dirname(collection_config_dir)
                base_name = os.path.basename(collection_config_dir)
                existing_dirs = [d for d in os.listdir(parent_dir) if os.path.join(parent_dir, d).startswith(collection_config_dir)]
                
                # Find the highest suffix
                for dir_name in existing_dirs:
                    if dir_name == base_name:
                        continue
                    
                    # Check if the directory has a suffix pattern like .001, .002, etc.
                    match = re.search(r'\.(\d{3})$', dir_name)
                    if match:
                        current_suffix = int(match.group(1))
                        if current_suffix >= suffix:
                            suffix = current_suffix + 1
                
                # Format the new suffix as a 3-digit number with leading zeros
                new_suffix = f".{suffix:03d}"
                collection_config_dir = f"{base_dir}{new_suffix}"
                auth_dir = os.path.join(collection_config_dir, "auth")
                logger.info(f"Creating new config directory: {collection_config_dir}")
                print(f"Creating new config directory: {collection_config_dir}")
                break
            else:
                print("Invalid choice. Please enter 'replace' or 'new'.")
    
    # Create the directory structure
    os.makedirs(collection_config_dir, exist_ok=True)
    os.makedirs(auth_dir, exist_ok=True)
    
    # Also create other config directories for future use
    os.makedirs(os.path.join(collection_config_dir, "proxies"), exist_ok=True)
    os.makedirs(os.path.join(collection_config_dir, "workflows"), exist_ok=True)
    
    # Import authentication methods
    imported_count = 0
    for auth in identify_auth_in_collection(collection_data):
        auth_type = auth["type"]
        auth_name = auth["name"]
        
        # Skip if needs configuration
        if auth.get("needs_config", False):
            logger.info(f"Skipping {auth_type} auth '{auth_name}' as it needs manual configuration")
            print(f"Skipping {auth_type} auth '{auth_name}' as it needs manual configuration")
            continue
        
        # Extract the request path from the item name
        # The item_name is in the format: parent_subparent_endpoint
        # We want to create a directory structure like: parent/subparent/
        path_parts = []
        name_parts = auth_name.split('_')
        
        # Skip the collection name part (first part)
        if name_parts and name_parts[0] == sanitized_collection_name.split('_')[0]:  # Handle timestamped names
            name_parts = name_parts[1:]
        
        # The last part is the endpoint and auth type, so we'll use it for the filename
        if len(name_parts) > 1:
            path_parts = name_parts[:-1]  # All but the last part
            endpoint_name = name_parts[-1]
        else:
            endpoint_name = name_parts[0] if name_parts else "unknown"
        
        # Remove "Collection" from path parts if it exists
        path_parts = [part for part in path_parts if part.lower() != "collection"]
        
        # Create the directory path
        current_dir = auth_dir
        for part in path_parts:
            current_dir = os.path.join(current_dir, part)
            os.makedirs(current_dir, exist_ok=True)
            logger.debug(f"Created directory: {current_dir}")
        
        # Create auth file
        auth_file_path = os.path.join(current_dir, f"{endpoint_name}.json")
        
        try:
            # Prepare auth data based on type
            auth_data = {}
            
            # Common fields for all auth types
            common_fields = {
                "label": auth.get("label", f"{auth_name}"),
                "type": auth_type,
                "enabled": auth.get("enabled", True),
                "collection_id": auth.get("collection_id", "")
            }
            
            # Add request context
            if auth.get("method") or auth.get("url") or auth.get("request_name") or auth.get("request_description"):
                common_fields["request_context"] = {
                    "method": auth.get("method", ""),
                    "url": auth.get("url", {}),
                    "name": auth.get("request_name", ""),
                    "description": auth.get("request_description", "")
                }
            
            # Add 'in' field if available - this indicates where the auth is located (header, query, body)
            if "in" in auth:
                common_fields["auth_loc"] = auth["in"]  # Use auth_loc as requested
            
            if auth_type == "basic":
                auth_data = {
                    **common_fields,
                    "username": auth["username"],
                    "password": auth["password"]
                }
            elif auth_type == "bearer":
                auth_data = {
                    **common_fields,
                    "token": auth["token"]
                }
                
                # Add dynamic token fields if applicable
                if auth.get("is_dynamic", False):
                    auth_data.update({
                        "token": None,
                        "is_dynamic": True,
                        "auth_url": auth.get("auth_url", "https://api.example.com/auth/token"),
                        "auth_method": auth.get("auth_method", "POST"),
                        "auth_headers": auth.get("auth_headers", {"Content-Type": "application/json"}),
                        "auth_body": auth.get("auth_body", "{}"),
                        "token_refresh_interval": auth.get("token_refresh_interval", 3600),
                        "token_location": auth.get("token_location", "data.access_token")
                    })
                    
                    # Add variable name if available
                    if "variable_name" in auth:
                        auth_data["variable_name"] = auth["variable_name"]
            elif auth_type == "apikey":
                auth_data = {
                    **common_fields,
                    "key": auth["key"],
                    "value": auth["value"]
                }
            
            # Save auth data to file
            with open(auth_file_path, 'w') as f:
                json.dump(auth_data, f, indent=2)
            
            logger.info(f"Imported {auth_type} auth to {auth_file_path}")
            print(f"Imported {auth_type} auth: {auth.get('label', auth_name)}")
            imported_count += 1
        except Exception as e:
            logger.error(f"Could not import {auth_type} auth '{auth_name}': {e}")
            print(f"Error: Could not import {auth_type} auth '{auth_name}': {e}")
    
    if imported_count > 0:
        logger.info(f"Successfully imported {imported_count} authentication methods")
        print(f"Successfully imported {imported_count} authentication methods")
    else:
        logger.warning("No authentication methods were imported")
        print("No authentication methods were imported")
    
    return imported_count > 0 