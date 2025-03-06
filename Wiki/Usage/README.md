
## Step-by-Step Usage

### 1. Export Your Postman Collection

1. Open Postman
2. Select the collection you want to export
3. Click the three dots (⋮) next to the collection name
4. Select "Export"
5. Choose "Collection v2.1" format
6. Save the JSON file to the `./collections` directory in your Repl installation

### 2. Extracting Variables

Extract all variables from your collection to create a insertion point template:

```bash
python repl.py --collection "your_collection.json" --extract-keys
```

This generates a insertion point file in the `./profiles` directory with a UUID filename (e.g., `f1e8e5b7-dc12-4a1c-9e37-42a7df1f9ef2.json`).

Edit the generated insertion point file and fill in the values for each variable:

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

** Basic Usage
**
```bash
python repl.py --collection "your_collection.json" --insertion-point"your_profile.json"
```

#### With Custom Proxy Settings

```bash
python repl.py --collection "your_collection.json" --insertion-point"your_profile.json" --proxy localhost:8080
```

** Skip Proxy Check
**
Useful if you're sure the proxy is running:

```bash
python repl.py --collection "your_collection.json" --insertion-point"your_profile.json" --skip-proxy-check
```

** Save Configuration for Future Use
**
```bash
python repl.py --collection "your_collection.json" --insertion-point"your_profile.json" --proxy localhost:8080 --save-config
```

### 5. Review Results in Burp Suite

1. Open the HTTP history tab in Burp Suite
2. You should see all the requests from your Postman collection
3. Analyze the requests and responses for security testing

## Command-Line Options

```
usage: repl.py [-h] --collection COLLECTION [--insertion-pointENVIRONMENT]
                       [--extract-keys [OUTPUT_FILE]] [--proxy PROXY] 
                       [--proxy-host PROXY_HOST] [--proxy-port PROXY_PORT]
                       [--verify-ssl] [--skip-proxy-check] [--no-auto-detect]
                       [--output OUTPUT] [--verbose] [--save-config]
```

For more features and options, see the [[Features|Additional Features]] guide.

## Next Steps

- [[Features|Additional Features]]
- [[Configuration]]
- [[Troubleshooting]] 