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

## 🔮 Assumptions

The user operates under the following assumptions:

| Assumption | Description |
|------------|-------------|
| 📁 Collection Location | User has exported a Postman collection to the `/collections` directory of this repository |
| 🧩 Collection Format | The exported collection follows Postman Collection v2.1 format |
| 🔄 Variable Usage | Collection may contain environment variables that need resolution |
| 🌐 Proxy Availability | A proxy (like Burp Suite) is running and accessible |
| 🔒 Authentication | Any required authentication tokens can be provided via environment variables |

## 📋 Table of Contents

- [Postman2Burp](#postman2burp)
  - [🔮 Assumptions](#-assumptions)
  - [📋 Table of Contents](#-table-of-contents)
  - [🎯 Purpose](#-purpose)
  - [📦 Requirements](#-requirements)
  - [🚀 Quick Start](#-quick-start)
  - [✨ Features](#-features)
  - [⚠️ Limitations](#️-limitations)
  - [📚 Documentation](#-documentation)
  - [📜 License](#-license)
  - [👥 Contributing](#-contributing)
    - [Code Style](#code-style)
    - [Bug Reports](#bug-reports)
    - [Feature Requests](#feature-requests)

## 🎯 Purpose

To automate API security testing by:

| Step | Description |
|------|-------------|
| 1️⃣ | Reading Postman collection JSON files |
| 2️⃣ | Parsing all requests (including nested folders) |
| 3️⃣ | Resolving environment variables |
| 4️⃣ | Sending requests through Burp Suite proxy |
| 5️⃣ | Logging results |

## 📦 Requirements

- Python 3.6+
- Required packages (auto-installed):
  - requests
  - urllib3
  - python-dotenv

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/darmado/postman2burp.git
cd postman2burp

# Set up the environment
chmod +x setup_venv.sh
./setup_venv.sh

# Run the tool
python postman2burp.py --collection "your_collection.json"
```

For detailed usage instructions, see the [Wiki](https://github.com/darmado/postman2burp/wiki).

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
| 🔑 Variable Extraction | Extracts variables from collections to create environment templates |

## ⚠️ Limitations

- Limited support for file uploads in multipart/form-data
- No support for WebSocket requests
- No execution of Postman pre-request and test scripts

## 📚 Documentation

Comprehensive documentation is available in the [Wiki](https://github.com/darmado/postman2burp/wiki):

- [Installation Guide](https://github.com/darmado/postman2burp/wiki/Installation)
- [Usage Guide](https://github.com/darmado/postman2burp/wiki/Usage)
- [Advanced Usage](https://github.com/darmado/postman2burp/wiki/Advanced)
- [Configuration Options](https://github.com/darmado/postman2burp/wiki/Configuration)
- [Troubleshooting](https://github.com/darmado/postman2burp/wiki/Troubleshooting)

## 📜 License

This project is licensed under the [Apache License 2.0](LICENSE).

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