# Function Map

This page provides a comprehensive overview of all functions in the Postman2Burp tool, organized by category. This map helps developers understand the codebase structure and the role of each function.

## Core Functions

| Function | Description | Return Type |
|----------|-------------|-------------|
| `validate_json_file(file_path)` | Validates if a file contains valid JSON and returns the parsed content | `Tuple[bool, Optional[Dict]]` |
| `load_config()` | Loads configuration from the config file | `Dict` |
| `save_config(config)` | Saves configuration to the config file | `bool` |
| `resolve_collection_path(collection_path)` | Resolves the full path to a collection file | `str` |

## Proxy Management

| Function | Description | Return Type |
|----------|-------------|-------------|
| `check_proxy_connection(host, port)` | Checks if a proxy is running at the specified host and port using socket connection | `bool` |
| `detect_running_proxy()` | Auto-detects running proxy by checking common proxy configurations | `Tuple[Optional[str], Optional[int]]` |
| `verify_proxy_with_request(host, port)` | Verifies proxy by making a test HTTP request through it | `bool` |

## Variable Management

| Function | Description | Return Type |
|----------|-------------|-------------|
| `extract_variables_from_text(text)` | Extracts variables ({{variable}}) from text | `Set[str]` |
| `extract_variables_from_collection(collection_path)` | Extracts all variables from a Postman collection | `Tuple[Set[str], Optional[str]]` |
| `generate_variables_template(collection_path, output_path)` | Generates a template file with all variables from a collection | `None` |

## PostmanToBurp Class Methods

| Method | Description | Return Type |
|--------|-------------|-------------|
| `__init__(collection_path, ...)` | Initializes the PostmanToBurp object with configuration | `None` |
| `load_collection()` | Loads and validates the Postman collection | `bool` |
| `load_profile()` | Loads and validates the profile with variables | `bool` |
| `replace_variables(text)` | Replaces variables in text with values from the profile | `str` |
| `extract_requests_from_item(item, folder_name)` | Extracts requests from a collection item | `List[Dict]` |
| `extract_all_requests(collection)` | Extracts all requests from the collection | `List[Dict]` |
| `prepare_request(request_data)` | Prepares a request for sending (replaces variables, etc.) | `Dict` |
| `send_request(prepared_request)` | Sends a request through the proxy | `Dict` |
| `process_collection()` | Processes the entire collection | `None` |
| `run()` | Runs the entire process and returns results | `Dict` |
| `check_proxy()` | Checks if the proxy is running | `bool` |
| `save_results()` | Saves results to the output file | `None` |

## Helper Functions

| Function | Description | Return Type |
|----------|-------------|-------------|
| `process_url(url)` | Processes URL to extract variables (internal) | `Set[str]` |
| `process_body(body)` | Processes request body to extract variables (internal) | `Set[str]` |
| `process_headers(headers)` | Processes headers to extract variables (internal) | `Set[str]` |
| `process_request(request)` | Processes a request to extract variables (internal) | `Set[str]` |
| `process_item(item)` | Processes a collection item to extract variables (internal) | `Set[str]` |

## Main Function

| Function | Description | Return Type |
|----------|-------------|-------------|
| `main()` | Entry point for the command-line interface | `None` |

## Function Dependencies

The following diagram shows the main function dependencies:

```
main()
  ├── load_config()
  │     └── validate_json_file()
  ├── resolve_collection_path()
  ├── PostmanToBurp.run()
  │     ├── load_collection()
  │     │     └── validate_json_file()
  │     ├── load_profile()
  │     │     └── validate_json_file()
  │     ├── check_proxy()
  │     │     ├── check_proxy_connection()
  │     │     ├── detect_running_proxy()
  │     │     └── verify_proxy_with_request()
  │     ├── process_collection()
  │     │     ├── extract_all_requests()
  │     │     │     └── extract_requests_from_item()
  │     │     ├── prepare_request()
  │     │     │     └── replace_variables()
  │     │     └── send_request()
  │     └── save_results()
  └── save_config()
```

## Testing Functions

The test suite includes tests for all major functions to ensure they work correctly. See the [[Tests]] page for more information on the test suite.
