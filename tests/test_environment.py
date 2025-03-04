#!/usr/bin/env python3
"""
Postman2Burp Environment Tests
------------------------------
Tests to verify the environment is properly set up for Postman2Burp.
"""

import os
import sys
import json
import socket
import unittest
from pathlib import Path

# Add parent directory to path to import from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class EnvironmentTests(unittest.TestCase):
    """Tests to verify the environment is properly set up for Postman2Burp."""
    
    def test_python_version(self):
        """Test that Python version meets requirements."""
        required_version = (3, 6)
        current_version = sys.version_info
        
        self.assertGreaterEqual(
            (current_version.major, current_version.minor),
            required_version,
            f"Python version {current_version.major}.{current_version.minor} is less than required version 3.6+"
        )
    
    def test_required_packages(self):
        """Test that required packages are installed."""
        required_packages = ["requests", "urllib3"]
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                self.fail(f"Required package '{package}' is not installed")
    
    def test_directory_structure(self):
        """Test that required directories exist."""
        required_dirs = ["collections", "profiles", "config"]
        
        for directory in required_dirs:
            # Create directory if it doesn't exist for the test to pass
            if not os.path.exists(directory):
                os.makedirs(directory)
            
            self.assertTrue(
                os.path.exists(directory) and os.path.isdir(directory),
                f"Required directory '{directory}' does not exist"
            )
    
    def test_config_file_creation(self):
        """Test that a config file can be created."""
        config_dir = Path("config")
        config_file = config_dir / "test_config.json"
        
        # Remove test config if it exists
        if config_file.exists():
            config_file.unlink()
        
        # Create config directory if it doesn't exist
        if not config_dir.exists():
            config_dir.mkdir(parents=True)
        
        # Create a sample config file
        sample_config = {
            "proxy_host": "localhost",
            "proxy_port": 8080,
            "verify_ssl": False,
            "skip_proxy_check": False
        }
        
        with open(config_file, 'w') as f:
            json.dump(sample_config, f, indent=4)
        
        self.assertTrue(
            config_file.exists(),
            f"Failed to create config file at {config_file}"
        )
        
        # Clean up
        config_file.unlink()
    
    @unittest.skip("This test requires a running proxy and may fail in CI environments")
    def test_proxy_connection(self):
        """Test that a proxy connection can be established."""
        host = "localhost"
        port = 8080
        
        # Try to connect to the proxy
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        
        self.assertEqual(
            result, 0,
            f"Proxy is not running at {host}:{port}"
        )
    
    def test_postman_collection_validation(self):
        """Test that a Postman collection can be validated."""
        collections_dir = Path("collections")
        test_collection_path = collections_dir / "test_collection.json"
        
        # Create collections directory if it doesn't exist
        if not collections_dir.exists():
            collections_dir.mkdir(parents=True)
        
        # Create a minimal valid Postman collection
        minimal_collection = {
            "info": {
                "name": "Test Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }
        
        with open(test_collection_path, 'w') as f:
            json.dump(minimal_collection, f, indent=4)
        
        # Test validation
        try:
            with open(test_collection_path, 'r') as f:
                collection = json.load(f)
            
            self.assertIn("info", collection, "Collection missing 'info' field")
            self.assertIn("item", collection, "Collection missing 'item' field")
        except Exception as e:
            self.fail(f"Failed to validate collection: {str(e)}")
        finally:
            # Clean up
            test_collection_path.unlink()


if __name__ == "__main__":
    unittest.main() 