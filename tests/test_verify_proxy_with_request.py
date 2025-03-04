#!/usr/bin/env python3
"""
Test for verify_proxy_with_request function
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path to import from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the function to test
import postman2burp

class TestVerifyProxyWithRequest(unittest.TestCase):
    """Test the verify_proxy_with_request function."""
    
    def test_verify_proxy_with_request_success(self):
        """Test successful proxy verification."""
        # Mock the requests.get function to return a successful response
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # Call the function
            result = postman2burp.verify_proxy_with_request("localhost", 8080)
            
            # Verify the result
            self.assertTrue(result)
            
            # Verify that requests.get was called with the expected arguments
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            self.assertEqual(kwargs['proxies']['http'], "http://localhost:8080")
            self.assertEqual(kwargs['proxies']['https'], "http://localhost:8080")
    
    def test_verify_proxy_with_request_failure(self):
        """Test failed proxy verification."""
        # Mock the requests.get function to return a failed response
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            
            # Call the function
            result = postman2burp.verify_proxy_with_request("localhost", 8080)
            
            # Verify the result
            self.assertFalse(result)
    
    def test_verify_proxy_with_request_exception(self):
        """Test exception handling in proxy verification."""
        # Mock the requests.get function to raise an exception
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Test error")
            
            # Call the function - this should not raise an exception
            result = postman2burp.verify_proxy_with_request("localhost", 8080)
            
            # Verify the result
            self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()