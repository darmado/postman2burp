# Usage Guide

This guide explains how to use Postman2Burp to send Postman collection requests through Burp Suite proxy.

## Step-by-Step Usage

### 1. Export Your Postman Collection

1. Open Postman
2. Select the collection you want to export
3. Click the three dots (⋮) next to the collection name
4. Select "Export"
5. Choose "Collection v2.1" format
6. Save the JSON file to the `./collections` directory in your Postman2Burp installation

### 2. Extracting Variables

Extract all variables from your collection to create a profile template:

```bash
python postman2burp.py --collection "your_collection.json" --extract-keys
```

This generates a profile file in the `./profiles` directory with a UUID filename (e.g., `f1e8e5b7-dc12-4a1c-9e37-42a7df1f9ef2.json`).

Edit the generated profile file and fill in the values for each variable:

```json
{
  "variables": {
    "base_url": "https://api.example.com",
    "api_key": "your-api-key-here",
    "username": "your-username",
    "password": "your-password"
  }
}
```

### 3. Start Your Proxy

1. Start Burp Suite (or another proxy tool)
2. Ensure the proxy is listening on a port (default is usually localhost:8080)
3. Configure Burp Suite to intercept traffic as needed

### 4. Running the Tool

#### Basic Usage

```bash
python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json"
```

#### With Custom Proxy Settings

```bash
python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json" --proxy localhost:8080
```

#### Skip Proxy Check

Useful if you're sure the proxy is running:

```bash
python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json" --skip-proxy-check
```

#### Save Configuration for Future Use

```bash
python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json" --proxy localhost:8080 --save-config
```

### 5. Review Results in Burp Suite

1. Open the HTTP history tab in Burp Suite
2. You should see all the requests from your Postman collection
3. Analyze the requests and responses for security testing

## Command-Line Options

```
usage: postman2burp.py [-h] --collection COLLECTION [--target-profile ENVIRONMENT]
                       [--extract-keys [OUTPUT_FILE]] [--proxy PROXY] 
                       [--proxy-host PROXY_HOST] [--proxy-port PROXY_PORT]
                       [--verify-ssl] [--skip-proxy-check] [--no-auto-detect]
                       [--output OUTPUT] [--verbose] [--save-config]
```

For more advanced options, see the [Advanced Usage Guide](../Advanced/README.md).

## Next Steps

- [Advanced Usage](../Advanced/README.md)
- [Configuration Options](../Configuration/README.md)
- [Troubleshooting](../Troubleshooting/README.md) 