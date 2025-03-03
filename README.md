# Postman2Burp

Automates sending Postman collection requests through Burp Suite proxy for API security testing.

## Purpose

This tool automates API security testing by:

1. Reading Postman collection JSON files
2. Parsing all requests (including nested folders)
3. Resolving environment variables
4. Sending requests through Burp Suite proxy
5. Logging results

## Requirements

- Python 3.6+
- Required packages (auto-installed):
  - requests
  - urllib3
  - python-dotenv

## Setup

### Quick Setup

```bash
# Make executable
chmod +x setup_venv.sh

# Run setup
./setup_venv.sh
```

### Manual Setup

1. Create virtual environment:
   ```bash
   python3 -m venv venv
   ```

2. Activate environment:
   ```bash
   # macOS/Linux
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```

3. Install packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Start Burp Suite with proxy on localhost:8080

## Usage

### Run Script

```bash
# Make executable
chmod +x run_postman_to_burp.sh

# Run tool
./run_postman_to_burp.sh
```

The script:
1. Sets up the environment if needed
2. Verifies Burp Suite is running
3. Sends requests from the example collection

### Manual Usage

```bash
# Activate environment
source venv/bin/activate

# Basic usage
python postman2burp.py --collection /path/to/collection.json

# With environment variables
python postman2burp.py --collection /path/to/collection.json --environment /path/to/environment.json

# Custom proxy
python postman2burp.py --collection /path/to/collection.json --proxy-host 127.0.0.1 --proxy-port 8081

# Save results
python postman2burp.py --collection /path/to/collection.json --output results.json

# Verbose logging
python postman2burp.py --collection /path/to/collection.json --verbose

# Deactivate when done
deactivate
```

## Options

```
usage: postman2burp.py [-h] --collection COLLECTION [--environment ENVIRONMENT]
                       [--proxy-host PROXY_HOST] [--proxy-port PROXY_PORT]
                       [--verify-ssl] [--output OUTPUT] [--verbose]

options:
  -h, --help            show help message and exit
  --collection COLLECTION
                        Path to Postman collection JSON file
  --environment ENVIRONMENT
                        Path to Postman environment JSON file
  --proxy-host PROXY_HOST
                        Burp proxy host (default: localhost)
  --proxy-port PROXY_PORT
                        Burp proxy port (default: 8080)
  --verify-ssl          Verify SSL certificates
  --output OUTPUT       Path to save results JSON file
  --verbose             Enable verbose logging
```

## Features

- Handles nested folders in collections
- Supports environment variables
- Processes multiple request body types
- Handles authentication headers
- Logs request results
- Verifies proxy before sending requests

## Testing Workflow

1. Receive Postman collection
2. Configure Burp Suite
3. Run this tool
4. Analyze captured requests in Burp
5. Review results file

## Included Examples

- `real_world_postman_collection.json`: Comprehensive API collection
- `real_world_environment.json`: Matching environment variables

## Troubleshooting

- **Environment Issues**: Remove `venv` directory and run `setup_venv.sh` again
- **SSL Errors**: Use `--verify-ssl` to enable certificate verification
- **Connection Errors**: Verify Burp Suite is running with correct proxy settings
- **Auth Issues**: Check environment variables contain necessary credentials
- **Variable Resolution**: Verify environment file format is correct
- **Proxy Not Running**: Start Burp Suite before running the tool

## Limitations

- Limited support for file uploads in multipart/form-data
- No support for WebSocket requests
- No execution of Postman pre-request and test scripts
