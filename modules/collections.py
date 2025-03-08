"""
Collections Module

This module provides functionality for managing Postman collections.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Set, Tuple, Any

# Configure logger
logger = logging.getLogger('repl.collections')

# Constants
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLLECTIONS_DIR = os.path.join(SCRIPT_DIR, "collections")

# Import the config module directly
from modules.config import validate_json_file
config_available = True

    # Define a simple validate_json_file function if the config module is not available
def validate_json_file(file_path: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate a JSON file and return its contents.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Tuple[bool, Optional[Dict]]: A tuple containing a boolean indicating if the file is valid,
                                        and the file contents if valid, None otherwise
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return True, data
        except Exception as e:
            logger.error(f"Error validating JSON file: {e}")
            return False, None

def select_collection_file() -> str:
    """
    List all JSON collection files in the collections directory and allow the user to select one.
    Handles hierarchical directory structure.
    Returns the path to the selected collection file.
    """
    logger.info("Listing available collection files for selection")
    
    # Create collections directory if it doesn't exist
    if not os.path.exists(COLLECTIONS_DIR):
        try:
            os.makedirs(COLLECTIONS_DIR)
            logger.debug(f"Created collections directory at {COLLECTIONS_DIR}")
        except Exception as e:
            logger.error(f"Could not create collections directory: {e}")
            print(f"Error: Could not create collections directory: {e}")
            return ""
    
    # Get all collection files recursively
    collection_files = []
    try:
        for root, _, files in os.walk(COLLECTIONS_DIR):
            for file in files:
                if file.endswith('.json'):
                    rel_path = os.path.relpath(os.path.join(root, file), COLLECTIONS_DIR)
                    collection_files.append(rel_path)
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
    check if it exists in the collections directory or its subdirectories.
    
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
    
    # Search recursively in the collections directory
    try:
        for root, _, files in os.walk(COLLECTIONS_DIR):
            for file in files:
                if file == collection_path or file == collection_path + '.json':
                    return os.path.join(root, file)
                
                # Check if the path is a relative path within the collections directory
                rel_path = os.path.relpath(os.path.join(root, file), COLLECTIONS_DIR)
                if rel_path == collection_path or rel_path == collection_path + '.json':
                    return os.path.join(root, file)
    except Exception as e:
        logger.error(f"Error searching for collection file: {e}")
    
    logger.warning(f"Collection file not found: {collection_path}")
    return collection_path

def list_collections(format_type="tree"):
    """
    List all available collection files and directories.
    
    Args:
        format_type: Output format - "tree" or "table"
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
    
    # Get all items in the collections directory
    try:
        items = os.listdir(COLLECTIONS_DIR)
    except Exception as e:
        logger.error(f"Could not list collections directory: {e}")
        return
    
    if not items:
        print("No collection files or directories found.")
        print(f"Place your Postman collection JSON files in the {COLLECTIONS_DIR} directory.")
        return
    
    # Choose the appropriate display format
    if format_type.lower() == "tree":
        _display_tree_format(items)
    else:
        _display_table_format(items)

def _display_tree_format(items):
    """
    Display collections in a tree format with separation lines between main parent directories.
    
    Args:
        items: List of items in the collections directory
    """
    print("\nAvailable collections:")
    
    # First, handle files at the root level
    root_files = []
    for item in items:
        item_path = os.path.join(COLLECTIONS_DIR, item)
        if os.path.isfile(item_path) and item.endswith('.json'):
            root_files.append(item)
    
    # Print root files
    for file in sorted(root_files):
        print(f"├── {file}")
    
    # Add a separation line if we have both root files and directories
    dirs = [item for item in items if os.path.isdir(os.path.join(COLLECTIONS_DIR, item))]
    if root_files and dirs:
        print("│")
    
    # Then process directories
    last_dir_index = len(dirs) - 1
    
    for i, dir_name in enumerate(sorted(dirs)):
        is_last = (i == last_dir_index)
        prefix = "└── " if is_last else "├── "
        print(f"{prefix}{dir_name}/")
        _print_directory_tree(os.path.join(COLLECTIONS_DIR, dir_name), "    " if is_last else "│   ")
        
        # Add a separation line between main directories (except after the last one)
        if not is_last:
            print("│")

def _print_directory_tree(directory_path, prefix):
    """
    Recursively print a directory tree.
    
    Args:
        directory_path: Path to the directory
        prefix: Prefix to use for indentation
    """
    try:
        items = os.listdir(directory_path)
    except Exception as e:
        logger.error(f"Could not list directory {directory_path}: {e}")
        return
    
    # Separate directories and files
    dirs = []
    files = []
    
    for item in items:
        item_path = os.path.join(directory_path, item)
        if os.path.isdir(item_path):
            dirs.append(item)
        elif item.endswith('.json'):
            files.append(item)
    
    # Sort both lists
    dirs.sort()
    files.sort()
    
    # Process files first
    for i, file in enumerate(files):
        is_last_file = (i == len(files) - 1) and not dirs
        file_prefix = "└── " if is_last_file else "├── "
        print(f"{prefix}{file_prefix}{file}")
    
    # Then process directories
    for i, dir_name in enumerate(dirs):
        is_last = (i == len(dirs) - 1)
        dir_prefix = "└── " if is_last else "├── "
        print(f"{prefix}{dir_prefix}{dir_name}/")
        
        new_prefix = prefix + ("    " if is_last else "│   ")
        _print_directory_tree(os.path.join(directory_path, dir_name), new_prefix)

def _display_table_format(items):
    """
    Display collections in a compact table format with separation lines between different parent directories.
    
    Args:
        items: List of items in the collections directory
    """
    # Collect all files with their full directory path
    collection_files = []
    
    # First, handle files at the root level
    for item in items:
        item_path = os.path.join(COLLECTIONS_DIR, item)
        if os.path.isfile(item_path) and item.endswith('.json'):
            collection_files.append(([], item))
    
    # Then recursively process directories
    for item in items:
        item_path = os.path.join(COLLECTIONS_DIR, item)
        if os.path.isdir(item_path):
            _collect_files_with_path(item_path, [item], collection_files)
    
    # Group files by their directory path
    grouped_files = {}
    for path, filename in collection_files:
        path_tuple = tuple(path)
        if path_tuple not in grouped_files:
            grouped_files[path_tuple] = []
        grouped_files[path_tuple].append(filename)
    
    # Determine the maximum depth of directories
    max_depth = 0
    for path in grouped_files.keys():
        max_depth = max(max_depth, len(path))
    
    # Print the table header
    print("\nAvailable collections:")
    
    # Create header columns based on max depth
    header_cols = []
    for i in range(max_depth):
        header_cols.append(f"Directory {i+1}")
    header_cols.append("Files")
    
    # Print header with less padding
    header_format = ""
    for _ in range(max_depth):
        header_format += "{:<20} "
    header_format += "{:<40}"
    
    print(header_format.format(*header_cols))
    
    # Create a separator line
    separator = "-" * (20 * max_depth + 40)
    print(separator)
    
    # Print the table rows
    current_parent = None
    
    for path, files in sorted(grouped_files.items()):
        # Check if we're starting a new parent directory
        if path and (not current_parent or path[0] != current_parent):
            if current_parent:  # Add separator between different parent directories
                print(separator)
            current_parent = path[0] if path else None
        
        # Pad the path with empty strings if needed
        padded_path = list(path) + [""] * (max_depth - len(path))
        
        # Join all files with commas
        files_str = ", ".join(sorted(files))
        
        # Create the row format
        row_format = ""
        for _ in range(max_depth):
            row_format += "{:<20} "
        row_format += "{:<40}"
        
        # Print the row
        print(row_format.format(*(padded_path + [files_str])))

def _collect_files_with_path(directory_path, current_path, collection_files):
    """
    Helper function to collect files recursively with their full directory path.
    
    Args:
        directory_path: Path to the directory
        current_path: List of directory names in the current path
        collection_files: List to store the collected files
    """
    try:
        items = os.listdir(directory_path)
    except Exception as e:
        logger.error(f"Could not list directory {directory_path}: {e}")
        return
    
    # Process files in this directory
    for item in items:
        item_path = os.path.join(directory_path, item)
        if os.path.isfile(item_path) and item.endswith('.json'):
            # Store as (path, filename)
            collection_files.append((current_path, item))
    
    # Process subdirectories
    for item in items:
        item_path = os.path.join(directory_path, item)
        if os.path.isdir(item_path):
            # Create a new path by appending the current directory
            new_path = current_path + [item]
            _collect_files_with_path(item_path, new_path, collection_files)

def load_collection(collection_path: str) -> Tuple[bool, Dict]:
    """
    Load a collection from a file.
    
    Args:
        collection_path: Path to the collection file
        
    Returns:
        Tuple[bool, Dict]: A tuple containing a boolean indicating if the collection was loaded successfully,
                          and the collection data if successful, an empty dict otherwise
    """
    logger.debug(f"load_collection called with path: {collection_path}")
    
    # Resolve the collection path if it's not absolute
    if not os.path.isabs(collection_path):
        resolved_path = resolve_collection_path(collection_path)
    else:
        resolved_path = collection_path
    
    if not resolved_path or not os.path.exists(resolved_path):
        logger.error(f"Collection file not found: {collection_path}")
        return False, {}
    
    # Validate and load the collection file
    is_valid, collection_data = validate_json_file(resolved_path)
    
    if not is_valid or not collection_data:
        logger.error(f"Invalid collection file: {resolved_path}")
        return False, {}
    
    logger.info(f"Collection loaded successfully: {resolved_path}")
    return True, collection_data

def extract_collection_id(collection_path: str) -> Optional[str]:
    """
    Extract the collection ID from a Postman collection file.
    
    Args:
        collection_path: Path to the collection file
        
    Returns:
        Optional[str]: Collection ID if found, None otherwise
    """
    logger.debug(f"extract_collection_id called with path: {collection_path}")
    
    # Resolve the collection path if it's not absolute
    if not os.path.isabs(collection_path):
        resolved_path = resolve_collection_path(collection_path)
    else:
        resolved_path = collection_path
    
    if not resolved_path or not os.path.exists(resolved_path):
        logger.error(f"Collection file not found: {collection_path}")
        return None
    
    # Validate the collection file
    is_valid, collection_data = validate_json_file(resolved_path)
    
    if not is_valid or not collection_data:
        logger.error(f"Invalid collection file: {resolved_path}")
        return None
    
    # Extract collection ID
    if "info" in collection_data and "_postman_id" in collection_data["info"]:
        return collection_data["info"]["_postman_id"]
    
    return None 