# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with Repl.

## Common Issues and Solutions

### Proxy Connection Issues

#### Problem: "Proxy is not running at localhost:8080"

**Solutions:**
- Ensure Burp Suite is running and the proxy is listening on the specified port
- Use `--proxy` to specify a different proxy address:
  ```bash
  python repl.py --collection "your_collection.json" --proxy localhost:9090
  ```
- Use `--skip-proxy-check` to bypass the proxy check:
  ```bash
  python repl.py --collection "your_collection.json" --skip-proxy-check
  ```

#### Problem: "Failed to connect to proxy"

**Solutions:**
- Check if there's a firewall blocking the connection
- Verify the proxy host and port are correct
- Try using the IP address instead of hostname

### Variable Substitution Issues

#### Problem: Variables not being substituted in requests

**Solutions:**
- Check that your insertion point file contains all required variables
- Ensure variable names match exactly (case-sensitive)
- Use `--verbose` to see detailed logs of variable substitution:
  ```bash
  python repl.py --collection "your_collection.json" --insertion-point"your_profile.json" --verbose
  ```
- Verify the insertion point file is valid JSON

### Collection Loading Issues

#### Problem: "Failed to load collection"

**Solutions:**
- Verify the collection file exists and is valid JSON
- Ensure the collection is in Postman Collection v2.1 format
- Check file permissions
- Try using the absolute path to the collection file

### Spaces in Filenames

#### Problem: Command fails with "unrecognized arguments" when filenames contain spaces

**Solutions:**
- Wrap filenames in quotes:
  ```bash
  python repl.py --collection "My Collection.json" --insertion-point"My Profile.json"
  ```
- Rename files to use underscores instead of spaces

### SSL Certificate Issues

#### Problem: SSL certificate verification errors

**Solutions:**
- By default, SSL verification is disabled. If you've enabled it and are experiencing issues, you can disable it again:
  ```bash
  # Remove the --verify-ssl flag if you were using it
  python repl.py --collection "your_collection.json"
  ```
- If you need to keep SSL verification enabled, ensure the necessary CA certificates are installed on your system

### Environment Setup Issues

#### Problem: "ModuleNotFoundError: No module named 'requests'"

**Solutions:**
- Ensure you've activated the virtual environment:
  ```bash
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```
- Reinstall dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- If issues persist, try recreating the virtual environment:
  ```bash
  rm -rf venv
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

## Debugging Techniques

### Enable Verbose Logging

Use the `--verbose` flag to get detailed information about what's happening:

```bash
python repl.py --collection "your_collection.json" --verbose
```

### Check Proxy Connection Manually

Test if your proxy is accessible:

```bash
curl -x localhost:8080 https://www.example.com
```

### Validate JSON Files

Ensure your collection and insertion point files are valid JSON:

```bash
python -m json.tool your_collection.json > /dev/null
python -m json.tool your_profile.json > /dev/null
```

### Check Python Version

Ensure you're using Python 3.6 or higher:

```bash
python --version
```

## Getting Help

If you're still experiencing issues:

1. Check the [GitHub Issues](https://github.com/darmado/repl/issues) to see if your problem has been reported
2. Open a new issue with:
   - A clear description of the problem
   - Steps to reproduce
   - Error messages
   - Your environment details (OS, Python version, etc.)

## Next Steps

- [[Installation]]
- [[Usage]]
- [[Features|Additional Features]]
- [[Configuration]] 