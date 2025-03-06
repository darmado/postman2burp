# Function Map

This page provides a comprehensive overview of all functions in the Repl tool, organized by category.

## Core Functions

| Function | Description | Return Type |
|----------|-------------|-------------|
| `validate_json_file(file_path)` | Validates JSON files and returns parsed content | `Tuple[bool, Dict]` |
| `load_collection(collection_path)` | Loads and validates Postman collection | `Dict` |
| `resolve_collection_path(collection_path)` | Resolves full path to collection file | `str` |
| `select_collection_file()` | Interactive collection selection | `str` |

## Proxy Management
    
| Function | Description | Return Type |
|----------|-------------|-------------|
| `check_proxy_connection(host, port)` | Verifies proxy connection using socket | `bool` |
| `verify_proxy_with_request(host, port)` | Tests proxy with HTTP request | `bool` |
| `load_proxy(proxy_path)` | Loads proxy configuration | `Dict` |
| `save_proxy(proxy)` | Saves proxy configuration | `bool` |
| `select_proxy_file()` | Interactive proxy selection | `str` |

## Variable Management

| Function | Description | Return Type |
|----------|-------------|-------------|
| `extract_variables_from_text(text)` | Extracts {{variable}} patterns from text | `Set[str]` |
| `extract_variables_from_collection(collection_path)` | Extracts all variables from collection | `Tuple[Set[str], str, Dict]` |
| `generate_variables_template(collection_path, output_path)` | Creates insertion point template | `None` |
| `replace_variables(text, variables)` | Replaces variables with values | `str` |

## Encoding Functions

| Function | Description | Return Type |
|----------|-------------|-------------|
| `Encoder.encode(value, encoding_type, iterations)` | Encodes a value using specified method | `str` |
| `Encoder.url_encode(value)` | URL encodes a string | `str` |
| `Encoder.double_url_encode(value)` | Double URL encodes a string | `str` |
| `Encoder.html_encode(value)` | HTML entity encodes a string | `str` |
| `Encoder.xml_encode(value)` | XML encodes a string | `str` |
| `Encoder.unicode_escape(value)` | Unicode escapes a string | `str` |
| `Encoder.hex_escape(value)` | Hex escapes a string | `str` |
| `Encoder.octal_escape(value)` | Octal escapes a string | `str` |
| `Encoder.base64_encode(value)` | Base64 encodes a string | `str` |
| `Encoder.sql_char_encode(value)` | Converts to SQL CHAR() function | `str` |
| `Encoder.js_escape(value)` | JavaScript escapes a string | `str` |
| `Encoder.css_escape(value)` | CSS escapes a string | `str` |
| `process_insertion_point(insertion_point)` | Processes encodings in insertion point | `Dict` |
| `apply_encoding_to_value(value, encoding_type, iterations)` | Applies encoding to a single value | `str` |

## Request Processing

| Function | Description | Return Type |
|----------|-------------|-------------|
| `extract_requests_from_item(item, folder_name)` | Extracts requests from collection item | `List[Dict]` |
| `extract_all_requests(collection)` | Extracts all requests from collection | `List[Dict]` |
| `prepare_request(request_data, variables)` | Prepares request for sending | `Dict` |
| `send_request(prepared_request, proxy_config)` | Sends request through proxy | `Dict` |
| `add_custom_headers(headers, custom_headers)` | Adds/modifies request headers | `Dict` |

## Authentication

| Function | Description | Return Type |
|----------|-------------|-------------|
| `load_auth_profile(profile_name)` | Loads authentication profile | `Dict` |
| `save_auth_profile(profile_name, auth_data)` | Saves authentication profile | `bool` |
| `list_auth_profiles()` | Lists available auth profiles | `List[str]` |
| `apply_auth(request, auth_config)` | Applies authentication to request | `Dict` |

## Logging

| Function | Description | Return Type |
|----------|-------------|-------------|
| `setup_logging(log_level, log_file, verbose)` | Configures logging system | `logging.Logger` |
| `log_request(logger, request, verbose)` | Logs request details | `None` |
| `log_response(logger, response, verbose)` | Logs response details | `None` |

## Main Function

| Function | Description | Return Type |
|----------|-------------|-------------|
| `main()` | Command-line interface entry point | `int` |

## Function Dependencies

```
main()
  ├── select_collection_file()
  ├── resolve_collection_path()
  ├── extract_variables_from_collection()
  ├── generate_variables_template()
  ├── select_proxy_file()
  ├── load_proxy()
  ├── load_auth_profile()
  ├── setup_logging()
  ├── load_collection()
  ├── load_insertion_point()
  │     └── process_insertion_point()  # Applies encodings if specified
  ├── extract_all_requests()
  │     └── extract_requests_from_item()
  ├── prepare_request()
  │     ├── replace_variables()
  │     ├── add_custom_headers()
  │     └── apply_auth()
  ├── check_proxy_connection()
  ├── verify_proxy_with_request()
  ├── send_request()
  │     ├── log_request()
  │     └── log_response()
  └── save_proxy()
```

## Testing Functions

The test suite includes tests for all major functions to ensure they work correctly. See the [[Tests]] page for more information on the test suite.
