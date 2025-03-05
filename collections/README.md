# API Collections

This directory contains Postman collection files for various API testing scenarios. Each collection is designed for testing a specific type of API.

## Collection Structure

Each collection sample follows the Postman Collection v2.1.0 format with the following structure:

```json
{
    "info": {
        "_postman_id": "unique-id",
        "name": "Collection Name",
        "description": "Collection Description",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "Folder Name",
            "item": [
                {
                    "name": "Request Name",
                    "request": {
                        "method": "HTTP_METHOD",
                        "header": [...],
                        "body": {...},
                        "url": {...}
                    },
                    "response": []
                }
            ]
        }
    ],
    "variable": [
        {
            "key": "variable_name",
            "value": "default_value"
        }
    ]
}
```

## Available Collections

### E-commerce API (`ecommerce_api.json`)
Contains endpoints for testing e-commerce functionality including:
- Authentication (login, register)
- Products (list, details, create, update, delete)
- Orders (create, view, update)
- User profiles

### Weather API (`weather_api.json`)
Contains endpoints for testing weather service functionality including:
- Current weather by city
- Current weather by coordinates
- Forecast data
- Location search

### Social Media API (`social_media_api.json`)
Contains endpoints for testing social media platform functionality including:
- User authentication
- Profile management
- Posts and feeds
- Comments and likes

### Banking API (`banking_api.json`)
Contains endpoints for testing banking service functionality including:
- Authentication with 2FA
- Account management
- Transactions
- Transfers

### Healthcare API (`healthcare_api.json`)
Contains endpoints for testing healthcare service functionality including:
- Provider and patient authentication
- Patient management
- Appointments
- Medical records

### Security Testing API (`security_testing_api.json`)
Contains endpoints specifically designed for testing security vulnerabilities including:
- Authentication tests
- Injection tests
- Access control tests
- Data validation tests
- Rate limiting tests

## Using Collections

These collections can be used with the repl tool to send requests through a proxy server (like Burp Suite or OWASP ZAP) for security testing:

```bash
python repl.py --collection collections/ecommerce_api.json
```

You can also use them with a specific profile to provide variable values:

```bash
python repl.py --collection collections/ecommerce_api.json --target-profile profiles/ecommerce_profile.json
```

## Customizing Collections

You can customize these collections by:
1. Importing them into Postman
2. Modifying the requests as needed
3. Exporting them back to JSON format
4. Placing them in this directory

## Creating New Collections

To create a new collection:
1. Create a new collection in Postman
2. Add your requests and organize them into folders
3. Export the collection as a JSON file (v2.1.0 format)
4. Place it in this directory

Alternatively, you can copy and modify an existing collection JSON file directly. 