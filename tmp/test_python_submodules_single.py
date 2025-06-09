#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, '/Users/ctn/src/aitomatic/opendxa')

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox

def test_python_submodules_single():
    print("=== Testing Python Submodules with Single Imports ===")
    
    sandbox = DanaSandbox()
    
    # Test 1: os.path with single imports
    print("\n1. os.path with single from-imports:")
    result1 = sandbox.eval('from os.path.py import exists')
    print(f"   from os.path.py import exists: {result1.success}")
    
    result2 = sandbox.eval('from os.path.py import join')  
    print(f"   from os.path.py import join: {result2.success}")
    
    if result1.success and result2.success:
        result3 = sandbox.eval('exists("/")')
        print(f"   exists('/'): {result3.success} -> {result3.result}")
        
        result4 = sandbox.eval('join("usr", "local")')
        print(f"   join(): {result4.success} -> {result4.result}")
    
    # Test 2: urllib.parse 
    print("\n2. urllib.parse with single imports:")
    result1 = sandbox.eval('from urllib.parse.py import urlparse')
    print(f"   from urllib.parse.py import urlparse: {result1.success}")
    
    result2 = sandbox.eval('from urllib.parse.py import urljoin')
    print(f"   from urllib.parse.py import urljoin: {result2.success}")
    
    if result1.success and result2.success:
        result3 = sandbox.eval('urlparse("https://example.com/path?q=1")')
        print(f"   urlparse(): {result3.success} -> {type(result3.result)}")
        
        result4 = sandbox.eval('urljoin("https://example.com/", "page")')
        print(f"   urljoin(): {result4.success} -> {result4.result}")
    
    # Test 3: Multiple Python submodules in sequence
    print("\n3. Multiple Python submodule imports:")
    results = []
    
    commands = [
        'import os.path.py',
        'import urllib.parse.py', 
        'import xml.etree.py'
    ]
    
    for cmd in commands:
        result = sandbox.eval(cmd)
        results.append((cmd, result.success))
        print(f"   {cmd}: {result.success}")
    
    # Test using all imported modules
    if all(success for _, success in results):
        print("\n   Testing usage of all imported modules:")
        
        result1 = sandbox.eval('os.path.exists("/tmp")')
        print(f"   os.path.exists(): {result1.success} -> {result1.result}")
        
        result2 = sandbox.eval('urllib.parse.quote("hello world")')
        print(f"   urllib.parse.quote(): {result2.success} -> {result2.result}")
    
    # Test 4: Check if dotted names are properly stored
    print("\n4. Check module namespace structure:")
    result = sandbox.eval('import os.path.py')
    if result.success:
        try:
            # Try to access the nested structure
            result2 = sandbox.eval('type(os)')
            print(f"   type(os): {result2.success} -> {result2.result}")
            
            result3 = sandbox.eval('type(os.path)')
            print(f"   type(os.path): {result3.success} -> {result3.result}")
            
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    test_python_submodules_single() 