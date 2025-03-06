# Workflows

Repl preserves the sequence of requests in Postman collections, allowing you to execute multi-step API workflows through proxy tools.

## What Are API Workflows?

API workflows are HTTP request sequences that make organizing your security test cases and collection replays easier. 

- Authentication followed by data operations
- Creating a resource and then modifying it
- Multi-step business processes
- Session-based interactions
- System integrations

## How Repl Handles Workflows

Repl processes collection requests in the exact order they appear in the collection:

1. Maintains request sequence as defined in the collection
2. Preserves folder structure and organization
3. Respect parent-child relationships between requests
4. Passes data between requests using variables

## Benefits for API Testing

- Execute complete API flows through proxy tools
- Maintain context and state between requests
- Preserve authentication across multiple endpoints
- Test complex business processes end-to-end
- Validate multi-step operations in sequence

## Best Practices for Collection Organization

Structure your Postman collection to reflect logical workflows:

- Group-related requests in folders
- Name requests to indicate their sequence
- Add descriptions to document dependencies
- Use variables to pass data between requests

### Example Workflow Structure

```
Authentication
├── Login
├── Get User Profile
Data Operations
├── List Items
├── Create Item
├── Update Item
├── Delete Item
```

## Variable Usage in Workflows

Variables are essential for maintaining state across requests:

- Store authentication tokens from login responses
- Save resource IDs from creation responses
- Track session information across requests
- Pass data between different steps in the workflow

## Common Workflow Examples

### Authentication Flow

1. Send credentials to obtain an authentication token
2. Store the token in a variable
3. Use token in subsequent request headers
4. Refresh the token when needed

### Resource Management

1. Create a resource and capture its ID
2. Use the ID to retrieve the resource details
3. Modify the resource with an update request
4. Verify changes with another GET request
5. Delete the resource when finished

### Business Process

1. Create an order (capture order ID)
2. Add items to the order (using order ID)
3. Apply for discounts or promotions
4. Process payment
5. Generate invoice or receipt

## Executing Workflows with Repl

```bash
python3 repl.py --collection "workflow_collection.json" --insertion-point "variables.json" --log
```

This executes all requests in the collection in sequence, replacing variables with values from the insertion point file, and logs the results for analysis.

## Proxy Configuration for Workflows

Repl supports routing workflow requests through proxy tools with several configuration options:

```bash
# Specify proxy directly
python3 repl.py --collection "workflow_collection.json" --proxy 127.0.0.1:8080

# Specify host and port separately
python3 repl.py --collection "workflow_collection.json" --proxy-host 127.0.0.1 --proxy-port 8080

# Save proxy settings for reuse
python3 repl.py --collection "workflow_collection.json" --proxy 127.0.0.1:8080 --save-proxy
```

If no proxy is specified, Repl automatically detects running proxies on common ports (8080, 8081, 8082).

## Integration with Security Testing

Workflows can be integrated into security testing processes:

- **Automation**: Use in CI/CD pipelines for API security testing
- **Batch Processing**: Process multiple workflow collections sequentially
- **Custom Headers**: Add security testing headers to all requests in a workflow
- **Proxy Chaining**: Route workflow requests through multiple security tools

Example of integrating workflows in a CI/CD pipeline:

```bash
# Example CI/CD script
#!/bin/bash
# Clone the repository
git clone https://github.com/your-org/api-tests.git
cd api-tests

# Install Repl
pip install -r requirements.txt

# Run authentication workflow through proxy
python3 repl.py --collection "auth_workflow.json" --insertion-point "prod_creds.json" --proxy 127.0.0.1:8080 --log

# Run data manipulation workflow
python3 repl.py --collection "data_workflow.json" --insertion-point "test_data.json" --proxy 127.0.0.1:8080 --log

# Analyze logs for security issues
python3 analyze_logs.py --directory logs/
```

For detailed implementation examples, see the Function Map documentation.
