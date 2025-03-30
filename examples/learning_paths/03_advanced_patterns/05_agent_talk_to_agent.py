import asyncio
import json
from dxa.agent import Agent
from dxa.agent.resource import McpLocalResource, McpRemoteResource
from dxa.common import DXA_LOGGER

# Configure logging
DXA_LOGGER.basicConfig(level=DXA_LOGGER.INFO)
logger = DXA_LOGGER.getLogger("multi_agent_mcp")

# Paths to MCP service scripts
RESEARCH_SERVICE_SCRIPT = "./mcp_servers/research.py"
REASONING_SERVICE_SCRIPT = "./mcp_servers/reasoning.py"
EXECUTION_SERVICE_SCRIPT = "./mcp_servers/execution.py"

async def setup_agents():
    """Create and configure all agents with their MCP resources"""
    
    # Create the research agent with exposed MCP server
    research_agent = Agent("research-agent").with_resources({
        "research": McpLocalResource(
            name="research",
            connection_params={
                "command": "python3",
                "args": [RESEARCH_SERVICE_SCRIPT]
            },
            expose=True
        )
    })
    
    # Initialize research agent resources to start the server
    await research_agent.resources["research"].initialize()
    
    # Get connection parameters from the research agent
    research_local_connection_params = research_agent.resources["research"].get_connection_params()
    reasoning_agent = Agent("reasoning-agent").with_resources({
        "reasoning": McpLocalResource(
            name="reasoning",
            connection_params={
                "command": "python3",
                "args": [REASONING_SERVICE_SCRIPT]
            },
            expose=True
        ),
        # Connect to research agent's MCP server using its connection parameters
        "research": McpLocalResource(
            name="research",
            connection_params=research_local_connection_params
        )
    })
    
    # Initialize reasoning agent resources
    await reasoning_agent.resources["reasoning"].initialize()
    
    # Get connection parameters from the reasoning agent
    reasoning_local_connection_params = reasoning_agent.resources["reasoning"].get_connection_params()
    
    # Create the execution agent with connections to other agents
    execution_agent = Agent("execution-agent").with_resources({
        "execution": McpLocalResource(
            name="execution",
            connection_params={
                "command": "python3",
                "args": [EXECUTION_SERVICE_SCRIPT]
            }
        ),
        # Connect to reasoning agent's MCP server using its connection parameters
        "reasoning": McpLocalResource(
            name="reasoning",
            connection_params=reasoning_local_connection_params
        ),
        # Also connect to research agent's MCP server
        "research": McpLocalResource(
            name="research",
            connection_params=research_local_connection_params
        )
    })
    
    # Initialize execution agent resources
    await execution_agent.resources["execution"].initialize()
    
    return research_agent, reasoning_agent, execution_agent

async def execute_research_task(research_agent):
    """Execute a research task directly using the research agent"""
    logger.info("Executing research task...")
    
    # Query the research agent's MCP resource directly
    response = await research_agent.resources["research"].query({
        "tool": "gather_data",
        "arguments": {"topic": "renewable energy", "data_points": 5}
    })
    
    if not response.success:
        logger.error(f"Research failed: {response.error}")
        return None
    
    content = response.content.content[0].text          
    logger.info(f"Research data: {json.dumps(content, indent=2)}")
    return content

async def execute_analysis_task(reasoning_agent, research_data):
    """Execute an analysis task directly using the reasoning agent"""
    logger.info("Executing analysis task...")
    
    # Query the reasoning agent's MCP resource directly
    response = await reasoning_agent.resources["reasoning"].query({
        "tool": "analyze",
        "arguments": {"data": research_data}
    })
    
    if not response.success:
        logger.error(f"Analysis failed: {response.error}")
        return None
        
    content = response.content.content[0].text
    logger.info(f"Analysis results: {json.dumps(content, indent=2)}")
    return content

async def execute_plan(execution_agent, plan):
    """Execute a plan using the execution agent"""
    logger.info("Executing plan...")
    
    # Query the execution agent's MCP resource directly
    response = await execution_agent.resources["execution"].query({
        "tool": "execute_plan",
        "arguments": {"plan": plan}
    })
    
    if not response.success:
        logger.error(f"Execution failed: {response.error}")
        return None
        
    content = response.content.content[0].text
    logger.info(f"Execution results: {json.dumps(content, indent=2)}")
    return content

async def agent_to_agent_communication(execution_agent):
    """Demonstrate agent-to-agent communication through MCP resources"""
    logger.info("Demonstrating agent-to-agent communication...")
    
    # Execution agent queries research agent through MCP
    research_response = await execution_agent.resources["research"].query({
        "tool": "search",
        "arguments": {"query": "climate change mitigation"}
    })
    
    if not research_response.success:
        logger.error(f"Research query failed: {research_response.error}")
        return
    
    content = research_response.content.content[0].text
    logger.info(f"Research results: {json.dumps(content, indent=2)}")
    
    # Execution agent queries reasoning agent through MCP
    options = ["Implement solar panels", "Invest in wind turbines", "Develop geothermal solutions"]
    reasoning_response = await execution_agent.resources["reasoning"].query({
        "tool": "evaluate_options",
        "arguments": {"options": options}
    })
    
    if not reasoning_response.success:
        logger.error(f"Reasoning query failed: {reasoning_response.error}")
        return
        
    content = reasoning_response.content.content[0].text
    logger.info(f"Reasoning results: {json.dumps(content, indent=2)}")
    
    # Create and execute a plan based on reasoning results
    content = json.loads(content)
    best_option = content.get("best_option")
    plan = {
        "steps": [best_option],
        "reasoning": content.get("reasoning", "")
    }
    
    await execute_plan(execution_agent, plan)

async def complex_workflow(research_agent, reasoning_agent, execution_agent):
    """Execute a complex workflow involving all three agents"""
    logger.info("Executing complex workflow...")
    
    # Step 1: Research phase
    research_data = await execute_research_task(research_agent)
    if not research_data:
        return
    
    # Step 2: Analysis phase
    analysis = await execute_analysis_task(reasoning_agent, research_data)
    if not analysis:
        return
    
    # Step 3: Create options based on analysis
    content = json.loads(analysis)
    options = [
        f"Implement {content['key_insights'][0]}",
        f"Develop strategy for {content['key_insights'][1]}",
        f"Research more on {content['key_insights'][2]}"
    ]
    
    # Step 4: Evaluate options using reasoning agent
    reasoning_response = await reasoning_agent.resources["reasoning"].query({
        "tool": "evaluate_options",
        "arguments": {"options": options}
    })
    
    if not reasoning_response.success:
        logger.error(f"Option evaluation failed: {reasoning_response.error}")
        return
    
    # Step 5: Create a plan
    content = json.loads(reasoning_response.content.content[0].text)
    best_option = content.get("best_option")
    plan = {
        "steps": [best_option],
        "reasoning": content.get("reasoning", "")
    }
    
    # Step 6: Execute the plan
    execution_result = await execute_plan(execution_agent, plan)
    if not execution_result:
        return
    
    # Step 7: Send notification through execution agent
    notification_response = await execution_agent.resources["execution"].query({
        "tool": "notify",
        "arguments": {
            "message": f"Workflow completed successfully. Executed: {best_option}",
            "channel": "admin"
        }
    })
    
    if notification_response.success:
        content = notification_response.content.content[0].text
        logger.info(f"Notification sent: {json.dumps(content, indent=2)}")
    else:
        logger.error(f"Notification failed: {notification_response.error}")


async def main():
    """Main function to orchestrate the multi-agent system"""
    try:
        # Setup all agents
        research_agent, reasoning_agent, execution_agent = await setup_agents()
        
        await execute_research_task(research_agent)
        
        # Run agent-to-agent communication example
        await agent_to_agent_communication(execution_agent)
        
        # Run complex workflow involving all agents
        await complex_workflow(research_agent, reasoning_agent, execution_agent)
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
    finally:
        for agent in (research_agent, reasoning_agent, execution_agent):
            if agent:
                for resource in agent.resources.values():
                    await resource.cleanup()

if __name__ == "__main__":
    asyncio.run(main())