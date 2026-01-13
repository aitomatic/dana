#!/usr/bin/env python3
"""
Simple test for GoogleSearchService.

This test script demonstrates how to use the Google Search Service with
different search depths and configurations.

Prerequisites:
1. Fill in the .env file with your Google API credentials
2. Install dependencies: pip install python-dotenv loguru
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to Python path to handle relative imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Load environment variables from .env file in this directory
env_path = current_dir / ".env"
load_dotenv(env_path)

try:
    from google_search_service import GoogleSearchService, MockGoogleSearchService
    from core.models import SearchRequest, SearchDepth
except ImportError as e:
    print(f"Import error: {e}")
    print("Attempting to run from module context...")

    # Try to run as module
    import subprocess

    result = subprocess.run([sys.executable, "-m", "test_google_search_module"], cwd=current_dir.parent, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    sys.exit(0)


async def test_basic_search():
    """Test basic Google search functionality."""
    print("=" * 60)
    print("🔍 Testing Basic Google Search")
    print("=" * 60)

    # Check if credentials are available
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")

    if not api_key or not cse_id:
        print("❌ Google credentials not found in .env file")
        print("📝 Using MockGoogleSearchService instead")
        service = MockGoogleSearchService()
    else:
        print("✅ Google credentials found")
        try:
            service = GoogleSearchService()
            if not service.is_available():
                print("❌ Google Search Service not available")
                return
        except Exception as e:
            print(f"❌ Failed to initialize GoogleSearchService: {e}")
            print("📝 Using MockGoogleSearchService instead")
            service = MockGoogleSearchService()

    # Test query
    query = "Python web scraping with BeautifulSoup"

    request = SearchRequest(query=query, search_depth=SearchDepth.QUICK, with_full_content=False)

    print(f"🔍 Searching for: {query}")
    print(f"🎯 Search depth: {request.search_depth}")
    print()

    try:
        # Execute search
        results = await service.search(request)

        if results.success:
            print("✅ Search completed successfully!")
            print(f"📊 Found {len(results.sources)} results")
            print()

            # Display results
            for i, source in enumerate(results.sources[:3], 1):  # Show first 3 results
                print(f"📄 Result {i}:")
                print(f"   URL: {source.url}")
                print(f"   Content preview: {source.content[:150]}...")
                print()

            if results.raw_data:
                print("📊 Raw search metadata:")
                print(results.raw_data)

        else:
            print(f"❌ Search failed: {results.error_message}")

    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback

        traceback.print_exc()


async def test_different_search_depths():
    """Test different search depths."""
    print("=" * 60)
    print("🎯 Testing Different Search Depths")
    print("=" * 60)

    # Use mock service for this test to avoid API usage
    service = MockGoogleSearchService()
    query = "machine learning algorithms"

    search_depths = [SearchDepth.QUICK, SearchDepth.STANDARD, SearchDepth.EXTENSIVE]

    for depth in search_depths:
        print(f"\n🔍 Testing {depth} search...")

        request = SearchRequest(query=query, search_depth=depth, with_full_content=False)

        try:
            results = await service.search(request)

            if results.success:
                print(f"✅ {depth} search: {len(results.sources)} results")
            else:
                print(f"❌ {depth} search failed: {results.error_message}")

        except Exception as e:
            print(f"❌ Error in {depth} search: {e}")


async def test_content_summarization():
    """Test content summarization capability."""
    print("=" * 60)
    print("📝 Testing Content Summarization")
    print("=" * 60)

    # Check if OpenAI key is available
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY not found - content summarization will be disabled")
    else:
        print("✅ OpenAI API key found - content summarization enabled")

    try:
        # Try to initialize with summarization
        service = GoogleSearchService(enable_summarization=True)
        print(f"✅ Service initialized: {service}")

        # Check if content processor is available
        if service.content_processor:
            print("✅ Content processing enabled")
        else:
            print("❌ Content processing disabled")

    except Exception as e:
        print(f"❌ Failed to test content summarization: {e}")


async def test_service_availability():
    """Test service availability and configuration."""
    print("=" * 60)
    print("⚙️  Testing Service Configuration")
    print("=" * 60)

    try:
        # Test with environment configuration
        api_key = os.getenv("GOOGLE_API_KEY")
        cse_id = os.getenv("GOOGLE_CSE_ID")

        if api_key and cse_id:
            service = GoogleSearchService()
            print(f"✅ Service configuration: {service}")
            print(f"✅ Service available: {service.is_available()}")

            config = service.get_config()
            print(f"📊 Max results: {config.max_results}")
            print(f"📊 Content extraction: {config.enable_content_extraction}")
            print(f"📊 Timeout: {config.timeout_seconds}s")

        else:
            print("❌ Missing credentials - cannot test real service")
            print("📝 Please fill in your .env file with Google API credentials")

    except Exception as e:
        print(f"❌ Error testing service configuration: {e}")


async def main():
    """Run all tests."""
    print("🚀 Google Search Service Test Suite")
    print("=" * 60)

    await test_service_availability()
    await test_basic_search()
    await test_different_search_depths()
    await test_content_summarization()

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())
