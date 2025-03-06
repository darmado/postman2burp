## Introducton

Repl bridges the gap between API development and security testing by automatically sending Postman collection requests through Burp Suite proxy. The tool solves the critical problem of translating existing API test collections into security testing workflows without manual recreation of complex request sequences.

Repl directly addresses these technical challenges:
- Converting Postman's request format to work with Burp Suite's proxy
- Maintaining session state across multi-step API flows
- Substituting environment variables with actual values
- Preserving authentication headers and tokens across requests
- Handling complex data structures in both requests and responses

## Who is Repl For?

Repl serves:

- **Security Engineers** testing APIs for OWASP Top 10 vulnerabilities using existing collections
- **Penetration Testers** who need to analyze API traffic for injection points and authentication bypasses
- **API Developers** validating security fixes without rebuilding test cases
- **DevSecOps Teams** automating security scans in CI/CD pipelines
- **QA Engineers** extending functional tests to include security validation

## Key Use Cases

Repl addresses several critical API security testing challenges:

| Use Case | Problem | Solution |
|----------|---------|----------|
| **OAuth2 Flow Analysis** | Complex authentication flows with token extraction | Maintains request sequence and handles token extraction |
| **GraphQL API Security** | Complex nested queries difficult to recreate | Preserves exact query structure and variables |
| **Anti-CSRF Protection** | Token extraction and reuse across requests | Extracts and applies tokens automatically |
| **Authorization Testing** | Testing with different user contexts | Supports running collections with different insertion points  |
| **API Gateway Testing** | Complex headers and request signing | Preserves all authentication mechanisms |

For detailed examples, code samples, and technical implementation details for each use case, see the [[Use Cases]] documentation.

## Get Started

Ready to enhance your API security testing? Follow these steps to get started with Repl:

1. **Install the Tool**
   
   Clone the repository and set up the environment:
   ```bash
   git clone https://github.com/darmado/repl.git
   cd repl
   ./setup_venv.sh
   ```

2. **Export Your Postman Collection**
   
   Export your collection from Postman in Collection v2.1 format.

3. **Extract Variables**
   
   Generate a insertion point template from your collection:
   ```bash
   python repl.py --collection "your_collection.json" --extract-keys
   ```

4. **Configure Your Environment**
   
   Edit the generated insertion point file with your environment variables.

5. **Run the Tool**
   
   Send your collection through Burp Suite:
   ```bash
   python repl.py --collection "your_collection.json" --insertion-point"your_profile.json" --proxy localhost:8080
   ```

6. **Analyze Results in Burp Suite**
   
   Review the requests and responses in Burp Suite to identify security issues.

For more detailed instructions, see the [[Usage]] guide.