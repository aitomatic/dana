#!/usr/bin/env python3
"""Debug script to understand safe_asyncio_run behavior"""

import asyncio
import warnings
warnings.simplefilter('always', RuntimeWarning)

from dana.common.utils.misc import Misc

class TestClass:
    async def async_method(self):
        await asyncio.sleep(0.1)
        return "success"

def test_safe_asyncio_run():
    """Test how safe_asyncio_run handles async methods"""
    obj = TestClass()
    
    print("Testing safe_asyncio_run with async method...")
    
    try:
        # This is how it's called in eager_promise.py
        result = Misc.safe_asyncio_run(obj.async_method)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_safe_asyncio_run()