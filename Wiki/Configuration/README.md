# Configuration Guide

This guide explains how to configure Repl using configuration files and command-line options.

##

### Configuration File

Repl supports configuration via a `config.json` file, making it easier to maintain consistent settings across multiple runs.

***Location***

The tool looks for a `config.json` file in the `config` directory. If found, it loads settings from this file.

***Sample Configuration File***

```json
{
    "proxy_host": "localhost",
    "proxy_port": 8080,
    "verify_ssl": false,
    "skip_proxy_check": false
}
```

***Available Configuration Options***

| Option | Type | Description |
|--------|------|-------------|
| `proxy_host` | String | The hostname or IP address of the proxy server |
| `proxy_port` | Integer | The port number of the proxy server |
| `verify_ssl` | Boolean | Whether to verify SSL certificates |
| `skip_proxy_check` | Boolean | Whether to skip the proxy connection check |

##

### Creating a Configuration File

You can create a configuration file in two ways:

***1. Manually***

Create a `config.json` file in the `config` directory using the sample above.

***2. Automatically***

Run the script with your desired settings and add the `--save-config` flag:

```bash
python repl.py --collection your_collection.json --proxy-host your-proxy-host --proxy-port 9090 --save-config
```

##

### Command-Line Priority

Command-line arguments always take precedence over configuration file settings. This allows you to:

1. Maintain default settings in the configuration file
2. Override specific settings as needed for individual runs

##

### Usage Examples

***Using Configuration File Only***

```bash
# Assuming config.json exists with your settings
python repl.py --collection your_collection.json
```

***Overriding Configuration File***

```bash
# Override proxy host from config file
python repl.py --collection your_collection.json --proxy-host different-proxy

# Override proxy port from config file
python repl.py --collection your_collection.json --proxy-port 9090
```

***Saving New Configuration***

```bash
# Save current settings to config.json
python repl.py --collection your_collection.json --proxy-host your-proxy --proxy-port 9090 --save-config
```

##

### Environment Variables

Repl also supports environment variables for configuration. These take precedence over the configuration file but are overridden by command-line arguments.

***Supported Environment Variables***

| Environment Variable | Description |
|----------------------|-------------|
| `PROXY_HOST` | Proxy hostname/IP |
| `PROXY_PORT` | Proxy port number |
| `VERIFY_SSL` | Set to "true" to verify SSL certificates |
| `SKIP_PROXY_CHECK` | Set to "true" to skip proxy check |

***Example Usage***

```bash
# Set environment variables
export PROXY_HOST=localhost
export PROXY_PORT=8080

# Run the tool (will use environment variables)
python repl.py --collection your_collection.json
```

##

### Next Steps

- [[Troubleshooting]] 