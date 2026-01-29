#!/usr/bin/env python3
"""OpenAI Web Search Script - Uses OpenAI Responses API with web_search_preview tool."""

import argparse
import json
import os
from openai import OpenAI


def search(query: str, max_results: int = 5) -> dict:
    """Execute web search via OpenAI Responses API."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    response = client.responses.create(
        model="gpt-4.1",
        tools=[{"type": "web_search_preview"}],
        input=query,
    )

    # Extract results from response
    sources = []
    summary = ""

    for item in response.output:
        if item.type == "web_search_call":
            # Extract search results
            if hasattr(item, "results"):
                for result in item.results[:max_results]:
                    sources.append({"url": result.url, "title": result.title, "content": result.snippet or ""})
        elif item.type == "message":
            summary = item.content[0].text if item.content else ""

    return {"success": True, "query": query, "sources": sources, "summary": summary}


def main():
    parser = argparse.ArgumentParser(description="OpenAI Web Search")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--max-results", "-n", type=int, default=5, help="Max results")
    args = parser.parse_args()

    try:
        result = search(args.query, args.max_results)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
