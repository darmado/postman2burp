# Logging

Repl provides comprehensive logging capabilities to record request and response details for analysis and troubleshooting.

## Enabling Logging

Enable logging to file:

```bash
python3 repl.py --collection "api_collection.json" --log
```

Enable verbose logging (displays detailed information in the console):

```bash
python3 repl.py --collection "api_collection.json" --verbose
```

Use both for maximum detail:

```bash
python3 repl.py --collection "api_collection.json" --log --verbose
```

## Log File Location

Log files are stored in the `logs` directory with timestamps in the filename:

```
logs/repl_YYYYMMDD_HHMMSS.log
```

## Log Contents

Each log file contains:

1. **Session Information**
   - Collection name and ID
   - Proxy configuration
   - Command-line arguments

2. **Request Details**
   - URL
   - Method
   - Headers
   - Body (if present)
   - Timestamp

3. **Response Details**
   - Status code
   - Headers
   - Body
   - Response time

4. **Error Information**
   - Connection errors
   - Proxy issues
   - Authentication failures

## Log Format

Logs use a standard format with timestamps and log levels:

```
2023-06-15 14:30:45 - repl - INFO - Loaded collection: API Collection (abc123)
2023-06-15 14:30:46 - repl - INFO - Sending request: GET https://api.example.com/users
2023-06-15 14:30:47 - repl - INFO - Response: 200 OK (156ms)
```

## Using Logs for Analysis

Logs can be used for:
- Troubleshooting API issues
- Documenting API behavior
- Analyzing response patterns
- Verifying request parameters
- Measuring API performance

## Log Retention

Log files are not automatically deleted. You should periodically clean up old log files to manage disk space.
