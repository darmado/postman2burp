# Postman2Burp Test Suite

This directory contains tests for the Postman2Burp tool. The tests are designed to verify that the environment is properly set up and that the core functionality works as expected.

## Test Structure

The test suite is organized into the following files:

- `test_environment.py`: Tests to verify the environment is properly set up
- `test_core_functions.py`: Comprehensive tests for individual functions in the main script
- `test_json_validation.py`: Tests to verify that malformed JSON files are properly detected and handled
- `test_schema.py`: Tests to validate Postman collections against the official schema
- `test_json_lint.py`: Simple JSON lint tests to detect syntax errors in JSON files
- `test_verify_proxy_with_request.py`: Specific tests for the proxy verification functionality

## Running the Tests

To run all tests:

```bash
python -m unittest discover tests
```

Or use the provided test runner:

```bash
python run_tests.py
```

To run a specific test file:

```bash
python -m unittest tests/test_environment.py
```

Or with the test runner:

```bash
python run_tests.py --type environment
python run_tests.py --type core_functions
python run_tests.py --type json
python run_tests.py --type schema
python run_tests.py --type lint
python run_tests.py --type proxy
```

To run a specific test case:

```bash
python -m unittest tests.test_environment.EnvironmentTests.test_python_version
```

## Test Coverage

The tests cover the following aspects of Postman2Burp:

### Environment Tests

- Python version check
- Required packages check
- Directory structure check
- Config file creation
- Proxy connection check (skipped by default)
- Postman collection validation

### Core Functions Tests

- JSON validation functions (`validate_json_file`)
- Configuration management (`load_config`, `save_config`)
- Proxy management (`check_proxy_connection`, `detect_running_proxy`, `verify_proxy_with_request`)
- Variable extraction and management (`extract_variables_from_text`, `extract_variables_from_collection`, `generate_variables_template`)
- Path resolution (`resolve_collection_path`)
- PostmanToBurp class methods:
  - Collection and profile loading
  - Variable replacement
  - Request extraction and preparation
  - Request sending and processing

### JSON Validation Tests

- Detection of malformed JSON files (syntax errors)
- Validation of Postman collection schema
- Validation of profile schema
- Validation of config schema
- Type checking for configuration values

### Schema Validation Tests

- Validation against the official Postman Collection v2.1.0 schema
- Detection of schema violations in collections
- Structural validation of collections
- Handling of malformed JSON files
- Schema directory management

### JSON Lint Tests

- Simple syntax validation of JSON files
- Detection of malformed JSON with clear error messages
- Validation of files in collections, profiles, and config directories
- Reporting of specific JSON syntax errors

### Proxy Verification Tests

- Testing successful proxy connections
- Testing failed proxy connections
- Testing exception handling in proxy verification
- Ensuring robust error handling for network issues

## Adding New Tests

To add new tests:

1. Create a new test file in the `tests` directory
2. Import the necessary modules
3. Create a test class that inherits from `unittest.TestCase`
4. Add test methods that start with `test_`
5. Run the tests to verify they work

Example:

```python
import unittest

class NewFeatureTests(unittest.TestCase):
    def test_new_feature(self):
        # Test code here
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
```

## CI Integration

These tests are designed to be run in a CI environment. The `test_proxy_connection` test is skipped by default because it requires a running proxy, which may not be available in CI environments.

To run the tests in CI, add the following to your GitHub Actions workflow:

```yaml
- name: Test with pytest
  run: |
    python -m unittest discover tests
``` 