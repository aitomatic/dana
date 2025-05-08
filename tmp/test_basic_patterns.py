#!/usr/bin/env python
"""Test basic pattern handling in DANA transcoder."""

import asyncio
import re
from opendxa.common.types import BaseResponse
from opendxa.dana.runtime.repl import REPL
from opendxa.dana.language.parser import parse

# Mock LLM resource for testing
class MockLLMResource:
    def __init__(self):
        self.provider = 'mock'
        self.model = 'test'
        self.name = 'mock_llm'
    
    async def query(self, request):
        # Just return something simple for testing
        return BaseResponse(success=True, content='private.result = 42')

def test_regex_patterns():
    """Test that the regex patterns correctly match inputs."""
    print("\n=== Testing Regex Patterns ===")
    
    # Test inputs
    inputs = [
        "5+5",
        "-899",
        "a=5"
    ]
    
    # Test regex patterns
    pattern_math = r'^\s*\d+\s*[+\-*/]\s*\d+\s*$'
    pattern_number = r'^\s*-?\d+\.?\d*\s*$'
    pattern_assignment = r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)\s*$'
    
    for input_text in inputs:
        print(f"\nInput: '{input_text}'")
        
        # Test each pattern
        math_match = re.match(pattern_math, input_text)
        number_match = re.match(pattern_number, input_text)
        assignment_match = re.match(pattern_assignment, input_text)
        
        print(f"Math pattern match: {bool(math_match)}")
        print(f"Number pattern match: {bool(number_match)}")
        print(f"Assignment pattern match: {bool(assignment_match)}")
        
        # Generate DANA code for matching patterns
        if math_match:
            dana_code = f"private.result = {input_text}"
            print(f"→ Math pattern generates: {dana_code}")
            
            # Test parsing
            try:
                result = parse(dana_code)
                print(f"  Parse valid: {result.is_valid}")
            except Exception as e:
                print(f"  Parse error: {e}")
        
        if number_match:
            dana_code = f"private.result = {input_text}"
            print(f"→ Number pattern generates: {dana_code}")
            
            # Test parsing
            try:
                result = parse(dana_code)
                print(f"  Parse valid: {result.is_valid}")
            except Exception as e:
                print(f"  Parse error: {e}")
        
        if assignment_match:
            var_name = assignment_match.group(1)
            value = assignment_match.group(2)
            dana_code = f"private.{var_name} = {value}"
            print(f"→ Assignment pattern generates: {dana_code}")
            
            # Test parsing
            try:
                result = parse(dana_code)
                print(f"  Parse valid: {result.is_valid}")
            except Exception as e:
                print(f"  Parse error: {e}")

async def test_repl_parsing():
    """Test basic patterns with REPL NLP mode."""
    print("\n=== Testing REPL Parsing ===")
    
    # Create mock LLM resource
    llm = MockLLMResource()
    
    # Create REPL with NLP mode enabled
    repl = REPL(llm_resource=llm, nlp_mode=True)
    
    # Test inputs
    inputs = [
        "5+5",
        "-899",
        "a=5"
    ]
    
    for input_text in inputs:
        print(f"\nREPL input: '{input_text}'")
        try:
            result = await repl.execute(input_text)
            print(f"Success! Result: {result}")
            
            # Print context value
            if 'private' in repl.context._state:
                if 'result' in repl.context._state['private']:
                    print(f"Context value: private.result = {repl.context._state['private']['result']}")
                if input_text.startswith('a='):
                    print(f"Context value: private.a = {repl.context._state['private'].get('a', 'not found')}")
        except Exception as e:
            print(f"Failed: {e}")

async def main():
    # Test regex patterns
    test_regex_patterns()
    
    # Test REPL with NLP mode
    await test_repl_parsing()

if __name__ == "__main__":
    asyncio.run(main())