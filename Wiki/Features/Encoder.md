# Encoder

Repl's encoding module converts values using various methods for security testing and handling special characters.

## Usage

The encoder can be used in two ways:

1. **Command-line encoding**: Encode values directly from the command line
2. **Insertion point encoding**: Apply encoding to variables in insertion point files

## Command-Line Encoding

Encode values directly from the command line:

```bash
# URL encode
python3 repl.py --encode-url "param=value&other=value"

# HTML encode
python3 repl.py --encode-html "<script>alert(1)</script>"

# Base64 encode
python3 repl.py --encode-base64 "username:password"
```

Use cases:
- Generate encoded payloads for testing
- Verify encoding transformations
- Prepare values for other tools

## Supported Encoding Methods

| Encoding | Command | Description | Example |
|----------|---------|-------------|---------|
| URL | `--encode-url` | URL encoding | `Test & Space` → `Test%20%26%20Space` |
| Double URL | `--encode-double-url` | Double URL encoding | `Test & Space` → `Test%2520%2526%2520Space` |
| HTML | `--encode-html` | HTML entity encoding | `<script>` → `&lt;script&gt;` |
| XML | `--encode-xml` | XML encoding | `<tag>` → `&lt;tag&gt;` |
| Unicode | `--encode-unicode` | Unicode escaping | `Café` → `Caf\u00e9` |
| Hex | `--encode-hex` | Hexadecimal escaping | `ABC` → `\x41\x42\x43` |
| Octal | `--encode-octal` | Octal escaping | `ABC` → `\101\102\103` |
| Base64 | `--encode-base64` | Base64 encoding | `Test` → `VGVzdA==` |
| SQL CHAR | `--encode-sql-char` | SQL CHAR() function | `ABC` → `CHAR(65,66,67)` |
| JavaScript | `--encode-js` | JavaScript escaping | `"test"` → `\"test\"` |
| CSS | `--encode-css` | CSS escaping | `#test` → `\#test` |

## Insertion Point Encoding

Apply encoding to variables in insertion point files by adding an `encoding` field:

```json
{
    "variables": [
        {
            "key": "api_param",
            "value": "test<script>alert(1)</script>",
            "encoding": "html"
        },
        {
            "key": "search_query",
            "value": "param=value&other=value",
            "encoding": "url"
        }
    ]
}
```

When using this insertion point file, Repl applies the specified encoding before inserting variables into requests.

### Multiple Encoding Iterations

Apply multiple iterations of the same encoding:

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

This is useful for WAF bypass testing or encoding already encoded values.

## Security Testing Use Cases

### XSS Payload Testing

```bash
# HTML-encoded XSS payload
python3 repl.py --encode-html "<script>alert(document.cookie)</script>"

# JavaScript-escaped payload
python3 repl.py --encode-js "alert('XSS')"
```

### SQL Injection Testing

```bash
# URL encode SQL injection
python3 repl.py --encode-url "' OR 1=1 --"

# SQL CHAR() representation
python3 repl.py --encode-sql-char "SELECT * FROM users"
```

### WAF Bypass Testing

```bash
# Double URL encode
python3 repl.py --encode-double-url "SELECT * FROM users"

# Hex encode
python3 repl.py --encode-hex "<script>alert(1)</script>"
```

## Context-Specific Encoding Recommendations

| Context | Recommended Encoding |
|---------|---------------------|
| URL Parameters | `url` |
| HTML Content | `html` |
| JavaScript | `js_escape` |
| XML/SOAP | `xml` |
| SQL Testing | `sql_char` |
| WAF Bypass | `double_url` or multiple iterations |
| HTTP Headers | `url` |
| JSON Data | `unicode` |
| Basic Auth | `base64` |

## Integration with Other Features

The encoder works with other Repl features:

- **Variable Extraction**: Apply encoding in generated templates
- **Authentication**: Encode credentials or tokens
- **Custom Headers**: Encode header values for testing

## Best Practices

- Use appropriate encoding for the context
- For WAF bypass, try multiple encoding methods or iterations
- For XSS, use HTML encoding for body content and JavaScript encoding for script contexts
- Document successful encoding methods
- Use insertion point encoding for repeatable testing

## Technical Details

Implemented in `encoder.py` with the `Encoder` class and `process_insertion_point` function.

For variable handling details, see [Key Extractions](Key%20Extractions.md). 