# Additional Features

This guide covers additional features and techniques for getting the most out of Postman2Burp.

## Batch Processing

Process multiple collections at once using shell scripting:

```bash
for collection in ./collections/*.json; do
  python postman2burp.py --collection "$collection" --target-profile "your_profile.json"
done
```

## Custom Proxy Configuration

### Combined Host:Port Format

```bash
python postman2burp.py --collection "your_collection.json" --proxy 127.0.0.1:8888
```

### Separate Host and Port

```bash
python postman2burp.py --collection "your_collection.json" --proxy-host 127.0.0.1 --proxy-port 8888
```

## SSL Verification

Enable SSL certificate verification (disabled by default):

```bash
python postman2burp.py --collection "your_collection.json" --verify-ssl
```

## Output Saving

Save request and response details to a JSON file for later analysis:

```bash
python postman2burp.py --collection "your_collection.json" --output "results.json"
```

The output file contains an array of request/response pairs with details like:
- URL
- Method
- Headers
- Request body
- Response status
- Response body
- Timing information

## Configuration Management

### Saving Configuration

Save your current settings to the config file for future use:

```bash
python postman2burp.py --collection "your_collection.json" --proxy localhost:8080 --save-config
```

### Loading Configuration

The tool automatically loads settings from `config.json` if it exists. You can override specific settings with command-line arguments:

```bash
# Uses proxy from config.json but specifies a different collection
python postman2burp.py --collection "different_collection.json"
```

## CI/CD Integration

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    stages {
        stage('Security Testing') {
            steps {
                sh '''
                # Clone the repository
                git clone https://github.com/darmado/postman2burp.git
                cd postman2burp
                
                # Set up environment
                python -m venv venv
                source venv/bin/activate
                pip install -r requirements.txt
                
                # Start Burp Suite in headless mode (requires Burp Suite Professional)
                java -jar burpsuite_pro.jar --headless --project-file=project.burp &
                sleep 10  # Wait for Burp to start
                
                # Run Postman2Burp
                python postman2burp.py --collection "../api_collection.json" --proxy localhost:8080 --output "results.json"
                
                # Optional: Process results
                python process_results.py results.json
                '''
            }
        }
    }
}
```

## Environment Variables

Use environment variables in your profile file:

```json
{
  "variables": {
    "api_key": "${API_KEY}",
    "username": "${USERNAME}",
    "password": "${PASSWORD}"
  }
}
```

Then set these environment variables before running the tool:

```bash
export API_KEY="your-api-key"
export USERNAME="your-username"
export PASSWORD="your-password"
python postman2burp.py --collection "your_collection.json" --target-profile "your_profile.json"
```

## Handling Large Collections

For large collections, you can:

1. Split the collection into smaller files
2. Use the `--output` flag to save results for each run
3. Process collections in parallel (in separate terminals)

```bash
# Terminal 1
python postman2burp.py --collection "part1.json" --output "results1.json"

# Terminal 2
python postman2burp.py --collection "part2.json" --output "results2.json"
```

## Next Steps

- [[Configuration]]
- [[Troubleshooting]]
- [[Use Cases]] 