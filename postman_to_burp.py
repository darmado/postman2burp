#!/usr/bin/env python3
"""
Postman2Burp - Automated API Endpoint Scanner

This tool reads a Postman collection JSON file and sends all the requests
through Burp Suite proxy. This allows for automated scanning of API endpoints
defined in a Postman collection during penetration testing.

Usage:
    python postman2burp.py --collection <postman_collection.json> --environment <postman_environment.json> --proxy-host localhost --proxy-port 8080

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
from typing import Dict, List, Optional, Any
import requests

# Disable SSL warnings when using proxy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PostmanToBurp:
    def __init__(
        self,
        collection_path: str,
        environment_path: Optional[str] = None,
        proxy_host: str = "localhost",
        proxy_port: int = 8080,
        verify_ssl: bool = False,
        output_file: Optional[str] = None
    ):
        self.collection_path = collection_path
        self.environment_path = environment_path
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.verify_ssl = verify_ssl
        self.output_file = output_file
        self.proxies = {
            "http": f"http://{proxy_host}:{proxy_port}",
            "https": f"http://{proxy_host}:{proxy_port}"
        }
        self.environment_variables = {}
        self.collection_variables = {}
        self.results = []

    def load_collection(self) -> Dict:
        """Load the Postman collection from JSON file."""
        try:
            with open(self.collection_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load collection: {e}")
            sys.exit(1)

    def load_environment(self) -> None:
        """Load the Postman environment variables if provided."""
        if not self.environment_path:
            return
        
        try:
            with open(self.environment_path, 'r') as f:
                env_data = json.load(f)
                
                # Handle different Postman environment formats
                if "values" in env_data:
                    for var in env_data["values"]:
                        if "enabled" in var and not var["enabled"]:
                            continue
                        self.environment_variables[var["key"]] = var["value"]
                elif "environment" in env_data and "values" in env_data["environment"]:
                    for var in env_data["environment"]["values"]:
                        if "enabled" in var and not var["enabled"]:
                            continue
                        self.environment_variables[var["key"]] = var["value"]
        except Exception as e:
            logger.error(f"Failed to load environment: {e}")
            sys.exit(1)

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
            result = self.send_request(prepared_request)
            self.results.append(result)
            
        # Save results if output file is specified
        if self.output_file:
            with open(self.output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
                
        # Print summary
        success_count = sum(1 for r in self.results if r.get("success", False))
        logger.info(f"Summary: {success_count}/{len(self.results)} requests successful")

def main():
    parser = argparse.ArgumentParser(description="Send Postman collection requests through Burp Suite proxy")
    parser.add_argument("--collection", required=True, help="Path to Postman collection JSON file")
    parser.add_argument("--environment", help="Path to Postman environment JSON file")
    parser.add_argument("--proxy-host", default="localhost", help="Burp proxy host (default: localhost)")
    parser.add_argument("--proxy-port", type=int, default=8080, help="Burp proxy port (default: 8080)")
    parser.add_argument("--verify-ssl", action="store_true", help="Verify SSL certificates")
    parser.add_argument("--output", help="Path to save results JSON file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    processor = PostmanToBurp(
        collection_path=args.collection,
        environment_path=args.environment,
        proxy_host=args.proxy_host,
        proxy_port=args.proxy_port,
        verify_ssl=args.verify_ssl,
        output_file=args.output
    )
    
    processor.process_collection()

if __name__ == "__main__":
    main() 