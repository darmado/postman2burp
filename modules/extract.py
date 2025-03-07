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
from typing import Dict, List, Set, Tuple, Optional

# Configure logger
logger = logging.getLogger('repl.extract')

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
    Create a directory structure based on the collection hierarchy.
    
    Args:
        collection_path (str): Path to the collection file
        output_dir (str, optional): Base directory to create the structure in. If None, use the collection name.
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.debug(f"Creating directory structure from {collection_path}")
    
    # Load collection file
    try:
        with open(collection_path, 'r') as f:
            collection_data = json.load(f)
    except Exception as e:
        logger.error(f"Could not load collection file: {e}")
        return False
    
    # Get collection name
    collection_name = "unknown_collection"
    if "info" in collection_data and "name" in collection_data["info"]:
        collection_name = collection_data["info"]["name"]
    
    # Create base directory
    if output_dir is None:
        # Replace spaces with underscores and remove special characters
        base_dir = re.sub(r'[^\w\s]', '', collection_name).replace(' ', '_')
        # Ensure it's in the collections directory
        base_dir = os.path.join('collections', base_dir)
    else:
        base_dir = output_dir
    
    # Create base directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)
    logger.info(f"Created base directory: {base_dir}")
    
    # Process items recursively
    def process_items(items, current_path):
        for item in items:
            if "name" not in item:
                continue
            
            # Replace spaces with underscores and remove special characters
            item_name = re.sub(r'[^\w\s]', '', item["name"]).replace(' ', '_')
            
            # If item has nested items, it's a folder
            if "item" in item and isinstance(item["item"], list):
                # Create folder
                folder_path = os.path.join(current_path, item_name)
                os.makedirs(folder_path, exist_ok=True)
                logger.debug(f"Created folder: {folder_path}")
                
                # Process nested items
                process_items(item["item"], folder_path)
            else:
                # It's an endpoint, create a file
                endpoint_name = item["name"]
                # Use CamelCase for file names
                endpoint_file = ''.join(word.capitalize() for word in endpoint_name.split())
                file_path = os.path.join(current_path, f"{endpoint_file}.json")
                
                # Extract request details
                if "request" in item:
                    request_data = {
                        "name": endpoint_name,
                        "request": item["request"]
                    }
                    
                    # Save request to file
                    try:
                        with open(file_path, 'w') as f:
                            json.dump(request_data, f, indent=2)
                        logger.debug(f"Created endpoint file: {file_path}")
                    except Exception as e:
                        logger.error(f"Could not save endpoint file: {e}")
    
    # Process top-level items
    if "item" in collection_data and isinstance(collection_data["item"], list):
        process_items(collection_data["item"], base_dir)
    
    # Create variables file
    variables, _, _ = extract_variables_from_collection(collection_path)
    if variables:
        variables_file = os.path.join(base_dir, "variables.json")
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
            with open(variables_file, 'w') as f:
                json.dump(template, f, indent=2)
            logger.info(f"Variables template saved to {variables_file}")
        except Exception as e:
            logger.error(f"Could not save variables template: {e}")
    
    logger.info(f"Directory structure created successfully in {base_dir}")
    return True

def extract_collection_to_structure(collection_path: str, output_dir: str = None) -> bool:
    """
    Extract a collection to a directory structure with variables.
    
    Args:
        collection_path (str): Path to the collection file
        output_dir (str, optional): Base directory to create the structure in. If None, use the collection name.
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.debug(f"Extracting collection to structure: {collection_path}")
    
    if not os.path.exists(collection_path):
        logger.error(f"Collection file not found: {collection_path}")
        return False
    
    # Ensure collections directory exists
    collections_dir = 'collections'
    if not os.path.exists(collections_dir):
        try:
            os.makedirs(collections_dir)
            logger.debug(f"Created collections directory: {collections_dir}")
        except Exception as e:
            logger.error(f"Could not create collections directory: {e}")
            return False
    
    # Create directory structure
    success = create_directory_structure(collection_path, output_dir)
    
    if success:
        print(f"\nCollection extracted successfully from {os.path.basename(collection_path)}")
        print(f"Directory structure created based on collection hierarchy")
        
        # Extract variables
        variables, _, _ = extract_variables_from_collection(collection_path)
        if variables:
            print(f"\nFound {len(variables)} variables in collection:")
            for var in sorted(variables):
                print(f"  - {var}")
    
    return success 