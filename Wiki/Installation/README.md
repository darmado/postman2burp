# Installation Guide

This guide explains how to install and set up Postman2Burp on your system.

## Prerequisites

- Python 3.6 or higher
- Git (for cloning the repository)
- Burp Suite or another HTTP proxy

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/darmado/postman2burp.git
cd postman2burp
```

### 2. Set Up the Environment

#### Automated Setup (Recommended)

Run the setup script to create a virtual environment and install dependencies:

```bash
# Make the setup script executable
chmod +x setup_venv.sh

# Run the setup script
./setup_venv.sh
```

#### Manual Setup

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Verify Installation

Verify that the installation was successful by running:

```bash
python postman2burp.py --help
```

You should see the help message with available options.

## Next Steps

After installation, you can:

1. [Export your Postman collection](../Usage/README.md)
2. [Extract variables from your collection](../Usage/README.md#extracting-variables)
3. [Run the tool with your collection and profile](../Usage/README.md#running-the-tool) 