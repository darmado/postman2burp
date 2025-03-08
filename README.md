<h1 align="center">
<br>
<img src="./img/repl.png" atl="Repl - Load and Send Postman Collections through any proxy tool"></a>
<br>
</h1>
<div align="center">

<h1>Replay Postman collections through Burp, ZAP, and any other proxy tool.
</h1>

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Burp Suite](https://img.shields.io/badge/Burp%20Suite-Compatible-orange.svg)](https://portswigger.net/burp)
[![Postman](https://img.shields.io/badge/Postman-v11.35.0-orange.svg)](https://www.postman.com/)
[![Postman Collections](https://img.shields.io/badge/Postman%20Collections-v2.1-orange.svg)](https://schema.getpostman.com/json/collection/v2.1.0/collection.json)

> ⚠️ **Warning**: This tool is currently unstable and under active development. Features may change without notice, and unexpected behavior may occur. Use at your own risk in production environments.

Repl makes it easy to customize and replay API collections from Postman to BurpSuite, ZAP, and any other proxy tool during API security assessments.

</div>



##

<div align="center">

| [Purpose](#-purpose)  | [✨ Features](#-features) | [🎯 Use Cases](#-use-cases) |  [📚 Documentation](#-documentation) | 
|:----------------------:|:------------------------------:|:-------------------------:|:----------------------------:|
| [⚠️ Limitations](#️-limitations) | [📜 License](#-license) | [👥 Contributing](#-contributing) || 

</div>

##


##

### Installation

```bash
curl -fsSL https://raw.githubusercontent.com/darmado/repl/refs/heads/main/install.sh | sh
```

##

### Quick Start Guide

1. **Launch your proxy tool** (Burp Suite, ZAP, etc.)

2. **Export your Postman collection** (Use Collection Format v2.1)
   ```bash
   # Save your collection from Postman as a JSON file
   ```

3. **Run repl with your collection**
   ```bash
   # Extract variables from the collection to a template file
   python repl.py --collection your_collection.json --extract-keys variables.json
   
   # Edit the variables.json file to add your values
   
   # Execute the collection through your proxy
   python repl.py --collection your_collection.json --insertion-point variables.json --proxy 127.0.0.1 8080
   ```

4. **Analyze the results in your proxy tool**

##

### Command-Line Arguments

| Category | Argument | Description |
|----------|----------|-------------|
| **Collection Management** | `--collection [FILE]` | Specify Postman collection file. If no file provided, shows a selection menu. |
| | `--import` | Import collection and create directory structure in 'collections' folder. |
| | `--extract-structure` | Extract collection to a directory structure. |
| **Variables & Configuration** | `--extract-keys [FILE]` | Extract variables from collection. If no file provided, prints to console. |
| | `--insertion-point FILE` | Insert values into API request variables from specified file. |
| **Encoding** | `--encode-base64 [VALUE]` | Encode input as base64. If no value provided, prompts for input. |
| | `--encode-url [VALUE]` | URL-encode input. If no value provided, prompts for input. |
| | `--encode-hex [VALUE]` | Encode input as hex. If no value provided, prompts for input. |
| | `--encode-payloads` | Encode variables in an insertion point file using methods specified in the file. |
| **Request Execution** | `--request-id ID` | Replay a specific request by its ID. Use with --collection. |
| | `--proxy HOST PORT` | Specify proxy server for requests (e.g., 127.0.0.1 8080). |
| | `--header, -H HEADER` | Add custom header to requests. Format: 'Name: Value'. Can be used multiple times. |
| **Authentication** | `--auth [PROFILE]` | Load saved authentication profile. If no profile provided, shows a selection menu. |
| | `--auth-basic USERNAME PASSWORD` | Use HTTP Basic Authentication. |
| | `--auth-bearer TOKEN` | Use Bearer Token Authentication. |
| | `--auth-apikey KEY VALUE IN` | Use API Key Authentication. IN must be 'header' or 'query'. |
| **Analysis** | `--list [TYPE]` | List available configurations. Types: collections, variables, insertion-points, results, auth. |
| | `--show TYPE NAME` | Show details of a specific configuration. Example: --show auth basic/myauth |
| | `--search [QUERY]` | Search logs for requests and responses. Example: --search "status:200" |
| | `--collection-filter COLLECTION` | Filter search results to a specific collection. |
| | `--folder-filter FOLDER` | Filter search results to a specific folder within a collection. |
| **General** | `--banner` | Display the tool banner. |
| | `--verbose, -v` | Enable verbose output for debugging. |
| | `--version` | Show program version and exit. |

For detailed usage instructions, see the [Wiki](https://github.com/darmado/repl/wiki).

##

### ⚠️ Limitations

| Limitation | Description | Workaround |
|------------|-------------|------------|
| **File Uploads** | Limited support for multipart/form-data file uploads | Use base64-encoded content for simple file uploads |
| **WebSocket** | No support for WebSocket connections | Use dedicated WebSocket testing tools |
| **GraphQL** | Basic support for GraphQL queries | Structure GraphQL queries as regular POST requests |
| **OAuth Flows** | Limited support for complex OAuth flows | Use pre-generated tokens when possible |
| **Dynamic Scripts** | No support for Postman pre-request and test scripts | Prepare requests with necessary values beforehand |

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
- [API Security Testing - Burp Suite](https://portswigger.net/burp/documentation/desktop/running-scans/api-scans/)
- [Burp Suite Postman Integration](https://github.com/portswigger/postman-integration)
- [Postman CLI Collection Runner](https://learning.postman.com/docs/postman-cli/postman-cli-run-collection)
- [Python Request Authentication Guide](https://datagy.io/python-requests-authentication/)
- [Awesome API Clients Directory](https://github.com/stepci/awesome-api-clients)



### 📜 License

This project is licensed under the [Apache License 2.0](LICENSE).

##
