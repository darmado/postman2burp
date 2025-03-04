# Postman2Burp v0.0.6.9-alpha Release

## Changes

- Fixed proxy handling to respect user-specified proxy settings
- Added auto-detection of common proxy configurations
- Improved error handling for malformed configuration files
- Enhanced variable extraction from Postman collections
- Added support for filenames with spaces

## New Features

- Extract variables from collections with `--extract-keys`
- Save configuration with `--save-config`
- Skip proxy check with `--skip-proxy-check`
- Specify custom proxy with `--proxy host:port`
- Save results to file with `--output filename`


## Bug Fixes

- Fixed issue with proxy auto-detection overriding user-specified proxy
- Fixed handling of malformed JSON in config files
- Fixed path resolution for collections and profiles
- Fixed variable substitution in request bodies

## Known Issues

- Limited support for multipart/form-data requests
- No support for client certificates
- No support for OAuth2 authentication flows

## Upcoming Features

- Support for client certificates
- Enhanced OAuth2 support
- Improved handling of multipart/form-data
- Parallel request processing 