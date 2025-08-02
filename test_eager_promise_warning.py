#!/usr/bin/env python3
"""Test script to reproduce the RuntimeWarning in eager_promise.py"""

import asyncio
import warnings
warnings.simplefilter('always')

from dana.core.runtime.eager_promise import EagerPromise
from dana.core.lang.sandbox_context import SandboxContext

async def slow_coroutine():
    """A coroutine that takes some time to complete"""
    await asyncio.sleep(0.2)
    return 'slow result'

def test_eager_promise_warning():
    """Test that reproduces the RuntimeWarning"""
    print("Creating EagerPromise with async coroutine...")
    
    context = SandboxContext()
    
    # Create the promise - this starts execution immediately
    promise = EagerPromise(slow_coroutine(), context)
    
    # Immediately try to access the result - this should trigger _wait_for_result
    # and potentially the RuntimeWarning
    print("Accessing result immediately...")
    result = str(promise)
    print(f"Result: {result}")

if __name__ == "__main__":
    test_eager_promise_warning()