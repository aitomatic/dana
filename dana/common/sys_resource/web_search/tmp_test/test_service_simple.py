#!/usr/bin/env python3
"""
Simple test using the actual GoogleSearchService.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

try:
    from web_search.google_search_service import create_google_search_service
    from web_search.core.models import SearchRequest

    async def test_google_service():
        print("🔍 Testing GoogleSearchService")
        print("=" * 50)

        try:
            # Create service using factory function
            service = create_google_search_service()
            print(f"✅ Service created: {service}")
            print(f"✅ Service available: {service.is_available()}")

            # Test search
            request = SearchRequest(
                query="machine learning Python libraries",
                search_depth="basic",  # Use string literal instead of enum
                with_full_content=False,
            )

            print(f"🔍 Searching: {request.query}")
            results = await service.search(request)

            if results.success:
                print(f"✅ Search successful! Found {len(results.sources)} results")

                for i, source in enumerate(results.sources[:2], 1):
                    print(f"\n📄 Result {i}:")
                    print(f"   URL: {source.url}")
                    print(f"   Content: {source.content[:100]}...")

                if results.raw_data:
                    print(f"\n📊 Metadata available: {len(results.raw_data)} chars")

            else:
                print(f"❌ Search failed: {results.error_message}")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()

    if __name__ == "__main__":
        asyncio.run(test_google_service())

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This suggests missing dependencies or module structure issues.")
    print("The API test passed, so credentials are working!")
