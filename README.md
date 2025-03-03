# Postman2Burp

Automated tool for sending Postman collection requests through Burp Suite proxy for penetration testing.

## Purpose

During penetration testing, you often receive a Postman collection that defines the API scope. Instead of manually sending each request through Burp Suite, this tool automates the process by:

1. Reading a Postman collection JSON file
2. Parsing all requests (including those in folders)
3. Resolving environment variables
4. Sending each request through Burp Suite proxy
5. Logging the results

## Requirements

- Python 3.6+
- Required Python packages (installed automatically with setup script):
  - requests
  - urllib3
  - python-dotenv

## Setup

### Quick Setup (Recommended)


```bash
# Make the setup script executable
chmod +x setup_venv.sh

# Run the setup script
./setup_venv.sh
```

### Manual Setup


1. Create a Python virtual environment:
   ```bash
   python3 -m venv venv
   ```

2. Activate the virtual environment:
   ```bash
   # On macOS/Linux
   source venv/bin/activate

   # On Windows
   venv\Scripts\activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Export your Postman collection as a JSON file (v2.1 format)
5. If your collection uses environment variables, export the environment as a JSON file
6. Make sure Burp Suite is running and the proxy is configured (default: localhost:8080)

## Usage

### Using the Run Script

The easiest way to run the tool is using the provided run script:

```bash
# Make the run script executable
chmod +x run_postman2burp.sh

# Run the script
./run_postman2burp.sh
```

This script will:
1. Check if the virtual environment exists and set it up if needed
2. Activate the virtual environment
3. Verify Burp Suite is running
4. Run the tool with the example collection and environment

### Manual Usage

If you want to run the script manually with your own parameters:

```bash
# Activate the virtual environment
source venv/bin/activate

# Basic usage
python postman2burp.py --collection /path/to/collection.json

# With environment variables
python postman2burp.py --collection /path/to/collection.json --environment /path/to/environment.json

# Custom proxy settings
python postman2burp.py --collection /path/to/collection.json --proxy-host 127.0.0.1 --proxy-port 8081

# Save results to a file
python postman2burp.py --collection /path/to/collection.json --output results.json

# Enable verbose logging
python postman2burp.py --collection /path/to/collection.json --verbose

# When finished, deactivate the virtual environment
deactivate
```

## Full Options

```
usage: postman2burp.py [-h] --collection COLLECTION [--environment ENVIRONMENT]
                         [--proxy-host PROXY_HOST] [--proxy-port PROXY_PORT]
                         [--verify-ssl] [--output OUTPUT] [--verbose]

Send Postman collection requests through Burp Suite proxy

options:
  -h, --help            show this help message and exit
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

- Handles nested folders in Postman collections
- Supports environment variables
- Processes different request body types (raw, urlencoded, formdata)
- Handles authentication headers
- Logs request results and statistics
- Option to save results to a JSON file

## Workflow for Penetration Testing

1. Receive Postman collection from client
2. Configure Burp Suite with appropriate scanning settings
3. Run this script to send all requests through Burp
4. Burp will capture all requests for analysis, scanning, and further testing
5. Review the script output for any failed requests

## Troubleshooting

- **Virtual Environment Issues**: If you encounter issues with the virtual environment, try removing the `venv` directory and running `setup_venv.sh` again.
- **SSL Certificate Errors**: By default, SSL verification is disabled when using a proxy. Use `--verify-ssl` if you need to enable it.
- **Connection Errors**: Ensure Burp Suite is running and the proxy is correctly configured.
- **Authentication Issues**: If requests require authentication, make sure the necessary tokens/credentials are included in the Postman environment variables.
- **Variable Resolution**: If you see unresolved variables in requests (like `{{variable}}`), check that your environment file is correctly formatted and loaded.

## Limitations

- File uploads in multipart/form-data are not fully supported
- WebSocket requests are not supported
- Pre-request and test scripts from Postman are not executed
