# Features

This document provides a technical overview of the core features in Repl, focusing on implementation details and code logic.

## Core Features

### Postman Collection Parsing

Loads and validates Postman Collection v2.1 schema files. The function caches collection data in instance variables for reuse, including collection ID, name, and variables to avoid repeated lookups.

```python
def load_collection(self) -> bool:
    is_valid, json_data = validate_json_file(self.collection_path)
    if not is_valid or not json_data:
        self.logger.error(f"Failed to load collection: {self.collection_path}")
        return False
        
    self.collection = json_data
    self.collection_id = self.collection.get("info", {}).get("_postman_id", "unknown")
    self.collection_name = self.collection.get("info", {}).get("name", "Unknown Collection")
    
    if "variable" in self.collection:
        for var in self.collection["variable"]:
            if "key" in var and "value" in var:
                self.collection_variables[var["key"]] = var["value"]
    
    self.logger.info(f"Loaded collection: {self.collection_name} ({self.collection_id})")
    return True
```

### Postman 2.1 Schema Support

Full support for Postman Collection Format v2.1, including all request types, authentication methods, and variable formats. The tool validates schema compliance during collection loading.

```python
def validate_collection_schema(collection_data):
    if "info" not in collection_data or "schema" not in collection_data["info"]:
        return False
        
    schema = collection_data["info"]["schema"]
    if not schema.startswith("https://schema.getpostman.com/"):
        return False
        
    schema_version = schema.split("/")[-2]
    if schema_version not in ["v2.1.0", "v2.0.0"]:
        return False
        
    return True
```

### Variable Extraction

Extracts variables in the format {{variable}} from text. Uses sets for O(1) lookups and automatic deduplication of variable names.

```python
def extract_variables_from_text(text: str) -> Set[str]:
    if not text or not isinstance(text, str):
        return set()
        
    pattern = r'{{([^{}]+)}}'
    matches = re.findall(pattern, text)
    return {match for match in matches if not match.startswith('$')}
```

### Variable Replacement

Replaces Postman variables with their values from profiles. Also handles environment variables in the format ${ENV_VAR}.

```python
def replace_variables(self, text: str) -> str:
    if not text or not isinstance(text, str):
        return text
        
    env_var_pattern = r'\${([A-Za-z0-9_]+)}'
    for match in re.finditer(env_var_pattern, text):
        env_var_name = match.group(1)
        env_var_value = os.environ.get(env_var_name, '')
        text = text.replace(f'${{{env_var_name}}}', env_var_value)
    
    for var_name, var_value in self.variables.items():
        text = text.replace(f'{{{{{var_name}}}}}', str(var_value))
        
    return text
```

## HTTP Request Processing

### Request Preparation

Prepares HTTP requests by replacing variables in URL, headers, and body. Handles different body types (raw, form-data, urlencoded) and processes authentication methods.

```python
def prepare_request(self, request_data: Dict) -> Dict:
    url = self.replace_variables(request_data.get('url', ''))
    
    headers = {}
    for header in request_data.get('headers', []):
        key = self.replace_variables(header.get('key', ''))
        value = self.replace_variables(header.get('value', ''))
        headers[key] = value
```

### Custom Headers

Supports adding, modifying, and removing custom headers for all requests. Headers can be specified in the insertion point or added via command line arguments.

```python
def add_custom_headers(self, headers: Dict, custom_headers: Dict) -> Dict:
    result_headers = headers.copy()
    
    for key, value in custom_headers.items():
        if value is None:  # Remove header if value is None
            if key in result_headers:
                del result_headers[key]
        else:  # Add or replace header
            result_headers[key] = self.replace_variables(value)
            
    return result_headers
```

Usage example:

```bash
python repl.py --collection "your_collection.json" --header "X-API-Key:your-key" --header "User-Agent:Custom-Agent"
```

### Proxy Support

Routes requests through the specified proxy and returns the response. Handles various HTTP methods, body types, and authentication methods.

```python
def send_request(self, prepared_request: Dict) -> Dict:
    proxies = None
    if self.proxy_host and self.proxy_port:
        proxy_url = f"http://{self.proxy_host}:{self.proxy_port}"
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
```

## Proxy Management

### Proxy Detection and Verification

Checks if a proxy is running at the specified host and port using a direct socket connection. Verifies proxy by making a test HTTP request to ensure it properly forwards HTTP traffic.

```python
def check_proxy_connection(host: str, port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((host, port))
            return True
    except:
        return False

def verify_proxy_with_request(host: str, port: int) -> bool:
    try:
        proxies = {
            "http": f"http://{host}:{port}",
            "https": f"http://{host}:{port}"
        }
        response = requests.get("http://httpbin.org/get", 
                               proxies=proxies, 
                               timeout=5,
                               verify=False)
        return response.status_code == 200
    except:
        return False
```

## Profile Management

### Profile Loading and Validation

Loads and validates target insertion points  containing variable values. Supports both JSON files and interactive insertion point creation.

```python
def load_profile(self) -> bool:
    if not self.insertion_point:
        return True  # No insertion point specified, continue without variables
        
    is_valid, profile_data = validate_json_file(self.insertion_point)
    if not is_valid or not profile_data:
        return False
        
    if "variables" in profile_data:
        self.variables = profile_data["variables"]
    else:
        self.variables = profile_data  # Assume the entire file is variables
        
    return True
```

## File Naming and Organization

The tool uses a structured file naming convention and directory organization:

1. **Collections Directory**: Stores Postman collection files
   - Naming pattern: `[project_name]_collection.json`

2. **Insertion Points Directory**: Stores variable profiles
   - Naming pattern: `[project_name]_[environment].json`

3. **Proxies Directory**: Stores proxy configurations
   - Naming pattern: `[proxy_name].json`

4. **Logs Directory**: Stores execution logs
   - Naming pattern: `repl_[timestamp].log`

This organization allows for easy management of multiple projects and environments.

## Logging System

Comprehensive logging system with configurable verbosity levels. Logs are stored in the `logs` directory with timestamps for easy tracking.

```python
def setup_logging(self, log_level=logging.INFO):
    self.logger = logging.getLogger("repl")
    self.logger.setLevel(log_level)
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # File handler with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"repl_{timestamp}.log")
    file_handler = logging.FileHandler(log_file)
    
    # Console handler
    console_handler = logging.StreamHandler()
    
    # Set format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    self.logger.addHandler(file_handler)
    if self.verbose:
        self.logger.addHandler(console_handler)
        console_handler.setLevel(logging.INFO)
    else:
        console_handler.setLevel(logging.WARNING)
```

## Command Line Interface

Provides a command-line interface with options for collection selection, insertion point management, proxy configuration, and output control.

```python
def main():
    parser = argparse.ArgumentParser(description="Replace, Load, and Replay Postman collections through any proxy tool")
    
    # Collection options
    parser.add_argument("--collection", help="Path to Postman collection JSON file (supports Postman Collection Format v2.1)")
    
    # Profile options
    parser.add_argument("--target-profile", help="Path to insertion point JSON file containing values for replacing variables")
    parser.add_argument("--extract-keys", nargs="?", const="interactive", help="Extract variable keys from collection and exit")
    
    # Proxy options
    parser.add_argument("--proxy", help="Proxy in format host:port")
    parser.add_argument("--proxy-host", help="Proxy host")
    parser.add_argument("--proxy-port", type=int, help="Proxy port")
    parser.add_argument("--verify-ssl", action="store_true", help="Verify SSL certificates")
    
    # Header options
    parser.add_argument("--header", action="append", help="Add custom header in format 'Key:Value'")
    
    # Output options
    parser.add_argument("--output", help="Output file for request results")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
```

## Interactive Features

### Interactive Collection Selection

When no collection is specified, the tool provides an interactive menu to select from available collections in the collections directory.

```python
def select_collection_file() -> str:
    collections_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "collections")
    if not os.path.exists(collections_dir):
        os.makedirs(collections_dir)
        
    collection_files = [f for f in os.listdir(collections_dir) if f.endswith('.json')]
    
    if not collection_files:
        print("No collection files found in the collections directory.")
        return ""
        
    print("\nAvailable collection files:")
    for i, file in enumerate(collection_files, 1):
        print(f"{i}. {file}")
        
    while True:
        try:
            choice = int(input("\nSelect a collection file (number): "))
            if 1 <= choice <= len(collection_files):
                return os.path.join(collections_dir, collection_files[choice-1])
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a number.")
```

### Interactive Variable Extraction

When using the `--extract-keys` option, the tool can interactively guide users through creating a insertion point with all variables from a collection.

```python
def generate_variables_template(collection_path: str, output_path: str = None) -> None:
    variables, collection_name, _ = extract_variables_from_collection(collection_path)
    
    if not variables:
        print("No variables found in the collection.")
        return
        
    print(f"\nFound {len(variables)} variables in collection: {collection_name}")
    
    if output_path is None:
        # Interactive mode
        profiles_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")
        if not os.path.exists(profiles_dir):
            os.makedirs(profiles_dir)
            
        default_filename = f"{collection_name.lower().replace(' ', '_')}_profile.json"
        default_path = os.path.join(profiles_dir, default_filename)
        
        print(f"\nCreating insertion point template at: {default_path}")
        print("Enter values for each variable (leave empty to skip):")
        
        variables_dict = {}
        for var in sorted(variables):
            value = input(f"{var}: ")
            if value:
                variables_dict[var] = value
                
        with open(default_path, 'w') as f:
            json.dump({"variables": variables_dict}, f, indent=2)
            
        print(f"\nProfile template created at: {default_path}")
    else:
        # Non-interactive mode
        variables_dict = {var: "" for var in variables}
        with open(output_path, 'w') as f:
            json.dump({"variables": variables_dict}, f, indent=2)
```

### Interactive Proxy Selection

When no proxy is specified, the tool can interactively select from available proxy configurations.

```python
def select_proxy_file() -> str:
    proxies_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxies")
    if not os.path.exists(proxies_dir):
        os.makedirs(proxies_dir)
        
    proxy_profiles = [f for f in os.listdir(proxies_dir) if f.endswith('.json')]
    
    if not proxy_profiles:
        print("No proxy configuration files found in the proxies directory.")
        return ""
        
    print("\nAvailable proxy configurations:")
    for i, file in enumerate(proxy_profiles, 1):
        print(f"{i}. {file}")
        
    while True:
        try:
            choice = int(input("\nSelect a proxy configuration (number): "))
            if 1 <= choice <= len(proxy_profiles):
                return os.path.join(proxies_dir, proxy_profiles[choice-1])
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a number.")
```

## Technical Implementation Details

### Error Handling

Implements error handling throughout the codebase with appropriate fallbacks and logging.

```python
try:
    result = operation()
except Exception as e:
    if self.verbose:
        print(f"Error: {str(e)}")
```

### Performance Optimizations

#### Caching

Frequently used data is cached to avoid redundant processing. Collection data is loaded once and stored in instance variables.

```python
def load_collection(self) -> bool:
    is_valid, json_data = validate_json_file(self.collection_path)
    if not is_valid or not json_data:
        self.logger.error(f"Failed to load collection: {self.collection_path}")
        return False
        
    self.collection = json_data
    self.collection_id = self.collection.get("info", {}).get("_postman_id", "unknown")
    self.collection_name = self.collection.get("info", {}).get("name", "Unknown Collection")
    
    if "variable" in self.collection:
        for var in self.collection["variable"]:
            if "key" in var and "value" in var:
                self.collection_variables[var["key"]] = var["value"]
    
    self.logger.info(f"Loaded collection: {self.collection_name} ({self.collection_id})")
    return True
```

#### Lazy Loading

Resources are loaded only when needed. The run method only loads collections, profiles, and checks proxies when required.

```python
def run(self) -> Dict:
    self.logger.info(f"Starting conversion of {os.path.basename(self.collection_path)}")
    
    if not self.load_collection():
        self.logger.error("Failed to load collection")
        return {"error": "Failed to load collection"}
    
    if not self.load_profile():
        self.logger.error("Failed to load profile")
        return {"error": "Failed to load profile"}
    
    if not self.check_proxy():
        self.logger.error("Failed to connect to proxy")
        return {"error": "Failed to connect to proxy"}
    
    self.process_collection()
    
    if self.output_file:
        self.save_results()
    
    return self.results
```

#### Efficient Data Structures

Sets are used for variable extraction to ensure uniqueness and O(1) lookups.

```python
def extract_variables_from_text(text: str) -> Set[str]:
    if not text:
        return set()
    
    pattern = r'{{([^{}]+)}}'
    matches = re.findall(pattern, text)
    
    return {match for match in matches if not match.startswith('$')}
```

```python
def extract_variables_from_collection(collection_path: str) -> Tuple[Set[str], Optional[str], Dict]:
    variables = set()
    
    def process_item(item):
        variables.update(extract_variables_from_text(item["name"]))
    
    for item in collection_data.get("item", []):
        process_item(item)
    
    return variables, collection_id, collection_data
```

#### Minimized I/O Operations

File operations are optimized to reduce disk access. Results are written in a single operation.

```python
def save_results(self) -> None:
    if not self.output_file or not self.results:
        return
        
    output_dir = os.path.dirname(self.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(self.output_file, 'w') as f:
        json.dump(self.results, f, indent=2)
```

### Security Considerations

1. **SSL Verification Control**: Users can enable/disable SSL certificate verification
2. **Environment Variable Support**: Sensitive data can be stored in environment variables
3. **File Path Validation**: All file paths are validated before use

## Integration Capabilities

1. **Scriptable Interface**: Can be used in shell scripts for batch processing
2. **JSON Output**: Results are saved in structured JSON format for easy parsing
3. **Exit Codes**: Returns appropriate exit codes for use in automation pipelines

## Usage Examples

### Batch Processing

Process multiple collections at once using shell scripting:

```bash
for collection in ./collections/*.json; do
  python repl.py --collection "$collection" --insertion-point"your_profile.json"
done
```

### Custom Proxy Configuration

**Combined Host:Port Format**

```bash
python repl.py --collection "your_collection.json" --proxy 127.0.0.1:8888
```

**Separate Host and Port**

```bash
python repl.py --collection "your_collection.json" --proxy-host 127.0.0.1 --proxy-port 8888
```

**SSL Verification**

Enable SSL certificate verification (disabled by default):

```bash
python repl.py --collection "your_collection.json" --verify-ssl
```

**Saving requests to a log file**

Save request and response details to a JSON file for later analysis:

```bash
python repl.py --collection "your_collection.json" --output "results.json"
```

The output file contains an array of request/response pairs with details like:
- URL
- Method
- Headers
- Request body
- Response status
- Response body
- Timing information

### Configuration Management

**Saving Configuration**

Save your current settings to the config file for future use:

```bash
python repl.py --collection "your_collection.json" --proxy localhost:8080 --save-config
```

**Loading Configuration**

The tool automatically loads settings from `config.json` if it exists. You can override specific settings with command-line arguments:

```bash
# Uses proxy from config.json but specifies a different collection
python repl.py --collection "different_collection.json"
``` 