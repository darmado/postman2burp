# Authentication

Repl supports multiple authentication methods for API requests, allowing you to test endpoints with different credentials.

## Supported Authentication Methods

| Method | Description | Command Line Option |
|--------|-------------|---------------------|
| Basic Auth | Username and password authentication | `--auth-basic USERNAME PASSWORD` |
| Bearer Token | Token-based authentication | `--auth-bearer TOKEN` |
| API Key | Key-based authentication in header, query, or cookie | `--auth-api-key KEY LOCATION` |
| OAuth1 | OAuth 1.0 authentication | `--auth-oauth1 CONSUMER_KEY CONSUMER_SECRET` |
| OAuth2 | OAuth 2.0 authentication | `--auth-oauth2 CLIENT_ID CLIENT_SECRET` |

## Basic Usage Examples

```bash
# Basic usage with authentication
python3 repl.py --collection "api_collection.json" --auth-bearer "token123"

# Using a saved authentication profile
python3 repl.py --collection "api_collection.json" --auth "prod-profile"

# Interactive mode (select collection and authentication)
python3 repl.py
```

## Authentication Profiles

Save frequently used authentication settings as profiles for reuse:

```bash
python3 repl.py --auth-bearer "your-token" --create-auth "prod-token"
```

## Using Authentication Profiles

Load a saved authentication profile:

```bash
python3 repl.py --collection "api_collection.json" --auth "prod-token"
```

List available authentication profiles:

```bash
python3 repl.py --list-auth
```

## Authentication Options

### Basic Auth

```bash
python3 repl.py --collection "api.json" --auth-basic "username" "password"
```

### Bearer Token

```bash
python3 repl.py --collection "api.json" --auth-bearer "your-token"
```

### API Key

```bash
python3 repl.py --collection "api.json" --auth-api-key "your-key" "header"
```

Customize the API key name (default is X-API-Key):

```bash
python3 repl.py --collection "api.json" --auth-api-key "your-key" "header" --auth-api-key-name "Custom-Key"
```

### OAuth1

```bash
python3 repl.py --collection "api.json" --auth-oauth1 "consumer-key" "consumer-secret" --auth-oauth1-token "token" "token-secret"
```

### OAuth2

```bash
python3 repl.py --collection "api.json" --auth-oauth2 "client-id" "client-secret" --auth-oauth2-token-url "https://api.example.com/oauth/token"
```

Additional OAuth2 options:
- `--auth-oauth2-grant`: Grant type (client_credentials, password, refresh_token)
- `--auth-oauth2-username` and `--auth-oauth2-password`: For password grant
- `--auth-oauth2-refresh-url`: URL for refreshing tokens
- `--auth-oauth2-scope`: Space-separated list of scopes
