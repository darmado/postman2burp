#!/usr/bin/env python3
"""
Authentication module for Repl

This module provides authentication functionality for the Repl tool,
supporting various authentication methods including:
- Basic Authentication
- Bearer Token (fixed and dynamic)
- API Key / Custom Token (fixed and dynamic)
- OAuth1 Authentication
- OAuth2 Authentication

The module leverages requests.auth classes where possible.
"""

import os
import json
import time
import logging
import requests
from requests.auth import AuthBase, HTTPBasicAuth
from requests_oauthlib import OAuth1 as OAuth1Session
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient, LegacyApplicationClient
import base64
from typing import Dict, Optional, List, Any, Tuple, Union

# Setup logging
logger = logging.getLogger(__name__)

# Constants
AUTH_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "auth")

# Ensure auth config directory exists
os.makedirs(AUTH_CONFIG_DIR, exist_ok=True)

class AuthMethod:
    """Base class for authentication methods"""
    
    def __init__(self, label: str):
        """
        Initialize the authentication method
        
        Args:
            label: A unique identifier for this authentication method
        """
        self.label = label
        self.type = "base"  # Will be overridden by subclasses
    
    def get_auth(self) -> Optional[AuthBase]:
        """
        Get the requests auth object for this method
        
        Returns:
            AuthBase or None: The auth object to use with requests
        """
        return None
    
    def apply_to_request(self, headers: Dict[str, str], params: Dict[str, str], cookies: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """
        Apply authentication to the request
        
        Args:
            headers: Request headers
            params: Request query parameters
            cookies: Request cookies
            
        Returns:
            Tuple of (headers, params, cookies) with authentication applied
        """
        # Base implementation does nothing
        return headers, params, cookies
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the authentication method to a dictionary for serialization
        
        Returns:
            Dict representation of the authentication method
        """
        return {
            "label": self.label,
            "type": self.type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthMethod':
        """
        Create an authentication method from a dictionary
        
        Args:
            data: Dictionary representation of the authentication method
            
        Returns:
            An AuthMethod instance
        """
        auth_type = data.get("type", "")
        
        if auth_type == "basic":
            return BasicAuth.from_dict(data)
        elif auth_type == "bearer":
            return BearerToken.from_dict(data)
        elif auth_type == "apikey":
            return ApiKey.from_dict(data)
        elif auth_type == "oauth1":
            return OAuth1.from_dict(data)
        elif auth_type == "oauth2":
            return OAuth2.from_dict(data)
        else:
            # Default fallback
            return cls(data.get("label", "Unknown"))


class BasicAuth(AuthMethod):
    """Basic Authentication method using requests.auth.HTTPBasicAuth"""
    
    def __init__(self, label: str, username: str, password: str):
        """
        Initialize Basic Authentication
        
        Args:
            label: A unique identifier for this authentication method
            username: The username for Basic Authentication
            password: The password for Basic Authentication
        """
        super().__init__(label)
        self.type = "basic"
        self.username = username
        self.password = password
        self._auth = HTTPBasicAuth(username, password)
    
    def get_auth(self) -> HTTPBasicAuth:
        """Get the HTTPBasicAuth object for requests"""
        return self._auth
    
    def apply_to_request(self, headers: Dict[str, str], params: Dict[str, str], cookies: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """Apply Basic Authentication to the request headers"""
        # This is a fallback if not using the get_auth() method
        auth_string = f"{self.username}:{self.password}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_auth}"
        return headers, params, cookies
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "username": self.username,
            "password": self.password
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BasicAuth':
        """Create from dictionary"""
        return cls(
            data.get("label", "Basic Auth"),
            data.get("username", ""),
            data.get("password", "")
        )


class BearerTokenAuth(AuthBase):
    """Custom AuthBase implementation for Bearer Token authentication"""
    
    def __init__(self, token: str):
        self.token = token
    
    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


class BearerToken(AuthMethod):
    """Bearer Token Authentication method"""
    
    def __init__(self, label: str, token: str = None, is_dynamic: bool = False,
                 auth_url: str = None, auth_method: str = "POST",
                 auth_headers: Dict[str, str] = None, auth_body: str = None,
                 token_refresh_interval: int = 3600, token_location: str = None):
        """
        Initialize Bearer Token Authentication
        
        Args:
            label: A unique identifier for this authentication method
            token: The bearer token (for fixed token)
            is_dynamic: Whether the token is dynamic (needs to be refreshed)
            auth_url: URL for token retrieval (for dynamic token)
            auth_method: HTTP method for token retrieval (for dynamic token)
            auth_headers: Headers for token retrieval (for dynamic token)
            auth_body: Request body for token retrieval (for dynamic token)
            token_refresh_interval: How often to refresh the token in seconds (for dynamic token)
            token_location: Location of token in response (for dynamic token)
        """
        super().__init__(label)
        self.type = "bearer"
        self.token = token
        self.is_dynamic = is_dynamic
        self.auth_url = auth_url
        self.auth_method = auth_method
        self.auth_headers = auth_headers or {}
        self.auth_body = auth_body
        self.token_refresh_interval = token_refresh_interval
        self.token_location = token_location
        self.last_refresh = 0
    
    def get_auth(self) -> Optional[BearerTokenAuth]:
        """Get the BearerTokenAuth object for requests"""
        # For dynamic tokens, check if we need to refresh
        if self.is_dynamic and (time.time() - self.last_refresh > self.token_refresh_interval):
            self._refresh_token()
        
        if self.token:
            return BearerTokenAuth(self.token)
        return None
    
    def apply_to_request(self, headers: Dict[str, str], params: Dict[str, str], cookies: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """Apply Bearer Token to the request headers"""
        # For dynamic tokens, check if we need to refresh
        if self.is_dynamic and (time.time() - self.last_refresh > self.token_refresh_interval):
            self._refresh_token()
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        return headers, params, cookies
    
    def _refresh_token(self) -> None:
        """Refresh the dynamic token"""
        if not self.auth_url:
            logger.warning("Cannot refresh token: No authentication URL provided")
            return
        
        try:
            response = requests.request(
                method=self.auth_method,
                url=self.auth_url,
                headers=self.auth_headers,
                data=self.auth_body,
                timeout=30
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                # Extract token from response
                if self.token_location:
                    # Handle JSON response
                    if response.headers.get('Content-Type', '').startswith('application/json'):
                        json_data = response.json()
                        # Navigate through nested JSON using dot notation
                        token = json_data
                        for key in self.token_location.split('.'):
                            if key in token:
                                token = token[key]
                            else:
                                logger.error(f"Token location '{self.token_location}' not found in response")
                                return
                        self.token = token
                    # Handle XML response
                    elif response.headers.get('Content-Type', '').startswith('application/xml') or response.headers.get('Content-Type', '').startswith('text/xml'):
                        # Simple XML parsing - for complex XML, use a proper XML parser
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(response.text)
                        # Use XPath to find the token
                        elements = root.findall(self.token_location)
                        if elements and len(elements) > 0:
                            self.token = elements[0].text
                        else:
                            logger.error(f"Token location '{self.token_location}' not found in XML response")
                            return
                else:
                    # Use entire response as token
                    self.token = response.text
                
                self.last_refresh = time.time()
                logger.info(f"Successfully refreshed bearer token for {self.label}")
            else:
                logger.error(f"Failed to refresh token: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "token": self.token,
            "is_dynamic": self.is_dynamic,
            "auth_url": self.auth_url,
            "auth_method": self.auth_method,
            "auth_headers": self.auth_headers,
            "auth_body": self.auth_body,
            "token_refresh_interval": self.token_refresh_interval,
            "token_location": self.token_location
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BearerToken':
        """Create from dictionary"""
        return cls(
            data.get("label", "Bearer Token"),
            data.get("token"),
            data.get("is_dynamic", False),
            data.get("auth_url"),
            data.get("auth_method", "POST"),
            data.get("auth_headers", {}),
            data.get("auth_body"),
            data.get("token_refresh_interval", 3600),
            data.get("token_location")
        )


class ApiKeyAuth(AuthBase):
    """Custom AuthBase implementation for API Key authentication"""
    
    def __init__(self, key: str, param_name: str, location: str = "header"):
        self.key = key
        self.param_name = param_name
        self.location = location.lower()
    
    def __call__(self, r):
        if self.location == "header":
            r.headers[self.param_name] = self.key
        elif self.location == "query":
            # Parse existing query parameters
            url_parts = list(r.url.partition('?'))
            params = {}
            
            if url_parts[1] and url_parts[2]:
                for param in url_parts[2].split('&'):
                    if '=' in param:
                        k, v = param.split('=', 1)
                        params[k] = v
            
            # Add API key
            params[self.param_name] = self.key
            
            # Rebuild query string
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            url_parts[1] = '?'
            url_parts[2] = query_string
            r.url = ''.join(url_parts)
        
        return r


class ApiKey(AuthMethod):
    """API Key / Custom Token Authentication method"""
    
    def __init__(self, label: str, key: str = None, location: str = "header",
                 param_name: str = "X-API-Key", is_dynamic: bool = False,
                 auth_url: str = None, auth_method: str = "POST",
                 auth_headers: Dict[str, str] = None, auth_body: str = None,
                 key_refresh_interval: int = 3600, key_location: str = None):
        """
        Initialize API Key Authentication
        
        Args:
            label: A unique identifier for this authentication method
            key: The API key or token (for fixed key)
            location: Where to add the key (header, query, cookie)
            param_name: Name of the header, query parameter, or cookie
            is_dynamic: Whether the key is dynamic (needs to be refreshed)
            auth_url: URL for key retrieval (for dynamic key)
            auth_method: HTTP method for key retrieval (for dynamic key)
            auth_headers: Headers for key retrieval (for dynamic key)
            auth_body: Request body for key retrieval (for dynamic key)
            key_refresh_interval: How often to refresh the key in seconds (for dynamic key)
            key_location: Location of key in response (for dynamic key)
        """
        super().__init__(label)
        self.type = "apikey"
        self.key = key
        self.location = location.lower()  # header, query, or cookie
        self.param_name = param_name
        self.is_dynamic = is_dynamic
        self.auth_url = auth_url
        self.auth_method = auth_method
        self.auth_headers = auth_headers or {}
        self.auth_body = auth_body
        self.key_refresh_interval = key_refresh_interval
        self.key_location = key_location
        self.last_refresh = 0
    
    def get_auth(self) -> Optional[ApiKeyAuth]:
        """Get the ApiKeyAuth object for requests"""
        # For dynamic keys, check if we need to refresh
        if self.is_dynamic and (time.time() - self.last_refresh > self.key_refresh_interval):
            self._refresh_key()
        
        if self.key and self.location != "cookie":  # Cookies need special handling
            return ApiKeyAuth(self.key, self.param_name, self.location)
        return None
    
    def apply_to_request(self, headers: Dict[str, str], params: Dict[str, str], cookies: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """Apply API Key to the request based on location"""
        # For dynamic keys, check if we need to refresh
        if self.is_dynamic and (time.time() - self.last_refresh > self.key_refresh_interval):
            self._refresh_key()
        
        if self.key:
            if self.location == "header":
                headers[self.param_name] = self.key
            elif self.location == "query":
                params[self.param_name] = self.key
            elif self.location == "cookie":
                cookies[self.param_name] = self.key
        
        return headers, params, cookies
    
    def _refresh_key(self) -> None:
        """Refresh the dynamic API key"""
        if not self.auth_url:
            logger.warning("Cannot refresh API key: No authentication URL provided")
            return
        
        try:
            response = requests.request(
                method=self.auth_method,
                url=self.auth_url,
                headers=self.auth_headers,
                data=self.auth_body,
                timeout=30
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                # Extract key from response
                if self.key_location:
                    # Handle JSON response
                    if response.headers.get('Content-Type', '').startswith('application/json'):
                        json_data = response.json()
                        # Navigate through nested JSON using dot notation
                        key = json_data
                        for k in self.key_location.split('.'):
                            if k in key:
                                key = key[k]
                            else:
                                logger.error(f"Key location '{self.key_location}' not found in response")
                                return
                        self.key = key
                    # Handle XML response
                    elif response.headers.get('Content-Type', '').startswith('application/xml') or response.headers.get('Content-Type', '').startswith('text/xml'):
                        # Simple XML parsing - for complex XML, use a proper XML parser
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(response.text)
                        # Use XPath to find the key
                        elements = root.findall(self.key_location)
                        if elements and len(elements) > 0:
                            self.key = elements[0].text
                        else:
                            logger.error(f"Key location '{self.key_location}' not found in XML response")
                            return
                else:
                    # Use entire response as key
                    self.key = response.text
                
                self.last_refresh = time.time()
                logger.info(f"Successfully refreshed API key for {self.label}")
            else:
                logger.error(f"Failed to refresh API key: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"Error refreshing API key: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "key": self.key,
            "location": self.location,
            "param_name": self.param_name,
            "is_dynamic": self.is_dynamic,
            "auth_url": self.auth_url,
            "auth_method": self.auth_method,
            "auth_headers": self.auth_headers,
            "auth_body": self.auth_body,
            "key_refresh_interval": self.key_refresh_interval,
            "key_location": self.key_location
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApiKey':
        """Create from dictionary"""
        return cls(
            data.get("label", "API Key"),
            data.get("key"),
            data.get("location", "header"),
            data.get("param_name", "X-API-Key"),
            data.get("is_dynamic", False),
            data.get("auth_url"),
            data.get("auth_method", "POST"),
            data.get("auth_headers", {}),
            data.get("auth_body"),
            data.get("key_refresh_interval", 3600),
            data.get("key_location")
        )


class OAuth1Auth(AuthBase):
    """Custom AuthBase implementation for OAuth1 authentication"""
    
    def __init__(self, client_key: str, client_secret: str, resource_owner_key: str = None, 
                 resource_owner_secret: str = None, signature_method: str = 'HMAC-SHA1'):
        self.client_key = client_key
        self.client_secret = client_secret
        self.resource_owner_key = resource_owner_key
        self.resource_owner_secret = resource_owner_secret
        self.signature_method = signature_method
        self._auth = OAuth1Session(
            client_key=client_key,
            client_secret=client_secret,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            signature_method=signature_method
        )
    
    def __call__(self, r):
        # Apply the OAuth1 signature to the request
        return self._auth(r)


class OAuth1(AuthMethod):
    """OAuth1 Authentication method"""
    
    def __init__(self, label: str, client_key: str, client_secret: str, 
                 resource_owner_key: str = None, resource_owner_secret: str = None,
                 signature_method: str = 'HMAC-SHA1'):
        """
        Initialize OAuth1 Authentication
        
        Args:
            label: A unique identifier for this authentication method
            client_key: The client key (consumer key)
            client_secret: The client secret (consumer secret)
            resource_owner_key: The resource owner key (access token)
            resource_owner_secret: The resource owner secret (access token secret)
            signature_method: The signature method (default: HMAC-SHA1)
        """
        super().__init__(label)
        self.type = "oauth1"
        self.client_key = client_key
        self.client_secret = client_secret
        self.resource_owner_key = resource_owner_key
        self.resource_owner_secret = resource_owner_secret
        self.signature_method = signature_method
    
    def get_auth(self) -> OAuth1Auth:
        """Get the OAuth1Auth object for requests"""
        return OAuth1Auth(
            client_key=self.client_key,
            client_secret=self.client_secret,
            resource_owner_key=self.resource_owner_key,
            resource_owner_secret=self.resource_owner_secret,
            signature_method=self.signature_method
        )
    
    def apply_to_request(self, headers: Dict[str, str], params: Dict[str, str], cookies: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """
        Apply OAuth1 authentication to the request
        
        Note: This is a fallback method. The preferred approach is to use get_auth()
        which properly handles OAuth1 signature generation.
        """
        logger.warning("OAuth1 authentication should use the get_auth() method for proper signature generation")
        return headers, params, cookies
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "resource_owner_key": self.resource_owner_key,
            "resource_owner_secret": self.resource_owner_secret,
            "signature_method": self.signature_method
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OAuth1':
        """Create from dictionary"""
        return cls(
            data.get("label", "OAuth1"),
            data.get("client_key", ""),
            data.get("client_secret", ""),
            data.get("resource_owner_key"),
            data.get("resource_owner_secret"),
            data.get("signature_method", "HMAC-SHA1")
        )


class OAuth2Auth(AuthBase):
    """Custom AuthBase implementation for OAuth2 authentication"""
    
    def __init__(self, token: Dict[str, str]):
        self.token = token
    
    def __call__(self, r):
        r.headers['Authorization'] = f"Bearer {self.token.get('access_token', '')}"
        return r


class OAuth2(AuthMethod):
    """OAuth2 Authentication method"""
    
    def __init__(self, label: str, client_id: str, client_secret: str, 
                 token: Dict[str, str] = None, token_url: str = None,
                 refresh_url: str = None, scope: List[str] = None,
                 grant_type: str = "client_credentials", username: str = None,
                 password: str = None, redirect_uri: str = None,
                 auto_refresh_url: str = None, auto_refresh_kwargs: Dict[str, str] = None,
                 token_updater: callable = None):
        """
        Initialize OAuth2 Authentication
        
        Args:
            label: A unique identifier for this authentication method
            client_id: The client ID
            client_secret: The client secret
            token: The token dictionary (if already obtained)
            token_url: The token endpoint URL
            refresh_url: The refresh token endpoint URL
            scope: The requested scopes
            grant_type: The grant type (client_credentials, password, authorization_code)
            username: The username (for password grant)
            password: The password (for password grant)
            redirect_uri: The redirect URI (for authorization_code grant)
            auto_refresh_url: URL to refresh the token when it expires
            auto_refresh_kwargs: Additional arguments for token refresh
            token_updater: Callback function to update the token
        """
        super().__init__(label)
        self.type = "oauth2"
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = token or {}
        self.token_url = token_url
        self.refresh_url = refresh_url
        self.scope = scope or []
        self.grant_type = grant_type
        self.username = username
        self.password = password
        self.redirect_uri = redirect_uri
        self.auto_refresh_url = auto_refresh_url
        self.auto_refresh_kwargs = auto_refresh_kwargs or {}
        self.token_updater = token_updater
        self.last_refresh = time.time() if token else 0
    
    def get_auth(self) -> Optional[OAuth2Auth]:
        """Get the OAuth2Auth object for requests"""
        # Check if we need to get/refresh the token
        if not self.token or self._token_expired():
            self._get_token()
        
        if self.token and 'access_token' in self.token:
            return OAuth2Auth(self.token)
        return None
    
    def apply_to_request(self, headers: Dict[str, str], params: Dict[str, str], cookies: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """Apply OAuth2 token to the request headers"""
        # Check if we need to get/refresh the token
        if not self.token or self._token_expired():
            self._get_token()
        
        if self.token and 'access_token' in self.token:
            headers["Authorization"] = f"Bearer {self.token['access_token']}"
        
        return headers, params, cookies
    
    def _token_expired(self) -> bool:
        """Check if the token has expired"""
        if not self.token:
            return True
        
        expires_at = self.token.get('expires_at')
        if expires_at:
            # Add a 10-second buffer to avoid edge cases
            return time.time() > (expires_at - 10)
        
        # If no expires_at, check if it's been more than an hour since last refresh
        return (time.time() - self.last_refresh) > 3600
    
    def _get_token(self) -> None:
        """Get or refresh the OAuth2 token"""
        if not self.token_url:
            logger.warning("Cannot get/refresh token: No token URL provided")
            return
        
        try:
            if self.grant_type == 'client_credentials':
                # Client credentials grant
                client = BackendApplicationClient(client_id=self.client_id)
                oauth = OAuth2Session(client=client, scope=self.scope)
                self.token = oauth.fetch_token(
                    token_url=self.token_url,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    scope=self.scope
                )
            elif self.grant_type == 'password':
                # Resource owner password credentials grant
                if not self.username or not self.password:
                    logger.warning("Cannot get token: Username or password missing for password grant")
                    return
                
                client = LegacyApplicationClient(client_id=self.client_id)
                oauth = OAuth2Session(client=client, scope=self.scope)
                self.token = oauth.fetch_token(
                    token_url=self.token_url,
                    username=self.username,
                    password=self.password,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    scope=self.scope
                )
            elif self.grant_type == 'refresh_token':
                # Refresh token grant
                if not self.token.get('refresh_token'):
                    logger.warning("Cannot refresh token: No refresh token available")
                    return
                
                oauth = OAuth2Session(client_id=self.client_id, scope=self.scope)
                self.token = oauth.refresh_token(
                    self.refresh_url or self.token_url,
                    refresh_token=self.token['refresh_token'],
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    scope=self.scope
                )
            else:
                logger.warning(f"Unsupported grant type: {self.grant_type}")
                return
            
            # Update last refresh time
            self.last_refresh = time.time()
            
            # If token doesn't have expires_at, add it
            if 'expires_at' not in self.token and 'expires_in' in self.token:
                self.token['expires_at'] = time.time() + self.token['expires_in']
            
            # Call token updater if provided
            if self.token_updater:
                self.token_updater(self.token)
            
            logger.info(f"Successfully obtained/refreshed OAuth2 token for {self.label}")
        except Exception as e:
            logger.error(f"Error getting/refreshing OAuth2 token: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "token": self.token,
            "token_url": self.token_url,
            "refresh_url": self.refresh_url,
            "scope": self.scope,
            "grant_type": self.grant_type,
            "username": self.username,
            "password": self.password,
            "redirect_uri": self.redirect_uri,
            "auto_refresh_url": self.auto_refresh_url,
            "auto_refresh_kwargs": self.auto_refresh_kwargs
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OAuth2':
        """Create from dictionary"""
        return cls(
            data.get("label", "OAuth2"),
            data.get("client_id", ""),
            data.get("client_secret", ""),
            data.get("token", {}),
            data.get("token_url"),
            data.get("refresh_url"),
            data.get("scope", []),
            data.get("grant_type", "client_credentials"),
            data.get("username"),
            data.get("password"),
            data.get("redirect_uri"),
            data.get("auto_refresh_url"),
            data.get("auto_refresh_kwargs", {})
        )


class AuthManager:
    """Manager for authentication methods"""
    
    def __init__(self):
        """Initialize the authentication manager"""
        self.auth_methods = {}
        self.active_method = None
        self._migrate_auth_files()
        self.load_auth_methods()
    
    def _migrate_auth_files(self) -> None:
        """
        Migrate existing auth files from the main directory to type-specific subdirectories
        """
        if not os.path.exists(AUTH_CONFIG_DIR):
            return
        
        # Create subdirectories if they don't exist
        for auth_type in ["basic", "bearer", "apikey", "oauth1", "oauth2"]:
            os.makedirs(os.path.join(AUTH_CONFIG_DIR, auth_type), exist_ok=True)
        
        # Check for files in the main directory
        for filename in os.listdir(AUTH_CONFIG_DIR):
            if not filename.endswith('.json') or os.path.isdir(os.path.join(AUTH_CONFIG_DIR, filename)):
                continue
                
            file_path = os.path.join(AUTH_CONFIG_DIR, filename)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                # Skip if no type information
                if "type" not in data:
                    logger.warning(f"Skipping migration for {filename}: No type information")
                    continue
                    
                auth_type = data["type"].lower()
                type_dir = os.path.join(AUTH_CONFIG_DIR, auth_type)
                
                # Create directory if it doesn't exist
                os.makedirs(type_dir, exist_ok=True)
                
                # Move file to type-specific directory
                new_path = os.path.join(type_dir, filename)
                if not os.path.exists(new_path):
                    import shutil
                    shutil.copy2(file_path, new_path)
                    logger.info(f"Migrated auth file: {filename} to {auth_type}/{filename}")
                    
                    # Remove original file after successful copy
                    os.remove(file_path)
                    logger.debug(f"Removed original auth file: {filename}")
            except Exception as e:
                logger.error(f"Error migrating auth file {filename}: {str(e)}")
    
    def load_auth_methods(self) -> None:
        """Load authentication methods from config files"""
        if not os.path.exists(AUTH_CONFIG_DIR):
            logger.debug(f"Auth config directory does not exist: {AUTH_CONFIG_DIR}")
            return
        
        # Load auth methods from the main directory (legacy support)
        self._load_from_directory(AUTH_CONFIG_DIR)
        
        # Load auth methods from type-specific subdirectories
        for dirname in os.listdir(AUTH_CONFIG_DIR):
            subdir_path = os.path.join(AUTH_CONFIG_DIR, dirname)
            if os.path.isdir(subdir_path):
                self._load_from_directory(subdir_path)
    
    def _load_from_directory(self, directory: str) -> None:
        """
        Load authentication methods from a specific directory
        
        Args:
            directory: Directory to load auth methods from
        """
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                file_path = os.path.join(directory, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        auth_method = AuthMethod.from_dict(data)
                        self.auth_methods[auth_method.label] = auth_method
                        logger.debug(f"Loaded authentication method: {auth_method.label} from {file_path}")
                except Exception as e:
                    logger.error(f"Error loading authentication method from {file_path}: {str(e)}")
    
    def save_auth_method(self, auth_method: AuthMethod) -> bool:
        """
        Save an authentication method to a config file
        
        Args:
            auth_method: The authentication method to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(AUTH_CONFIG_DIR):
            os.makedirs(AUTH_CONFIG_DIR, exist_ok=True)
        
        # Create type-specific subdirectory
        auth_type = auth_method.type.lower()
        type_dir = os.path.join(AUTH_CONFIG_DIR, auth_type)
        os.makedirs(type_dir, exist_ok=True)
        
        # Create filename based on label
        filename = f"{auth_method.label.lower().replace(' ', '_')}.json"
        file_path = os.path.join(type_dir, filename)
        
        try:
            with open(file_path, 'w') as f:
                json.dump(auth_method.to_dict(), f, indent=2)
            logger.info(f"Saved authentication method to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving authentication method to {file_path}: {str(e)}")
            return False
    
    def delete_auth_method(self, label: str) -> bool:
        """
        Delete an authentication method
        
        Args:
            label: The label of the authentication method to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if label not in self.auth_methods:
            logger.warning(f"Authentication method not found: {label}")
            return False
        
        auth_method = self.auth_methods[label]
        auth_type = auth_method.type.lower()
        
        # Check in type-specific directory first
        type_dir = os.path.join(AUTH_CONFIG_DIR, auth_type)
        filename = f"{label.lower().replace(' ', '_')}.json"
        file_path = os.path.join(type_dir, filename)
        
        # If not found, check in main directory (legacy support)
        if not os.path.exists(file_path):
            file_path = os.path.join(AUTH_CONFIG_DIR, filename)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                del self.auth_methods[label]
                logger.info(f"Deleted authentication method: {label}")
                return True
            except Exception as e:
                logger.error(f"Error deleting authentication method {label}: {str(e)}")
                return False
        else:
            logger.warning(f"Authentication method file not found: {file_path}")
            return False
    
    def set_active_method(self, label: str) -> bool:
        """
        Set the active authentication method
        
        Args:
            label: The label of the authentication method to set as active
            
        Returns:
            bool: True if successful, False otherwise
        """
        if label not in self.auth_methods:
            logger.warning(f"Authentication method not found: {label}")
            return False
        
        self.active_method = self.auth_methods[label]
        logger.info(f"Set active authentication method: {label}")
        return True
    
    def get_auth(self) -> Optional[AuthBase]:
        """
        Get the active authentication method's auth object for requests
        
        Returns:
            AuthBase or None: The auth object to use with requests
        """
        if not self.active_method:
            return None
        
        return self.active_method.get_auth()
    
    def apply_auth(self, headers: Dict[str, str], params: Dict[str, str], cookies: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        """
        Apply the active authentication method to a request
        
        Args:
            headers: Request headers
            params: Request query parameters
            cookies: Request cookies
            
        Returns:
            Tuple of (headers, params, cookies) with authentication applied
        """
        if not self.active_method:
            return headers, params, cookies
        
        return self.active_method.apply_to_request(headers, params, cookies)
    
    def get_auth_methods(self) -> List[str]:
        """
        Get a list of available authentication method labels
        
        Returns:
            List of authentication method labels
        """
        return list(self.auth_methods.keys())
    
    def get_auth_method(self, label: str) -> Optional[AuthMethod]:
        """
        Get an authentication method by label
        
        Args:
            label: The label of the authentication method
            
        Returns:
            The authentication method, or None if not found
        """
        return self.auth_methods.get(label)
    
    def create_basic_auth(self, label: str, username: str, password: str) -> BasicAuth:
        """
        Create a new Basic Authentication method
        
        Args:
            label: A unique identifier for this authentication method
            username: The username for Basic Authentication
            password: The password for Basic Authentication
            
        Returns:
            The created BasicAuth instance
        """
        auth_method = BasicAuth(label, username, password)
        self.auth_methods[label] = auth_method
        self.save_auth_method(auth_method)
        return auth_method
    
    def create_bearer_token(self, label: str, token: str = None, is_dynamic: bool = False,
                           auth_url: str = None, auth_method: str = "POST",
                           auth_headers: Dict[str, str] = None, auth_body: str = None,
                           token_refresh_interval: int = 3600, token_location: str = None) -> BearerToken:
        """
        Create a new Bearer Token Authentication method
        
        Args:
            label: A unique identifier for this authentication method
            token: The bearer token (for fixed token)
            is_dynamic: Whether the token is dynamic (needs to be refreshed)
            auth_url: URL for token retrieval (for dynamic token)
            auth_method: HTTP method for token retrieval (for dynamic token)
            auth_headers: Headers for token retrieval (for dynamic token)
            auth_body: Request body for token retrieval (for dynamic token)
            token_refresh_interval: How often to refresh the token in seconds (for dynamic token)
            token_location: Location of token in response (for dynamic token)
            
        Returns:
            The created BearerToken instance
        """
        auth_method = BearerToken(label, token, is_dynamic, auth_url, auth_method,
                                 auth_headers, auth_body, token_refresh_interval, token_location)
        self.auth_methods[label] = auth_method
        self.save_auth_method(auth_method)
        return auth_method
    
    def create_api_key(self, label: str, key: str = None, location: str = "header",
                      param_name: str = "X-API-Key", is_dynamic: bool = False,
                      auth_url: str = None, auth_method: str = "POST",
                      auth_headers: Dict[str, str] = None, auth_body: str = None,
                      key_refresh_interval: int = 3600, key_location: str = None) -> ApiKey:
        """
        Create a new API Key Authentication method
        
        Args:
            label: A unique identifier for this authentication method
            key: The API key or token (for fixed key)
            location: Where to add the key (header, query, cookie)
            param_name: Name of the header, query parameter, or cookie
            is_dynamic: Whether the key is dynamic (needs to be refreshed)
            auth_url: URL for key retrieval (for dynamic key)
            auth_method: HTTP method for key retrieval (for dynamic key)
            auth_headers: Headers for key retrieval (for dynamic key)
            auth_body: Request body for key retrieval (for dynamic key)
            key_refresh_interval: How often to refresh the key in seconds (for dynamic key)
            key_location: Location of key in response (for dynamic key)
            
        Returns:
            The created ApiKey instance
        """
        auth_method = ApiKey(label, key, location, param_name, is_dynamic, auth_url,
                            auth_method, auth_headers, auth_body, key_refresh_interval, key_location)
        self.auth_methods[label] = auth_method
        self.save_auth_method(auth_method)
        return auth_method
    
    def create_oauth1(self, label: str, client_key: str, client_secret: str, 
                     resource_owner_key: str = None, resource_owner_secret: str = None,
                     signature_method: str = 'HMAC-SHA1') -> OAuth1:
        """
        Create a new OAuth1 Authentication method
        
        Args:
            label: A unique identifier for this authentication method
            client_key: The client key (consumer key)
            client_secret: The client secret (consumer secret)
            resource_owner_key: The resource owner key (access token)
            resource_owner_secret: The resource owner secret (access token secret)
            signature_method: The signature method (default: HMAC-SHA1)
            
        Returns:
            The created OAuth1 instance
        """
        auth_method = OAuth1(label, client_key, client_secret, resource_owner_key, 
                           resource_owner_secret, signature_method)
        self.auth_methods[label] = auth_method
        self.save_auth_method(auth_method)
        return auth_method
    
    def create_oauth2(self, label: str, client_id: str, client_secret: str, 
                     token: Dict[str, str] = None, token_url: str = None,
                     refresh_url: str = None, scope: List[str] = None,
                     grant_type: str = "client_credentials", username: str = None,
                     password: str = None, redirect_uri: str = None,
                     auto_refresh_url: str = None, auto_refresh_kwargs: Dict[str, str] = None) -> OAuth2:
        """
        Create a new OAuth2 Authentication method
        
        Args:
            label: A unique identifier for this authentication method
            client_id: The client ID
            client_secret: The client secret
            token: The token dictionary (if already obtained)
            token_url: The token endpoint URL
            refresh_url: The refresh token endpoint URL
            scope: The requested scopes
            grant_type: The grant type (client_credentials, password, authorization_code)
            username: The username (for password grant)
            password: The password (for password grant)
            redirect_uri: The redirect URI (for authorization_code grant)
            auto_refresh_url: URL to refresh the token when it expires
            auto_refresh_kwargs: Additional arguments for token refresh
            
        Returns:
            The created OAuth2 instance
        """
        auth_method = OAuth2(label, client_id, client_secret, token, token_url,
                           refresh_url, scope, grant_type, username, password,
                           redirect_uri, auto_refresh_url, auto_refresh_kwargs)
        self.auth_methods[label] = auth_method
        self.save_auth_method(auth_method)
        return auth_method


# Create a singleton instance
auth_manager = AuthManager() 