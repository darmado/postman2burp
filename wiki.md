# Postman2Burp Step-by-Step Guide

This guide provides detailed instructions for using the Postman2Burp tool to automate API security testing by sending Postman collection requests through Burp Suite proxy.

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/postman2burp.git
   cd postman2burp
   ```

2. **Set up the environment**
   ```bash
   # Make the setup script executable
   chmod +x setup_venv.sh
   
   # Run the setup script
   ./setup_venv.sh
   ```
   
   Alternatively, you can set up manually:
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate environment
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

## Step-by-Step Usage Guide

### 1. Export Your Postman Collection

1. Open Postman
2. Select the collection you want to export
3. Click the three dots (⋮) next to the collection name
4. Select "Export"
5. Choose "Collection v2.1" format
6. Save the JSON file to the `./collections` directory in your Postman2Burp installation

### 2. Extract Variables from the Collection

1. Run the following command to extract all variables from your collection:
   ```bash
   python postman2burp.py --collection "your_collection.json" --extract-keys
   ```

2. This will generate a profile file in the `./profiles` directory with a UUID filename (e.g., `f1e8e5b7-dc12-4a1c-9e37-42a7df1f9ef2.json`)

3. Open the generated profile file and fill in the values for each variable:
   ```json
   {
     "variables": {
       "base_url": "https://api.example.com",
       "api_key": "your-api-key-here",
       "username": "your-username",
       "password": "your-password"
     }
   }
   ```

### 3. Start Your Proxy

1. Start Burp Suite (or another proxy tool)
2. Ensure the proxy is listening on a port (default is usually localhost:8080)
3. Configure Burp Suite to intercept traffic as needed

### 4. Run the Tool with Your Collection and Profile

1. Basic usage:
   ```bash
   python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json"
   ```

2. With custom proxy settings:
   ```bash
   python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json" --proxy localhost:8080
   ```

3. Skip proxy check (useful if you're sure the proxy is running):
   ```bash
   python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json" --skip-proxy-check
   ```

4. Save your configuration for future use:
   ```bash
   python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json" --proxy localhost:8080 --save-config
   ```

### 5. Review Results in Burp Suite

1. Open the HTTP history tab in Burp Suite
2. You should see all the requests from your Postman collection
3. Analyze the requests and responses for security testing

## Advanced Usage

### Verbose Output

For detailed logging, add the `--verbose` flag:
```bash
python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json" --verbose
```

### Log Results to a File

Use the `--log` flag to save results automatically to the `./logs` directory:

```bash
python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json" --log
```

This will create a file in the `./logs` directory with a name like `f1e8e5b7-dc12-4a1c-9e37-42a7df1f9ef2.json` (where the UUID is the postman_id from the profile). No filename is required as it will be automatically generated based on the profile's postman_id.

If you use the `--verbose` flag along with `--log`, the tool will also log all HTTP requests and responses:

```bash
python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json" --log --verbose
```

This will create two files:
- `f1e8e5b7-dc12-4a1c-9e37-42a7df1f9ef2.json` - Contains the summary results
- `f1e8e5b7-dc12-4a1c-9e37-42a7df1f9ef2_requests.log` - Contains detailed HTTP request/response logs

### Proxy Settings

When you explicitly specify a proxy (either via command line or through the configuration file), the tool will respect your settings and will not attempt to auto-detect other proxies:

```bash
# Using command-line proxy specification
python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json" --proxy localhost:8080
```

The tool will only attempt to auto-detect proxies when:
1. No proxy is specified in the command line
2. No proxy is specified in the configuration file

This ensures that your specified proxy settings are always respected. If the specified proxy is not available, the tool will notify you rather than falling back to other proxies.

## Configuration Options

Postman2Burp supports configuration via a `config.json` file, making it easier to maintain consistent settings across multiple runs.

### Configuration File

The tool looks for a `config.json` file in the `config` directory. If found, it loads settings from this file. Command-line arguments always take precedence over configuration file settings.

### Sample config.json

```json
{
    "proxy_host": "localhost",
    "proxy_port": 8080,
    "verify_ssl": false,
    "skip_proxy_check": false
}
```

### Available Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `proxy_host` | String | The hostname or IP address of the proxy server |
| `proxy_port` | Integer | The port number of the proxy server |
| `verify_ssl` | Boolean | Whether to verify SSL certificates |
| `skip_proxy_check` | Boolean | Whether to skip the proxy connection check |

### Creating a Configuration File

You can create a configuration file in two ways:

1. **Manually**: Create a `config.json` file in the `config` directory using the sample above.

2. **Automatically**: Run the script with your desired settings and add the `--save-config` flag:
   ```bash
   python postman2burp.py --collection your_collection.json --proxy-host your-proxy-host --proxy-port 9090 --save-config
   ```

### Command-Line Priority

Command-line arguments always take precedence over configuration file settings. This allows you to:

1. Maintain default settings in the configuration file
2. Override specific settings as needed for individual runs

### Usage Examples

**Using Configuration File Only**:
```bash
# Assuming config.json exists with your settings
python postman2burp.py --collection your_collection.json
```

**Overriding Configuration File**:
```bash
# Override proxy host from config file
python postman2burp.py --collection your_collection.json --proxy-host different-proxy

# Override proxy port from config file
python postman2burp.py --collection your_collection.json --proxy-port 9090
```

**Saving New Configuration**:
```bash
# Save current settings to config.json
python postman2burp.py --collection your_collection.json --proxy-host your-proxy --proxy-port 9090 --save-config
```

## Troubleshooting

### Proxy Connection Issues

**Problem**: "Proxy is not running at localhost:8080"
**Solution**: 
- Ensure Burp Suite is running and the proxy is listening on the specified port
- Use `--proxy` to specify a different proxy address
- Use `--skip-proxy-check` to bypass the proxy check

### Variable Substitution Issues

**Problem**: Variables not being substituted in requests
**Solution**:
- Check that your profile file contains all required variables
- Ensure variable names match exactly (case-sensitive)
- Use `--verbose` to see detailed logs of variable substitution

### Collection Loading Issues

**Problem**: "Failed to load collection"
**Solution**:
- Verify the collection file exists and is valid JSON
- Ensure the collection is in Postman Collection v2.1 format
- Check file permissions

### Spaces in Filenames

**Problem**: Command fails with "unrecognized arguments" when filenames contain spaces
**Solution**:
- Wrap filenames in single quotes: `--collection 'My Collection.json'`
- Alternatively, rename files to use underscores instead of spaces

## Directory Structure

- `./collections/`: Store your Postman collection JSON files here
- `./profiles/`: Contains variable profiles for your collections
- `./config/`: Configuration files for the tool
- `./logs/`: Output logs and results from the tool
- `./venv/`: Python virtual environment (created during setup)

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details. 