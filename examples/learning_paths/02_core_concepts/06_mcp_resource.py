"""MCP Resource Example

Demonstrates:
1. Creating and using local MCP services
2. Using remote MCP resources
3. Exposing and connecting between MCP services
"""

import asyncio
import os
from typing import cast
from dxa.agent import Agent
from dxa.agent.resource import McpLocalResource
from dxa.common import DXA_LOGGER

# Configure logging
DXA_LOGGER.basicConfig(level=DXA_LOGGER.DEBUG)
logger = DXA_LOGGER.getLogger(__file__.rsplit('/', maxsplit=1)[-1])

def _extract_files_from_gdrive_search_response(text):
    """Extract document information from text.
    
    Args:
        text (str): Text containing document information
        
    Returns:
        List[Dict[str, str]]: List of documents with id, name and type
    """
    print("\nProcessing Google Drive search response...")
    documents = []
    lines = text.split('\n')
    
    for line in lines:
        if not line.strip():
            continue
            
        # Split by space and get first part as ID
        parts = line.split()
        if not parts:
            continue
            
        doc_id = parts[0]
        
        # Get name by joining parts between ID and type
        type_start = line.rfind('(')  # Changed to rfind to get last parenthesis
        if type_start == -1:
            continue
            
        name = line[len(doc_id):type_start].strip()
        doc_type = line[type_start:].strip('()')
        
        documents.append({
            'id': doc_id,
            'name': name,
            'type': doc_type
        })
    
    print(f"Found {len(documents)} documents in the search results")
    return documents

async def run_gdrive_example():
    """Run the gdrive example"""
    print("\n=== Starting Google Drive MCP Resource Example ===")
    print("Initializing Google Drive MCP resource...")
    
    gdrive = McpLocalResource(
        name="gdrive",
        connection_params={
            "command": "npx",
            "args": ["-y", "@isaacphi/mcp-gdrive"],
            "env": {
                "GDRIVE_CREDS_DIR": os.getenv("GDRIVE_CREDS_DIR"),
                "CLIENT_ID": os.getenv("CLIENT_ID"),
                "CLIENT_SECRET": os.getenv("CLIENT_SECRET")
            }
        }
    )

    print("Creating agent with Google Drive resource...")
    agent = Agent("MCP-Demo-Agent").with_resources({
        "gdrive": gdrive
    })

    # Example: Using google drive service
    print("\n=== Step 1: Discovering Available Tools ===")
    print("Querying available Google Drive tools...")
    resource = cast(McpLocalResource, agent.resources["gdrive"])
    tools = await resource.list_tools()
    print(f"Found {len(tools)} available tools")
    
    for tool in tools:
        print(f"\nTool: {tool.name}")
        print(f"Description: {tool.description}")
        print("Parameters:")
        for param_name, param_details in tool.inputSchema['properties'].items():
            print(f"  - {param_name}: {param_details['description']}")
            if param_details.get('optional'):
                print("    (Optional)")
        print(f"Required parameters: {', '.join(tool.inputSchema['required'])}")
    
    print("\n=== Step 2: Searching Google Drive ===")
    print("Executing search query for 'dxa'...")
    gdrive_response = await agent.resources["gdrive"].query({
        "tool": "gdrive_search",
        "arguments": {
            "query": "dxa",
            "pageSize": 10
        }
    })
    print('-' * 50)

    assert gdrive_response is not None, "gdrive_response is None"
    assert gdrive_response.content is not None, "gdrive_response.content is None"
    assert gdrive_response.content.content is not None, "gdrive_response.content.content is None"
    assert len(gdrive_response.content.content) > 0, "gdrive_response.content.content is empty"
    documents = _extract_files_from_gdrive_search_response(gdrive_response.content.content[0].text)
    print("\nSearch Results:")
    for doc in documents:
        print(f"ID: {doc['id']}")
        print(f"Name: {doc['name']}")
        print(f"Type: {doc['type']}")
        print('-' * 50)

    print("\n=== Step 3: File Reading (Commented Out) ===")
    print("Note: The file reading functionality is commented out to avoid potential issues.")
    print("To read a file, uncomment the code block below and provide a valid file ID.")
    # print("\n===================== Read file from Google Drive ======================")
    # gdrive_response = await agent.resources["gdrive"].query({
    #     "tool": "gdrive_read_file",
    #     "arguments": {
    #         "fileId": documents[0]['id']
    #     }
    # })
    # print(f"File content: {gdrive_response.content}")


async def main():
    """Main function demonstrating MCP resource usage"""
    print("=== MCP Resource Examples ===")
    print("This example demonstrates how to use MCP (Model Control Protocol) resources")
    
    await run_gdrive_example()


if __name__ == "__main__":
    asyncio.run(main())
