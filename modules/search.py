"""
Search Module

This module provides functionality to search HTTP requests and responses in log files.
It helps testers find specific requests by ID or content patterns.
"""

import os
import glob
import json
import logging
from typing import List, Dict, Any, Optional
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored terminal output
init()

# Configure logger
logger = logging.getLogger('repl.search')

def search_logs(query: str, collection_name: str = None, folder_path: str = None) -> List[Dict]:
    """
    Search for HTTP requests and responses containing the specified query.
    
    Args:
        query (str): The search query (request ID or content pattern)
        collection_name (str, optional): Name of the collection to search in
        folder_path (str, optional): Path within the collection to search in
        
    Returns:
        List[Dict]: List of matching request/response pairs
    """
    logger.debug(f"Searching for: {query}")
    
    # Find all potential result files
    result_files = find_result_files(collection_name, folder_path)
    
    if not result_files:
        print(f"{Fore.YELLOW}No request/response logs found to search.{Style.RESET_ALL}")
        if collection_name:
            print(f"Collection: {collection_name}")
        if folder_path:
            print(f"Folder: {folder_path}")
            
        # Show available collections
        available_collections = get_available_collections()
        if available_collections:
            print(f"\n{Fore.CYAN}Available collections:{Style.RESET_ALL}")
            for collection in available_collections:
                print(f"  - {collection}")
            
            # If collection is specified, show available folders
            if collection_name and collection_name in available_collections:
                available_folders = get_available_folders(collection_name)
                if available_folders:
                    print(f"\n{Fore.CYAN}Available folders in {collection_name}:{Style.RESET_ALL}")
                    for folder in available_folders:
                        print(f"  - {folder}")
        
        return []
    
    print(f"Searching {len(result_files)} result files for: '{query}'")
    
    # Search files for matching requests/responses
    matches = []
    for file_path in result_files:
        file_matches = search_result_file(file_path, query)
        matches.extend(file_matches)
    
    # Display results
    if matches:
        print(f"\n{Fore.GREEN}Found {len(matches)} matching requests for '{query}':{Style.RESET_ALL}")
        
        for i, match in enumerate(matches, 1):
            print(f"\n{Fore.CYAN}Match #{i} - Request ID: {match['request_id']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}File: {match['file']}{Style.RESET_ALL}")
            
            # Print request details
            print(f"\n{Fore.MAGENTA}REQUEST:{Style.RESET_ALL}")
            print(f"  Method: {match['method']} {match['url']}")
            if match.get('headers'):
                print("  Headers:")
                for header, value in match['headers'].items():
                    print(f"    {header}: {highlight_match(value, query)}")
            if match.get('body'):
                print("  Body:")
                print(f"    {highlight_match(match['body'], query)}")
            
            # Print response details
            if match.get('response'):
                print(f"\n{Fore.MAGENTA}RESPONSE:{Style.RESET_ALL}")
                print(f"  Status: {match['response'].get('status_code', 'N/A')}")
                if match['response'].get('headers'):
                    print("  Headers:")
                    for header, value in match['response']['headers'].items():
                        print(f"    {header}: {highlight_match(value, query)}")
                if match['response'].get('body'):
                    print("  Body:")
                    print(f"    {highlight_match(match['response']['body'], query)}")
            
            print(f"\n{Fore.CYAN}To replay this request:{Style.RESET_ALL}")
            print(f"  python repl.py --collection <collection> --request-id {match['request_id']}")
            
            # Add separator between matches
            if i < len(matches):
                print("\n" + "-" * 80)
    else:
        print(f"{Fore.YELLOW}No matches found for '{query}'{Style.RESET_ALL}")
    
    return matches

def find_result_files(collection_name: str = None, folder_path: str = None) -> List[str]:
    """
    Find all potential result files containing HTTP requests and responses.
    
    Args:
        collection_name (str, optional): Name of the collection to search in
        folder_path (str, optional): Path within the collection to search in
        
    Returns:
        List[str]: List of file paths
    """
    # Get base directory (where the script is located)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define logs directory
    logs_dir = os.path.join(base_dir, "logs")
    
    # Find all JSON files that might contain results
    result_files = []
    
    if collection_name:
        # Search in specific collection
        collection_dir = os.path.join(logs_dir, collection_name)
        if os.path.exists(collection_dir):
            if folder_path:
                # Search in specific folder within collection
                folder_dir = os.path.join(collection_dir, folder_path.replace('/', os.sep))
                if os.path.exists(folder_dir):
                    # Look for JSON files in the specific folder
                    result_files.extend(glob.glob(os.path.join(folder_dir, "*.json")))
            else:
                # Search in all folders within collection
                for root, _, files in os.walk(collection_dir):
                    for file in files:
                        if file.endswith(".json"):
                            result_files.append(os.path.join(root, file))
    else:
        # Search in all collections
        if os.path.exists(logs_dir):
            for collection_dir in os.listdir(logs_dir):
                collection_path = os.path.join(logs_dir, collection_dir)
                if os.path.isdir(collection_path):
                    for root, _, files in os.walk(collection_path):
                        for file in files:
                            if file.endswith(".json"):
                                result_files.append(os.path.join(root, file))
    
    # Also look for JSON files in the results directory
    results_dir = os.path.join(base_dir, "results")
    if os.path.exists(results_dir):
        result_files.extend(glob.glob(os.path.join(results_dir, "*.json")))
    
    # Remove duplicates
    return list(set(result_files))

def get_available_collections() -> List[str]:
    """
    Get a list of available collections in the logs directory.
    
    Returns:
        List[str]: List of collection names
    """
    # Get base directory (where the script is located)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define logs directory
    logs_dir = os.path.join(base_dir, "logs")
    
    if not os.path.exists(logs_dir):
        return []
    
    collections = []
    for item in os.listdir(logs_dir):
        item_path = os.path.join(logs_dir, item)
        if os.path.isdir(item_path):
            collections.append(item)
    
    return sorted(collections)

def get_available_folders(collection_name: str) -> List[str]:
    """
    Get a list of available folders in a collection.
    
    Args:
        collection_name (str): Name of the collection
        
    Returns:
        List[str]: List of folder paths
    """
    # Get base directory (where the script is located)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define collection directory
    collection_dir = os.path.join(base_dir, "logs", collection_name)
    
    if not os.path.exists(collection_dir):
        return []
    
    folders = []
    for root, dirs, _ in os.walk(collection_dir):
        rel_path = os.path.relpath(root, collection_dir)
        if rel_path != '.':
            folders.append(rel_path)
    
    return sorted(folders)

def search_result_file(file_path: str, query: str) -> List[Dict]:
    """
    Search a result file for requests/responses matching the query.
    
    Args:
        file_path (str): Path to the result file
        query (str): The search query
        
    Returns:
        List[Dict]: List of matching request/response pairs
    """
    matches = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                # Try to parse the file as JSON
                data = json.load(f)
                
                # Check if it's a collection result file
                if isinstance(data, dict) and 'requests' in data:
                    # Process collection result format
                    for request in data['requests']:
                        if is_match(request, query):
                            match = {
                                'file': os.path.basename(file_path),
                                'full_path': file_path,
                                'request_id': request.get('id', 'unknown'),
                                'method': request.get('method', 'GET'),
                                'url': request.get('url', ''),
                                'headers': request.get('headers', {}),
                                'body': request.get('body', ''),
                                'response': request.get('response', {})
                            }
                            matches.append(match)
                elif isinstance(data, list):
                    # Process list of requests format
                    for request in data:
                        if isinstance(request, dict) and is_match(request, query):
                            match = {
                                'file': os.path.basename(file_path),
                                'full_path': file_path,
                                'request_id': request.get('id', 'unknown'),
                                'method': request.get('method', 'GET'),
                                'url': request.get('url', ''),
                                'headers': request.get('headers', {}),
                                'body': request.get('body', ''),
                                'response': request.get('response', {})
                            }
                            matches.append(match)
            except json.JSONDecodeError:
                # Not a valid JSON file, try line-by-line parsing for log files
                logger.debug(f"Not a valid JSON file: {file_path}")
    except Exception as e:
        logger.debug(f"Error searching file {file_path}: {e}")
    
    return matches

def is_match(request: Dict[str, Any], query: str) -> bool:
    """
    Check if a request matches the search query.
    
    Args:
        request (Dict[str, Any]): The request data
        query (str): The search query
        
    Returns:
        bool: True if the request matches the query, False otherwise
    """
    # Check if query is a request ID
    if 'id' in request and query.lower() in str(request['id']).lower():
        return True
    
    # Check URL
    if 'url' in request and query.lower() in str(request['url']).lower():
        return True
    
    # Check method
    if 'method' in request and query.lower() in str(request['method']).lower():
        return True
    
    # Check headers
    if 'headers' in request and isinstance(request['headers'], dict):
        for header, value in request['headers'].items():
            if query.lower() in str(header).lower() or query.lower() in str(value).lower():
                return True
    
    # Check body
    if 'body' in request and query.lower() in str(request['body']).lower():
        return True
    
    # Check response
    if 'response' in request and isinstance(request['response'], dict):
        response = request['response']
        
        # Check status code
        if 'status_code' in response and query.lower() in str(response['status_code']).lower():
            return True
        
        # Check response headers
        if 'headers' in response and isinstance(response['headers'], dict):
            for header, value in response['headers'].items():
                if query.lower() in str(header).lower() or query.lower() in str(value).lower():
                    return True
        
        # Check response body
        if 'body' in response and query.lower() in str(response['body']).lower():
            return True
    
    return False

def highlight_match(text: str, query: str) -> str:
    """
    Highlight parts of the text that match the query.
    
    Args:
        text (str): The text to highlight
        query (str): The search query
        
    Returns:
        str: Text with matching parts highlighted
    """
    if not text or not query:
        return str(text)
    
    # Convert to string if not already
    text_str = str(text)
    query_lower = query.lower()
    
    # Simple case-insensitive replacement
    result = text_str
    i = result.lower().find(query_lower)
    
    # If no match or empty query, return original text
    if i < 0 or not query:
        return text_str
    
    # Replace all occurrences
    while i >= 0:
        # Get the actual text (preserving case)
        actual_text = result[i:i+len(query)]
        result = result[:i] + f"{Fore.RED}{actual_text}{Style.RESET_ALL}" + result[i+len(query):]
        
        # Find next occurrence, accounting for the added color codes
        offset = i + len(actual_text) + len(Fore.RED) + len(Style.RESET_ALL)
        i = result.lower().find(query_lower, offset)
    
    return result
