#!/usr/bin/env python3
"""
Postman2Burp - Automated API Endpoint Scanner

This tool reads a Postman collection JSON file and sends all the requests
through Burp Suite proxy. This allows for automated scanning of API endpoints
defined in a Postman collection during penetration testing.

Usage:
    Basic Usage:
        python postman2burp.py --collection <collection.json>
    
    Environment Variables:
        python postman2burp.py --collection <collection.json> --target-profile <environment.json>
    
    Proxy Settings:
        python postman2burp.py --collection <collection.json> --proxy-host <host> --proxy-port <port>
    
    Log Options:
        python postman2burp.py --collection <collection.json> --log --verbose
    
    Configuration:
        python postman2burp.py --collection <collection.json> --save-config
        
    Extract Variables:
        python postman2burp.py --collection <collection.json> --extract-keys [output_file.json]

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
from typing import Dict, List, Optional, Any, Tuple, Set
import requests
import time
import datetime
import uuid

# Disable SSL warnings when using proxy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Default configuration
DEFAULT_CONFIG = {
    "proxy_host": "localhost",
    "proxy_port": 8080,
    "verify_ssl": False,
    "skip_proxy_check": False
}

# Common proxy configurations to check
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
    # Fiddler defaultclear
    {"host": "localhost", "port": 8888},
    {"host": "127.0.0.1", "port": 8888},
]

# Path to config file
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.json")

# Path to variables templates directory
VARIABLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")

# Path to collections directory
COLLECTIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "collections")

def validate_json_file(file_path: str) -> Tuple[bool, Optional[Dict]]:
    """
    Validate a JSON file to ensure it's properly formatted.
    Returns a tuple of (is_valid, parsed_json).
    If the file is invalid, parsed_json will be None.
    """
    try:
        with open(file_path, 'r') as f:
            file_content = f.read()
            # Try to parse the JSON
            parsed_json = json.loads(file_content)
            return True, parsed_json
    except json.JSONDecodeError as e:
        logger.warning(f"JSON validation failed for {os.path.basename(file_path)}: {e}")
        return False, None
    except Exception as e:
        logger.warning(f"Error reading file {os.path.basename(file_path)}: {e}")
        return False, None

def load_config() -> Dict:
    """
    Load configuration from config.json file if it exists,
    otherwise return default configuration.
    If the config file exists but is malformed, return an empty dictionary
    to ensure we rely only on command-line arguments.
    """
    config = DEFAULT_CONFIG.copy()
    
    try:
        # Create config directory if it doesn't exist
        if not os.path.exists(CONFIG_DIR):
            try:
                os.makedirs(CONFIG_DIR)
                logger.debug(f"Created config directory at {CONFIG_DIR}")
            except Exception as e:
                logger.warning(f"Could not create config directory: {e}")
        
        if os.path.exists(CONFIG_FILE_PATH):
            # Validate the JSON file before loading
            is_valid, parsed_config = validate_json_file(CONFIG_FILE_PATH)
            
            if is_valid and parsed_config:
                config.update(parsed_config)
                # Get just the directory name and filename instead of full path
                config_dir = os.path.basename(os.path.dirname(CONFIG_FILE_PATH))
                config_file = os.path.basename(CONFIG_FILE_PATH)
                logger.info(f"Loaded configuration from {config_dir}/{config_file}")
            else:
                logger.warning(f"Config file {os.path.basename(CONFIG_FILE_PATH)} is malformed, using default settings")
                # Return empty dictionary to ensure we rely only on command-line arguments
                return {}
        else:
            logger.info(f"No config file found at {os.path.basename(CONFIG_FILE_PATH)}, using default settings")
            # Auto-generate config file with default settings
            try:
                with open(CONFIG_FILE_PATH, 'w') as f:
                    json.dump(DEFAULT_CONFIG, f, indent=4)
                logger.info(f"Generated default configuration file: {os.path.basename(CONFIG_FILE_PATH)}")
            except Exception as e:
                logger.warning(f"Could not create default config file: {e}")
    except Exception as e:
        logger.warning(f"Error loading config file: {e}. Using default settings.")
        # Return empty dictionary to ensure we rely only on command-line arguments
        return {}
    
    return config

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

def detect_running_proxy() -> Tuple[Optional[str], Optional[int]]:
    """
    Auto-detect running proxy by checking common proxy configurations.
    Returns a tuple of (host, port) if a proxy is found, otherwise (None, None).
    """
    logger.info("Attempting to auto-detect running proxy...")
    
    for proxy in COMMON_PROXIES:
        host, port = proxy["host"], proxy["port"]
        if check_proxy_connection(host, port):
            logger.info(f"Detected running proxy at {host}:{port}")
            return host, port
    
    logger.warning("No running proxy detected on common ports")
    return None, None

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
        response = requests.get(
            test_url, 
            proxies=proxies, 
            verify=False, 
            timeout=5
        )
        
        if response.status_code == 200:
            logger.info(f"Proxy test request successful through {host}:{port}")
            return True
        else:
            logger.warning(f"Proxy test request failed with status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"Proxy test request failed: {str(e)}")
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

def extract_variables_from_collection(collection_path: str) -> Tuple[Set[str], Optional[str]]:
    """
    Extract all variables used in a Postman collection.
    Returns a tuple of (set of variable names, collection_id).
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
                if "value" in param and param.get("type") == "text":
                    variables.update(extract_variables_from_text(param["value"]))
    
    def process_headers(headers):
        if not headers:
            return
            
        for header in headers:
            if "key" in header:
                variables.update(extract_variables_from_text(header["key"]))
            if "value" in header:
                variables.update(extract_variables_from_text(header["value"]))
    
    def process_request(request):
        if "url" in request:
            process_url(request["url"])
        if "header" in request:
            process_headers(request["header"])
        if "body" in request:
            process_body(request["body"])
    
    def process_item(item):
        if "request" in item:
            process_request(item["request"])
        
        # Process any scripts that might contain variables
        if "event" in item:
            for event in item["event"]:
                if "script" in event and "exec" in event["script"]:
                    for line in event["script"]["exec"]:
                        variables.update(extract_variables_from_text(line))
        
        # Process nested items recursively
        if "item" in item:
            for sub_item in item["item"]:
                process_item(sub_item)
    
    # Process collection-level variables
    if "variable" in collection:
        for var in collection["variable"]:
            if "value" in var:
                variables.update(extract_variables_from_text(str(var["value"])))
    
    # Process all items
    if "item" in collection:
        for item in collection["item"]:
            process_item(item)
    
    # Process auth if present
    if "auth" in collection:
        auth = collection["auth"]
        if isinstance(auth, dict) and "bearer" in auth:
            for item in auth["bearer"]:
                if "value" in item:
                    variables.update(extract_variables_from_text(item["value"]))
    
    # Process pre-request and test scripts
    if "event" in collection:
        for event in collection["event"]:
            if "script" in event and "exec" in event["script"]:
                for line in event["script"]["exec"]:
                    variables.update(extract_variables_from_text(line))
    
    logger.info(f"Found {len(variables)} unique variables in collection")
    return variables, collection_id

def generate_variables_template(collection_path: str, output_path: str) -> None:
    """
    Extract variables from a collection and generate a Postman environment template file.
    The template will be saved in the profiles directory if output_path is not an absolute path.
    
    Args:
        collection_path: Path to the Postman collection JSON file
        output_path: Path to save the variables template file
    """
    # Extract variables from collection
    variables, collection_id = extract_variables_from_collection(collection_path)
    
    # Create profiles directory if it doesn't exist
    if not os.path.exists(VARIABLES_DIR):
        try:
            os.makedirs(VARIABLES_DIR)
            logger.debug(f"Created profiles directory at {VARIABLES_DIR}")
        except Exception as e:
            logger.warning(f"Could not create profiles directory: {e}")
    
    # If collection_id is provided and output_path is the default, use collection_id for filename
    if collection_id and output_path == "variables_template.json":
        output_path = os.path.join(VARIABLES_DIR, f"{collection_id}.json")
        logger.info(f"Using collection ID for filename: {os.path.basename(output_path)}")
    elif not os.path.isabs(output_path) and not output_path.startswith('./'):
        # If output_path is not an absolute path or doesn't start with ./, put it in profiles dir
        output_path = os.path.join(VARIABLES_DIR, output_path)
    
    template = {
        "id": f"auto-generated-{int(time.time())}",
        "name": "Auto-Generated Environment",
        "values": [],
        "_postman_variable_scope": "environment",
        "_postman_exported_at": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "_postman_exported_using": "Postman2Burp/Extract"
    }
    
    # If we have a collection ID, add it to the template
    if collection_id:
        template["_postman_collection_id"] = collection_id
    
    for var in sorted(variables):
        template["values"].append({
            "key": var,
            "value": "",
            "type": "default",
            "enabled": True
        })
    
    try:
        with open(output_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        # Print a more concise output with just the path and next command
        relative_path = os.path.relpath(output_path)
        profile_filename = os.path.basename(output_path)
        
        # Wrap filenames in single quotes if they contain spaces
        collection_name = f"'{os.path.basename(collection_path)}'" if ' ' in os.path.basename(collection_path) else os.path.basename(collection_path)
        profile_name = f"'{profile_filename}'" if ' ' in profile_filename else profile_filename
        
        print(f"\n[✓] Successfully extracted {len(variables)} variables to {relative_path}")
        print(f"\nNext command to run:")
        print(f"python3 postman2burp.py --collection {collection_name} --target-profile {profile_name}")
        
    except Exception as e:
        logger.error(f"Failed to save variables template: {e}")
        sys.exit(1)

def save_config(config: Dict) -> bool:
    """
    Save configuration to config.json file.
    
    Args:
        config: Configuration dictionary to save
        
    Returns:
        bool: True if the configuration was saved successfully, False otherwise
    """
    try:
        # Create config directory if it doesn't exist
        if not os.path.exists(CONFIG_DIR):
            try:
                os.makedirs(CONFIG_DIR)
                logger.debug(f"Created config directory at {CONFIG_DIR}")
            except Exception as e:
                logger.warning(f"Could not create config directory: {e}")
                return False
        
        with open(CONFIG_FILE_PATH, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Configuration saved to {os.path.basename(CONFIG_DIR)}/{os.path.basename(CONFIG_FILE_PATH)}")
        return True
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        return False

def resolve_collection_path(collection_path: str) -> str:
    """
    Resolve the collection path. If the path is not absolute and the file doesn't exist,
    check if it exists in the collections directory.
    
    Args:
        collection_path: Path to the collection file
        
    Returns:
        str: Resolved path to the collection file
    """
    # If the path is absolute or the file exists, return it as is
    if os.path.isabs(collection_path) or os.path.exists(collection_path):
        return collection_path
    
    # Check if the file exists in the collections directory
    collections_path = os.path.join(COLLECTIONS_DIR, os.path.basename(collection_path))
    if os.path.exists(collections_path):
        logger.debug(f"Found collection in collections directory: {os.path.basename(collections_path)}")
        return collections_path
    
    # Create collections directory if it doesn't exist
    if not os.path.exists(COLLECTIONS_DIR):
        try:
            os.makedirs(COLLECTIONS_DIR)
            logger.debug(f"Created collections directory at {COLLECTIONS_DIR}")
        except Exception as e:
            logger.warning(f"Could not create collections directory: {e}")
    
    # If the file doesn't exist in the collections directory, return the original path
    return collection_path

class PostmanToBurp:
    def __init__(self, collection_path: str, target_profile: str = None, proxy_host: str = None, proxy_port: int = None,
                 verify_ssl: bool = False, skip_proxy_check: bool = False, auto_detect_proxy: bool = True,
                 verbose: bool = False):
        """
        Initialize the PostmanToBurp converter.
        
        Args:
            collection_path: Path to the Postman collection JSON file
            target_profile: Path to the Postman environment JSON file
            proxy_host: Proxy host
            proxy_port: Proxy port
            verify_ssl: Whether to verify SSL certificates
            skip_proxy_check: Whether to skip proxy connection check
            auto_detect_proxy: Whether to auto-detect proxy settings
            verbose: Whether to enable verbose logging
        """
        self.collection_path = collection_path
        self.target_profile = target_profile
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.verify_ssl = verify_ssl
        self.skip_proxy_check = skip_proxy_check
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
        """
        Load the Postman collection from the specified file.
        Also sets up the log file path based on the collection ID.
        
        Returns:
            bool: True if the collection was loaded successfully, False otherwise
        """
        self.logger.info(f"Loading collection: {os.path.basename(self.collection_path)}")
        
        # Validate the collection file
        is_valid, json_data = validate_json_file(self.collection_path)
        if not is_valid:
            self.logger.error(f"Failed to load collection: {os.path.basename(self.collection_path)} - Malformed JSON")
            return False
            
        self.collection = json_data
        
        # Generate log file path based on collection ID
        collection_id = self.collection.get("info", {}).get("_postman_id", "unknown")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{collection_id}_{timestamp}.json"
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        self.log_path = os.path.join("logs", log_filename)
        self.logger.info(f"Log file will be saved to: {self.log_path}")
        return True
    
    def load_profile(self) -> bool:
        """
        Load the Postman environment variables from the specified file.
        If the path is not absolute, check in the profiles directory first.
        
        Returns:
            bool: True if the environment was loaded successfully, False otherwise
        """
        if not self.target_profile:
            return True
        
        # If the path is not absolute, check if it exists in the profiles directory
        target_path = self.target_profile
        if not os.path.isabs(target_path) and not os.path.exists(target_path):
            profiles_path = os.path.join(VARIABLES_DIR, os.path.basename(target_path))
            if os.path.exists(profiles_path):
                target_path = profiles_path
                self.logger.debug(f"Found profile in profiles directory: {os.path.basename(target_path)}")
            
        self.logger.info(f"Loading environment: {os.path.basename(target_path)}")
        
        # Validate the environment file
        is_valid, json_data = validate_json_file(target_path)
        if not is_valid:
            self.logger.warning(f"Failed to load environment: {os.path.basename(target_path)} - Malformed JSON")
            self.logger.warning("Continuing without environment variables")
            return False
            
        # Extract environment variables
        if "values" in json_data:
            for var in json_data["values"]:
                if "key" in var and "value" in var and var.get("enabled", True):
                    self.environment[var["key"]] = var["value"]
        
        self.logger.info(f"Resolved {len(self.environment)} environment variables")
        return True

    def replace_variables(self, text: str) -> str:
        """Replace Postman variables in the given text."""
        if not text:
            return text
            
        # First try environment variables, then collection variables
        for key, value in self.environment.items():
            if value is not None:
                text = text.replace(f"{{{{${key}}}}}", str(value))
                text = text.replace(f"{{{{{key}}}}}", str(value))
                
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
        
        # Extract URL
        url = ""
        if isinstance(request.get("url"), str):
            url = self.replace_variables(request.get("url", ""))
        elif isinstance(request.get("url"), dict):
            url_obj = request.get("url", {})
            
            # Build URL from components
            protocol = url_obj.get("protocol", "https")
            host = url_obj.get("host", [])
            if isinstance(host, list):
                host = ".".join(host)
            host = self.replace_variables(host)
            
            path = url_obj.get("path", [])
            if isinstance(path, list):
                path = "/".join(path)
            path = self.replace_variables(path)
            
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
            
            url = f"{protocol}://{host}/{path}{query_string}"
        
        # Fix double protocol issue (https://https://example.com)
        if url.startswith("http://http://") or url.startswith("https://https://"):
            url = url.replace("http://http://", "http://").replace("https://https://", "https://")
        
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
        
        # Set proxy
        proxies = None
        if self.proxy_host and self.proxy_port:
            proxy_url = f"http://{self.proxy_host}:{self.proxy_port}"
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            self.logger.debug(f"Using proxy: {proxy_url}")
        
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
            
            # Send request
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                proxies=proxies,
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
            
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            response_data.update({
                "error": str(e)
            })
        
        return response_data

    def process_collection(self) -> None:
        """Process the entire Postman collection and send requests through Burp."""
        # Load collection and environment
        self.load_collection()
        self.load_profile()
        
        # Extract all requests
        requests = self.extract_all_requests(self.collection)
        self.logger.info(f"Found {len(requests)} requests in the collection")
        
        # Process each request
        for i, request_data in enumerate(requests, 1):
            self.logger.info(f"Processing request {i}/{len(requests)}: {request_data['name']}")
            prepared_request = self.prepare_request(request_data)
            
            # Try the request with retries
            max_retries = 3
            retry_count = 0
            result = None
            
            while retry_count < max_retries:
                result = self.send_request(prepared_request)
                if result.get("success", False) or "error" not in result:
                    break
                
                retry_count += 1
                if retry_count < max_retries:
                    retry_delay = 2 ** retry_count  # Exponential backoff
                    self.logger.warning(f"Request failed: {result.get('error')}. Retrying in {retry_delay}s... (Attempt {retry_count+1}/{max_retries})")
                    time.sleep(retry_delay)
            
            if retry_count > 0 and not result.get("success", False):
                self.logger.error(f"Request failed after {retry_count} retries: {result.get('error')}")
            
            self.results["requests"].append(result)
            
        # Save results if output file is specified
        if self.log_path:
            self.save_results()
                
        # Print summary
        self.results["total"] = len(self.results["requests"])
        self.results["success"] = sum(1 for r in self.results["requests"] if r.get("success", False))
        self.results["failed"] = self.results["total"] - self.results["success"]
        self.logger.info(f"Summary: {self.results['success']}/{self.results['total']} requests successful")

    def run(self) -> Dict:
        """
        Run the conversion process.
        
        Returns:
            Dict: Results of the conversion
        """
        # Check proxy connection
        if not self.check_proxy():
            return self.results
            
        # Load collection
        if not self.load_collection():
            return self.results
            
        # Load environment variables
        self.load_profile()
        
        # Process collection
        self.process_collection()
        
        # Save results
        if self.log_path:
            self.save_results()
            
        return self.results

    def check_proxy(self) -> bool:
        """
        Check if the proxy is running and accessible.
        Auto-detect proxy only if no proxy settings are explicitly provided.
        
        Returns:
            bool: True if proxy is available, False otherwise
        """
        # Set up proxy URLs
        if self.proxy_host and self.proxy_port:
            # User explicitly provided proxy settings - use these and don't auto-detect
            self.proxies = {
                "http": f"http://{self.proxy_host}:{self.proxy_port}",
                "https": f"http://{self.proxy_host}:{self.proxy_port}"
            }
            self.logger.debug(f"Using user-specified proxy: {self.proxies}")
            
            # Skip proxy check if requested
            if self.skip_proxy_check:
                self.logger.info(f"Skipping proxy connection check (using {self.proxy_host}:{self.proxy_port})")
                return True
                
            # Check if the specified proxy is running
            if not check_proxy_connection(self.proxy_host, self.proxy_port):
                self.logger.error(f"Specified proxy not running at {self.proxy_host}:{self.proxy_port}")
                
                # Wrap filenames in single quotes to handle spaces
                collection_name = f"'{os.path.basename(self.collection_path)}'" if ' ' in os.path.basename(self.collection_path) else os.path.basename(self.collection_path)
                profile_name = f"'{os.path.basename(self.target_profile)}'" if self.target_profile and ' ' in os.path.basename(self.target_profile) else (os.path.basename(self.target_profile) if self.target_profile else 'profile.json')
                
                print("\nSuggestion:")
                print("  1. Start your proxy at the specified address or")
                print("  2. Run with --skip-proxy-check flag:")
                print(f"     python3 postman2burp.py --collection {collection_name} --target-profile {profile_name} --proxy {self.proxy_host}:{self.proxy_port} --skip-proxy-check")
                print("  3. Or specify a different proxy:")
                print(f"     python3 postman2burp.py --collection {collection_name} --target-profile {profile_name} --proxy host:port")
                return False
        else:
            # No proxy explicitly specified
            self.proxies = {}
            
            # Skip proxy check if requested
            if self.skip_proxy_check:
                self.logger.info("Skipping proxy connection check")
                return True
                
            # Auto-detect proxy if enabled and no proxy explicitly provided
            if self.auto_detect_proxy:
                self.logger.info("No proxy specified. Attempting to auto-detect running proxy...")
                detected_host, detected_port = detect_running_proxy()
                
                if detected_host and detected_port:
                    self.proxy_host = detected_host
                    self.proxy_port = detected_port
                    self.proxies = {
                        "http": f"http://{self.proxy_host}:{self.proxy_port}",
                        "https": f"http://{self.proxy_host}:{self.proxy_port}"
                    }
                    self.logger.info(f"Using auto-detected proxy: {self.proxy_host}:{self.proxy_port}")
                    return True
                else:
                    self.logger.error("No proxy detected on common ports")
                    
                    # Wrap filenames in single quotes to handle spaces
                    collection_name = f"'{os.path.basename(self.collection_path)}'" if ' ' in os.path.basename(self.collection_path) else os.path.basename(self.collection_path)
                    profile_name = f"'{os.path.basename(self.target_profile)}'" if self.target_profile and ' ' in os.path.basename(self.target_profile) else (os.path.basename(self.target_profile) if self.target_profile else 'profile.json')
                    
                    print("\nSuggestion:")
                    print("  1. Start your proxy (Burp Suite, ZAP, etc.) or")
                    print("  2. Run with --skip-proxy-check flag:")
                    print(f"     python3 postman2burp.py --collection {collection_name} --target-profile {profile_name} --skip-proxy-check")
                    print("  3. Or specify a proxy:")
                    print(f"     python3 postman2burp.py --collection {collection_name} --target-profile {profile_name} --proxy host:port")
                    print("  4. Save your preferred configuration:")
                    print(f"     python3 postman2burp.py --collection {collection_name} --proxy host:port --save-config")
                    return False
            else:
                self.logger.error("No proxy specified and auto-detection is disabled")
                return False
            
        # Verify proxy works by making a test request
        try:
            test_url = "https://httpbin.org/get"
            response = self.session.get(
                test_url,
                proxies=self.proxies,
                timeout=5
            )
            
            if response.status_code == 200:
                self.logger.info(f"Proxy test request successful through {self.proxy_host}:{self.proxy_port}")
                return True
            else:
                self.logger.warning(f"Proxy test request failed with status code {response.status_code}")
                
                # Wrap filenames in single quotes to handle spaces
                collection_name = f"'{os.path.basename(self.collection_path)}'" if ' ' in os.path.basename(self.collection_path) else os.path.basename(self.collection_path)
                profile_name = f"'{os.path.basename(self.target_profile)}'" if self.target_profile and ' ' in os.path.basename(self.target_profile) else (os.path.basename(self.target_profile) if self.target_profile else 'profile.json')
                
                print("\nSuggestion:")
                print("  1. Check if your proxy is configured correctly")
                print("  2. Run with --skip-proxy-check flag:")
                print(f"     python3 postman2burp.py --collection {collection_name} --target-profile {profile_name} --skip-proxy-check")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Proxy test request failed: {str(e)}")
            self.logger.warning("Continuing anyway, but requests might fail")
            return True  # Continue anyway to allow for internal proxies
            
    def save_results(self) -> None:
        """Save the results to a file."""
        if not self.log_path:
            self.logger.error("Log path not set")
            return
            
        self.logger.info(f"Saving results to {self.log_path}")
        
        try:
            # Extract collection ID from the loaded collection
            collection_id = self.collection.get("info", {}).get("_postman_id", "unknown")
            collection_name = self.collection.get("info", {}).get("name", "Postman Collection")
            
            # Convert results to Postman Collection format
            postman_collection = {
                "info": {
                    "name": f"Postman2Burp Results - {collection_name}",
                    "description": f"Results from running Postman collection {collection_id} through Burp Suite proxy",
                    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                    "_postman_id": str(uuid.uuid4()),
                    "version": "1.0.0"
                },
                "item": []
            }
            
            # Group requests by folder
            folders = {}
            for request in self.results.get("requests", []):
                folder_name = request.get("folder", "")
                if not folder_name:
                    folder_name = "Ungrouped Requests"
                
                if folder_name not in folders:
                    folders[folder_name] = []
                
                # Create Postman request format
                postman_request = {
                    "name": request.get("name", "Unnamed Request"),
                    "request": {
                        "method": request.get("method", "GET"),
                        "header": [],
                        "url": request.get("url", "")
                    },
                    "response": []
                }
                
                # Add headers
                for key, value in request.get("headers", {}).items():
                    postman_request["request"]["header"].append({
                        "key": key,
                        "value": value,
                        "type": "text"
                    })
                
                # Add body if present
                if "body" in request and request["body"]:
                    body_content = request["body"]
                    if isinstance(body_content, str):
                        postman_request["request"]["body"] = {
                            "mode": "raw",
                            "raw": body_content.strip()
                        }
                    elif isinstance(body_content, dict):
                        # Handle form data
                        postman_request["request"]["body"] = {
                            "mode": "urlencoded",
                            "urlencoded": []
                        }
                        for key, value in body_content.items():
                            postman_request["request"]["body"]["urlencoded"].append({
                                "key": key,
                                "value": value,
                                "type": "text"
                            })
                
                # Add response if available
                if "status_code" in request:
                    response = {
                        "name": f"Response {request.get('status_code', 'Unknown')}",
                        "originalRequest": postman_request["request"],
                        "status": str(request.get("status_code", "")),
                        "code": request.get("status_code", 0),
                        "header": [],
                        "_postman_previewlanguage": "json",
                        "cookie": [],
                        "responseTime": int(request.get("response_time", 0) * 1000) if request.get("response_time") else None,
                        "body": request.get("response_body", "")
                    }
                    
                    # Add response headers
                    for key, value in request.get("response_headers", {}).items():
                        response["header"].append({
                            "key": key,
                            "value": str(value),
                            "name": key,
                            "description": ""
                        })
                    
                    postman_request["response"] = [response]
                
                folders[folder_name].append(postman_request)
            
            # Add folders to collection
            for folder_name, requests in folders.items():
                folder = {
                    "name": folder_name,
                    "item": requests
                }
                postman_collection["item"].append(folder)
            
            # Add summary as a variable
            postman_collection["variable"] = [
                {
                    "key": "total_requests",
                    "value": str(self.results.get("total", 0))
                },
                {
                    "key": "successful_requests",
                    "value": str(self.results.get("success", 0))
                },
                {
                    "key": "failed_requests",
                    "value": str(self.results.get("failed", 0))
                }
            ]
            
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump(postman_collection, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Results saved to {self.log_path}")
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")

def main():
    """
    Main entry point for the script.
    """
    # Load configuration
    config = load_config()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Convert Postman collections to Burp Suite requests")
    parser.add_argument("--collection", required=True, help="Path to Postman collection JSON file")
    
    # Environment options
    env_group = parser.add_argument_group("Environment Options")
    env_group.add_argument("--target-profile", help="Path to Postman environment JSON file")
    env_group.add_argument("--extract-keys", nargs="?", const="print", metavar="OUTPUT_FILE",
                          help="Extract all variables from collection. If no file is specified, prints the list of keys. Otherwise, saves to template file.")
    
    # Proxy options
    proxy_group = parser.add_argument_group("Proxy Options")
    proxy_group.add_argument("--proxy", help="Proxy in host:port format")
    proxy_group.add_argument("--proxy-host", help="Proxy host")
    proxy_group.add_argument("--proxy-port", type=int, help="Proxy port")
    proxy_group.add_argument("--verify-ssl", action="store_true", help="Verify SSL certificates")
    proxy_group.add_argument("--skip-proxy-check", action="store_true", help="Skip proxy connection check")
    proxy_group.add_argument("--no-auto-detect", action="store_true", help="Disable auto-detection of proxy settings")
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument("--log", action="store_true", help="Enable logging (always enabled, included for backward compatibility)")
    output_group.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    output_group.add_argument("--save-config", action="store_true", help="Save current settings as default configuration")
    
    args = parser.parse_args()
    
    # Configure logging
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_date_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format=log_format, datefmt=log_date_format)
    logger = logging.getLogger(__name__)
    
    # Resolve collection path
    collection_path = resolve_collection_path(args.collection)
    
    # Extract variables from collection if requested
    if args.extract_keys is not None:
        variables, collection_id = extract_variables_from_collection(collection_path)
        
        if args.extract_keys == "print":
            # Print the list of keys
            print(f"\n[✓] Found {len(variables)} variables in collection {os.path.basename(collection_path)}:")
            for var in sorted(variables):
                print(f"  - {var}")
            print("\nTo create a template file with these variables:")
            print(f"python3 postman2burp.py --collection {os.path.basename(collection_path)} --extract-keys variables_template.json")
        else:
            # Generate template file
            generate_variables_template(collection_path, args.extract_keys)
        return
    
    # Parse proxy settings - prioritize command line arguments over config
    # If config is empty (due to malformed config file), use DEFAULT_CONFIG values only if no command line args
    proxy_host = args.proxy_host or config.get("proxy_host") or DEFAULT_CONFIG["proxy_host"]
    proxy_port = args.proxy_port or config.get("proxy_port") or DEFAULT_CONFIG["proxy_port"]
    
    if args.proxy:
        try:
            proxy_parts = args.proxy.split(":")
            proxy_host = proxy_parts[0]
            proxy_port = int(proxy_parts[1])
        except (IndexError, ValueError):
            logger.error("Invalid proxy format. Use host:port")
            return
    
    # Create converter instance
    converter = PostmanToBurp(
        collection_path=collection_path,
        target_profile=args.target_profile,
        proxy_host=proxy_host,
        proxy_port=proxy_port,
        verify_ssl=args.verify_ssl or config.get("verify_ssl", DEFAULT_CONFIG["verify_ssl"]),
        skip_proxy_check=args.skip_proxy_check or config.get("skip_proxy_check", DEFAULT_CONFIG["skip_proxy_check"]),
        auto_detect_proxy=not args.no_auto_detect and config.get("auto_detect_proxy", True),
        verbose=args.verbose or config.get("verbose", False)
    )
    
    # Run the converter
    result = converter.run()
    if result["success"]:
        # Save configuration if requested
        if args.save_config:
            config_to_save = {
                "proxy_host": converter.proxy_host,
                "proxy_port": converter.proxy_port,
                "verify_ssl": args.verify_ssl,
                "skip_proxy_check": args.skip_proxy_check,
                "auto_detect_proxy": not args.no_auto_detect,
                "verbose": args.verbose
            }
            
            if save_config(config_to_save):
                logger.info("Configuration saved successfully")
            else:
                logger.error("Failed to save configuration")

if __name__ == "__main__":
    main() 