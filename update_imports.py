#!/usr/bin/env python
"""Script to update interpreter imports in test files."""

import os
import re

def update_file(file_path):
    """Update imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace import statements
    new_content = re.sub(
        r'from opendxa\.dana\.runtime\.interpreter import', 
        r'from opendxa.dana.runtime.interpreter_new import', 
        content
    )
    
    # Only write if changes were made
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    return False

def main():
    """Find and update all test files."""
    tests_dir = os.path.join("tests", "dana")
    updated_files = []
    
    for root, _, files in os.walk(tests_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if update_file(file_path):
                    updated_files.append(file_path)
    
    print(f"Updated {len(updated_files)} files:")
    for file in updated_files:
        print(f"  - {file}")

if __name__ == "__main__":
    main()