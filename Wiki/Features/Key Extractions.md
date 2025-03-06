# Key Extractions

Repl can extract variables from Postman collections to create insertion point templates. This feature helps identify all variables that need values before executing a collection.

## What Are Key Extractions?

Key extractions identify all variables (in the format `{{variable_name}}`) used in a Postman collection, including:

- URL parameters
- Path variables
- Query parameters
- Header values
- Request body content
- Authentication tokens
- Environment variables

## Variable Encoding

Repl supports encoding variables before insertion into requests, useful for security testing and handling special characters.

### Supported Encoding Methods

| Encoding | Description | Example |
|----------|-------------|---------|
| `url` | URL encoding | `Test & Space` → `Test%20%26%20Space` |
| `double_url` | Double URL encoding | `Test & Space` → `Test%2520%2526%2520Space` |
| `html` | HTML entity encoding | `<script>` → `&lt;script&gt;` |
| `xml` | XML encoding | `<tag>` → `&lt;tag&gt;` |
| `unicode` | Unicode escaping | `Café` → `Caf\u00e9` |
| `hex` | Hexadecimal escaping | `ABC` → `\x41\x42\x43` |
| `octal` | Octal escaping | `ABC` → `\101\102\103` |
| `base64` | Base64 encoding | `Test` → `VGVzdA==` |
| `sql_char` | SQL CHAR() function | `ABC` → `CHAR(65,66,67)` |
| `js_escape` | JavaScript escaping | `"test"` → `\"test\"` |
| `css_escape` | CSS escaping | `#test` → `\#test` |

### Using Encoding

Add an `encoding` field to variables in your insertion point template:

```json
{
    "variables": [
        {
            "key": "api_param",
            "value": "test<script>alert(1)</script>",
            "encoding": "html"
        }
    ]
}
```

For multiple encoding iterations, add `encoding_iterations`:

```json
{
    "variables": [
        {
            "key": "param",
            "value": "test&value",
            "encoding": "url",
            "encoding_iterations": 2
        }
    ]
}
```

### Context-Specific Encoding

| Context | Recommended Encoding |
|---------|---------------------|
| URL Parameters | `url` |
| HTML Content | `html` |
| JavaScript | `js_escape` |
| XML/SOAP | `xml` |
| SQL Testing | `sql_char` |
| WAF Bypass | `double_url` or multiple iterations |

## Extracting Keys from Collections

### Basic Extraction

Extract all variables from a collection and create a template file:

```bash
python3 repl.py --collection "api_collection.json" --extract-keys
```

This command:
1. Scans the entire collection for variables
2. Creates a template file in the `profiles` directory
3. Populates the template with all found variables (empty values)

### Display Variables Without Creating a File

To view variables without creating a template file:

```bash
python3 repl.py --collection "api_collection.json" --extract-keys print
```

### Save Template to a Specific Location

To save the template to a specific file:

```bash
python3 repl.py --collection "api_collection.json" --extract-keys "my_template.json"
```

## Interactive Key Extraction

When running extraction without specifying an output file, Repl enters interactive mode:

```bash
python3 repl.py --collection "api_collection.json" --extract-keys
```

In interactive mode, Repl:
1. Displays all found variables
2. Prompts for values for each variable
3. Creates a template with the provided values
4. Saves the template to the `profiles` directory

## Template Structure

The generated template follows this structure:

```json
{
    "variables": [
        {
            "key": "variable_name",
            "value": "variable_value",
            "description": "Description of the variable"
        },
        ...
    ]
}
```

## Common Variables to Extract

Key extraction commonly finds these types of variables:

- **API Keys**: `{{api_key}}`, `{{apiKey}}`
- **Authentication Tokens**: `{{auth_token}}`, `{{bearerToken}}`
- **Base URLs**: `{{base_url}}`, `{{apiEndpoint}}`
- **User Credentials**: `{{username}}`, `{{password}}`
- **Resource IDs**: `{{user_id}}`, `{{order_id}}`
- **Environment Settings**: `{{environment}}`, `{{stage}}`

## Using Extracted Templates

After creating a template and filling in values, use it with the collection:

```bash
python3 repl.py --collection "api_collection.json" --insertion-point "my_template.json"
```

## Best Practices

- Extract keys before running a collection for the first time
- Create different templates for different environments (dev, staging, production)
- Include descriptive comments for each variable
- Store sensitive values securely
- Use consistent naming conventions for variables
- Update templates when the collection changes
- Use appropriate encoding for different contexts when testing security
