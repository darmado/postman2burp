# Configuration Options

Postman2Burp now supports configuration via a `config.json` file, making it easier to maintain consistent settings across multiple runs.

## Configuration File

The tool looks for a `config.json` file in the same directory as the script. If found, it loads settings from this file. Command-line arguments always take precedence over configuration file settings.

### Sample config.json

```json
{
    "proxy_host": "localhost",
    "proxy_port": 8080,
    "verify_ssl": false,
    "skip_proxy_check": false
}
```

### Available Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `proxy_host` | String | The hostname or IP address of the proxy server |
| `proxy_port` | Integer | The port number of the proxy server |
| `verify_ssl` | Boolean | Whether to verify SSL certificates |
| `skip_proxy_check` | Boolean | Whether to skip the proxy connection check |

## Creating a Configuration File

You can create a configuration file in two ways:

1. **Manually**: Create a `config.json` file in the same directory as the script using the sample above.

2. **Automatically**: Run the script with your desired settings and add the `--save-config` flag:
   ```bash
   python postman2burp.py --collection your_collection.json --proxy-host your-proxy-host --proxy-port 9090 --save-config
   ```

## Command-Line Priority

Command-line arguments always take precedence over configuration file settings. This allows you to:

1. Maintain default settings in the configuration file
2. Override specific settings as needed for individual runs

## Usage Examples

### Using Configuration File Only

```bash
# Assuming config.json exists with your settings
python postman2burp.py --collection your_collection.json
```

### Overriding Configuration File

```bash
# Override proxy host from config file
python postman2burp.py --collection your_collection.json --proxy-host different-proxy

# Override proxy port from config file
python postman2burp.py --collection your_collection.json --proxy-port 9090
```

### Saving New Configuration

```bash
# Save current settings to config.json
python postman2burp.py --collection your_collection.json --proxy-host your-proxy --proxy-port 9090 --save-config
``` 