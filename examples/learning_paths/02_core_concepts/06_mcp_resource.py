"""MCP Resource Example

Demonstrates:
1. Creating and using local MCP services
2. Using remote MCP resources
3. Exposing and connecting between MCP services
"""

import asyncio
import os
from typing import Dict, Any
from dxa.agent import Agent
from dxa.agent.resource import McpLocalResource, McpRemoteResource
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
        
    return documents

async def run_gdrive_example():
    """Run the gdrive example"""
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

    agent = Agent("MCP-Demo-Agent").with_resources({
        "gdrive": gdrive
    })

    # Example: Using google drive service
    print("===================== Listing tools ======================")
    tools = await agent.resources["gdrive"].list_tools()
    for tool in tools:
        print(f"\nTool name: {tool.name}")
        print(f"Description: {tool.description}")
        print(f"Parameters:")
        for param_name, param_details in tool.inputSchema['properties'].items():
            print(f"  - {param_name}: {param_details['description']}")
            if param_details.get('optional'):
                print("    (Optional)")
        print(f"Required parameters: {', '.join(tool.inputSchema['required'])} \n")
    
    print("\n===================== Search files in Google Drive ======================")
    gdrive_response = await agent.resources["gdrive"].query({
        "tool": "gdrive_search",
        "arguments": {
            "query": "dxa",
            "pageSize": 10
        }
    })
    print('-' * 50)
    documents = _extract_files_from_gdrive_search_response(gdrive_response.content.content[0].text)
    for doc in documents:
        print(f"ID: {doc['id']}")
        print(f"Name: {doc['name']}")
        print(f"Type: {doc['type']}")
        print('-' * 50)

    # print("\n===================== Read file from Google Drive ======================")
    # gdrive_response = await agent.resources["gdrive"].query({
    #     "tool": "gdrive_read_file",
    #     "arguments": {
    #         "fileId": documents[0]['id']
    #     }
    # })
    # print(f"File content: {gdrive_response.content}")

async def run_mysql_example():
    """Run the mysql example"""
    mysql = McpLocalResource(
        name="mysql",
        connection_params={
            "command": "npx",
            "args": ["-y", "@h1deya/mcp-server-mysql"]
        }
    )

    agent = Agent("MCP-Demo-Agent").with_resources({
        "mysql": mysql
    })


async def main():

    """Main function demonstrating MCP resource usage"""
    
    await run_gdrive_example()

    await run_mysql_example()

    # https://github.com/cr7258/elasticsearch-mcp-server
    # await run_elasticsearch_example()


if __name__ == "__main__":
    asyncio.run(main())
