#!/usr/bin/env python3
"""
encoder.py - Encoding module for Repl insertion point variables

This module provides various encoding methods for variables in insertion points.
It's used when the insertion_point object includes an 'encoding' field.
"""

import urllib.parse
import html
import xml.sax.saxutils
import json
import base64

class Encoder:
    """
    Encoder class that provides methods for encoding strings using various techniques.
    """
    
    @staticmethod
    def encode(value, encoding_type, iterations=1):
        """
        Encode a value using the specified encoding type.
        
        Args:
            value (str): The value to encode
            encoding_type (str): The encoding type to use
            iterations (int): Number of times to apply the encoding (for multiple encodings)
            
        Returns:
            str: The encoded value
        """
        if not isinstance(value, str):
            value = str(value)
            
        encoding_functions = {
            "url": Encoder.url_encode,
            "double_url": Encoder.double_url_encode,
            "html": Encoder.html_encode,
            "xml": Encoder.xml_encode,
            "unicode": Encoder.unicode_escape,
            "hex": Encoder.hex_escape,
            "octal": Encoder.octal_escape,
            "base64": Encoder.base64_encode,
            "sql_char": Encoder.sql_char_encode,
            "js_escape": Encoder.js_escape,
            "css_escape": Encoder.css_escape
        }
        
        if encoding_type not in encoding_functions:
            raise ValueError(f"Unsupported encoding type: {encoding_type}")
        
        result = value
        for _ in range(iterations):
            result = encoding_functions[encoding_type](result)
        
        return result
    
    @staticmethod
    def url_encode(value):
        """URL encode a string"""
        return urllib.parse.quote(value)
    
    @staticmethod
    def double_url_encode(value):
        """Double URL encode a string"""
        return urllib.parse.quote(urllib.parse.quote(value))
    
    @staticmethod
    def html_encode(value):
        """HTML encode a string"""
        return html.escape(value)
    
    @staticmethod
    def xml_encode(value):
        """XML encode a string"""
        return xml.sax.saxutils.escape(value, {'"': "&quot;", "'": "&apos;"})
    
    @staticmethod
    def unicode_escape(value):
        """Unicode escape a string"""
        result = ""
        for char in value:
            if ord(char) > 127:
                result += f"\\u{ord(char):04x}"
            else:
                result += char
        return result
    
    @staticmethod
    def hex_escape(value):
        """Hex escape a string"""
        return ''.join(f"\\x{ord(char):02x}" for char in value)
    
    @staticmethod
    def octal_escape(value):
        """Octal escape a string"""
        return ''.join(f"\\{ord(char):03o}" for char in value)
    
    @staticmethod
    def base64_encode(value):
        """Base64 encode a string"""
        return base64.b64encode(value.encode()).decode()
    
    @staticmethod
    def sql_char_encode(value):
        """SQL CHAR() function encoding"""
        return f"CHAR({','.join(str(ord(char)) for char in value)})"
    
    @staticmethod
    def js_escape(value):
        """JavaScript string escape"""
        result = ""
        for char in value:
            if char in "\\\"'\n\r\t":
                if char == "\n": result += "\\n"
                elif char == "\r": result += "\\r"
                elif char == "\t": result += "\\t"
                else: result += "\\" + char
            elif ord(char) < 32 or ord(char) > 126:
                result += f"\\u{ord(char):04x}"
            else:
                result += char
        return result
    
    @staticmethod
    def css_escape(value):
        """CSS escape sequences"""
        result = ""
        for char in value:
            if ord(char) < 32 or ord(char) > 126:
                result += f"\\{ord(char):x} "
            else:
                result += char
        return result


def process_insertion_point(insertion_point):
    """
    Process an insertion point object and apply encodings to variables if specified.
    
    Args:
        insertion_point (dict): The insertion point object
        
    Returns:
        dict: The processed insertion point with encoded values
    """
    if not isinstance(insertion_point, dict):
        return insertion_point
    
    # Deep copy to avoid modifying the original
    result = json.loads(json.dumps(insertion_point))
    
    # Process variables if they exist
    if "variables" in result:
        for i, variable in enumerate(result["variables"]):
            # Skip base_url as it should never be encoded
            if variable.get("key") == "base_url":
                # Remove any encoding info from base_url to prevent encoding
                if "encoding" in result["variables"][i]:
                    del result["variables"][i]["encoding"]
                if "encoding_iterations" in result["variables"][i]:
                    del result["variables"][i]["encoding_iterations"]
                continue
                
            if "encoding" in variable:
                encoding_type = variable["encoding"]
                iterations = variable.get("encoding_iterations", 1)
                
                if isinstance(iterations, str) and iterations.isdigit():
                    iterations = int(iterations)
                
                if not isinstance(iterations, int) or iterations < 1:
                    iterations = 1
                
                try:
                    result["variables"][i]["value"] = Encoder.encode(
                        variable["value"], 
                        encoding_type, 
                        iterations
                    )
                    # Remove encoding info to prevent double encoding
                    del result["variables"][i]["encoding"]
                    if "encoding_iterations" in result["variables"][i]:
                        del result["variables"][i]["encoding_iterations"]
                except ValueError as e:
                    print(f"Warning: {e}")
    
    # Handle Postman environment format (with values array)
    elif "values" in result and isinstance(result["values"], list):
        for i, variable in enumerate(result["values"]):
            # Skip base_url as it should never be encoded
            if variable.get("key") == "base_url":
                # Remove any encoding info from base_url to prevent encoding
                if "encoding" in result["values"][i]:
                    del result["values"][i]["encoding"]
                if "encoding_iterations" in result["values"][i]:
                    del result["values"][i]["encoding_iterations"]
                continue
                
            if "encoding" in variable:
                encoding_type = variable["encoding"]
                iterations = variable.get("encoding_iterations", 1)
                
                if isinstance(iterations, str) and iterations.isdigit():
                    iterations = int(iterations)
                
                if not isinstance(iterations, int) or iterations < 1:
                    iterations = 1
                
                try:
                    result["values"][i]["value"] = Encoder.encode(
                        variable["value"], 
                        encoding_type, 
                        iterations
                    )
                    # Remove encoding info to prevent double encoding
                    del result["values"][i]["encoding"]
                    if "encoding_iterations" in result["values"][i]:
                        del result["values"][i]["encoding_iterations"]
                except ValueError as e:
                    print(f"Warning: {e}")
    
    return result


def apply_encoding_to_value(value, encoding_type, iterations=1):
    """
    Apply encoding to a single value.
    
    Args:
        value (str): The value to encode
        encoding_type (str): The encoding type to use
        iterations (int): Number of times to apply the encoding
        
    Returns:
        str: The encoded value
    """
    return Encoder.encode(value, encoding_type, iterations)


if __name__ == "__main__":
    # Example usage
    test_value = "Test<>&\"' 123"
    
    print(f"Original: {test_value}")
    print(f"URL Encoded: {Encoder.url_encode(test_value)}")
    print(f"Double URL Encoded: {Encoder.double_url_encode(test_value)}")
    print(f"HTML Encoded: {Encoder.html_encode(test_value)}")
    print(f"XML Encoded: {Encoder.xml_encode(test_value)}")
    print(f"Unicode Escaped: {Encoder.unicode_escape(test_value)}")
    print(f"Hex Escaped: {Encoder.hex_escape(test_value)}")
    print(f"Octal Escaped: {Encoder.octal_escape(test_value)}")
    print(f"Base64 Encoded: {Encoder.base64_encode(test_value)}")
    print(f"SQL CHAR(): {Encoder.sql_char_encode(test_value)}")
    print(f"JS Escaped: {Encoder.js_escape(test_value)}")
    print(f"CSS Escaped: {Encoder.css_escape(test_value)}")
    
    # Example of processing an insertion point
    sample_insertion_point = {
        "variables": [
            {
                "key": "normal_var",
                "value": "normal value"
            },
            {
                "key": "url_encoded_var",
                "value": "value with spaces & special chars",
                "encoding": "url"
            },
            {
                "key": "double_encoded_var",
                "value": "value with spaces & special chars",
                "encoding": "url",
                "encoding_iterations": 2
            }
        ]
    }
    
    processed = process_insertion_point(sample_insertion_point)
    print("\nProcessed Insertion Point:")
    print(json.dumps(processed, indent=2)) 