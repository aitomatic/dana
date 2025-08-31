#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')

from dana.core.lang.interpreter.context_detection import ContextDetector

detector = ContextDetector()

# Test the specific case that's failing with comprehensive debug output
docstring = 'Return type dict'
print(f'Testing: "{docstring}"')
docstring_lower = docstring.lower()
print(f'Lowercase: "{docstring_lower}"')

# Simulate the exact logic from the method
print('\n--- Simulating method logic ---')

# First pattern loop
type_patterns = [
    'returns:', 'returns', 'return:', 'return', 'rtype:', 'rtype', 'return type:'
]

print(f'Type patterns: {type_patterns}')

for pattern in type_patterns:
    if pattern in docstring_lower:
        print(f'Pattern "{pattern}" found in docstring')
        parts = docstring_lower.split(pattern)
        print(f'Split parts: {parts}')
        if len(parts) > 1:
            after_pattern = parts[1].strip()
            print(f'After pattern: "{after_pattern}"')
            words = after_pattern.split()
            print(f'Words: {words}')
            if words:
                articles = ['a', 'an', 'the', 'value', 'result']
                for word in words:
                    potential_type = word.strip('.,;:')
                    print(f'Checking word: "{potential_type}"')
                    if potential_type not in articles:
                        print(f'Found potential type: "{potential_type}"')
                        type_mapping = {
                            'string': 'str',
                            'integer': 'int',
                            'boolean': 'bool',
                            'float': 'float',
                            'list': 'list',
                            'dict': 'dict',
                            'object': 'dict',
                            'array': 'list',
                        }
                        result = type_mapping.get(potential_type, potential_type)
                        print(f'Returning: {result}')
                        # Don't actually return, just simulate
                        break
                else:
                    print('No valid type found in this pattern')
                    continue
                break
        else:
            print('No parts after splitting')
    else:
        print(f'Pattern "{pattern}" NOT found')

print('\n--- Checking "return type" pattern ---')
if "return type" in docstring_lower:
    print('"return type" found in docstring')
    parts = docstring_lower.split("return type")
    print(f'Split parts: {parts}')
    if len(parts) > 1:
        type_part = parts[1].strip()
        print(f'Type part: "{type_part}"')
        words = type_part.split()
        print(f'Words: {words}')
        if words:
            start_idx = 0
            if words[start_idx].strip('.,;:') == "type":
                start_idx = 1
                print(f'Starting index after skipping "type": {start_idx}')
            
            if start_idx < len(words):
                potential_type = words[start_idx].strip('.,;:')
                print(f'Potential type: "{potential_type}"')
                type_mapping = {
                    'string': 'str',
                    'integer': 'int',
                    'boolean': 'bool',
                    'float': 'float',
                    'list': 'list',
                    'dict': 'dict',
                    'object': 'dict',
                    'array': 'list',
                }
                result = type_mapping.get(potential_type, potential_type)
                print(f'Would return: {result}')
            else:
                print('No words left after skipping "type"')
        else:
            print('No words found in type part')
    else:
        print('No parts after splitting')
else:
    print('"return type" NOT found in docstring')

print('\n--- Full method test ---')
result = detector._extract_type_from_docstring(docstring)
print(f'Final result: {result!r}')
