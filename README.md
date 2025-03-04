# Postman2Burp

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Burp Suite](https://img.shields.io/badge/Burp%20Suite-Compatible-orange.svg)](https://portswigger.net/burp)
[![Postman](https://img.shields.io/badge/Postman-Collection-orange.svg)](https://www.postman.com/)

> **Problem Statement:** Security teams need to efficiently test API endpoints in Burp Suite but manually recreating Postman collections is time-consuming and error-prone.

Postman2Burp bridges the gap between API development and security testing by automatically sending Postman collection requests through Burp Suite proxy.

## 📋 Table of Contents

- [Postman2Burp](#postman2burp)
  - [📋 Table of Contents](#-table-of-contents)
  - [🎯 Purpose](#-purpose)
  - [🔍 Use Cases](#-use-cases)
    - [1. API Security Assessment](#1-api-security-assessment)
    - [2. Custom Proxy Configuration](#2-custom-proxy-configuration)
    - [3. Handling Authentication](#3-handling-authentication)
    - [4. Configuration File](#4-configuration-file)
  - [📦 Requirements](#-requirements)
  - [🔧 Setup](#-setup)
    - [Quick Setup](#quick-setup)
    - [Manual Setup](#manual-setup)
  - [🚀 Usage](#-usage)
    - [Run Script](#run-script)
    - [Manual Usage](#manual-usage)
  - [⚙️ Options](#️-options)
  - [✨ Features](#-features)
  - [📈 Testing Workflow](#-testing-workflow)
  - [📚 Included Examples](#-included-examples)
  - [🔧 Troubleshooting](#-troubleshooting)
  - [⚠️ Limitations](#️-limitations)
  - [📜 License](#-license)
  - [👥 Contributing](#-contributing)
    - [Code Style](#code-style)
    - [Bug Reports](#bug-reports)
    - [Feature Requests](#feature-requests)

## 🎯 Purpose

This tool automates API security testing by:

| Step | Description |
|------|-------------|
| 1️⃣ | Reading Postman collection JSON files |
| 2️⃣ | Parsing all requests (including nested folders) |
| 3️⃣ | Resolving environment variables |
| 4️⃣ | Sending requests through Burp Suite proxy |
| 5️⃣ | Logging results |

## 🔍 Use Cases

### 1. API Security Assessment

When performing a security assessment of an API that has a Postman collection:

```bash
$ ./run_postman_to_burp.sh
Activating virtual environment...
Running Postman2Burp tool...
2024-03-04 10:15:23 - INFO - Attempting to auto-detect running proxy...
2024-03-04 10:15:23 - INFO - Detected running proxy at localhost:8080
2024-03-04 10:15:23 - INFO - Loading collection: ./postman_collection.json
2024-03-04 10:15:23 - INFO - Loading environment: ./variables.json
2024-03-04 10:15:23 - INFO - Processing folder: User Management
2024-03-04 10:15:24 - INFO - Processing request: User Management/Get Users
2024-03-04 10:15:24 - INFO - Processing request: User Management/Get User by ID
2024-03-04 10:15:25 - INFO - Processing request: User Management/Create User
2024-03-04 10:15:25 - INFO - Processing folder: Authentication
2024-03-04 10:15:26 - INFO - Processing request: Authentication/Login
2024-03-04 10:15:26 - INFO - Processing request: Authentication/Refresh Token

Summary:
  Total requests: 5
  Successful: 5
  Failed: 0
Results saved to: ./burp_results.json

Success! All requests have been sent through Burp Suite.
```

### 2. Custom Proxy Configuration

Testing with a non-standard proxy setup:

```bash
$ python postman2burp.py --collection api_collection.json --proxy 192.168.1.100:9090 --verbose
2024-03-04 10:20:15 - INFO - Using proxy 192.168.1.100:9090 from --proxy argument
2024-03-04 10:20:15 - INFO - Proxy connection successful at 192.168.1.100:9090
2024-03-04 10:20:15 - DEBUG - Using proxy: http://192.168.1.100:9090
2024-03-04 10:20:15 - INFO - Loading collection: api_collection.json
2024-03-04 10:20:16 - DEBUG - Found 12 requests in collection
2024-03-04 10:20:16 - INFO - Processing request: Get Products
2024-03-04 10:20:16 - DEBUG - Sending GET request to https://api.example.com/products
2024-03-04 10:20:17 - DEBUG - Response: 200 OK (0.342s)
...

Summary:
  Total requests: 12
  Successful: 11
  Failed: 1
```

### 3. Handling Authentication

Using environment variables for authenticated API testing:

```bash
$ python postman2burp.py --collection secure_api.json --environment prod_env.json
2024-03-04 10:30:45 - INFO - Attempting to auto-detect running proxy...
2024-03-04 10:30:45 - INFO - Detected running proxy at localhost:8080
2024-03-04 10:30:45 - INFO - Proxy connection successful at localhost:8080
2024-03-04 10:30:45 - INFO - Loading collection: secure_api.json
2024-03-04 10:30:45 - INFO - Loading environment: prod_env.json
2024-03-04 10:30:45 - INFO - Resolved 8 environment variables
2024-03-04 10:30:46 - INFO - Processing request: Authenticate
2024-03-04 10:30:47 - INFO - Processing request: Get Protected Resource
2024-03-04 10:30:47 - INFO - Processing request: Update Resource

Summary:
  Total requests: 3
  Successful: 3
  Failed: 0
```

### 4. Configuration File

Store your settings in a `config.json` file to avoid repetitive command-line arguments:

| Option | Type | Description |
|--------|------|-------------|
| `proxy_host` | String | Proxy server hostname or IP |
| `proxy_port` | Integer | Proxy server port |
| `verify_ssl` | Boolean | Verify SSL certificates |
| `skip_proxy_check` | Boolean | Skip proxy connection check |

Create a configuration file:

```bash
# Save current settings to config.json
$ python postman2burp.py --collection api_collection.json --proxy 10.0.0.1:9090 --save-config
2024-03-04 10:40:12 - INFO - Configuration saved to /path/to/config.json
```

Use the configuration file:

```bash
# Use settings from config.json
$ python postman2burp.py --collection api_collection.json
2024-03-04 10:41:30 - INFO - Loaded configuration from /path/to/config.json
2024-03-04 10:41:30 - INFO - Using proxy host from config: 10.0.0.1
2024-03-04 10:41:30 - INFO - Using proxy port from config: 9090
```

Override specific settings:

```bash
# Override proxy from config.json
$ python postman2burp.py --collection api_collection.json --proxy localhost:8888
2024-03-04 10:42:45 - INFO - Loaded configuration from /path/to/config.json
2024-03-04 10:42:45 - INFO - Using proxy localhost:8888 from --proxy argument
```

## 📦 Requirements

- Python 3.6+
- Required packages (auto-installed):
  - requests
  - urllib3
  - python-dotenv

## 🔧 Setup

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

4. Start Burp Suite with proxy on localhost:8080 (or let the tool auto-detect your proxy)

## 🚀 Usage

### Run Script

Use the provided shell script for quick execution:

```bash
chmod +x run_postman_to_burp.sh
./run_postman_to_burp.sh
```

This script:
- Sets up the Python environment
- Automatically detects if Burp Suite is running
- Sends requests from the example collection

### Manual Usage

| Command | Description |
|---------|-------------|
| **Basic Usage** | |
| `python postman2burp.py --collection FILE` | Process a Postman collection |
| **Environment Variables** | |
| `--environment FILE` | Use Postman environment variables |
| **Proxy Settings** | |
| `--proxy HOST:PORT` | Specify proxy in host:port format |
| `--proxy-host HOST` | Specify proxy hostname/IP |
| `--proxy-port PORT` | Specify proxy port number |
| `--no-auto-detect` | Disable proxy auto-detection |
| **Output Options** | |
| `--output FILE` | Save results to JSON file |
| `--verbose` | Enable detailed logging |
| **Configuration** | |
| `--save-config` | Save settings to config.json |

#### Examples

**Basic scan:**
```bash
python postman2burp.py --collection api_collection.json
```

**With environment variables:**
```bash
python postman2burp.py --collection api_collection.json --environment variables.json
```

**Custom proxy settings:**
```bash
python postman2burp.py --collection api_collection.json --proxy localhost:8080
```

**Save results and configuration:**
```bash
python postman2burp.py --collection api_collection.json --output results.json --save-config
```

#### Complete Session

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Run the tool
python postman2burp.py --collection api_collection.json --environment variables.json

# 3. Deactivate when done
deactivate
```

## ⚙️ Options

```
usage: postman2burp.py [-h] --collection COLLECTION [--environment ENVIRONMENT]
                       [--proxy PROXY] [--proxy-host PROXY_HOST] [--proxy-port PROXY_PORT]
                       [--verify-ssl] [--skip-proxy-check] [--no-auto-detect]
                       [--output OUTPUT] [--verbose] [--save-config]

options:
  -h, --help            show help message and exit
  --collection COLLECTION
                        Path to Postman collection JSON file

Environment Options:
  --environment ENVIRONMENT
                        Path to Postman environment JSON file

Proxy Options:
  --proxy PROXY         Proxy in format host:port (e.g., localhost:8080)
  --proxy-host PROXY_HOST
                        Proxy hostname/IP (default: auto-detected)
  --proxy-port PROXY_PORT
                        Proxy port (default: auto-detected or from config.json)
  --verify-ssl          Verify SSL certificates
  --skip-proxy-check    Skip proxy connection check
  --no-auto-detect      Disable proxy auto-detection (use config values only)

Output Options:
  --output OUTPUT       Save results to JSON file
  --verbose             Enable detailed logging

Configuration Options:
  --save-config         Save current settings to config.json
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 Proxy Auto-detection | Automatically detects running proxies on common ports |
| 📁 Nested Folders | Handles nested folders in collections |
| 🔄 Environment Variables | Supports environment variables |
| 📝 Multiple Body Types | Processes multiple request body types |
| 🔐 Authentication | Handles authentication headers |
| 📊 Logging | Logs request results |
| 🔍 Proxy Verification | Verifies proxy before sending requests |
| ⚙️ Configuration File | Stores settings in config.json |

## 📈 Testing Workflow

1. Receive Postman collection
2. Run this tool (it will auto-detect your proxy)
3. Analyze captured requests in Burp
4. Review results file

## 📚 Included Examples

- `postman_collection.json`: Comprehensive API collection
- `variables.json`: Matching environment variables

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Environment Issues** | Remove `venv` directory and run `setup_venv.sh` again |
| **SSL Errors** | Use `--verify-ssl` to enable certificate verification |
| **Connection Errors** | Ensure a proxy is running or specify one with `--proxy` |
| **Auth Issues** | Check environment variables contain necessary credentials |
| **Variable Resolution** | Verify environment file format is correct |
| **Proxy Not Detected** | Start Burp Suite or specify proxy with `--proxy host:port` |
| **Auto-detection Issues** | Use `--verbose` to see detailed proxy detection logs |

## ⚠️ Limitations

- Limited support for file uploads in multipart/form-data
- No support for WebSocket requests
- No execution of Postman pre-request and test scripts

## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

```
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   Copyright 2024 Postman2Burp Contributors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```

## 👥 Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines for Python code
- Use descriptive variable names
- Add comments for complex logic
- Write tests for new features

### Bug Reports

If you find a bug, please open an issue with:
- Clear description of the bug
- Steps to reproduce
- Expected behavior
- Screenshots (if applicable)
- Environment details

### Feature Requests

Have an idea for a new feature? Open an issue describing:
- The problem your feature would solve
- How your solution would work
- Any alternatives you've considered