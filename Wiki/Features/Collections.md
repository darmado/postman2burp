            # Collections

Repl works with Postman collections to execute API requests through proxy tools. This page explains how to use and manage collections.

## Supported Collection Format

Repl supports Postman Collection Format v2.1, which includes:
- Folders and subfolders
- All HTTP methods (GET, POST, PUT, DELETE, etc.)
- Request bodies (raw, form-data, urlencoded)
- Variables and environments
- Pre-request and test scripts (these are ignored during execution)

## Using Collections

### Specify a Collection

```bash
python3 repl.py --collection "path/to/collection.json"
```

### Interactive Selection

Run without specifying a collection to select interactively:

```bash
python3 repl.py
```

## Collection Organization

Collections are stored in the `collections` directory. The tool automatically creates this directory if it doesn't exist.

Repl organizes files in a structured directory layout:

```
repl/
├── collections/     # Postman collection files
├── profiles/        # Insertion point templates
├── logs/            # Request/response logs
└── config/          # Configuration files
```

## Variable Handling

### Extract Variables

Extract all variables from a collection:

```bash
python3 repl.py --collection "api_collection.json" --extract-keys
```

This creates a template file with all variables found in the collection.

### Print Variables

Display all variables without creating a file:

```bash
python3 repl.py --collection "api_collection.json" --extract-keys print
```

## Collection Processing

When processing a collection, Repl:

1. Loads the collection file
2. Validates the collection format
3. Extracts all requests (including those in folders)
4. Replaces variables with values from the insertion point
5. Sends each request through the configured proxy
6. Records the results (if logging is enabled)

## Best Practices

- Keep collections organized with folders for related endpoints
- Use descriptive names for requests
- Use variables for values that change between environments
- Document request parameters in the collection
- Keep collections up-to-date with the API
