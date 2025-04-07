#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 1: Setting up a Question-Answering Agent

This example demonstrates how to set up a basic DXA agent for question answering.
It covers agent creation, logging configuration, and adding LLM resources.

Key concepts:
- Agent creation and configuration
- Logging setup
- Resource integration
"""

import os
import asyncio
import logging

from opendxa.agent import Agent
from opendxa.agent.resource import LLMResource
from opendxa.common import DXA_LOGGER

# Step 1: Configure logging
DXA_LOGGER.configure(level=logging.INFO)

# Step 2: Create a basic agent
agent = Agent(name="qa_agent")

# Step 3: Configure LLM resource
# Replace with your actual API key or use environment variables
api_key = os.environ.get("OPENAI_API_KEY", "your_api_key_here")

llm_config = {
    "model": "openai:gpt-4",  # Specify the model to use
    "temperature": 0.7,       # Control randomness (0.0 to 1.0)
    "api_key": api_key,       # API key for authentication
}

# Step 4: Add LLM resource to the agent
agent.with_llm(LLMResource(config=llm_config))

# Step 5: Add capabilities to the agent
# Note: In a real implementation, you would use actual capability instances
# This is simplified for the tutorial
agent.with_capabilities({})  # Empty dict for now, will be covered in later steps

# Step 6: Test the agent setup
async def test_agent():
    """Test the agent setup with a simple question."""
    async with agent:
        # Simple direct question to test the setup
        response = await agent.ask("What is the capital of France?")
        print(f"Response: {response}")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_agent())

# Next steps:
# - Proceed to 02_workflow_creation.py to learn how to create a QA workflow
# - Experiment with different LLM models and parameters
# - Add additional capabilities to the agent 