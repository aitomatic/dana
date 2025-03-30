from mcp.server.fastmcp import FastMCP
import httpx
from typing import Dict, Any

# Create an MCP server
mcp = FastMCP("Research Service")

@mcp.tool()
async def search(query: str) -> Dict[str, Any]:
    """Search for information on a given topic using DuckDuckGo API.
    
    Args:
        query: The search query string
        
    Returns:
        Dict containing search results with titles and links
    """
    async with httpx.AsyncClient() as client:
        # Use DuckDuckGo Instant Answer API
        response = await client.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
        )
        data = response.json()
        
        results = {
            "abstract": data.get("Abstract", "No abstract found"),
            "related_topics": [
                {
                    "title": topic.get("Text", ""),
                    "url": topic.get("FirstURL", "")
                }
                for topic in data.get("RelatedTopics", [])[:5]
            ],
            "source_url": data.get("AbstractURL", "")
        }
        
        return results

@mcp.tool()
async def gather_data(topic: str, data_points: int = 5) -> dict:
    """Gather structured data about a specific topic by performing multiple searches.
    
    Args:
        topic: The main topic to research
        data_points: Number of data points to gather
        
    Returns:
        Dict containing gathered data and sources
    """
    search_results = await search(topic)
    
    return {
        "topic": topic,
        "abstract": search_results["abstract"],
        "data_points": [
            topic.get("title") 
            for topic in search_results["related_topics"][:data_points]
        ],
        "sources": [
            topic.get("url")
            for topic in search_results["related_topics"][:data_points]
        ]
    }

if __name__ == "__main__":
    mcp.run()
