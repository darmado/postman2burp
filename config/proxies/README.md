# Configuration Files

contains configuration files for the repl tool. Each configuration file is designed for a specific API testing scenario.

## Configuration Structure

Each configuration file is a JSON file with the following structure:

```json
{
    "proxy_host": "localhost",
    "proxy_port": 8080,
    "verify_ssl": false,
    "auto_detect_proxy": true,
    "verbose": true,
    "log": true,
    "collection": "path/to/collection.json",
    "target_profile": "path/to/profile.json",
    "save_config": false
}
```

## Configuration Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `proxy_host` | string | The hostname or IP address of the proxy server (e.g., Burp Suite, ZAP) |
| `proxy_port` | integer | The port number of the proxy server |
| `verify_ssl` | boolean | Whether to verify SSL certificates when making requests |
| `auto_detect_proxy` | boolean | Whether to automatically detect running proxy servers |
| `verbose` | boolean | Whether to display detailed output during execution |
| `log` | boolean | Whether to save logs to a file |
| `collection` | string | Path to the Postman collection file |
| `target_profile` | string | Path to the insertion point file containing variables |
| `save_config` | boolean | Whether to save the current configuration for future use |

## Available Configurations

### E-commerce API (`config_ecommerce.json`)
Configuration for testing e-commerce endpoints using:
- Collection: `collections/ecommerce_api.json`
- Profile: `profiles/ecommerce_profile.json`
- Proxy: `localhost:8080`

### Weather API (`config_weather.json`)
Configuration for testing weather service endpoints using:
- Collection: `collections/weather_api.json`
- Profile: `profiles/weather_profile.json`
- Proxy: `127.0.0.1:8090`

### Social Media API (`config_social.json`)
Configuration for testing social media platform endpoints using:
- Collection: `collections/social_media_api.json`
- Profile: `profiles/social_profile.json`
- Proxy: `localhost:8081`

### Banking API (`config_banking.json`)
Configuration for testing banking service endpoints using:
- Collection: `collections/banking_api.json`
- Profile: `profiles/banking_profile.json`
- Proxy: `127.0.0.1:8888`

### Healthcare API (`config_healthcare.json`)
Configuration for testing healthcare service endpoints using:
- Collection: `collections/healthcare_api.json`
- Profile: `profiles/healthcare_profile.json`
- Proxy: `127.0.0.1:9091`

### Security Testing API (`config_security.json`)
Configuration for testing security vulnerabilities using:
- Collection: `collections/security_testing_api.json`
- Profile: `profiles/security_profile.json`
- Proxy: `localhost:9090`

## Using Configurations

Configurations can be used with the repl tool in several ways:

1. Specified directly via command line:
   ```bash
   python repl.py --config config/config_ecommerce.json
   ```

2. Selected through the interactive menu:
   ```bash
   python repl.py --config select
   ```

## Customizing Configurations

You can customize these configurations by:
1. Editing the JSON file directly
2. Using command-line arguments to override specific settings:
   ```bash
   python repl.py --config config/config_ecommerce.json --proxy localhost:9090 --verbose
   ```

## Creating New Configurations

To create a new configuration:
1. Copy an existing configuration that's closest to your needs
2. Modify the parameters to match your requirements
3. Save it with a descriptive name (e.g., `config_my_api.json`)

You can also create a configuration from command-line arguments and save it:
```bash
python repl.py --collection your_collection.json --insertion-pointyour_profile.json --proxy localhost:8080 --save-config
``` 