#!/usr/bin/env python3
"""Test MSFT stock price query with STARAgent."""

import os
import sys
import logging
import re
from pathlib import Path

# Load environment
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.strip().startswith('#'):
            key, _, value = line.partition('=')
            os.environ[key.strip()] = value.strip()

logging.basicConfig(level=logging.WARNING)

from dana.core.agent.star_agent import STARAgent

def test_msft_price():
    """Test that STARAgent can get MSFT stock price."""
    print("Creating STARAgent...")
    agent = STARAgent()

    query = "What is the current MSFT stock price?"
    print(f"Sending query: '{query}'")
    print("=" * 60)

    result = agent.query(message=query)
    response = result.get("response", "No response")

    print("\nFINAL RESPONSE:")
    print("=" * 60)
    print(response)
    print("=" * 60)

    # Check for price
    has_price = bool(re.search(r'\$\d+\.?\d*', str(response)))
    print(f"\nContains price: {has_price}")

    return has_price

if __name__ == "__main__":
    success = test_msft_price()
    sys.exit(0 if success else 1)
