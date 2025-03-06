# Inessertoin Point Templates

contains variable insertion point templates for use with the repl tool. Each insertion point is designed for a specific type of API testing scenario.

## Profile Structure

Each insertion point is a JSON file with the following structure:

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

## Available Insertion Points

### E-commerce API (`ecommerce_profile.json`)
Contains variables for testing e-commerce endpoints including:
- Authentication credentials
- Product details
- Order information
- Payment methods

### Weather API (`weather_profile.json`)
Contains variables for testing weather service endpoints including:
- API keys
- Location coordinates
- City names
- Units of measurement

### Social Media API (`social_profile.json`)
Contains variables for testing social media platform endpoints including:
- User credentials
- Profile information
- Post content
- Media URLs

### Banking API (`banking_profile.json`)
Contains variables for testing banking service endpoints including:
- Account credentials
- Account numbers
- Transaction details
- Transfer information

### Healthcare API (`healthcare_profile.json`)
Contains variables for testing healthcare service endpoints including:
- Provider and patient credentials
- Patient information
- Appointment details
- Medication information

### Security Testing API (`security_profile.json`)
Contains variables for testing security vulnerabilities including:
- Authentication test payloads
- Injection test payloads
- XSS and CSRF test strings
- Manipulated tokens

## Using Insertion Points

Insertion Points can be used with the repl tool in several ways:

1. Specified directly via command line:
   ```bash
   python repl.py --collection collections/ecommerce_api.json --insertion-pointprofiles/ecommerce_profile.json
   ```

2. Referenced in a configuration file:
   ```json
   {
       "collection": "collections/ecommerce_api.json",
       "insertion_point": "profiles/ecommerce_profile.json",
       ...
   }
   ```

3. Selected through the interactive menu when using:
   ```bash
   python repl.py --config select
   ```

## Customizing Insertion Points

You can customize these insertion points  by:
1. Editing the variable values to match your testing environment
2. Adding new variables as needed for your specific API
3. Removing variables that aren't relevant to your testing scenario

## Creating New Insertion Points

To create a new profile:
1. Copy an existing insertion point that's closest to your needs
2. Modify the variables to match your API requirements
3. Save it with a descriptive name (e.g., `my_api_profile.json`)

Alternatively, you can generate a insertion point template from a Postman collection:
```bash
python repl.py --collection your_collection.json --generate-template
``` 