"""Example of automation agent for web scraping."""

import asyncio
import os
from dxa.agents.automation import AutomationAgent

# Define the workflow steps
SCRAPING_WORKFLOW = {
    "name": "web_scraping",
    "description": "Scrape data from a website",
    "steps": [
        {
            "name": "initialize",
            "description": "Set up browser and check site accessibility",
            "validation": lambda r, c: r.get("browser_ready", False)
        },
        {
            "name": "navigate",
            "description": "Navigate to target pages",
            "validation": lambda r, c: r.get("page_loaded", False)
        },
        {
            "name": "extract",
            "description": "Extract required data",
            "validation": lambda r, c: len(r.get("extracted_data", [])) > 0
        },
        {
            "name": "process",
            "description": "Process and format extracted data",
            "validation": lambda r, c: r.get("processed_data") is not None
        },
        {
            "name": "save",
            "description": "Save processed data",
            "validation": lambda r, c: r.get("saved", False)
        }
    ]
}

async def main():
    """Run web scraping automation example."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Create automation agent
    agent = AutomationAgent(
        name="web_scraper",
        llm_config={
            "api_key": api_key,
            "model": "gpt-4",
            "system_prompt": """You are a web scraping automation agent.
            Follow the workflow steps carefully and handle errors appropriately.
            Validate each step before proceeding."""
        },
        workflow=SCRAPING_WORKFLOW,
        description="Web scraping automation agent"
    )

    # Initialize agent
    await agent.initialize()

    try:
        # Run the workflow
        result = await agent.run({
            "target_url": "https://example.com",
            "data_requirements": ["title", "description", "price"],
            "output_format": "csv"
        })
        
        if result["success"]:
            print("Scraping completed successfully")
            print(f"Data saved: {result['workflow_state']['step_results'][-1]}")
        else:
            print(f"Scraping failed: {result.get('error')}")
    finally:
        # Clean up resources
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 