#!/usr/bin/env python
"""Fix pattern handlers in the DANA transcoder."""

import sys
import re

def fix_regex_patterns(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix all incomplete regex patterns (missing $ at end)
    # Be careful to only fix the pattern strings, not other code
    patterns = [
        (r'^\s*\d+\s*[+\-*/]\s*\d+\s*,', r'^\s*\d+\s*[+\-*/]\s*\d+\s*$',),
        (r'^\s*-?\d+\.?\d*\s*,', r'^\s*-?\d+\.?\d*\s*$',),
        (r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)\s*,', r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)\s*$',),
    ]
    
    # Replace the patterns
    fixed_content = content
    for old, new in patterns:
        old_with_quotes = f"r'{old}'"
        new_with_quotes = f"r'{new}'"
        fixed_content = fixed_content.replace(old_with_quotes, new_with_quotes)
    
    # Fix the message variable definition
    if "if input_lower.startswith(\"print \"):" in fixed_content:
        idx = fixed_content.find("if input_lower.startswith(\"print \"):")
        if idx > 0:
            next_line_idx = fixed_content.find("\n", idx) + 1
            # Add the missing message variable definition
            message_def = "            message = input_text[6:].strip()  # Remove \"print \"\n"
            fixed_content = fixed_content[:next_line_idx] + message_def + fixed_content[next_line_idx:]
    
    # Remove duplicate pattern handlers
    if "# Handle single number inputs like \"42\" or \"-899\"" in fixed_content:
        count = fixed_content.count("# Handle single number inputs like \"42\" or \"-899\"")
        if count > 1:
            # Keep only the first occurrence and remove duplicates
            first_idx = fixed_content.find("# Handle single number inputs like \"42\" or \"-899\"")
            rest_idx = fixed_content.find("# Handle single number inputs like \"42\" or \"-899\"", first_idx + 1)
            
            # Calculate where the block ends
            if rest_idx > 0:
                second_pattern_start = fixed_content.find("# Handle ", rest_idx + 10)
                if second_pattern_start > rest_idx:
                    # Remove the entire duplicate block
                    fixed_content = fixed_content[:rest_idx] + fixed_content[second_pattern_start:]
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    print(f"Fixed regex patterns in {file_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fix_regex_patterns(sys.argv[1])
    else:
        print("Usage: python fix_patterns.py <file_path>")