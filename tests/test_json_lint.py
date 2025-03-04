#!/usr/bin/env python3
"""
JSON Lint Tests for Postman2Burp
--------------------------------
Tests to validate JSON files for syntax errors.
"""

import os
import unittest
import tempfile
import json
import glob
from pathlib import Path


def validate_json_file(file_path):
    """
    Validate a JSON file for syntax errors.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True, None
    except json.JSONDecodeError as e:
        return False, f"JSON syntax error in {os.path.basename(file_path)}: {str(e)}"
    except Exception as e:
        return False, f"Error reading {os.path.basename(file_path)}: {str(e)}"


def validate_directory(directory_path, pattern="*.json"):
    """
    Validate all JSON files in a directory.
    
    Args:
        directory_path (str): Path to the directory containing JSON files
        pattern (str): Glob pattern to match files
        
    Returns:
        list: List of tuples (file_path, is_valid, error_message)
    """
    results = []
    
    if not os.path.exists(directory_path):
        return [(None, False, f"Directory {directory_path} does not exist")]
    
    for file_path in glob.glob(os.path.join(directory_path, pattern)):
        is_valid, error_message = validate_json_file(file_path)
        results.append((file_path, is_valid, error_message))
    
    return results


class JSONLintTests(unittest.TestCase):
    """Test case for JSON linting functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test directories if they don't exist
        self.test_dirs = {
            'collections': Path('tests/collections'),
            'profiles': Path('tests/profiles'),
            'config': Path('tests/config')
        }
        
        for dir_path in self.test_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create a temporary valid JSON file for testing
        self.valid_json_path = tempfile.mktemp(suffix='.json')
        with open(self.valid_json_path, 'w', encoding='utf-8') as f:
            json.dump({"test": "valid"}, f)

    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary valid JSON file
        if os.path.exists(self.valid_json_path):
            os.remove(self.valid_json_path)

    def test_validate_json_file(self):
        """Test validation of individual JSON files."""
        # Test with valid JSON
        is_valid, error_message = validate_json_file(self.valid_json_path)
        self.assertTrue(is_valid)
        self.assertIsNone(error_message)
        
        # Test with malformed collection
        malformed_collection = self.test_dirs['collections'] / 'malformed.collection.json'
        if malformed_collection.exists():
            is_valid, error_message = validate_json_file(str(malformed_collection))
            self.assertFalse(is_valid)
            self.assertIsNotNone(error_message)
            self.assertIn("JSON syntax error", error_message)
        
        # Test with malformed profile
        malformed_profile = self.test_dirs['profiles'] / 'malformed.profile.json'
        if malformed_profile.exists():
            is_valid, error_message = validate_json_file(str(malformed_profile))
            self.assertFalse(is_valid)
            self.assertIsNotNone(error_message)
            self.assertIn("JSON syntax error", error_message)
        
        # Test with malformed config
        malformed_config = self.test_dirs['config'] / 'malformed.config.json'
        if malformed_config.exists():
            is_valid, error_message = validate_json_file(str(malformed_config))
            self.assertFalse(is_valid)
            self.assertIsNotNone(error_message)
            self.assertIn("JSON syntax error", error_message)
        
        # Test with non-existent file
        non_existent_file = "non_existent_file.json"
        is_valid, error_message = validate_json_file(non_existent_file)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_message)
        self.assertIn("Error reading", error_message)

    def test_validate_directory(self):
        """Test validation of directories containing JSON files."""
        # Test with valid directory
        temp_dir = tempfile.mkdtemp()
        valid_file_path = os.path.join(temp_dir, "valid.json")
        with open(valid_file_path, 'w', encoding='utf-8') as f:
            json.dump({"test": "valid"}, f)
        
        results = validate_directory(temp_dir)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0][1])  # is_valid
        
        # Test with non-existent directory
        results = validate_directory("non_existent_directory")
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][1])  # is_valid
        self.assertIn("Directory", results[0][2])  # error_message
        
        # Test with collections directory
        if self.test_dirs['collections'].exists():
            results = validate_directory(str(self.test_dirs['collections']))
            self.assertGreater(len(results), 0)
            
            # Check if we have at least one invalid file
            has_invalid = any(not is_valid for _, is_valid, _ in results)
            if has_invalid:
                self.assertTrue(has_invalid)
        
        # Clean up
        os.remove(valid_file_path)
        os.rmdir(temp_dir)


if __name__ == "__main__":
    unittest.main() 