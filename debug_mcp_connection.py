"""
Debug the MCP connection to see what's actually happening.
"""

from dana_agent.dana.lib.resources import BrightQueryResource


def debug_mcp_connection():
    """Debug the MCP connection step by step."""
    print("=== Debugging MCP Connection ===")

    try:
        # Create BrightQueryResource
        print("1. Creating BrightQueryResource...")
        brightdata = BrightQueryResource(api_token="82610a5dd3b24178236d398910c40c0cbd1fba0434b7851e12c524c7f6c778bc")
        print("✓ Resource created")

        # Check if process is running
        print(f"2. Process running: {brightdata._process is not None}")
        if brightdata._process:
            print(f"   Process PID: {brightdata._process.pid}")
            print(f"   Process return code: {brightdata._process.poll()}")

        # Try to get available methods first
        print("3. Trying to get available methods...")
        try:
            methods = brightdata.get_available_methods()
            print(f"✓ Available methods: {methods}")
        except Exception as e:
            print(f"✗ Failed to get methods: {e}")

        # Try a simple search
        print("4. Trying a simple search...")
        try:
            result = brightdata.search(query="test", limit=1)
            print(f"✓ Search result: {result}")
        except Exception as e:
            print(f"✗ Search failed: {e}")

        # Check process status
        print("5. Checking process status...")
        if brightdata._process:
            print(f"   Process still running: {brightdata._process.poll() is None}")
            if brightdata._process.stderr:
                try:
                    stderr_output = brightdata._process.stderr.read()
                    if stderr_output:
                        print(f"   Stderr: {stderr_output}")
                except:
                    pass

        # Try to read from stdout
        print("6. Checking stdout...")
        if brightdata._process and brightdata._process.stdout:
            try:
                # Try to read a line
                import select
                import sys

                if sys.platform != "win32":
                    # Use select for non-Windows
                    ready, _, _ = select.select([brightdata._process.stdout], [], [], 1)
                    if ready:
                        line = brightdata._process.stdout.readline()
                        print(f"   Read from stdout: {line}")
                    else:
                        print("   No data available on stdout")
                else:
                    print("   Windows - skipping select check")
            except Exception as e:
                print(f"   Error reading stdout: {e}")

        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_manual_mcp_call():
    """Test making a manual MCP call to see the raw communication."""
    print("\n=== Testing Manual MCP Call ===")

    try:
        brightdata = BrightQueryResource(api_token="82610a5dd3b24178236d398910c40c0cbd1fba0434b7851e12c524c7f6c778bc")

        # Make a direct MCP call
        print("Making direct MCP call...")
        result = brightdata._make_mcp_call("search", {"query": "test", "limit": 1})
        print(f"Direct call result: {result}")

    except Exception as e:
        print(f"Direct call failed: {e}")


if __name__ == "__main__":
    debug_mcp_connection()
    test_manual_mcp_call()
