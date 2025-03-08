"""
List Module

This module provides functions to list various configurations in different formats.
"""

import os
import logging
from typing import List, Dict, Any, Optional

# Configure logger
logger = logging.getLogger('repl.list')

# Constants
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(SCRIPT_DIR, "config")
AUTH_CONFIG_DIR = os.path.join(CONFIG_DIR, "auth")
COLLECTIONS_DIR = os.path.join(SCRIPT_DIR, "collections")

def list_auth(format_type="tree"):
    """
    List all available authentication methods.
    
    Args:
        format_type: Output format - "tree" or "table"
    """
    logger.info("Listing available authentication methods")
    
    # Check if auth directory exists
    if not os.path.exists(AUTH_CONFIG_DIR):
        try:
            os.makedirs(AUTH_CONFIG_DIR, exist_ok=True)
            logger.debug(f"Created auth directory at {AUTH_CONFIG_DIR}")
        except Exception as e:
            logger.error(f"Could not create auth directory: {e}")
            return
    
    # Get all items in the auth directory
    try:
        items = os.listdir(AUTH_CONFIG_DIR)
    except Exception as e:
        logger.error(f"Could not list auth directory: {e}")
        return
    
    if not items:
        print("No authentication methods found.")
        print(f"Authentication methods will be stored in the {AUTH_CONFIG_DIR} directory.")
        return
    
    # Choose the appropriate display format
    if format_type.lower() == "tree":
        _display_auth_tree_format(items)
    else:
        _display_auth_table_format(items)

def _display_auth_tree_format(items):
    """
    Display authentication methods in a tree format with separation lines between main parent directories.
    
    Args:
        items: List of items in the auth directory
    """
    print("\nAvailable authentication methods:")
    
    # First, handle files at the root level
    root_files = []
    for item in items:
        item_path = os.path.join(AUTH_CONFIG_DIR, item)
        if os.path.isfile(item_path) and item.endswith('.json'):
            root_files.append(item)
    
    # Print root files
    for file in sorted(root_files):
        print(f"├── {file}")
    
    # Add a separation line if we have both root files and directories
    dirs = [item for item in items if os.path.isdir(os.path.join(AUTH_CONFIG_DIR, item))]
    if root_files and dirs:
        print("│")
    
    # Then process directories
    last_dir_index = len(dirs) - 1
    
    for i, dir_name in enumerate(sorted(dirs)):
        is_last = (i == last_dir_index)
        prefix = "└── " if is_last else "├── "
        print(f"{prefix}{dir_name}/")
        _print_auth_directory_tree(os.path.join(AUTH_CONFIG_DIR, dir_name), "    " if is_last else "│   ")
        
        # Add a separation line between main directories (except after the last one)
        if not is_last:
            print("│")

def _print_auth_directory_tree(directory_path, prefix):
    """
    Recursively print a directory tree for authentication methods.
    
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
        _print_auth_directory_tree(os.path.join(directory_path, dir_name), new_prefix)

def _display_auth_table_format(items):
    """
    Display authentication methods in a compact table format.
    
    Args:
        items: List of items in the auth directory
    """
    # Collect all files with their full directory path
    auth_files = []
    
    # First, handle files at the root level
    for item in items:
        item_path = os.path.join(AUTH_CONFIG_DIR, item)
        if os.path.isfile(item_path) and item.endswith('.json'):
            auth_files.append(([], item))
    
    # Then recursively process directories
    for item in items:
        item_path = os.path.join(AUTH_CONFIG_DIR, item)
        if os.path.isdir(item_path):
            _collect_auth_files_with_path(item_path, [item], auth_files)
    
    # Group files by their directory path
    grouped_files = {}
    for path, filename in auth_files:
        path_tuple = tuple(path)
        if path_tuple not in grouped_files:
            grouped_files[path_tuple] = []
        grouped_files[path_tuple].append(filename)
    
    # Print the grouped files
    print("\nAvailable authentication methods:")
    
    # First, print files at the root level
    if tuple() in grouped_files:
        print("\nRoot level:")
        for filename in sorted(grouped_files[tuple()]):
            print(f"  {filename}")
    
    # Then print files in subdirectories
    for path_tuple in sorted(grouped_files.keys()):
        if path_tuple == tuple():
            continue
        
        path_str = " > ".join(path_tuple)
        print(f"\n{path_str}:")
        for filename in sorted(grouped_files[path_tuple]):
            print(f"  {filename}")

def _collect_auth_files_with_path(directory_path, current_path, auth_files):
    """
    Recursively collect authentication files with their directory path.
    
    Args:
        directory_path: Path to the directory
        current_path: Current directory path as a list
        auth_files: List to store the collected files
    """
    try:
        items = os.listdir(directory_path)
    except Exception as e:
        logger.error(f"Could not list directory {directory_path}: {e}")
        return
    
    for item in items:
        item_path = os.path.join(directory_path, item)
        if os.path.isfile(item_path) and item.endswith('.json'):
            auth_files.append((current_path, item))
        elif os.path.isdir(item_path):
            new_path = current_path + [item]
            _collect_auth_files_with_path(item_path, new_path, auth_files)

def get_list_types():
    """
    Get all available list types for autocomplete.
    
    Returns:
        List[str]: List of available list types
    """
    return ["collections", "variables", "insertion-points", "results", "auth"]
