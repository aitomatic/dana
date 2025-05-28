#!/usr/bin/env python3
import os

import lark

# Read the common.lark file
common_path = os.path.join(os.path.dirname(lark.__file__), "grammars", "common.lark")
with open(common_path) as f:
    content = f.read()

# Look for string-related definitions
lines = content.split("\n")
for i, line in enumerate(lines):
    if "STRING" in line or "string" in line:
        print(f"Line {i+1}: {line}")
