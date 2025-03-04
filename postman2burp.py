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
        python postman2burp.py --collection <collection.json> --environment <environment.json>
    
    Proxy Settings:
        python postman2burp.py --collection <collection.json> --proxy-host <host> --proxy-port <port>
    
    Output Options:
        python postman2burp.py --collection <collection.json> --output <results.json> --verbose
    
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
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# Path to variables templates directory
VARIABLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "variables")

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
    """
    config = DEFAULT_CONFIG.copy()
    
    try:
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

def generate_variables_template(variables: Set[str], output_path: str, collection_id: Optional[str] = None) -> None:
    """
    Generate a Postman environment template file with the extracted variables.
    If collection_id is provided and output_path is not specified, the file will be saved
    in the variables directory with the collection ID as the filename.
    """
    # Create variables directory if it doesn't exist
    if not os.path.exists(VARIABLES_DIR):
        try:
            os.makedirs(VARIABLES_DIR)
            logger.debug(f"Created variables directory at {VARIABLES_DIR}")
        except Exception as e:
            logger.warning(f"Could not create variables directory: {e}")
    
    # If collection_id is provided and output_path is the default, use collection_id for filename
    if collection_id and output_path == "variables_template.json":
        output_path = os.path.join(VARIABLES_DIR, f"{collection_id}.json")
        logger.info(f"Using collection ID for filename: {os.path.basename(output_path)}")
    elif not os.path.isabs(output_path) and not output_path.startswith('./'):
        # If output_path is not an absolute path or doesn't start with ./, put it in variables dir
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
        logger.info(f"Variables template saved to {output_path}")
        
        # Print a more detailed summary with the actual variable names
        print(f"\n[✓] Successfully extracted {len(variables)} variables to {output_path}")
        print("\n[Variables Found]")
        print("----------------")
        # Group variables in columns if there are many
        var_list = sorted(variables)
        if len(var_list) > 6:
            # Create columns for better readability
            col_width = max(len(var) for var in var_list) + 4  # Add padding
            cols = 3  # Number of columns
            rows = (len(var_list) + cols - 1) // cols  # Ceiling division
            
            for i in range(rows):
                row = []
                for j in range(cols):
                    idx = i + j * rows
                    if idx < len(var_list):
                        row.append(var_list[idx].ljust(col_width))
                    else:
                        row.append("")
                print("".join(row))
        else:
            # For a small number of variables, just list them one per line
            for var in var_list:
                print(f"- {var}")
        
        print("\n[✓] Edit this file to add your values, then use it with --environment")
    except Exception as e:
        logger.error(f"Failed to save variables template: {e}")
        sys.exit(1)

class PostmanToBurp:
    def __init__(
        self,
        collection_path: str,
        environment_path: Optional[str] = None,
        proxy_host: str = None,
        proxy_port: int = None,
        verify_ssl: bool = None,
        output_file: Optional[str] = None
    ):
        # Load config
        config = load_config()
        
        self.collection_path = collection_path
        self.environment_path = environment_path
        
        # Use provided values or fall back to config values
        self.proxy_host = proxy_host if proxy_host is not None else config["proxy_host"]
        self.proxy_port = proxy_port if proxy_port is not None else config["proxy_port"]
        self.verify_ssl = verify_ssl if verify_ssl is not None else config["verify_ssl"]
        
        self.output_file = output_file
        
        # Construct proxy URLs
        self.proxies = {
            "http": f"http://{self.proxy_host}:{self.proxy_port}",
            "https": f"http://{self.proxy_host}:{self.proxy_port}"
        }
        
        logger.debug(f"Using proxy settings - Host: {self.proxy_host}, Port: {self.proxy_port}")
        logger.debug(f"Proxy URLs: {self.proxies}")
        
        self.environment_variables = {}
        self.collection_variables = {}
        self.results = []

    def load_collection(self) -> Dict:
        """Load the Postman collection from JSON file."""
        try:
            # Validate the JSON file before loading
            is_valid, parsed_collection = validate_json_file(self.collection_path)
            
            if is_valid and parsed_collection:
                return parsed_collection
            else:
                logger.error(f"Collection file {os.path.basename(self.collection_path)} is malformed")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load collection: {e}")
            sys.exit(1)

    def load_environment(self) -> None:
        """Load the Postman environment variables if provided."""
        if not self.environment_path:
            return
        
        try:
            # Validate the JSON file before loading
            is_valid, parsed_env = validate_json_file(self.environment_path)
            
            if not is_valid or not parsed_env:
                logger.warning(f"Environment file {os.path.basename(self.environment_path)} is malformed, skipping environment variables")
                return
                
            # Handle different Postman environment formats
            if "values" in parsed_env:
                for var in parsed_env["values"]:
                    if "enabled" in var and not var["enabled"]:
                        continue
                    self.environment_variables[var["key"]] = var["value"]
            elif "environment" in parsed_env and "values" in parsed_env["environment"]:
                for var in parsed_env["environment"]["values"]:
                    if "enabled" in var and not var["enabled"]:
                        continue
                    self.environment_variables[var["key"]] = var["value"]
            
            logger.info(f"Loaded {len(self.environment_variables)} variables from environment file")
        except Exception as e:
            logger.warning(f"Failed to load environment: {e}. Continuing without environment variables.")

    def replace_variables(self, text: str) -> str:
        """Replace Postman variables in the given text."""
        if not text:
            return text
            
        # First try environment variables, then collection variables
        for key, value in self.environment_variables.items():
            if value is not None:
                text = text.replace(f"{{{{${key}}}}}", str(value))
                text = text.replace(f"{{{{{key}}}}}", str(value))
                
        for key, value in self.collection_variables.items():
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
                self.collection_variables[var["key"]] = var["value"]
                
        # Extract requests from items
        if "item" in collection:
            for item in collection["item"]:
                requests.extend(self.extract_requests_from_item(item))
                
        return requests

    def prepare_request(self, request_data: Dict) -> Dict:
        """Prepare a request for sending."""
        request = request_data["request"]
        prepared_request = {
            "name": request_data["name"],
            "folder": request_data["folder"],
            "method": request["method"],
            "url": "",
            "headers": {},
            "body": None
        }
        
        # Process URL
        if isinstance(request["url"], dict):
            if "raw" in request["url"]:
                prepared_request["url"] = self.replace_variables(request["url"]["raw"])
            else:
                # Construct URL from host, path, etc.
                host = ".".join(request["url"].get("host", []))
                path = "/".join(request["url"].get("path", []))
                protocol = request["url"].get("protocol", "https")
                prepared_request["url"] = f"{protocol}://{host}/{path}"
        else:
            prepared_request["url"] = self.replace_variables(request["url"])
            
        # Process headers
        if "header" in request:
            for header in request["header"]:
                if "disabled" in header and header["disabled"]:
                    continue
                prepared_request["headers"][header["key"]] = self.replace_variables(header["value"])
                
        # Process body
        if "body" in request:
            body = request["body"]
            if body.get("mode") == "raw":
                prepared_request["body"] = self.replace_variables(body.get("raw", ""))
            elif body.get("mode") == "urlencoded":
                form_data = {}
                for param in body.get("urlencoded", []):
                    if "disabled" in param and param["disabled"]:
                        continue
                    form_data[param["key"]] = self.replace_variables(param["value"])
                prepared_request["body"] = form_data
            elif body.get("mode") == "formdata":
                # For multipart/form-data, we'd need more complex handling
                # This is a simplified version
                form_data = {}
                for param in body.get("formdata", []):
                    if "disabled" in param and param["disabled"]:
                        continue
                    if param["type"] == "text":
                        form_data[param["key"]] = self.replace_variables(param["value"])
                prepared_request["body"] = form_data
                
        return prepared_request

    def send_request(self, prepared_request: Dict) -> Dict:
        """Send a request through the Burp proxy and return the result."""
        method = prepared_request["method"]
        url = prepared_request["url"]
        headers = prepared_request["headers"]
        body = prepared_request["body"]
        
        logger.info(f"Sending {method} request to {url}")
        logger.debug(f"Using proxy: {self.proxies}")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body if isinstance(body, (str, dict)) else None,
                json=body if not isinstance(body, (str, dict)) and body is not None else None,
                proxies=self.proxies,
                verify=self.verify_ssl,
                timeout=30
            )
            
            result = {
                "name": prepared_request["name"],
                "folder": prepared_request["folder"],
                "method": method,
                "url": url,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "response_size": len(response.content),
                "success": 200 <= response.status_code < 300
            }
            
            logger.info(f"Response: {response.status_code} ({result['response_time']:.2f}s)")
            return result
            
        except requests.exceptions.ProxyError as e:
            logger.error(f"Proxy error: {e}")
            return {
                "name": prepared_request["name"],
                "folder": prepared_request["folder"],
                "method": method,
                "url": url,
                "error": f"Proxy error: {str(e)}",
                "success": False
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return {
                "name": prepared_request["name"],
                "folder": prepared_request["folder"],
                "method": method,
                "url": url,
                "error": f"Connection error: {str(e)}",
                "success": False
            }
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {
                "name": prepared_request["name"],
                "folder": prepared_request["folder"],
                "method": method,
                "url": url,
                "error": str(e),
                "success": False
            }

    def process_collection(self) -> None:
        """Process the entire Postman collection and send requests through Burp."""
        # Load collection and environment
        collection = self.load_collection()
        self.load_environment()
        
        # Extract all requests
        requests = self.extract_all_requests(collection)
        logger.info(f"Found {len(requests)} requests in the collection")
        
        # Process each request
        for i, request_data in enumerate(requests, 1):
            logger.info(f"Processing request {i}/{len(requests)}: {request_data['name']}")
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
                    logger.warning(f"Request failed: {result.get('error')}. Retrying in {retry_delay}s... (Attempt {retry_count+1}/{max_retries})")
                    time.sleep(retry_delay)
            
            if retry_count > 0 and not result.get("success", False):
                logger.error(f"Request failed after {retry_count} retries: {result.get('error')}")
            
            self.results.append(result)
            
        # Save results if output file is specified
        if self.output_file:
            with open(self.output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
                
        # Print summary
        success_count = sum(1 for r in self.results if r.get("success", False))
        logger.info(f"Summary: {success_count}/{len(self.results)} requests successful")

def main():
    # Load config first
    config = load_config()
    
    parser = argparse.ArgumentParser(
        description="Postman2Burp - Send Postman collection requests through Burp Suite proxy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic scan:
    python postman2burp.py --collection api_collection.json
  
  With environment variables:
    python postman2burp.py --collection api_collection.json --environment variables.json
  
  Custom proxy settings:
    python postman2burp.py --collection api_collection.json --proxy localhost:8080
  
  Save results and configuration:
    python postman2burp.py --collection api_collection.json --output results.json --save-config
    
  Extract variables:
    python postman2burp.py --collection api_collection.json --extract-keys variables_template.json
"""
    )
    
    # Required arguments
    parser.add_argument("--collection", required=True, 
                      help="Path to Postman collection JSON file")
    
    # Environment options
    env_group = parser.add_argument_group('Environment Options')
    env_group.add_argument("--environment", 
                         help="Path to Postman environment JSON file")
    env_group.add_argument("--extract-keys", nargs='?', const="variables_template.json", metavar="OUTPUT_FILE",
                         help="Extract all variables from collection and save to template file (default: variables_template.json)")
    
    # Proxy options
    proxy_group = parser.add_argument_group('Proxy Options')
    proxy_group.add_argument("--proxy", default=None, 
                           help="Proxy in format host:port (e.g., localhost:8080)")
    proxy_group.add_argument("--proxy-host", default=None, 
                           help="Proxy hostname/IP (default: auto-detected)")
    proxy_group.add_argument("--proxy-port", type=int, default=None, 
                           help="Proxy port (default: auto-detected or from config.json)")
    proxy_group.add_argument("--verify-ssl", action="store_true", 
                           help="Verify SSL certificates")
    proxy_group.add_argument("--skip-proxy-check", action="store_true", 
                           help="Skip proxy connection check")
    proxy_group.add_argument("--no-auto-detect", action="store_true", 
                           help="Disable proxy auto-detection (use config values only)")
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument("--output", 
                            help="Save results to JSON file")
    output_group.add_argument("--verbose", action="store_true", 
                            help="Enable detailed logging")
    
    # Configuration options
    config_group = parser.add_argument_group('Configuration Options')
    config_group.add_argument("--save-config", action="store_true", 
                            help="Save current settings to config.json")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Handle extract-keys mode
    if args.extract_keys is not None:
        output_file = args.extract_keys if args.extract_keys != True else "variables_template.json"
        variables, collection_id = extract_variables_from_collection(args.collection)
        generate_variables_template(variables, output_file, collection_id)
        return
    
    # Extract host and port from the combined proxy argument if provided
    proxy_host = args.proxy_host
    proxy_port = args.proxy_port
    
    if args.proxy:
        # Parse the combined proxy argument (host:port)
        if ':' in args.proxy:
            host_parts = args.proxy.split(':')
            proxy_host = host_parts[0]
            try:
                proxy_port = int(host_parts[1])
                logger.info(f"Using proxy {proxy_host}:{proxy_port} from --proxy argument")
            except (IndexError, ValueError):
                logger.warning(f"Could not extract port from '{args.proxy}', using default port")
        else:
            # If no port specified, use the host as-is
            proxy_host = args.proxy
            logger.info(f"Using proxy host {proxy_host} from --proxy argument (with default port)")
    elif proxy_host and ':' in proxy_host and not proxy_host.startswith('http'):
        # For backward compatibility, also handle port in the proxy-host argument
        host_parts = proxy_host.split(':')
        proxy_host = host_parts[0]
        try:
            proxy_port = int(host_parts[1])
            logger.info(f"Using port {proxy_port} from proxy host string")
        except (IndexError, ValueError):
            logger.warning(f"Could not extract port from '{proxy_host}', using provided port {proxy_port}")
    
    # Check if proxy host was explicitly provided
    proxy_host_provided = args.proxy is not None or args.proxy_host is not None
    
    # Auto-detect proxy if not explicitly disabled and proxy host not provided
    if not args.no_auto_detect and not proxy_host_provided:
        detected_host, detected_port = detect_running_proxy()
        
        if detected_host and detected_port:
            proxy_host = detected_host
            logger.info(f"Using auto-detected proxy host: {proxy_host}")
            
            # Only use detected port if not explicitly provided
            if proxy_port is None:
                proxy_port = detected_port
                logger.info(f"Using auto-detected proxy port: {proxy_port}")
    
    # If proxy settings still weren't provided, use config values
    if proxy_host is None:
        proxy_host = config["proxy_host"]
        logger.debug(f"Using proxy host from config: {proxy_host}")
    
    if proxy_port is None:
        proxy_port = config["proxy_port"]
        logger.debug(f"Using proxy port from config: {proxy_port}")
    
    # Determine if we should skip the proxy check
    skip_proxy_check = args.skip_proxy_check or config.get("skip_proxy_check", False)
    
    # Skip proxy check if explicitly requested
    if skip_proxy_check:
        logger.info(f"Skipping proxy connection check (using {proxy_host}:{proxy_port})")
    else:
        # First check if proxy is running
        if not check_proxy_connection(proxy_host, proxy_port):
            # If not running and not explicitly provided, try to auto-detect
            if not proxy_host_provided and not args.no_auto_detect:
                logger.warning(f"No proxy detected at {proxy_host}:{proxy_port}, attempting to auto-detect...")
                detected_host, detected_port = detect_running_proxy()
                
                if detected_host and detected_port:
                    proxy_host = detected_host
                    proxy_port = detected_port
                    logger.info(f"Using auto-detected proxy: {proxy_host}:{proxy_port}")
                else:
                    # No proxy detected, show error and exit
                    logger.error(f"No proxy detected at {proxy_host}:{proxy_port} and auto-detection failed")
                    print("\n[!] PROXY CONNECTION ERROR [!]")
                    print(f"[!] No proxy detected at {proxy_host}:{proxy_port}")
                    print("[!] Please start one of the following proxy tools:")
                    print("    - Burp Suite (default: localhost:8080)")
                    print("    - OWASP ZAP (default: localhost:8090)")
                    print("    - Mitmproxy (default: localhost:8081)")
                    print("    - Charles Proxy (default: localhost:8888)")
                    print("    - Fiddler (default: localhost:8888)")
                    print("[!] Or specify a custom proxy with --proxy host:port")
                    print("[!] Exiting...")
                    sys.exit(1)
            else:
                # Proxy was explicitly provided but not running
                logger.error(f"Proxy not running at {proxy_host}:{proxy_port}")
                print("\n[!] PROXY CONNECTION ERROR [!]")
                print(f"[!] No proxy detected at {proxy_host}:{proxy_port}")
                print("[!] Please verify your proxy settings and ensure the proxy is running")
                print("[!] Exiting...")
                sys.exit(1)
        
        # Verify proxy works by making a test request
        if not verify_proxy_with_request(proxy_host, proxy_port):
            logger.warning("Proxy connection test failed, but will attempt to continue anyway")
            print("\n[!] PROXY WARNING [!]")
            print(f"[!] Proxy at {proxy_host}:{proxy_port} is running but test request failed")
            print("[!] This might indicate proxy configuration issues")
            print("[!] Continuing anyway, but requests might fail...")
    
    # Save config if requested
    if args.save_config:
        new_config = {
            "proxy_host": proxy_host,
            "proxy_port": proxy_port,
            "verify_ssl": args.verify_ssl,
            "skip_proxy_check": skip_proxy_check
        }
        
        try:
            with open(CONFIG_FILE_PATH, 'w') as f:
                json.dump(new_config, f, indent=4)
            logger.info(f"Configuration saved to {os.path.basename(CONFIG_FILE_PATH)}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    processor = PostmanToBurp(
        collection_path=args.collection,
        environment_path=args.environment,
        proxy_host=proxy_host,
        proxy_port=proxy_port,
        verify_ssl=args.verify_ssl,
        output_file=args.output
    )
    
    processor.process_collection()

if __name__ == "__main__":
    main() 