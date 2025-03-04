#!/usr/bin/env python3
"""
Test Schema Validation for Postman2Burp
---------------------------------------
This module tests the schema validation functionality for Postman collections.
"""

import os
import json
import unittest
import tempfile
import shutil
import jsonschema
from pathlib import Path


def ensure_schema_directory():
    """
    Ensure the schema directory exists and contains the Postman collection schema.
    
    Returns:
        str: Path to the schema directory
    """
    schema_dir = Path("schemas")
    if not schema_dir.exists():
        schema_dir.mkdir(parents=True)
        print(f"Created schema directory: {schema_dir}")
    
    schema_file = schema_dir / "collection.2.1.0.json"
    if not schema_file.exists():
        print(f"Warning: Schema file not found at {schema_file}")
    
    return str(schema_dir)


def load_schema(schema_path=None):
    """
    Load the Postman collection schema from the specified path or the default location.
    
    Args:
        schema_path (str, optional): Path to the schema file. If None, uses the default schema.
        
    Returns:
        dict: The loaded schema as a dictionary
    """
    if schema_path is None:
        schema_dir = ensure_schema_directory()
        schema_path = os.path.join(schema_dir, "collection.2.1.0.json")
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load schema from {schema_path}: {str(e)}")


def validate_collection_structure(collection_path):
    """
    Validate the basic structure of a Postman collection.
    
    Args:
        collection_path (str): Path to the collection file
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        with open(collection_path, 'r', encoding='utf-8') as f:
            collection = json.load(f)
        
        # Check for required fields
        if 'info' not in collection:
            return False, "Collection missing 'info' field"
        
        if 'item' not in collection:
            return False, "Collection missing 'item' field"
        
        if 'name' not in collection['info']:
            return False, "Collection info missing 'name' field"
        
        if 'schema' not in collection['info']:
            return False, "Collection info missing 'schema' field"
        
        return True, None
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in collection file: {str(e)}"
    except Exception as e:
        return False, f"Error validating collection structure: {str(e)}"


def validate_collection(collection_path, schema_path=None):
    """
    Validate a Postman collection against the schema.
    
    Args:
        collection_path (str): Path to the collection file
        schema_path (str, optional): Path to the schema file. If None, uses the default schema.
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # First validate the basic structure
        is_valid, error_message = validate_collection_structure(collection_path)
        if not is_valid:
            return is_valid, error_message
        
        # Load the collection
        with open(collection_path, 'r', encoding='utf-8') as f:
            collection = json.load(f)
        
        # Load the schema
        schema = load_schema(schema_path)
        
        # Validate against the schema
        jsonschema.validate(collection, schema)
        
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        return False, f"Schema validation error: {str(e)}"
    except Exception as e:
        return False, f"Error validating collection: {str(e)}"


class SchemaValidationTests(unittest.TestCase):
    """Test case for schema validation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test directories if they don't exist
        self.test_dirs = {
            'collections': Path('tests/collections'),
            'schemas': Path('schemas')
        }
        
        for dir_path in self.test_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Define paths to test files
        self.valid_collection = str(self.test_dirs['collections'] / 'postman_collection.json')
        self.malformed_collection = str(self.test_dirs['collections'] / 'malformed.collection.json')
        self.schema_file = str(self.test_dirs['schemas'] / 'collection.2.1.0.json')
        
        # Create a temporary valid collection for testing
        self.temp_collection_path = tempfile.mktemp(suffix='.json')
        with open(self.temp_collection_path, 'w', encoding='utf-8') as f:
            json.dump({
                "info": {
                    "name": "Test Collection",
                    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
                },
                "item": []
            }, f)

    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary collection file
        if os.path.exists(self.temp_collection_path):
            os.remove(self.temp_collection_path)

    def test_load_schema(self):
        """Test loading the schema."""
        # Test loading the schema from the default location
        schema = load_schema()
        self.assertIsNotNone(schema)
        self.assertIn('$schema', schema)
        self.assertIn('properties', schema)
        
        # Test loading the schema from a specific location
        if os.path.exists(self.schema_file):
            schema = load_schema(self.schema_file)
            self.assertIsNotNone(schema)
            self.assertIn('$schema', schema)
            self.assertIn('properties', schema)

    def test_validate_collection_structure(self):
        """Test validating the structure of a collection."""
        # Test with a valid collection
        if os.path.exists(self.valid_collection):
            is_valid, error_message = validate_collection_structure(self.valid_collection)
            self.assertTrue(is_valid, f"Valid collection should pass structure validation: {error_message}")
        
        # Test with a minimal valid collection
        is_valid, error_message = validate_collection_structure(self.temp_collection_path)
        self.assertTrue(is_valid, f"Minimal valid collection should pass structure validation: {error_message}")
        
        # Test with a malformed collection
        if os.path.exists(self.malformed_collection):
            is_valid, error_message = validate_collection_structure(self.malformed_collection)
            self.assertFalse(is_valid, "Malformed collection should fail structure validation")

    def test_validate_collection(self):
        """Test validating a collection against the schema."""
        # Test with a valid collection
        if os.path.exists(self.valid_collection) and os.path.exists(self.schema_file):
            is_valid, error_message = validate_collection(self.valid_collection, self.schema_file)
            self.assertTrue(is_valid, f"Valid collection should pass schema validation: {error_message}")
        
        # Test with a malformed collection
        if os.path.exists(self.malformed_collection) and os.path.exists(self.schema_file):
            is_valid, error_message = validate_collection(self.malformed_collection, self.schema_file)
            self.assertFalse(is_valid, "Malformed collection should fail schema validation")

    def test_ensure_schema_directory(self):
        """Test ensuring the schema directory exists."""
        schema_dir = ensure_schema_directory()
        self.assertTrue(os.path.exists(schema_dir), "Schema directory should exist")
        self.assertTrue(os.path.isdir(schema_dir), "Schema directory should be a directory")


if __name__ == "__main__":
    unittest.main() 