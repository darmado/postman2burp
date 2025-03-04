# Advanced Usage

This guide covers advanced features and usage patterns for Postman2Burp.

## Verbose Output

For detailed logging, add the `--verbose` flag:

```bash
python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json" --verbose
```

This provides detailed information about:
- Variable substitution
- Request processing
- Proxy detection
- Response status

## Saving Results to a File

Use the `--output` option to save results to a file:

```bash
python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json" --output results.json
```

The output file contains:
- Request details
- Response status codes
- Execution time
- Error messages (if any)

## Proxy Settings

### Custom Proxy Configuration

Specify a custom proxy using one of these methods:

```bash
# Method 1: Combined host:port format
python postman2burp.py --collection "your_collection.json" --proxy localhost:8080

# Method 2: Separate host and port
python postman2burp.py --collection "your_collection.json" --proxy-host localhost --proxy-port 8080
```

### Proxy Auto-Detection

The tool automatically detects running proxies on common ports when no proxy is specified. This behavior occurs when:

1. No proxy is specified in the command line
2. No proxy is specified in the configuration file

When you explicitly specify a proxy (either via command line or configuration file), the tool respects your settings and does not attempt auto-detection.

### SSL Verification

By default, SSL certificate verification is disabled. To enable it:

```bash
python postman2burp.py --collection "your_collection.json" --verify-ssl
```

## Working with Variables

### Variable Extraction

Extract all variables from a collection:

```bash
python postman2burp.py --collection "your_collection.json" --extract-keys
```

### Variable Substitution

The tool automatically substitutes variables in:
- URL paths
- Query parameters
- Headers
- Request bodies (JSON, form data, etc.)

## Handling Complex Collections

### Nested Folders

The tool processes all requests in nested folders automatically. No special configuration is needed.

### Authentication Flows

For collections that require authentication:

1. Ensure authentication requests are included in the collection
2. Place authentication requests before dependent requests
3. Provide necessary authentication variables in the profile

## Batch Processing

Process multiple collections sequentially:

```bash
for collection in ./collections/*.json; do
  python postman2burp.py --collection "$collection" --target-profile "your_profile.json"
done
```

## Integration with CI/CD

For integration with CI/CD pipelines:

```bash
# Example Jenkins pipeline step
stage('API Security Scan') {
  steps {
    sh 'python postman2burp.py --collection "api_collection.json" --target-profile "ci_profile.json" --proxy ${BURP_PROXY} --output scan_results.json'
  }
}
```

## Binary Compilation

For information on compiling Postman2Burp into a standalone binary executable, see the [Binary Compilation Guide](binary-compilation.md).

## Next Steps

- [Configuration Options](../Configuration/README.md)
- [Troubleshooting](../Troubleshooting/README.md) 