#!/usr/bin/env python3
"""
Repl Test Runner
-----------------------
A simple script to run all tests for Repl.
"""

import os
import sys
import unittest
import argparse
from pathlib import Path

def run_tests(test_type=None, verbose=False):
    """Run the specified tests."""
    # Create the tests directory if it doesn't exist
    tests_dir = Path("tests")
    if not tests_dir.exists():
        tests_dir.mkdir(parents=True)
        print(f"Created tests directory: {tests_dir}")
    
    # Create a test loader
    loader = unittest.TestLoader()
    
    # Create a test suite
    if test_type == "all" or test_type is None:
        print("Running all tests...")
        test_suite = loader.discover("tests", pattern="test_*.py")
    elif test_type == "environment":
        print("Running environment tests...")
        test_suite = loader.discover("tests", pattern="test_environment.py")
    elif test_type == "core_functions":
        print("Running core functions tests...")
        test_suite = loader.discover("tests", pattern="test_core_functions.py")
    elif test_type == "json":
        print("Running JSON validation tests...")
        test_suite = loader.discover("tests", pattern="test_json_validation.py")
    elif test_type == "schema":
        print("Running schema validation tests...")
        test_suite = loader.discover("tests", pattern="test_schema.py")
    elif test_type == "lint":
        print("Running JSON lint tests...")
        test_suite = loader.discover("tests", pattern="test_json_lint.py")
    elif test_type == "proxy":
        print("Running proxy verification tests...")
        test_suite = loader.discover("tests", pattern="test_verify_proxy_with_request.py")
    else:
        print(f"Unknown test type: {test_type}")
        return 1
    
    # Create a test runner
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    
    # Run the tests
    result = runner.run(test_suite)
    
    # Return the result
    return 0 if result.wasSuccessful() else 1

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run tests for Repl")
    parser.add_argument("--type", choices=["all", "environment", "core_functions", "json", "schema", "lint", "proxy"], default="all",
                        help="Type of tests to run (default: all)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    return run_tests(args.type, args.verbose)

if __name__ == "__main__":
    sys.exit(main()) 