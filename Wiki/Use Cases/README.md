# Use Cases

This document provides detailed examples of how Postman2Burp solves specific API security testing challenges.

## OAuth2 Flow Analysis

**Problem:**  
OAuth2 authentication flows involve multiple sequential requests with token extraction and reuse. Testing these flows manually is error-prone because:

- Access tokens must be extracted from responses
- Tokens must be correctly formatted and inserted into subsequent requests
- Token expiration and refresh flows must be handled
- The entire sequence must be maintained in the correct order

**Solution:**  
Postman2Burp automatically:

1. Sends the initial authentication request
2. Extracts access tokens, refresh tokens, and other OAuth parameters from responses
3. Substitutes these tokens into subsequent requests
4. Maintains the entire authentication flow sequence

**Example:**

```bash
python postman2burp.py --collection "oauth_flow.json" --target-profile "oauth_creds.json" --verbose
```

**Sample Collection Structure:**

```json
{
  "item": [
    {
      "name": "Get Authorization Code",
      "request": {
        "method": "GET",
        "url": "{{auth_server}}/authorize?client_id={{client_id}}&response_type=code&redirect_uri={{redirect_uri}}"
      }
    },
    {
      "name": "Exchange Code for Token",
      "request": {
        "method": "POST",
        "url": "{{auth_server}}/token",
        "body": {
          "mode": "urlencoded",
          "urlencoded": [
            {"key": "grant_type", "value": "authorization_code"},
            {"key": "code", "value": "{{auth_code}}"},
            {"key": "client_id", "value": "{{client_id}}"},
            {"key": "client_secret", "value": "{{client_secret}}"},
            {"key": "redirect_uri", "value": "{{redirect_uri}}"}
          ]
        }
      }
    },
    {
      "name": "Access Protected Resource",
      "request": {
        "method": "GET",
        "url": "{{api_url}}/protected-resource",
        "header": [
          {"key": "Authorization", "value": "Bearer {{access_token}}"}
        ]
      }
    }
  ]
}
```

**Console Output:**

```
[INFO] Processing collection: oauth_flow.json
[INFO] Using proxy: localhost:8080
[INFO] Sending request: GET /authorize?client_id=myclient&response_type=code&redirect_uri=https://example.com/callback
[INFO] Response received: 302 Found
[INFO] Extracted auth_code from response: SplxlOBeZQQYbYS6WxSbIA
[INFO] Sending request: POST /token
[INFO] Response received: 200 OK
[INFO] Extracted access_token from response: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
[INFO] Extracted refresh_token from response: 8xLOxBtZp8
[INFO] Extracted expires_in from response: 3600
[INFO] Sending request: GET /protected-resource
[INFO] Substituted {{access_token}} in Authorization header
[INFO] Response received: 200 OK
[INFO] Completed processing collection
```

## GraphQL API Security Testing

**Problem:**  
GraphQL APIs present unique security testing challenges:

- Requests contain complex nested queries that are difficult to manually recreate
- Variables need to be properly substituted
- Query structure must be preserved exactly
- Introspection queries require special handling

**Solution:**  
Postman2Burp:

1. Preserves the exact structure of GraphQL queries
2. Properly formats query variables
3. Maintains introspection queries
4. Ensures all GraphQL-specific headers are included

**Example:**

```bash
python postman2burp.py --collection "graphql_api.json" --target-profile "graphql_vars.json"
```

**Sample GraphQL Request:**

```json
{
  "name": "Get User Data",
  "request": {
    "method": "POST",
    "url": "{{api_url}}/graphql",
    "header": [
      {"key": "Content-Type", "value": "application/json"}
    ],
    "body": {
      "mode": "raw",
      "raw": "{\"query\":\"query GetUserData($userId: ID!) { user(id: $userId) { id name email permissions { code description } } }\",\"variables\":{\"userId\":\"{{user_id}}\"}}"
    }
  }
}
```

## Anti-CSRF Protection Testing

**Problem:**  
APIs with anti-CSRF protection require:

- Extracting CSRF tokens from responses
- Including these tokens in subsequent requests
- Maintaining the correct sequence of requests
- Handling different token formats and locations

**Solution:**  
Postman2Burp:

1. Extracts CSRF tokens from response headers, cookies, or body
2. Automatically applies these tokens to follow-up requests
3. Maintains the correct request sequence

**Example:**

```bash
python postman2burp.py --collection "secured_workflow.json" --target-profile "test_env.json" --verbose
```

**Console Output:**

```
[INFO] Processing collection: secured_workflow.json
[INFO] Using proxy: localhost:8080
[INFO] Sending request: GET /form
[INFO] Response received: 200 OK
[INFO] Extracted csrf_token from response body: a8c3e5f7d9b1c4e2
[INFO] Sending request: POST /submit-form
[INFO] Substituted {{csrf_token}} in X-CSRF-Token header
[INFO] Response received: 302 Found
[INFO] Completed processing collection
```

## Broken Object Level Authorization Testing

**Problem:**  
Testing for BOLA/IDOR vulnerabilities requires:

- Sending identical requests with different user contexts
- Comparing responses to identify unauthorized access
- Maintaining complex request sequences
- Testing across multiple endpoints

**Solution:**  
Postman2Burp allows:

1. Running the same collection with different profile files
2. Saving results to output files for comparison
3. Maintaining the exact request structure across runs

**Example:**

```bash
# Run with admin credentials
python postman2burp.py --collection "user_management.json" --target-profile "admin_profile.json" --output "admin_results.json"

# Run with regular user credentials
python postman2burp.py --collection "user_management.json" --target-profile "user_profile.json" --output "user_results.json"
```

**Sample Comparison Script:**

```python
import json
import sys

def compare_responses(admin_file, user_file):
    with open(admin_file) as f:
        admin_results = json.load(f)
    
    with open(user_file) as f:
        user_results = json.load(f)
    
    for admin_req, user_req in zip(admin_results, user_results):
        if admin_req['url'] == user_req['url'] and admin_req['method'] == user_req['method']:
            if admin_req['status_code'] == user_req['status_code'] == 200:
                print(f"Potential BOLA vulnerability: {admin_req['method']} {admin_req['url']}")
                print(f"Both admin and regular user received 200 OK response")
                
                # Compare response content
                admin_data = json.loads(admin_req['response'])
                user_data = json.loads(user_req['response'])
                
                if admin_data == user_data:
                    print("CRITICAL: Identical response data returned to both users")
                else:
                    print("Different response data returned")
                
                print("---")

if __name__ == "__main__":
    compare_responses(sys.argv[1], sys.argv[2])
```

## API Gateway Configuration Testing

**Problem:**  
API gateways often require:

- Specific headers and API keys
- Request signing (e.g., AWS SigV4)
- Complex authentication mechanisms
- Special formatting for request parameters

**Solution:**  
Postman2Burp:

1. Maintains all headers and authentication mechanisms
2. Preserves request signing generated by pre-request scripts
3. Ensures proper formatting of all request components

**Example:**

```bash
python postman2burp.py --collection "aws_api.json" --target-profile "aws_creds.json"
```

**Sample AWS API Gateway Request:**

```json
{
  "name": "Get S3 Objects",
  "request": {
    "method": "GET",
    "url": "{{s3_endpoint}}/{{bucket_name}}",
    "header": [
      {"key": "Host", "value": "{{s3_host}}"},
      {"key": "X-Amz-Date", "value": "{{amz_date}}"},
      {"key": "X-Amz-Content-Sha256", "value": "{{content_sha256}}"},
      {"key": "Authorization", "value": "{{authorization}}"}
    ]
  }
}
```

The collection includes pre-request scripts that generate AWS SigV4 signatures, and Postman2Burp preserves these signatures in the requests sent to Burp Suite.
