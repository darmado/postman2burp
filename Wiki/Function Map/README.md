# Function Map

This page provides a comprehensive overview of all functions in the Repl tool, organized by category. This map helps developers understand the codebase structure and the role of each function.

## Core Functions

| Function | Description | Return Type |
|----------|-------------|-------------|
| `validate_json_file(file_path)` | Validates if a file contains valid JSON and returns the parsed content | `Tuple[bool, Optional[Dict]]` |
| `load_proxy(proxy_path)` | Loads proxy configuration from the specified file | `Dict` |
| `save_proxy(proxy)` | Saves proxy configuration to the default proxy file | `bool` |
| `resolve_collection_path(collection_path)` | Resolves the full path to a collection file | `str` |
| `select_collection_file()` | Interactive selection of collection files from the collections directory | `str` |
| `select_proxy_file()` | Interactive selection of proxy files from the proxies directory | `str` |

## Proxy Management

| Function | Description | Return Type |
|----------|-------------|-------------|
| `check_proxy_connection(host, port)` | Checks if a proxy is running at the specified host and port using socket connection | `bool` |
| `verify_proxy_with_request(host, port)` | Verifies proxy by making a test HTTP request through it | `bool` |

## Variable Management

| Function | Description | Return Type |
|----------|-------------|-------------|
| `extract_variables_from_text(text)` | Extracts variables ({{variable}}) from text | `Set[str]` |
| `extract_variables_from_collection(collection_path)` | Extracts all variables from a Postman collection | `Tuple[Set[str], Optional[str], Dict]` |
| `generate_variables_template(collection_path, output_path)` | Generates a template file with all variables from a collection | `None` |

## Repl Class Methods

| Method | Description | Return Type |
|--------|-------------|-------------|
| `__init__(collection_path, target_profile, proxy_host, proxy_port, verify_ssl, auto_detect_proxy, verbose)` | Initializes the Repl object with configuration | `None` |
| `load_collection()` | Loads and validates the Postman collection | `bool` |
| `load_profile()` | Loads and validates the insertion point with variables | `bool` |
| `replace_variables(text)` | Replaces variables in text with values from the insertion point | `str` |
| `extract_requests_from_item(item, folder_name)` | Extracts requests from a collection item | `List[Dict]` |
| `extract_all_requests(collection)` | Extracts all requests from the collection | `List[Dict]` |
| `prepare_request(request_data)` | Prepares a request for sending (replaces variables, etc.) | `Dict` |
| `send_request(prepared_request)` | Sends a request through the proxy | `Dict` |
| `process_items(items, folder_name)` | Processes items in a collection folder | `None` |
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
  ├── select_collection_file()
  ├── resolve_collection_path()
  ├── extract_variables_from_collection()
  │     ├── process_url()
  │     ├── process_body()
  │     ├── process_headers()
  │     ├── process_request()
  │     └── process_item()
  ├── generate_variables_template()
  ├── select_proxy_file()
  ├── load_proxy()
  │     └── validate_json_file()
  ├── Repl.run()
  │     ├── load_collection()
  │     │     └── validate_json_file()
  │     ├── load_profile()
  │     │     └── validate_json_file()
  │     ├── check_proxy()
  │     │     ├── check_proxy_connection()
  │     │     └── verify_proxy_with_request()
  │     ├── process_collection()
  │     │     ├── process_items()
  │     │     ├── extract_all_requests()
  │     │     │     └── extract_requests_from_item()
  │     │     ├── prepare_request()
  │     │     │     └── replace_variables()
  │     │     └── send_request()
  │     └── save_results()
  └── save_proxy()
```

## Testing Functions

The test suite includes tests for all major functions to ensure they work correctly. See the [[Tests]] page for more information on the test suite.
