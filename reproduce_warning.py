#!/usr/bin/env python3
"""Script to reproduce the exact RuntimeWarning"""

import asyncio
import warnings
import threading
import time
warnings.simplefilter('always', RuntimeWarning)

from dana.core.runtime.eager_promise import EagerPromise
from dana.core.lang.sandbox_context import SandboxContext

async def slow_async_computation():
    """A slow async computation that takes time"""
    print("Starting async computation...")
    await asyncio.sleep(0.5)  # Simulate work
    print("Async computation complete")
    return "async_result"

def test_concurrent_access():
    """Test scenario that might trigger the warning"""
    print("=== Testing Concurrent Access Scenario ===")
    
    context = SandboxContext()
    
    # Create the promise (starts execution immediately)
    promise = EagerPromise(slow_async_computation(), context)
    
    # Immediately try to access result before task completes
    # This should trigger _wait_for_result while task is still running
    print("Immediately accessing result...")
    result = str(promise)
    print(f"Final result: {result}")

def test_no_event_loop():
    """Test with no existing event loop"""
    print("\n=== Testing No Event Loop Scenario ===")
    
    context = SandboxContext()
    
    # Create the promise
    promise = EagerPromise(slow_async_computation(), context)
    
    # Access result
    result = str(promise)
    print(f"Result: {result}")

def test_with_event_loop():
    """Test within an existing event loop"""
    print("\n=== Testing With Event Loop Scenario ===")
    
    async def run_test():
        context = SandboxContext()
        
        # Create the promise within an async context
        promise = EagerPromise(slow_async_computation(), context)
        
        # Access result
        result = str(promise)
        print(f"Result in async context: {result}")
    
    asyncio.run(run_test())

if __name__ == "__main__":
    test_concurrent_access()
    test_no_event_loop() 
    test_with_event_loop()