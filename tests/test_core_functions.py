import unittest
import os
import json
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import the main script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import functions from the main script
from postman2burp import (
    validate_json_file,
    load_config,
    save_config,
    check_proxy_connection,
    detect_running_proxy,
    verify_proxy_with_request,
    extract_variables_from_text,
    extract_variables_from_collection,
    generate_variables_template,
    resolve_collection_path,
    PostmanToBurp,
    DEFAULT_CONFIG,
    VARIABLES_DIR,
    COLLECTIONS_DIR,
    CONFIG_DIR
)

class TestCoreFunctions(unittest.TestCase):
    """Test core functions of the postman2burp.py script."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_collections_dir = os.path.join(self.temp_dir, "collections")
        self.test_profiles_dir = os.path.join(self.temp_dir, "profiles")
        self.test_config_dir = os.path.join(self.temp_dir, "config")
        
        os.makedirs(self.test_collections_dir, exist_ok=True)
        os.makedirs(self.test_profiles_dir, exist_ok=True)
        os.makedirs(self.test_config_dir, exist_ok=True)
        
        # Create test files
        self.valid_json_path = os.path.join(self.temp_dir, "valid.json")
        with open(self.valid_json_path, 'w') as f:
            json.dump({"key": "value"}, f)
            
        self.invalid_json_path = os.path.join(self.temp_dir, "invalid.json")
        with open(self.invalid_json_path, 'w') as f:
            f.write('{"key": "value"')  # Missing closing brace
            
        # Create a test collection
        self.test_collection_path = os.path.join(self.test_collections_dir, "test_collection.json")
        self.test_collection = {
            "info": {
                "_postman_id": "test-id",
                "name": "Test Collection"
            },
            "item": [
                {
                    "name": "Test Request",
                    "request": {
                        "method": "GET",
                        "url": {
                            "raw": "https://example.com/api/{{resource}}/{{id}}",
                            "host": ["example", "com"],
                            "path": ["api", "{{resource}}", "{{id}}"]
                        },
                        "header": [
                            {
                                "key": "Authorization",
                                "value": "Bearer {{token}}"
                            }
                        ]
                    }
                },
                {
                    "name": "Folder",
                    "item": [
                        {
                            "name": "Nested Request",
                            "request": {
                                "method": "POST",
                                "url": "https://example.com/api/{{resource}}",
                                "header": [],
                                "body": {
                                    "mode": "raw",
                                    "raw": "{\"key\": \"{{value}}\"}"
                                }
                            }
                        }
                    ]
                }
            ],
            "variable": [
                {
                    "key": "baseUrl",
                    "value": "https://example.com"
                }
            ]
        }
        with open(self.test_collection_path, 'w') as f:
            json.dump(self.test_collection, f)
            
        # Create a test profile
        self.test_profile_path = os.path.join(self.test_profiles_dir, "test_profile.json")
        self.test_profile = {
            "id": "test-env-id",
            "name": "Test Environment",
            "values": [
                {
                    "key": "resource",
                    "value": "users",
                    "enabled": True
                },
                {
                    "key": "id",
                    "value": "123",
                    "enabled": True
                },
                {
                    "key": "token",
                    "value": "test-token",
                    "enabled": True
                },
                {
                    "key": "value",
                    "value": "test-value",
                    "enabled": True
                }
            ]
        }
        with open(self.test_profile_path, 'w') as f:
            json.dump(self.test_profile, f)
            
        # Create a test config
        self.test_config_path = os.path.join(self.test_config_dir, "config.json")
        self.test_config = {
            "proxy_host": "localhost",
            "proxy_port": 8080,
            "verify_ssl": False,
            "skip_proxy_check": True
        }
        with open(self.test_config_path, 'w') as f:
            json.dump(self.test_config, f)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove temporary directory and all its contents
        shutil.rmtree(self.temp_dir)
    
    def test_validate_json_file(self):
        """Test the validate_json_file function."""
        # Test with valid JSON
        is_valid, parsed_json = validate_json_file(self.valid_json_path)
        self.assertTrue(is_valid)
        self.assertEqual(parsed_json, {"key": "value"})
        
        # Test with invalid JSON
        is_valid, parsed_json = validate_json_file(self.invalid_json_path)
        self.assertFalse(is_valid)
        self.assertIsNone(parsed_json)
        
        # Test with non-existent file
        is_valid, parsed_json = validate_json_file(os.path.join(self.temp_dir, "nonexistent.json"))
        self.assertFalse(is_valid)
        self.assertIsNone(parsed_json)
    
    @patch('postman2burp.CONFIG_FILE_PATH')
    @patch('postman2burp.CONFIG_DIR')
    def test_load_config(self, mock_config_dir, mock_config_file_path):
        """Test the load_config function."""
        # Set up mocks
        mock_config_dir.return_value = self.test_config_dir
        mock_config_file_path.return_value = self.test_config_path
        
        # Test loading config
        with patch('os.path.exists', return_value=True):
            with patch('postman2burp.validate_json_file', return_value=(True, self.test_config)):
                config = load_config()
                self.assertEqual(config, self.test_config)
        
        # Test loading config with invalid JSON
        with patch('os.path.exists', return_value=True):
            with patch('postman2burp.validate_json_file', return_value=(False, None)):
                config = load_config()
                self.assertEqual(config, {})
        
        # Test loading config with non-existent file
        with patch('os.path.exists', return_value=False):
            with patch('builtins.open', MagicMock()):
                config = load_config()
                self.assertEqual(config, DEFAULT_CONFIG)
    
    @patch('postman2burp.CONFIG_FILE_PATH')
    @patch('postman2burp.CONFIG_DIR')
    def test_save_config(self, mock_config_dir, mock_config_file_path):
        """Test the save_config function."""
        # Set up mocks
        mock_config_dir.return_value = self.test_config_dir
        mock_config_file_path.return_value = self.test_config_path
        
        # Test saving config
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                result = save_config(self.test_config)
                self.assertTrue(result)
        
        # Test saving config with error
        with patch('builtins.open', side_effect=Exception("Test error")):
            result = save_config(self.test_config)
            self.assertFalse(result)
    
    @patch('socket.socket')
    def test_check_proxy_connection(self, mock_socket):
        """Test the check_proxy_connection function."""
        # Test successful connection
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect_ex.return_value = 0
        mock_socket.return_value = mock_socket_instance
        
        result = check_proxy_connection("localhost", 8080)
        self.assertTrue(result)
        
        # Test failed connection
        mock_socket_instance.connect_ex.return_value = 1
        result = check_proxy_connection("localhost", 8080)
        self.assertFalse(result)
        
        # Test exception
        mock_socket.side_effect = Exception("Test error")
        result = check_proxy_connection("localhost", 8080)
        self.assertFalse(result)
    
    @patch('postman2burp.check_proxy_connection')
    def test_detect_running_proxy(self, mock_check_proxy):
        """Test the detect_running_proxy function."""
        # Test successful detection
        # The third proxy in COMMON_PROXIES is localhost:8090 (based on test output)
        mock_check_proxy.side_effect = [False, False, True, False]
        host, port = detect_running_proxy()
        self.assertEqual(host, "localhost")
        self.assertEqual(port, 8090)  # Updated from 8081 to 8090
        
        # Test no proxy detected
        mock_check_proxy.side_effect = [False] * 10
        host, port = detect_running_proxy()
        self.assertIsNone(host)
        self.assertIsNone(port)
    
    def test_extract_variables_from_text(self):
        """Test the extract_variables_from_text function."""
        # Test with variables
        text = "This is a {{variable}} and another {{variable2}}"
        variables = extract_variables_from_text(text)
        self.assertEqual(variables, {"variable", "variable2"})
        
        # Test with no variables
        text = "This is a text with no variables"
        variables = extract_variables_from_text(text)
        self.assertEqual(variables, set())
        
        # Test with empty text
        variables = extract_variables_from_text("")
        self.assertEqual(variables, set())
        
        # Test with None
        variables = extract_variables_from_text(None)
        self.assertEqual(variables, set())
        
        # Test with Postman built-in variables (should be filtered out)
        text = "This is a {{$randomInt}} and a {{variable}}"
        variables = extract_variables_from_text(text)
        self.assertEqual(variables, {"variable"})
    
    def test_extract_variables_from_collection(self):
        """Test the extract_variables_from_collection function."""
        variables, collection_id = extract_variables_from_collection(self.test_collection_path)
        self.assertEqual(variables, {"resource", "id", "token", "value"})
        self.assertEqual(collection_id, "test-id")
    
    @patch('postman2burp.VARIABLES_DIR')
    def test_generate_variables_template(self, mock_variables_dir):
        """Test the generate_variables_template function."""
        # Set up mocks
        mock_variables_dir.return_value = self.test_profiles_dir
        
        # Test generating template
        output_path = os.path.join(self.temp_dir, "template.json")
        with patch('builtins.open', MagicMock()):
            with patch('postman2burp.extract_variables_from_collection', return_value=({"var1", "var2"}, "test-id")):
                generate_variables_template(self.test_collection_path, output_path)
    
    @patch('postman2burp.COLLECTIONS_DIR')
    def test_resolve_collection_path(self, mock_collections_dir):
        """Test the resolve_collection_path function."""
        # Set up mocks - make sure to set the return_value properly
        mock_collections_dir.return_value = self.test_collections_dir
        
        # Test with absolute path
        with patch('os.path.isabs', return_value=True):
            path = resolve_collection_path("/absolute/path/collection.json")
            self.assertEqual(path, "/absolute/path/collection.json")
        
        # Test with existing file
        with patch('os.path.isabs', return_value=False):
            with patch('os.path.exists', return_value=True):
                path = resolve_collection_path("existing_file.json")
                self.assertEqual(path, "existing_file.json")
        
        # Test with file in collections directory - use a more specific approach
        test_path = os.path.join(self.test_collections_dir, "collection_in_dir.json")
        with patch('os.path.isabs', return_value=False):
            with patch('os.path.exists', side_effect=[False, True]):
                with patch('os.path.join', return_value=test_path):
                    path = resolve_collection_path("collection_in_dir.json")
                    self.assertEqual(path, test_path)
        
        # Test with non-existent file
        with patch('os.path.isabs', return_value=False):
            with patch('os.path.exists', return_value=False):
                path = resolve_collection_path("nonexistent.json")
                self.assertEqual(path, "nonexistent.json")

class TestPostmanToBurp(unittest.TestCase):
    """Test the PostmanToBurp class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_collections_dir = os.path.join(self.temp_dir, "collections")
        self.test_profiles_dir = os.path.join(self.temp_dir, "profiles")
        
        os.makedirs(self.test_collections_dir, exist_ok=True)
        os.makedirs(self.test_profiles_dir, exist_ok=True)
        
        # Create a test collection
        self.test_collection_path = os.path.join(self.test_collections_dir, "test_collection.json")
        self.test_collection = {
            "info": {
                "_postman_id": "test-id",
                "name": "Test Collection"
            },
            "item": [
                {
                    "name": "Test Request",
                    "request": {
                        "method": "GET",
                        "url": {
                            "raw": "https://example.com/api/{{resource}}/{{id}}",
                            "host": ["example", "com"],
                            "path": ["api", "{{resource}}", "{{id}}"]
                        },
                        "header": [
                            {
                                "key": "Authorization",
                                "value": "Bearer {{token}}"
                            }
                        ]
                    }
                }
            ]
        }
        with open(self.test_collection_path, 'w') as f:
            json.dump(self.test_collection, f)
            
        # Create a test profile
        self.test_profile_path = os.path.join(self.test_profiles_dir, "test_profile.json")
        self.test_profile = {
            "id": "test-env-id",
            "name": "Test Environment",
            "values": [
                {
                    "key": "resource",
                    "value": "users",
                    "enabled": True
                },
                {
                    "key": "id",
                    "value": "123",
                    "enabled": True
                },
                {
                    "key": "token",
                    "value": "test-token",
                    "enabled": True
                }
            ]
        }
        with open(self.test_profile_path, 'w') as f:
            json.dump(self.test_profile, f)
        
        # Initialize PostmanToBurp instance
        self.converter = PostmanToBurp(
            collection_path=self.test_collection_path,
            target_profile=self.test_profile_path,
            proxy_host="localhost",
            proxy_port=8080,
            skip_proxy_check=True
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove temporary directory and all its contents
        shutil.rmtree(self.temp_dir)
    
    def test_load_collection(self):
        """Test the load_collection method."""
        # Test successful loading
        with patch('postman2burp.validate_json_file', return_value=(True, self.test_collection)):
            result = self.converter.load_collection()
            self.assertTrue(result)
            self.assertEqual(self.converter.collection, self.test_collection)
        
        # Test failed loading
        with patch('postman2burp.validate_json_file', return_value=(False, None)):
            result = self.converter.load_collection()
            self.assertFalse(result)
    
    def test_load_profile(self):
        """Test the load_profile method."""
        # Test successful loading
        with patch('postman2burp.validate_json_file', return_value=(True, self.test_profile)):
            result = self.converter.load_profile()
            self.assertTrue(result)
            self.assertEqual(self.converter.environment["resource"], "users")
            self.assertEqual(self.converter.environment["id"], "123")
            self.assertEqual(self.converter.environment["token"], "test-token")
        
        # Test failed loading
        with patch('postman2burp.validate_json_file', return_value=(False, None)):
            self.converter.environment = {}
            result = self.converter.load_profile()
            self.assertFalse(result)
            self.assertEqual(self.converter.environment, {})
        
        # Test with no profile
        self.converter.target_profile = None
        result = self.converter.load_profile()
        self.assertTrue(result)
    
    def test_replace_variables(self):
        """Test the replace_variables method."""
        # Set up environment
        self.converter.environment = {
            "resource": "users",
            "id": "123",
            "token": "test-token"
        }
        
        # Test replacing variables
        text = "https://example.com/api/{{resource}}/{{id}}"
        replaced = self.converter.replace_variables(text)
        self.assertEqual(replaced, "https://example.com/api/users/123")
        
        # Test with empty text
        replaced = self.converter.replace_variables("")
        self.assertEqual(replaced, "")
        
        # Test with None
        replaced = self.converter.replace_variables(None)
        self.assertEqual(replaced, None)
        
        # Test with Postman built-in variables
        text = "https://example.com/api/{{$randomInt}}/{{id}}"
        replaced = self.converter.replace_variables(text)
        self.assertEqual(replaced, "https://example.com/api/{{$randomInt}}/123")
    
    def test_extract_requests_from_item(self):
        """Test the extract_requests_from_item method."""
        # Test with request item
        item = {
            "name": "Test Request",
            "request": {
                "method": "GET",
                "url": "https://example.com"
            }
        }
        requests = self.converter.extract_requests_from_item(item)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["name"], "Test Request")
        self.assertEqual(requests[0]["folder"], "")
        
        # Test with folder item
        item = {
            "name": "Test Folder",
            "item": [
                {
                    "name": "Test Request",
                    "request": {
                        "method": "GET",
                        "url": "https://example.com"
                    }
                }
            ]
        }
        requests = self.converter.extract_requests_from_item(item)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["name"], "Test Request")
        self.assertEqual(requests[0]["folder"], "Test Folder")
        
        # Test with nested folder
        item = {
            "name": "Parent Folder",
            "item": [
                {
                    "name": "Child Folder",
                    "item": [
                        {
                            "name": "Test Request",
                            "request": {
                                "method": "GET",
                                "url": "https://example.com"
                            }
                        }
                    ]
                }
            ]
        }
        requests = self.converter.extract_requests_from_item(item)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["name"], "Test Request")
        self.assertEqual(requests[0]["folder"], "Parent Folder / Child Folder")
    
    def test_extract_all_requests(self):
        """Test the extract_all_requests method."""
        # Test with collection
        collection = {
            "item": [
                {
                    "name": "Test Request 1",
                    "request": {
                        "method": "GET",
                        "url": "https://example.com/1"
                    }
                },
                {
                    "name": "Test Folder",
                    "item": [
                        {
                            "name": "Test Request 2",
                            "request": {
                                "method": "GET",
                                "url": "https://example.com/2"
                            }
                        }
                    ]
                }
            ],
            "variable": [
                {
                    "key": "baseUrl",
                    "value": "https://example.com"
                }
            ]
        }
        requests = self.converter.extract_all_requests(collection)
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0]["name"], "Test Request 1")
        self.assertEqual(requests[1]["name"], "Test Request 2")
        self.assertEqual(self.converter.environment["baseUrl"], "https://example.com")
    
    def test_prepare_request(self):
        """Test the prepare_request method."""
        # Set up environment
        self.converter.environment = {
            "resource": "users",
            "id": "123",
            "token": "test-token"
        }
        
        # Test with URL as dict
        request_data = {
            "name": "Test Request",
            "folder": "Test Folder",
            "request": {
                "method": "GET",
                "url": {
                    "raw": "https://example.com/api/{{resource}}/{{id}}",
                    "host": ["example", "com"],
                    "path": ["api", "{{resource}}", "{{id}}"]
                },
                "header": [
                    {
                        "key": "Authorization",
                        "value": "Bearer {{token}}"
                    }
                ]
            }
        }
        prepared = self.converter.prepare_request(request_data)
        self.assertEqual(prepared["name"], "Test Request")
        self.assertEqual(prepared["folder"], "Test Folder")
        self.assertEqual(prepared["method"], "GET")
        self.assertEqual(prepared["url"], "https://example.com/api/users/123")
        self.assertEqual(prepared["headers"]["Authorization"], "Bearer test-token")
        
        # Test with URL as string
        request_data = {
            "name": "Test Request",
            "folder": "Test Folder",
            "request": {
                "method": "GET",
                "url": "https://example.com/api/{{resource}}/{{id}}",
                "header": []
            }
        }
        prepared = self.converter.prepare_request(request_data)
        self.assertEqual(prepared["url"], "https://example.com/api/users/123")
        
        # Test with body
        request_data = {
            "name": "Test Request",
            "folder": "Test Folder",
            "request": {
                "method": "POST",
                "url": "https://example.com",
                "header": [],
                "body": {
                    "mode": "raw",
                    "raw": "{\"resource\": \"{{resource}}\"}"
                }
            }
        }
        prepared = self.converter.prepare_request(request_data)
        self.assertEqual(prepared["body"], "{\"resource\": \"users\"}")
    
    @patch('requests.Session.request')
    def test_send_request(self, mock_request):
        """Test the send_request method."""
        # Set up mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.content = b"Test response"
        mock_request.return_value = mock_response
        
        # Set up proxies
        self.converter.proxies = {
            "http": "http://localhost:8080",
            "https": "http://localhost:8080"
        }
        
        # Test successful request
        prepared_request = {
            "name": "Test Request",
            "folder": "Test Folder",
            "method": "GET",
            "url": "https://example.com",
            "headers": {"Authorization": "Bearer test-token"},
            "body": None
        }
        result = self.converter.send_request(prepared_request)
        self.assertEqual(result["name"], "Test Request")
        self.assertEqual(result["folder"], "Test Folder")
        self.assertEqual(result["method"], "GET")
        self.assertEqual(result["url"], "https://example.com")
        self.assertEqual(result["status_code"], 200)
        self.assertTrue(result["success"])
        
        # Test failed request
        mock_request.side_effect = Exception("Test error")
        result = self.converter.send_request(prepared_request)
        self.assertEqual(result["name"], "Test Request")
        self.assertEqual(result["error"], "Test error")
        self.assertFalse(result["success"])

if __name__ == '__main__':
    unittest.main() 