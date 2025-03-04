<div align="center">
<h1>Postman2Burp</h1>
A tool to convert Postman collections to Burp Suite requests, allowing for automated security testing of APIs.

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Burp Suite](https://img.shields.io/badge/Burp%20Suite-Compatible-orange.svg)](https://portswigger.net/burp)
[![Postman](https://img.shields.io/badge/Postman-v11.35.0-orange.svg)](https://www.postman.com/)
[![Postman Collections](https://img.shields.io/badge/Postman%20Collections-v2.1-orange.svg)](https://schema.getpostman.com/json/collection/v2.1.0/collection.json)


Postman2Burp bridges the gap between API development and security testing by automatically sending Postman collection requests through Burp Suite proxy, supporting Postman 2.1 schema exports.

</div>



##

<div align="center">

| [🎯 Purpose](#-purpose) | [🔮 Assumptions](#-assumptions) | [✨ Features](#-features) | [🎯 Use Cases](#-use-cases) |
|:----------------------:|:------------------------------:|:-------------------------:|:----------------------------:|
| [⚠️ Limitations](#️-limitations) | [📚 Documentation](#-documentation) | [📜 License](#-license) | [👥 Contributing](#-contributing) |

</div>

##


| Problem | Solution |
|---------|----------|
| During engagements, clients provide large Postman collections with complex API flows that are difficult to manually recreate in Burp Suite | Postman2Burp automatically sends all requests through Burp Suite while maintaining the exact structure and sequence |
| Security testers need to log requests that rotate admin roles or API keys before using Burp Intruder, which doesn't log in history | Postman2Burp logs all requests with detailed information, preserving the complete testing context |
| API security testing requires multiple authentication flows with different tokens | Extracts and reuses tokens across requests in the correct sequence, maintaining proper authentication context |
| Penetration testers need to test the same endpoints with different privilege levels | Allows running identical collections with different profile files to test authorization boundaries |
| Security teams need to document findings with exact request/response pairs | Generates comprehensive logs in Postman-compatible format that can be included in reports |

##

###

### 🔮 Assumptions

The tool operates under the following assumptions:

| Assumption | Description |
|------------|-------------|
| 📁 Collection Location | User has exported a Postman collection to the `/collections` directory of this repository |
| 🧩 Collection Format | The exported collection follows Postman Collection v2.1 format |
| 🔄 Variable Usage | Collection may contain environment variables that need resolution |
| 🌐 Proxy Availability | A proxy (like Burp Suite) is running and accessible |
| 🔒 Authentication | Any required authentication tokens can be provided via environment variables |


##

### Installation

```bash
curl -L https://github.com/darmado/postman2burp/install.sh | sh
```

##

### Setup your Workspace:
0. Launch your proxy 

**1. Export our postman collection. Use Schema 2.1 [from Postman](https://learning.postman.com/docs/getting-started/importing-and-exporting/exporting-data/)
**
**2. Move your Postman collections directory.** 

  ```bash
   mv postman_collection.json ./postman2burp/collections/
   ```
   `./collections` 
   
**3. Exract keys from the Postman collection. The interactive prompt helps you **replace and store new parameter values** in the `./profiles` directory.**

```bash
python3 postman2burp.py --collection  postmanCollection.json --extract-keys 
```

**1. Excute postman2Burp**

```bash
python3 postman2burp.py --collection "postman_collection.json" --target-profile "f1e8e5b7-dc12-4a1c-9e37-42a7df1f9ef2_1741124383.json"
```

##

### Other Options

```bash
options:
  -h, --help            show this help message and exit
  --collection [COLLECTION]
                        Path to Postman collection JSON file (supports Postman 2.1 schema). Specify no path to select interactively.

Profile Options:
  --target-profile TARGET_PROFILE
                        Path to profile JSON file with values to replace variables in the collection
  --extract-keys [OUTPUT_FILE]
                        Extract variables from collection. Specify no file to enter interactive mode. Specify 'print' to display variables.
                        Specify a filename to save template.

Proxy Options:
  --proxy PROXY         Proxy in host:port format
  --proxy-host PROXY_HOST
                        Proxy host
  --proxy-port PROXY_PORT
                        Proxy port
  --verify-ssl          Verify SSL certificates

Output Options:
  --log                 Enable logging to file (saves detailed request results to logs directory)
  --verbose             Enable verbose logging
  --save-proxy          Save current settings as default proxy

Proxy Profiles:
  -profile [PROFILE]    Use specific proxy profile or select from available profiles if no file specified. Omit to select when multiple profiles
                        exist.
```


For detailed usage instructions, see the [Wiki](https://github.com/darmado/postman2burp/wiki).

##

### ✨ Features

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
| ⚙️ Configuration File | Stores settings in config.json | Reuse configurations across runs including target profiles |
| 🔑 Variable Extraction | Extracts variables from collections | Easily create environment templates or view all variables |

##

### 🎯 Use Cases

| Scenario | Challenge | Solution | Example Command |
|----------|-----------|----------|-----------------|
| **Client-Provided API Collection** | Client provides a 200+ endpoint Postman collection for an enterprise API during a time-limited assessment | Quickly import all endpoints into Burp Suite without manual recreation | `python3 postman2burp.py --collection "enterprise_api.json" --extract-keys` |
| **Privilege Escalation Testing** | Need to test the same API endpoints with admin, user, and guest credentials to identify authorization flaws | Run the same collection with different profile files containing various privilege levels | `python3 postman2burp.py --collection "user_api.json" --target-profile "admin_profile.json"` |
| **OAuth2 Token Capture** | Need to capture and reuse OAuth tokens that expire during testing | Automatically extract tokens from responses and use them in subsequent requests | `python3 postman2burp.py --collection "oauth_flow.json" --target-profile "oauth_creds.json" --verbose` |
| **API Key Rotation** | API uses rotating keys that must be captured and reused | Log all requests with key rotation before using Burp Intruder for attacks | `python3 postman2burp.py --collection "key_rotation_api.json" --log --verbose` |
| **Multi-Step API Attacks** | Complex API vulnerabilities require precise sequencing of requests | Maintain exact request sequence while sending through Burp for inspection | `python3 postman2burp.py --collection "complex_workflow.json" --target-profile "attack_vectors.json"` |
| **GraphQL Security Testing** | GraphQL endpoints with complex nested queries are difficult to manually recreate | Preserve exact query structure and variables while testing through Burp | `python3 postman2burp.py --collection "graphql_api.json" --target-profile "graphql_vars.json"` |
| **Report Documentation** | Need to document exact request/response pairs for vulnerability reports | Generate detailed logs of all requests and responses in a reportable format | `python3 postman2burp.py --collection "vulnerable_api.json" --log --verbose` |

For complete examples with code samples and technical details, see our [Use Cases Documentation](https://github.com/darmado/postman2burp/wiki/Use-Cases).

##

### ⚠️ Limitations

| Limitation | Description | Workaround |
|------------|-------------|------------|
| File Uploads | Limited support for multipart/form-data file uploads | Use simple file uploads with base64-encoded content |
| WebSocket Requests | No support for WebSocket requests | Use separate WebSocket testing tools |
| Pre-request Scripts | No execution of Postman pre-request scripts | Manually implement required functionality in your environment |

##

### 📚 Documentation

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


##

### 📜 License

This project is licensed under the [Apache License 2.0](LICENSE).

##

### 👥 Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

| Contribution Area | Guidelines |
|-------------------|------------|
| **Bug Reports** | • Clear description of the bug<br>• Steps to reproduce<br>• Expected behavior<br>• Screenshots (if applicable)<br>• Environment details |
| **Feature Requests** | • The problem your feature would solve<br>• How your solution would work<br>• Any alternatives you've considered |

For detailed usage instructions, see the [Wiki](https://github.com/darmado/postman2burp/wiki).