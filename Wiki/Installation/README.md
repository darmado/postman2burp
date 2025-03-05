# Installation Guide

This guide explains how to install and set up Repl on your system.

## Prerequisites

- Python 3.6 or higher
- Git (for cloning the repository)
- Burp Suite or another HTTP proxy

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/darmado/repl.git
cd repl
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
python repl.py --help
```

You should see the help message with available options.

## Next Steps

After installation, you can:

1. [[Usage|Export your Postman collection]]
2. [[Usage#extracting-variables|Extract variables from your collection]]
3. [[Usage#running-the-tool|Run the tool with your collection and profile]] 