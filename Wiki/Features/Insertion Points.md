# Insertion Point Templates

 Repl uses insertion points to insert payloads into Postman collection variables. Insertion point templates help testers organize and reuse payloads across different API endpoints without the need to edit, disable, or enable specific proxy profile settings. 

## Template Structure

Each insertion point is a JSON file with the following structure: 

```json
{
  "name": "DOGGE",
  "values": [
    {
      "key": "base_url",
      "value": "https://api.doge.com",
      "enabled": true,
      "description": "Base URL for the API"
    },
    {
      "key": "parameter",
      "value": "some_value",
      "enabled": true,
      "encoding": "unicode",
      "description": "API key for authentication"
    }
  ]
}

```

## Using Insertion Points

You can use insertion points with the repl tool in several ways:

1. Directly via command line:
 ```bash
   python3 repl.py --collection collections/api_collection.json --insertion-point profiles/variables.json
 ```

2. Selected through the interactive menu:
 ```bash
   python3 repl.py
 ```

## Creating Insertion Points

### Automatic Extraction

Extract variables from an existing collection:
```bash
python3 repl.py --collection your_collection.json --extract-keys
```

This creates a template with all variables found in the collection.

### Manual Creation

1. Create a JSON file with the structure shown above
2. Add variables that match the ones in your collection
3. Save it in the `profiles` directory with a descriptive name

## Customizing Insertion Points

Customize insertion points by:
1. Editing variable values to match your testing needs
2. Adding new variables for your specific API
3. Removing variables that aren't needed

## Common Use Cases

- Testing with different API keys
- Switching between environments (dev, staging, production)
- Testing with different user credentials
- Customizing request parameters for specific test scenarios 