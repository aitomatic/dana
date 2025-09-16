#!/usr/bin/env python3
"""
Standalone test for Google Search Service.

This test bypasses import issues by creating minimal test components.
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum
from dataclasses import dataclass

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


# Minimal test models to avoid import issues
class SearchDepth(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    EXTENSIVE = "extensive"


@dataclass
class SearchRequest:
    query: str
    search_depth: SearchDepth = SearchDepth.QUICK
    with_full_content: bool = False


@dataclass
class SearchSource:
    url: str
    content: str
    full_content: str = ""


@dataclass
class SearchResults:
    success: bool
    sources: list[SearchSource]
    error_message: str = ""
    raw_data: str = ""


async def test_google_api_directly():
    """Test Google Custom Search API directly."""
    print("=" * 60)
    print("🔍 Testing Google Custom Search API Directly")
    print("=" * 60)

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_SEARCH_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID") or os.getenv("GOOGLE_SEARCH_CX")

    print(f"API Key found: {'✅' if api_key else '❌'}")
    print(f"CSE ID found: {'✅' if cse_id else '❌'}")

    if not api_key or not cse_id:
        print("❌ Missing credentials. Please check your .env file.")
        return

    # Test with simple HTTP request
    import aiohttp

    query = "Python programming tutorial"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": 3,  # Small number for testing
    }

    try:
        print(f"🔍 Searching for: {query}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as response:
                print(f"📡 API Response Status: {response.status}")

                if response.status == 200:
                    data = await response.json()

                    if "items" in data:
                        items = data["items"]
                        print(f"✅ Found {len(items)} results")

                        for i, item in enumerate(items, 1):
                            print(f"\n📄 Result {i}:")
                            print(f"   Title: {item.get('title', 'No title')}")
                            print(f"   URL: {item.get('link', 'No URL')}")
                            print(f"   Snippet: {item.get('snippet', 'No snippet')[:100]}...")
                    else:
                        print("❌ No 'items' in response")
                        print(f"Response keys: {list(data.keys())}")

                elif response.status == 403:
                    error_data = await response.json()
                    print(f"❌ API Key Error (403): {error_data.get('error', {}).get('message', 'Unknown error')}")

                elif response.status == 400:
                    error_data = await response.json()
                    print(f"❌ Bad Request (400): {error_data.get('error', {}).get('message', 'Unknown error')}")

                else:
                    print(f"❌ HTTP Error {response.status}")
                    text = await response.text()
                    print(f"Response: {text[:200]}...")

    except Exception as e:
        print(f"❌ Error testing Google API: {e}")
        import traceback

        traceback.print_exc()


async def test_environment_variables():
    """Test environment variable loading."""
    print("=" * 60)
    print("⚙️  Testing Environment Variables")
    print("=" * 60)

    env_vars = ["GOOGLE_API_KEY", "GOOGLE_SEARCH_API_KEY", "GOOGLE_CSE_ID", "GOOGLE_SEARCH_CX", "OPENAI_API_KEY"]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask the value for security
            masked = value[:8] + "*" * (len(value) - 12) + value[-4:] if len(value) > 12 else "****"
            print(f"✅ {var}: {masked}")
        else:
            print(f"❌ {var}: Not set")

    # Check .env file exists
    env_file = Path(__file__).parent / ".env"
    print(f"\n📄 .env file exists: {'✅' if env_file.exists() else '❌'}")
    if env_file.exists():
        print(f"📄 .env file size: {env_file.stat().st_size} bytes")


async def test_web_scraping():
    """Test basic web scraping capability."""
    print("=" * 60)
    print("🌐 Testing Web Scraping Capability")
    print("=" * 60)

    test_url = "https://httpbin.org/html"

    try:
        import aiohttp
        from bs4 import BeautifulSoup

        print(f"🔗 Testing URL: {test_url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(test_url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    title = soup.find("title")
                    h1 = soup.find("h1")

                    print("✅ Successfully scraped content")
                    print(f"📄 Title: {title.text if title else 'No title'}")
                    print(f"📄 H1: {h1.text if h1 else 'No H1'}")
                    print(f"📄 Content length: {len(html)} chars")

                else:
                    print(f"❌ HTTP Error: {response.status}")

    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install with: pip install aiohttp beautifulsoup4")

    except Exception as e:
        print(f"❌ Error testing web scraping: {e}")


async def main():
    """Run all tests."""
    print("🚀 Google Search Service Standalone Test Suite")
    print("=" * 60)

    await test_environment_variables()
    await test_google_api_directly()
    await test_web_scraping()

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   1. If API test passed, the service should work!")
    print("   2. Install missing dependencies if needed")
    print("   3. Check that CSE is configured for web search")


if __name__ == "__main__":
    asyncio.run(main())
