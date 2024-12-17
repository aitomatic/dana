"""Data analysis example using DXA."""

from dxa.agent import Agent
from dxa.core.resource import LLMResource, DataResource, VisualizationResource

async def main():
    """Run data analysis task."""
    
    # Create analysis agent with DANA reasoning
    agent = Agent("analyst")\
        .with_reasoning("dana")\  # Best for data analysis
        .with_resources({
            "llm": LLMResource(model="gpt-4"),
            "data": DataResource(),  # For dataset handling
            "viz": VisualizationResource()  # For plotting
        })\
        .with_capabilities(["analysis", "statistics"])

    # Run analysis
    async with agent:
        result = await agent.run({
            "type": "analysis",
            "dataset": "sales_data.csv",
            "objectives": [
                "trend_analysis",
                "anomaly_detection",
                "forecasting"
            ],
            "output_format": "report_with_visuals"
        })
        
        print("Analysis Results:")
        print(result) 