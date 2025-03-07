<h1 align="center">
<br>
<img src="./img/repl.png" atl="Repl - Load and Send Postman Collections through any proxy tool"></a>
<br>
</h1>
<div align="center">

<h1>Modify, load, and replay Postman collections through any proxy tool in seconds.
</h1>

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Burp Suite](https://img.shields.io/badge/Burp%20Suite-Compatible-orange.svg)](https://portswigger.net/burp)
[![Postman](https://img.shields.io/badge/Postman-v11.35.0-orange.svg)](https://www.postman.com/)
[![Postman Collections](https://img.shields.io/badge/Postman%20Collections-v2.1-orange.svg)](https://schema.getpostman.com/json/collection/v2.1.0/collection.json)


Repl sends Postman collections through proxy tools like Burp Suite or ZAP for efficient API testing.

</div>



##

<div align="center">

| [🎯 Purpose](#-purpose)  | [✨ Features](#-features) | [🎯 Use Cases](#-use-cases) |  [📚 Documentation](#-documentation) | 
|:----------------------:|:------------------------------:|:-------------------------:|:----------------------------:|
| [⚠️ Limitations](#️-limitations) | [📜 License](#-license) | [👥 Contributing](#-contributing) || 

</div>

##


##

### Installation

```bash
curl -L https://raw.githubusercontent.com/darmado/repl/refs/heads/main/install.sh | sh
```

##

### Quick Start Guide

1. **Launch your proxy tool** (Burp Suite, ZAP, etc.)

2. **Export your Postman collection** (Use Schema 2.1) [from Postman](https://learning.postman.com/docs/getting-started/importing-and-exporting/exporting-data/)

3. **Move your Postman collection to the repl directory**
   ```bash
   mv postman_collection.json ./repl/collections/
   ```

4. **Extract variables from the collection**
   ```bash
   python3 repl.py --collection postmanCollection.json --extract-keys
   ```
   This creates templates with placeholders for API keys, tokens, and other variables.

5. **Execute the collection**
   ```bash
   python3 repl.py --collection "postman_collection.json" --insertion-point "variables.json"
   ```

##

### Command-Line Arguments

| Category | Argument | Description |
|----------|----------|-------------|
| **Basic** | `--collection [COLLECTION]` | Specify the Postman collection to test. Leave empty to select interactively. |
| | `--banner` | Display the tool banner |
| **Insertion Points** | `--insertion-point INSERTION_POINT` | Insert values into API request variables  |
| | `--extract-keys [COLLECTION]` | Extract variables and  parameters from a `collection` to create insertion point templates. |
| **Encoding** | `--encode-[METHOD] VALUE` | Wrap paylooad in quotes. Supports url, double-url, html, xml, unicode, hex, octal, base64, sql-char, js, css |
| **Authentication** | `--auth [AUTH]` | Load saved authentication profile. Leave empty to select interactively. |
| | `--auth-type TYPE` | Set authentication type (basic, bearer, api-key, oauth1, oauth2) |
| | `--auth-credentials KEY VALUE` | Set auth credentials (varies by type: username/password, token, api-key, etc.) |
| | `--auth-location LOCATION` | Specify where to place auth data (header, query, cookie) |
| | `--auth-param NAME` | Set custom parameter name for auth (default varies by type) |
| | `--auth-url URL` | Set auth endpoint (token URL, refresh URL) |
| | `--auth-method METHOD` | Set auth method (signature method, grant type) |
| | `--auth-scope SCOPE` | Set permission scopes for OAuth2 |
| **Proxy** | `--proxy PROXY` | Direct traffic through specified proxy (format: host:port) |
| | `--proxy-host HOST` | Set proxy hostname |
| | `--proxy-port PORT` | Set proxy port |
| | `--verify-ssl` | Enable SSL certificate validation |
| | `--proxy-profile [PROFILE]` | Load saved proxy settings |
| **Output** | `--log` | Record request/response data for analysis |
| | `--verbose` | Display detailed request information during execution |
| | `--save-proxy` | Save current proxy settings for future use |
| **Headers** | `--header HEADER` | Add custom headers to all requests (format: 'Key:Value') |

For detailed usage instructions, see the [Wiki](https://github.com/darmado/repl/wiki).

##

### ✨ Features

| Feature | Command-line Arguments | Use Case |
|---------|------------------------|-------------|
| 🔍 Proxy Auto-detection | `--proxy-host`, `--proxy-port` | Detect running proxy tools on common ports (8080, 8081, 8082) |
| 🔄 Custom Proxy Configuration | `--proxy host:port` | Direct traffic through any proxy tool or intercepting middleware |
| 💾 Proxy Profile Management | `--proxy-profile [PROFILE]` | Load and save proxy configurations for different environments |
| 🔑 Variable Extraction | `--extract-keys [OUTPUT_FILE]` | Extract API keys, tokens, and variables from collections for testing |
| 🔐 Payload Insertion | `--insertion-point PROFILE` | Insert values at specific points in API requests from template files |
| 🔒 Multi-auth Support | `--auth`, `--auth-basic`, `--auth-bearer` | Support for Basic Auth, Bearer Token, API Key, OAuth1, and OAuth2 |
| 📊 Logging | `--log`, `--verbose` | Record detailed request/response data for analysis and reporting |
| 🧩 Interactive Mode | `--collection` | Navigate through interactive prompts |
| 🔍 Proxy Verification | Automatic | Verify proxy connection before sending requests |
| 🔤 Header Customization | `--header KEY:VALUE` | Add or modify headers in all requests |
| 🔒 SSL Configuration | `--verify-ssl` | Enable or disable SSL certificate validation |
| 🔄 Encode your payloads | `--encode-` | Encode values using various encoding methods: URL, double URL, HTML, base64, SQL CHAR(), JavaScript, and CSS encoding |

##

### 🎯 Use Cases

For complete examples with code samples and technical details, see our [Use Cases Documentation](https://github.com/darmado/repl/wiki/Use-Cases).

##

### ⚠️ Limitations

| Limitation | Description | Workaround |
|------------|-------------|------------|
| File Uploads | Limited support for multipart/form-data file uploads | Use simple file uploads with base64-encoded content |
| WebSocket Requests | No support for WebSocket requests | Use separate WebSocket testing tools |

##

### 📚 Documentation

Documentation is available in the [Wiki](https://github.com/darmado/repl/wiki):

| Documentation | Description |
|---------------|-------------|
| [Overview](https://github.com/darmado/repl/wiki/Overview) | High-level understanding of Repl |
| [Installation](https://github.com/darmado/repl/wiki/Installation) | How to install and set up the tool |
| [Usage](https://github.com/darmado/repl/wiki/Usage) | Basic operations and commands |
| [Use Cases](https://github.com/darmado/repl/wiki/Use-Cases) | Detailed examples for specific scenarios |
| [Additional Features](https://github.com/darmado/repl/wiki/Features) | Extended features and techniques |
| [Configuration](https://github.com/darmado/repl/wiki/Configuration) | Configuration options and settings |
| [Troubleshooting](https://github.com/darmado/repl/wiki/Troubleshooting) | Solutions for common issues |
| [Function Map](https://github.com/darmado/repl/wiki/Function-Map) | Overview of all functions and their roles |
| [Variable Encoding](https://github.com/darmado/repl/wiki/Features/Encoder) | Guide to encoding variables for security testing |



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

For detailed usage instructions, see the [Wiki](https://github.com/darmado/repl/wiki).

##

### References
- Portswigger https://portswigger.net/burp/documentation/desktop/running-scans/api-scans/
- Postman https://learning.postman.com/docs/postman-cli/postman-cli-run-collection
- Python Auth: https://datagy.io/python-requests-authentication/
- 


### 📜 License

This project is licensed under the [Apache License 2.0](LICENSE).

##
