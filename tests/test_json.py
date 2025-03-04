#!/usr/bin/env python3
"""
Postman2Burp JSON Validation Tests
---------------------------------
Tests to verify that malformed JSON files are properly detected and handled.
"""

import os
import sys
import json
import unittest
from pathlib import Path

# Add parent directory to path to import from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class JSONValidationTests(unittest.TestCase):
    """Tests for validating JSON integrity in config, profile, and collection files."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test directories if they don't exist
        self.collections_dir = Path("collections")
        self.profiles_dir = Path("profiles")
        self.config_dir = Path("config")
        
        for directory in [self.collections_dir, self.profiles_dir, self.config_dir]:
            if not directory.exists():
                directory.mkdir(parents=True)
        
        # Create test files with valid JSON
        self.valid_collection_path = self.collections_dir / "valid_collection.json"
        self.valid_profile_path = self.profiles_dir / "valid_profile.json"
        self.valid_config_path = self.config_dir / "valid_config.json"
        
        # Create test files with malformed JSON
        self.malformed_collection_path = self.collections_dir / "malformed_collection.json"
        self.malformed_profile_path = self.profiles_dir / "malformed_profile.json"
        self.malformed_config_path = self.config_dir / "malformed_config.json"
        
        # Write valid JSON to files
        with open(self.valid_collection_path, 'w') as f:
            f.write('{"info": {"name": "Valid Collection"}, "item": []}')
        
        with open(self.valid_profile_path, 'w') as f:
            f.write('{"variables": {"base_url": "https://example.com"}}')
        
        with open(self.valid_config_path, 'w') as f:
            f.write('{"proxy_host": "localhost", "proxy_port": 8080}')
        
        # Write malformed JSON to files
        with open(self.malformed_collection_path, 'w') as f:
            f.write('{"info": {"name": "Malformed Collection", "item": []}')  # Missing closing brace
        
        with open(self.malformed_profile_path, 'w') as f:
            f.write('{"variables": {"base_url": "https://example.com"')  # Missing closing braces
        
        with open(self.malformed_config_path, 'w') as f:
            f.write('{"proxy_host": "localhost", "proxy_port": 8080,}')  # Extra comma
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up test files
        for file_path in [
            self.valid_collection_path, self.valid_profile_path, self.valid_config_path,
            self.malformed_collection_path, self.malformed_profile_path, self.malformed_config_path
        ]:
            if file_path.exists():
                file_path.unlink()
    
    def test_validate_json_file(self):
        """Test the JSON validation function with valid and malformed files."""
        # Define a function to validate JSON files
        def validate_json_file(file_path):
            """Validate a JSON file."""
            try:
                with open(file_path, 'r') as f:
                    json.load(f)
                return True
            except json.JSONDecodeError:
                return False
        
        # Test with valid files
        self.assertTrue(validate_json_file(self.valid_collection_path), 
                        f"Failed to validate valid collection: {self.valid_collection_path}")
        self.assertTrue(validate_json_file(self.valid_profile_path), 
                        f"Failed to validate valid profile: {self.valid_profile_path}")
        self.assertTrue(validate_json_file(self.valid_config_path), 
                        f"Failed to validate valid config: {self.valid_config_path}")
        
        # Test with malformed files
        self.assertFalse(validate_json_file(self.malformed_collection_path), 
                         f"Failed to detect malformed collection: {self.malformed_collection_path}")
        self.assertFalse(validate_json_file(self.malformed_profile_path), 
                         f"Failed to detect malformed profile: {self.malformed_profile_path}")
        self.assertFalse(validate_json_file(self.malformed_config_path), 
                         f"Failed to detect malformed config: {self.malformed_config_path}")
    
    def test_collection_schema_validation(self):
        """Test validation of Postman collection schema."""
        # Create a collection with valid structure but missing required fields
        invalid_schema_path = self.collections_dir / "invalid_schema.json"
        with open(invalid_schema_path, 'w') as f:
            f.write('{"item": []}')  # Missing "info" field
        
        # Define a function to validate collection schema
        def validate_collection_schema(file_path):
            """Validate a Postman collection schema."""
            try:
                with open(file_path, 'r') as f:
                    collection = json.load(f)
                
                # Check for required fields
                if "info" not in collection:
                    return False
                if "item" not in collection:
                    return False
                
                return True
            except Exception:
                return False
        
        # Test with valid and invalid schemas
        self.assertTrue(validate_collection_schema(self.valid_collection_path), 
                        f"Failed to validate valid collection schema: {self.valid_collection_path}")
        self.assertFalse(validate_collection_schema(invalid_schema_path), 
                         f"Failed to detect invalid collection schema: {invalid_schema_path}")
        
        # Clean up
        if invalid_schema_path.exists():
            invalid_schema_path.unlink()
    
    def test_profile_schema_validation(self):
        """Test validation of profile schema."""
        # Create a profile with valid structure but missing required fields
        invalid_schema_path = self.profiles_dir / "invalid_schema.json"
        with open(invalid_schema_path, 'w') as f:
            f.write('{"not_variables": {}}')  # Missing "variables" field
        
        # Define a function to validate profile schema
        def validate_profile_schema(file_path):
            """Validate a profile schema."""
            try:
                with open(file_path, 'r') as f:
                    profile = json.load(f)
                
                # Check for required fields
                if "variables" not in profile:
                    return False
                
                return True
            except Exception:
                return False
        
        # Test with valid and invalid schemas
        self.assertTrue(validate_profile_schema(self.valid_profile_path), 
                        f"Failed to validate valid profile schema: {self.valid_profile_path}")
        self.assertFalse(validate_profile_schema(invalid_schema_path), 
                         f"Failed to detect invalid profile schema: {invalid_schema_path}")
        
        # Clean up
        if invalid_schema_path.exists():
            invalid_schema_path.unlink()
    
    def test_config_schema_validation(self):
        """Test validation of config schema."""
        # Create a config with valid structure but invalid field types
        invalid_schema_path = self.config_dir / "invalid_schema.json"
        with open(invalid_schema_path, 'w') as f:
            f.write('{"proxy_host": "localhost", "proxy_port": "not_a_number"}')  # port should be a number
        
        # Define a function to validate config schema
        def validate_config_schema(file_path):
            """Validate a config schema."""
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                # Check field types
                if "proxy_port" in config and not isinstance(config["proxy_port"], int):
                    return False
                
                return True
            except Exception:
                return False
        
        # Test with valid and invalid schemas
        self.assertTrue(validate_config_schema(self.valid_config_path), 
                        f"Failed to validate valid config schema: {self.valid_config_path}")
        self.assertFalse(validate_config_schema(invalid_schema_path), 
                         f"Failed to detect invalid config schema: {invalid_schema_path}")
        
        # Clean up
        if invalid_schema_path.exists():
            invalid_schema_path.unlink()


if __name__ == "__main__":
    unittest.main() 