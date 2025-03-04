# Postman2Burp

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Burp Suite](https://img.shields.io/badge/Burp%20Suite-Compatible-orange.svg)](https://portswigger.net/burp)
[![Postman](https://img.shields.io/badge/Postman-v11.35.0-orange.svg)](https://www.postman.com/)
[![Postman Collections](https://img.shields.io/badge/Postman%20Collections-v2.1-orange.svg)](https://schema.getpostman.com/json/collection/v2.1.0/collection.json)

</div>

> **Problem Statement:** Security teams need to manually import postman collections into BurpSuite. It's time-consuming and error-prone.

Postman2Burp bridges the gap between API development and security testing by automatically sending Postman collection requests through Burp Suite proxy.

## 📋 Table of Contents

<div align="center">

| [🎯 Purpose](#-purpose) | [🔮 Assumptions](#-assumptions) | [📦 Requirements](#-requirements) | [🚀 Quick Start](#-quick-start) |
|:----------------------:|:------------------------------:|:--------------------------------:|:-------------------------------:|
| [✨ Features](#-features) | [🎯 Use Cases](#-use-cases) | [⚠️ Limitations](#️-limitations) | [📚 Documentation](#-documentation) |
|  | [📜 License](#-license) | [👥 Contributing](#-contributing) | |

</div>

## 🎯 Purpose

| Problem | Solution |
|---------|----------|
| Manual recreation of API requests in security tools is time-consuming and error-prone | Postman2Burp automates sending Postman collection requests through Burp Suite proxy |
| Complex API flows are difficult to test manually | Maintains request sequence and handles variable extraction/substitution automatically |
| Environment variables need manual substitution | Automatically resolves all environment variables from profile files |
| Authentication flows require careful token management | Extracts and reuses tokens across requests in the correct sequence |

## 🔮 Assumptions

The tool operates under the following assumptions:

| Assumption | Description |
|------------|-------------|
| 📁 Collection Location | User has exported a Postman collection to the `/collections` directory of this repository |
| 🧩 Collection Format | The exported collection follows Postman Collection v2.1 format |
| 🔄 Variable Usage | Collection may contain environment variables that need resolution |
| 🌐 Proxy Availability | A proxy (like Burp Suite) is running and accessible |
| 🔒 Authentication | Any required authentication tokens can be provided via environment variables |

## 📦 Requirements

| Requirement | Details |
|-------------|---------|
| **Python** | 3.6 or higher |
| **Packages** | Auto-installed via setup script:<br>• requests<br>• urllib3<br>• python-dotenv |
| **Operating System** | Windows, macOS, or Linux |

## 🚀 Quick Start

### One-Line Installation

```bash
curl -sSL https://raw.githubusercontent.com/darmado/postman2burp/main/install.sh | bash
```

This installation script will:
- Clone the repository
- Set up a Python virtual environment
- Install all dependencies
- Create necessary directories (collections, environments, logs)
- Generate a sample environment file
- Configure and make helper scripts executable

### Using the Tool

After installation:

1. Place your Postman collection JSON files in the `collections` directory
2. Place your environment files in the `environments` directory (optional)
3. Run the tool:

```bash
./run_postman_to_burp.sh --collection "your_collection.json" [--environment "your_environment.json"] [--verbose]
```

The tool will automatically:
- Generate a log file based on the collection ID and timestamp
- Store logs in the `logs` directory with detailed request and response information in Postman Collection format
- Send all requests through the detected proxy

#### Extracting Variables

To extract all variables from a collection:

```bash
# Print all variables in the collection
python postman2burp.py --collection "your_collection.json" --extract-keys

# Generate a template environment file with all variables
python postman2burp.py --collection "your_collection.json" --extract-keys "environment_template.json"
```

### Manual Installation

| Step | Command |
|------|---------|
| 1. Clone the repository | `git clone https://github.com/darmado/postman2burp.git`<br>`cd postman2burp` |
| 2. Set up the environment | `chmod +x setup_venv.sh`<br>`./setup_venv.sh` |
| 3. Create directories | `mkdir -p collections environments logs` |
| 4. Run the tool | `./run_postman_to_burp.sh --collection "your_collection.json"` |

For detailed usage instructions, see the [Wiki](https://github.com/darmado/postman2burp/wiki).

## ✨ Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| 🔍 Proxy Auto-detection | Automatically detects running proxies on common ports | No manual proxy configuration needed |
| 📁 Nested Folders | Handles nested folders in collections | Works with complex collection structures |
| 🔄 Environment Variables | Supports environment variables | Reuse collections across different environments |
| 📝 Multiple Body Types | Processes multiple request body types | Works with JSON, form data, raw text, etc. |
| 🔐 Authentication | Handles authentication headers | Maintains security context across requests |
| 📊 Logging | Logs request results | Easy troubleshooting and verification |
| 📋 Postman-Compatible Logs | Generates logs in Postman Collection format | Logs can be imported directly into Postman |
| 🔍 Proxy Verification | Verifies proxy before sending requests | Prevents failed test runs |
| ⚙️ Configuration File | Stores settings in config.json | Reuse configurations across runs |
| 🔑 Variable Extraction | Extracts variables from collections | Easily create environment templates or view all variables |

## 🎯 Use Cases

| Problem | Solution | Example Command | Details |
|---------|----------|-----------------|---------|
| **OAuth2 Flows**: Multiple sequential requests with token extraction and reuse | Maintains request sequence and handles token extraction automatically | `python postman2burp.py --collection "oauth_flow.json" --target-profile "oauth_creds.json" --verbose` | [View Details](https://github.com/darmado/postman2burp/wiki/Use-Cases#oauth2-flow-analysis) |
| **GraphQL Queries**: Complex nested queries difficult to recreate manually | Preserves exact query structure and variables | `python postman2burp.py --collection "graphql_api.json" --target-profile "graphql_vars.json"` | [View Details](https://github.com/darmado/postman2burp/wiki/Use-Cases#graphql-api-security-testing) |
| **Anti-CSRF Protection**: Tokens from responses must be included in subsequent requests | Extracts tokens from responses and applies them to follow-up requests | `python postman2burp.py --collection "secured_workflow.json" --target-profile "test_env.json" --verbose` | [View Details](https://github.com/darmado/postman2burp/wiki/Use-Cases#anti-csrf-protection-testing) |
| **BOLA/IDOR Testing**: Requires different user contexts for the same endpoints | Allows running the same collection with different profile files | `python postman2burp.py --collection "user_management.json" --target-profile "admin_profile.json" --output "admin_results.json"` | [View Details](https://github.com/darmado/postman2burp/wiki/Use-Cases#broken-object-level-authorization-testing) |
| **API Gateway Configurations**: Specific headers, API keys, and request signing | Maintains all headers and authentication mechanisms | `python postman2burp.py --collection "aws_api.json" --target-profile "aws_creds.json"` | [View Details](https://github.com/darmado/postman2burp/wiki/Use-Cases#api-gateway-configuration-testing) |

For complete examples with code samples and technical details, see our [Use Cases Documentation](https://github.com/darmado/postman2burp/wiki/Use-Cases).

## ⚠️ Limitations

| Limitation | Description | Workaround |
|------------|-------------|------------|
| File Uploads | Limited support for multipart/form-data file uploads | Use simple file uploads with base64-encoded content |
| WebSocket Requests | No support for WebSocket requests | Use separate WebSocket testing tools |
| Pre-request Scripts | No execution of Postman pre-request scripts | Manually implement required functionality in your environment |

## 📚 Documentation

Documentation is available in the [Wiki](https://github.com/darmado/postman2burp/wiki):

| Documentation | Description |
|---------------|-------------|
| [Overview](https://github.com/darmado/postman2burp/wiki/Overview) | High-level understanding of Postman2Burp |
| [Installation](https://github.com/darmado/postman2burp/wiki/Installation) | How to install and set up the tool |
| [Usage](https://github.com/darmado/postman2burp/wiki/Usage) | Basic operations and commands |
| [Use Cases](https://github.com/darmado/postman2burp/wiki/Use-Cases) | Detailed examples for specific scenarios |
| [Additional Features](https://github.com/darmado/postman2burp/wiki/Features) | Extended features and techniques |
| [Configuration](https://github.com/darmado/postman2burp/wiki/Configuration) | Configuration options and settings |
| [Troubleshooting](https://github.com/darmado/postman2burp/wiki/Troubleshooting) | Solutions for common issues |
| [Function Map](https://github.com/darmado/postman2burp/wiki/Function-Map) | Overview of all functions and their roles |


## 📜 License

This project is licensed under the [Apache License 2.0](LICENSE).

## 👥 Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

| Contribution Area | Guidelines |
|-------------------|------------|
| **Code Style** | • Follow PEP 8 guidelines for Python code<br>• Use descriptive variable names<br>• Add comments for complex logic<br>• Write tests for new features |
| **Bug Reports** | • Clear description of the bug<br>• Steps to reproduce<br>• Expected behavior<br>• Screenshots (if applicable)<br>• Environment details |
| **Feature Requests** | • The problem your feature would solve<br>• How your solution would work<br>• Any alternatives you've considered |