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
| | `--extract-keys [OUTPUT_FILE]` | Extract variables from collections to create insertion point templates. |
| **Encoding** | `--encode-url VALUE` | URL encode a string |
| | `--encode-double-url VALUE` | Double URL encode a string |
| | `--encode-html VALUE` | HTML encode a string |
| | `--encode-xml VALUE` | XML encode a string |
| | `--encode-unicode VALUE` | Unicode escape a string |
| | `--encode-hex VALUE` | Hex escape a string |
| | `--encode-octal VALUE` | Octal escape a string |
| | `--encode-base64 VALUE` | Base64 encode a string |
| | `--encode-sql-char VALUE` | SQL CHAR() encode a string |
| | `--encode-js VALUE` | JavaScript escape a string |
| | `--encode-css VALUE` | CSS escape a string |
| **Authentication** | `--auth [AUTH]` | Load saved authentication profile. Leave empty to select interactively. |
| | `--list-auth` | Display all saved authentication profiles |
| | `--create-auth` | Create a new authentication profile interactively |
| | `--auth-basic USERNAME PASSWORD` | Authenticate with Basic Auth credentials |
| | `--auth-bearer TOKEN` | Authenticate with Bearer token |
| | `--auth-api-key KEY LOCATION` | Authenticate with API key in header, query, or cookie |
| | `--auth-api-key-name NAME` | Set custom API key parameter name (default: X-API-Key) |
| | `--auth-oauth1 CONSUMER_KEY CONSUMER_SECRET` | Authenticate with OAuth1 credentials |
| | `--auth-oauth1-token TOKEN TOKEN_SECRET` | Add OAuth1 token pair |
| | `--auth-oauth1-signature SIGNATURE` | Configure OAuth1 signature method (default: HMAC-SHA1) |
| | `--auth-oauth2 CLIENT_ID CLIENT_SECRET` | Authenticate with OAuth2 credentials |
| | `--auth-oauth2-token-url URL` | Set OAuth2 token endpoint |
| | `--auth-oauth2-refresh-url URL` | Set OAuth2 refresh endpoint |
| | `--auth-oauth2-grant GRANT_TYPE` | Configure OAuth2 grant type (default: client_credentials) |
| | `--auth-oauth2-username USERNAME` | Add username for password grant |
| | `--auth-oauth2-password PASSWORD` | Add password for password grant |
| | `--auth-oauth2-scope SCOPE` | Set OAuth2 permission scopes |
| **Proxy** | `--proxy PROXY` | Direct traffic through specified proxy (format: host:port) |
| | `--proxy-host HOST` | Configure proxy hostname |
| | `--proxy-port PORT` | Configure proxy port |
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
| 🔐 Variable Insertion | `--insertion-point PROFILE` | Insert values at specific points in API requests from template files |
| 🔑 Variable Extraction | `--extract-keys [OUTPUT_FILE]` | Extract API keys, tokens, and variables from collections for testing |
| 🔒 Multiple Authentication Methods | `--auth`, `--auth-basic`, `--auth-bearer` | Support for Basic Auth, Bearer Token, API Key, OAuth1, and OAuth2 |
| 📊 Request Logging | `--log`, `--verbose` | Record detailed request/response data for analysis and reporting |
| 🧩 Interactive Mode | Run without arguments | Navigate through setup with interactive prompts |
| 🔍 Proxy Verification | Automatic | Verify proxy connection before sending requests |
| 🔤 Header Customization | `--header KEY:VALUE` | Add or modify headers in all requests |
| 🔒 SSL Configuration | `--verify-ssl` | Enable or disable SSL certificate validation |
| 🔄 Variable Encoding | `--encode-*` | Encode values using various methods for security testing and special character handling |

##

### 🎯 Use Cases

| Scenario | Challenge | Solution | Example Command |
|----------|-----------|----------|-----------------|
| **Client-Provided API Collection** | Client provides a 200+ endpoint Postman collection for an enterprise API during a time-limited assessment | Replay all endpoints through any proxy while maintaining request sequence and context | `python3 repl.py --collection "enterprise_api.json" --extract-keys` |
| **Privilege Escalation Testing** | Need to test API endpoints with admin, user, and guest credentials to identify authorization flaws | Execute the same collection with different insertion point files containing various privilege levels | `python3 repl.py --collection "user_api.json" --insertion-point "admin_profile.json"` |
| **OAuth2 Token Capture** | Need to capture and reuse OAuth tokens that expire during testing | Extract tokens from responses and apply them to subsequent requests automatically | `python3 repl.py --collection "oauth_flow.json" --insertion-point "oauth_creds.json" --verbose` |
| **API Key Rotation** | API uses rotating keys that must be captured and reused | Record all requests with key rotation before using Burp Intruder for attacks | `python3 repl.py --collection "key_rotation_api.json" --log --verbose` |
| **Multi-Step API Workflows** | API vulnerabilities require specific request sequencing | Execute requests in the exact defined sequence while sending through Burp for inspection | `python3 repl.py --collection "workflow.json" --insertion-point "attack_vectors.json"` |
| **GraphQL Security Testing** | GraphQL endpoints with nested queries require specific formatting | Maintain query structure and variables while testing through Burp | `python3 repl.py --collection "graphql_api.json" --insertion-point "graphql_vars.json"` |
| **Report Documentation** | Need to document request/response pairs for vulnerability reports | Generate structured logs of all requests and responses in a reportable format | `python3 repl.py --collection "vulnerable_api.json" --log --verbose` |
| **Large API Assessment** | Need to efficiently test hundreds of endpoints in a time-constrained engagement | Execute all requests through any proxy while preserving the exact sequence and context | `python3 repl.py --collection "large_api.json" --verbose` |
| **Token Context Preservation** | Need to maintain authentication state across multiple API calls | Extract and reuse tokens across requests in the correct sequence | `python3 repl.py --collection "stateful_api.json" --log` |
| **Evidence Sharing** | Need to provide reproducible evidence to clients | Generate logs in Postman Collection format that clients can replay | `python3 repl.py --collection "evidence.json" --log --verbose` |
| **XSS Payload Testing** | Need to test XSS payloads with proper encoding for different contexts | Encode payloads using appropriate methods for the target context | `python3 repl.py --encode-html "<script>alert(1)</script>"` |
| **WAF Bypass Testing** | Need to test WAF bypass techniques with various encoding methods | Apply multiple encoding layers to test WAF evasion techniques | `python3 repl.py --encode-double-url "SELECT * FROM users"` |

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
