<h1 align="center">
<br>
<img src="./img/repl.png" atl="Repl - Load and Send Postman Collections through any proxy tool"></a>
<br>
</h1>
<div align="center">

<h1>Modify, load,  and replay Postman collections through any proxy tool in seconds.
</h1>

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Burp Suite](https://img.shields.io/badge/Burp%20Suite-Compatible-orange.svg)](https://portswigger.net/burp)
[![Postman](https://img.shields.io/badge/Postman-v11.35.0-orange.svg)](https://www.postman.com/)
[![Postman Collections](https://img.shields.io/badge/Postman%20Collections-v2.1-orange.svg)](https://schema.getpostman.com/json/collection/v2.1.0/collection.json)


Repl makes it easy to modify, load, and replay Postman collections through any proxy tool.

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

### Setup your Workspace:
0. Launch your proxy 

**1. Export our postman collection. Use Schema 2.1** [from Postman](https://learning.postman.com/docs/getting-started/importing-and-exporting/exporting-data/)

**2. Move your Postman collections directory.** 

  ```bash
   mv postman_collection.json ./repl/collections/
   ```
   `./collections` 
   
**3. Exract keys from the Postman collection. The interactive prompt helps you **replace and store new parameter values** in the `./profiles` directory.**

```bash
python3 repl.py --collection  postmanCollection.json --extract-keys 
```

**1. Excute Repl**

```bash
python3 repl.py --collection "postman_collection.json" --insertion-point"f1e8e5b7-dc12-4a1c-9e37-42a7df1f9ef2_1741124383.json"
```

##

### Other Options

```bash
options:
  -h, --help            show this help message and exit
  --collection [COLLECTION]
                        Path to Postman collection JSON file (supports Postman 2.1 schema). Specify no path to select interactively.

Profile Options:
  --insertion-pointinsertion_point
                        Path to insertion point JSON file with values to replace variables in the collection
  --extract-keys [OUTPUT_FILE]
                        Extract variables from collection. Specify no file to enter interactive mode. Specify 'print' to display variables.
                        Specify a filename to save template.

Authentication Options:
  --auth [AUTH]         Use a saved authentication profile. Specify no value to select interactively.
  --auth-basic USERNAME PASSWORD
                        Use Basic Authentication with the specified username and password
  --auth-bearer TOKEN   Use Bearer Token Authentication with the specified token
  --auth-api-key KEY LOCATION
                        Use API Key Authentication with the specified key and location (header, query, or cookie)
  --auth-api-key-name NAME
                        Name of the API Key header/parameter/cookie (default: X-API-Key)
  --create-auth         Create a new authentication profile interactively
  --list-auth           List available authentication profiles

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

Proxy Insertion Points:
  -insertion point [PROFILE]    Use specific proxy insertion point or select from available insertion points  if no file specified. Omit to select when multiple profiles
                        exist.

Custom Headers:
  --header HEADER       Add custom header in format 'Key:Value'. Can be specified multiple times. These headers will be added to all requests and
                        will override any existing headers with the same name. Example: --header 'X-API-Key:12345' --header 'User-
                        Agent:PostmanToBurp'
```


For detailed usage instructions, see the [Wiki](https://github.com/darmado/repl/wiki).

##

### ✨ Features

| Feature | Command-line Arguments | Description |
|---------|------------------------|-------------|
| 🔍 Proxy Auto-detection | `--proxy-host`, `--proxy-port` | Detects running proxies on ports 8080, 8081, and 8082 when no proxy is specified |
| 🔄 Custom Proxy Configuration | `--proxy host:port` | Specifies proxy in combined host:port format |
| 💾 Proxy Profile Management | `--proxy-config [PROFILE]` | Loads and saves proxy configurations for reuse |
| 🔐 Variable Replacement | `--insertion-pointPROFILE` | Replaces Postman variables with values from specified insertion point |
| 🔑 Variable Extraction | `--extract-keys [OUTPUT_FILE]` | Extracts variables from collections to create insertion point templates |
| 🔒 Authentication | `--auth`, `--auth-basic`, `--auth-bearer`, `--auth-api-key` | Supports multiple authentication methods including Basic Auth, Bearer Token, and API Key |
| 📊 Request Logging | `--log`, `--verbose` | Records detailed request/response data to the logs directory |
| 🧩 Interactive Mode | Run without arguments | Provides interactive prompts for collection and insertion point selection |
| 🔍 Proxy Verification | Automatic | Validates proxy connectivity before executing requests |
| 🔤 Custom Headers | `--header KEY:VALUE` | Adds specified headers to all requests in the collection |
| 🔒 SSL Verification | `--verify-ssl` | Enables SSL certificate verification for secure connections |

##

### 🎯 Use Cases

| Scenario | Challenge | Solution | Example Command |
|----------|-----------|----------|-----------------|
| **Client-Provided API Collection** | Client provides a 200+ endpoint Postman collection for an enterprise API during a time-limited assessment | Replay all endpoints through any proxy while maintaining request sequence and context | `python3 repl.py --collection "enterprise_api.json" --extract-keys` |
| **Privilege Escalation Testing** | Need to test API endpoints with admin, user, and guest credentials to identify authorization flaws | Execute the same collection with different insertion point files containing various privilege levels | `python3 repl.py --collection "user_api.json" --insertion-point"admin_profile.json"` |
| **OAuth2 Token Capture** | Need to capture and reuse OAuth tokens that expire during testing | Extract tokens from responses and apply them to subsequent requests automatically | `python3 repl.py --collection "oauth_flow.json" --insertion-point"oauth_creds.json" --verbose` |
| **API Key Rotation** | API uses rotating keys that must be captured and reused | Record all requests with key rotation before using Burp Intruder for attacks | `python3 repl.py --collection "key_rotation_api.json" --log --verbose` |
| **Multi-Step API Workflows** | API vulnerabilities require specific request sequencing | Execute requests in the exact defined sequence while sending through Burp for inspection | `python3 repl.py --collection "workflow.json" --insertion-point"attack_vectors.json"` |
| **GraphQL Security Testing** | GraphQL endpoints with nested queries require specific formatting | Maintain query structure and variables while testing through Burp | `python3 repl.py --collection "graphql_api.json" --insertion-point"graphql_vars.json"` |
| **Report Documentation** | Need to document request/response pairs for vulnerability reports | Generate structured logs of all requests and responses in a reportable format | `python3 repl.py --collection "vulnerable_api.json" --log --verbose` |
| **Large API Assessment** | Need to efficiently test hundreds of endpoints in a time-constrained engagement | Execute all requests through any proxy while preserving the exact sequence and context | `python3 repl.py --collection "large_api.json" --verbose` |
| **Token Context Preservation** | Need to maintain authentication state across multiple API calls | Extract and reuse tokens across requests in the correct sequence | `python3 repl.py --collection "stateful_api.json" --log` |
| **Evidence Sharing** | Need to provide reproducible evidence to clients | Generate logs in Postman Collection format that clients can replay | `python3 repl.py --collection "evidence.json" --log --verbose` |

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
