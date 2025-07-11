"""
Agent Generator Module

This module processes user messages and generates appropriate Dana code for agent creation.
It uses LLM to understand user requirements and generate suitable agent templates.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.resource.llm.llm_configuration_manager import LLMConfigurationManager
from dana.common.types import BaseRequest, BaseResponse

logger = logging.getLogger(__name__)


class AgentGenerator:
    """
    Generates Dana agent code from user conversation messages.
    """
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent generator.
        
        Args:
            llm_config: Optional LLM configuration
        """
        self.llm_config = llm_config or {
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        # Initialize LLM resource with better error handling
        try:
            self.llm_resource = LLMResource(
                name="agent_generator_llm",
                description="LLM for generating Dana agent code",
                config=self.llm_config
            )
            logger.info("LLMResource created successfully")
        except Exception as e:
            logger.error(f"Failed to create LLMResource: {e}")
            self.llm_resource = None
        
    async def initialize(self):
        """Initialize the LLM resource."""
        if self.llm_resource is None:
            logger.error("LLMResource is None, cannot initialize")
            return False
            
        try:
            await self.llm_resource.initialize()
            logger.info("Agent Generator initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize LLMResource: {e}")
            return False
    
    async def generate_agent_code(self, messages: List[Dict[str, Any]], current_code: str = "") -> str:
        """
        Generate Dana agent code from user conversation messages.
        
        Args:
            messages: List of conversation messages with 'role' and 'content' fields
            current_code: Current Dana code to improve upon (default empty string)
            
        Returns:
            Generated Dana code as string
        """
        # Check if mock mode is enabled
        if os.environ.get("DANA_MOCK_AGENT_GENERATION", "").lower() == "true":
            logger.info("Using mock agent generation mode")
            return self._generate_mock_agent_code(messages, current_code)
        
        try:
            # Check if LLM resource is available
            if self.llm_resource is None:
                logger.warning("LLMResource is not available, using fallback template")
                return self._get_fallback_template()
            
            # Check if LLM is properly initialized
            if not hasattr(self.llm_resource, '_is_available') or not self.llm_resource._is_available:
                logger.warning("LLMResource is not available, using fallback template")
                return self._get_fallback_template()
            
            # Extract user requirements and intentions using LLM
            user_intentions = await self._extract_user_intentions(messages)
            logger.info(f"Extracted user intentions: {user_intentions[:100]}...")
            
            # Create prompt for LLM based on current code and new intentions
            prompt = self._create_generation_prompt(user_intentions, current_code)
            logger.debug(f"Generated prompt: {prompt[:200]}...")
            
            # Generate code using LLM
            request = BaseRequest(arguments={"prompt": prompt, "messages": [{"role": "user", "content": prompt}]})
            logger.info("Sending request to LLM...")
            
            response = await self.llm_resource.query(request)
            logger.info(f"LLM response success: {response.success}")
            
            if response.success:
                generated_code = response.content.get("choices", "")[0].get("message", {}).get("content", "")
                if not generated_code:
                    # Try alternative response formats
                    if isinstance(response.content, str):
                        generated_code = response.content
                    elif isinstance(response.content, dict):
                        # Look for common response fields
                        for key in ["content", "text", "message", "result"]:
                            if key in response.content:
                                generated_code = response.content[key]
                                break
                
                logger.info(f"Generated code length: {len(generated_code)}")
                
                # Clean up the generated code
                cleaned_code = self._clean_generated_code(generated_code)
                logger.info(f"Cleaned code length: {len(cleaned_code)}")
                
                if cleaned_code:
                    return cleaned_code
                else:
                    logger.warning("Generated code is empty, using fallback template")
                    return self._get_fallback_template()
            else:
                logger.error(f"LLM generation failed: {response.error}")
                return self._get_fallback_template()
                
        except Exception as e:
            logger.error(f"Error generating agent code: {e}")
            return self._get_fallback_template()
    
    async def _extract_user_intentions(self, messages: List[Dict[str, Any]]) -> str:
        """
        Use LLM to extract user intentions from conversation messages.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Extracted user intentions as string
        """
        try:
            # Create a prompt to extract intentions
            conversation_text = "\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in messages])
            
            intention_prompt = f"""
Analyze the following conversation and extract the user's intentions for creating a Dana agent. Focus on:
1. What type of agent they want
2. What functionality they need
3. Any specific requirements or constraints
4. The overall goal of the agent

Conversation:
{conversation_text}

Extract and summarize the user's intentions in a clear, concise way that can be used to generate appropriate Dana agent code.
"""
            
            request = BaseRequest(arguments={
                "messages": [{"role": "user", "content": intention_prompt}]
            })
            
            response = await self.llm_resource.query(request)
            
            if response.success:
                # Extract the intention from response
                intention = response.content.get("choices", "")[0].get("message", {}).get("content", "")
                if not intention:
                    # Fallback to simple extraction
                    return self._extract_requirements(messages)
                return intention
            else:
                # Fallback to simple extraction
                return self._extract_requirements(messages)
                
        except Exception as e:
            logger.error(f"Error extracting user intentions: {e}")
            # Fallback to simple extraction
            return self._extract_requirements(messages)
    
    def _extract_requirements(self, messages: List[Dict[str, Any]]) -> str:
        """
        Extract user requirements from conversation messages (fallback method).
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Extracted requirements as string
        """
        requirements = []
        
        for message in messages:
            role = message.get('role', '')
            content = message.get('content', '')
            
            if role == 'user' and content:
                requirements.append(content)
        
        return "\n".join(requirements)
    
    def _create_generation_prompt(self, intentions: str, current_code: str = "") -> str:
        """
        Create a prompt for the LLM to generate Dana agent code.
        
        Args:
            intentions: User intentions extracted by LLM
            current_code: Current Dana code to improve upon
            
        Returns:
            Formatted prompt for LLM
        """
        if current_code:
            # If there's existing code, ask for improvements
            prompt = f"""
You are an expert Dana language developer. Based on the user's intentions and the existing Dana agent code, improve or modify the agent to better meet their needs.

User Intentions:
{intentions}

Current Dana Agent Code:
{current_code}

Improve the Dana agent code to better match the user's intentions. You can:
1. Modify the existing agent structure
2. Add new resources if needed
3. Update the solve function
4. Change the agent name and description
5. Keep the improvements focused and simple

Use this template structure:

```dana
\"\"\"[Brief description of what the agent does].\"\"\"

# Agent resources (if needed)
[resource_name] = use("[resource_type]", [config])

# Agent Card declaration
agent [AgentName]:
    name : str = "[Descriptive Agent Name]"
    description : str = "[Brief description of what the agent does]"
    resources : list = [resource_name]  # if resources are used

# Agent's problem solver
def solve([agent_name] : [AgentName], problem : str):
    return reason(f"[How to handle the problem]", resources=[agent_name].resources)
```

Generate only the improved Dana code, no explanations or markdown formatting.
"""
        else:
            # If no existing code, create new agent
            prompt = f"""
You are an expert Dana language developer. Based on the following user intentions, generate a simple and focused Dana agent code.

User Intentions:
{intentions}

Generate a simple Dana agent that:
1. Has a descriptive name and description
2. Uses the 'agent' keyword syntax (not system:agent_name)
3. Includes appropriate resources if needed (mcp, web_search, etc.)
4. Has a simple solve function that handles the user's requirements
5. Uses proper Dana syntax and patterns
6. Keeps it simple and focused

Use this template structure:

```dana
\"\"\"[Brief description of what the agent does].\"\"\"

# Agent resources (if needed)
[resource_name] = use("[resource_type]", [config])

# Agent Card declaration
agent [AgentName]:
    name : str = "[Descriptive Agent Name]"
    description : str = "[Brief description of what the agent does]"
    resources : list = [resource_name]  # if resources are used

# Agent's problem solver
def solve([agent_name] : [AgentName], problem : str):
    return reason(f"[How to handle the problem]", resources=[agent_name].resources)
```

Keep it simple and focused on the specific requirement. Generate only the Dana code, no explanations or markdown formatting.
"""
        return prompt
    
    def _clean_generated_code(self, code: str) -> str:
        """
        Clean up the generated code by removing markdown and extra formatting.
        
        Args:
            code: Raw generated code
            
        Returns:
            Cleaned Dana code
        """
        if not code:
            return ""
            
        # Remove markdown code blocks
        if "```dana" in code:
            start = code.find("```dana") + 7
            end = code.find("```", start)
            if end != -1:
                code = code[start:end].strip()
        elif "```" in code:
            start = code.find("```") + 3
            end = code.find("```", start)
            if end != -1:
                code = code[start:end].strip()
        
        # Remove leading/trailing whitespace
        code = code.strip()
        
        return code
    
    def _get_fallback_template(self) -> str:
        """
        Get a fallback template when generation fails.
        
        Returns:
            Basic Dana agent template
        """
        return '''"""Basic Agent Template."""

# Define components of Agent Card
system:agent_name = "Basic Agent"
system:agent_description = "A basic agent that can handle general queries."

# Define solve function
def solve(input_data: str) -> str:
    """Solve a problem using reasoning."""
    return reason(f"Help me to answer the question: {input_data}")

# Example usage
example_input = "Hello, how can you help me?"
print(solve(example_input))'''
    
    async def cleanup(self):
        """Clean up resources."""
        if self.llm_resource:
            await self.llm_resource.cleanup()
        logger.info("Agent Generator cleaned up")

    def _generate_mock_agent_code(self, messages: List[Dict[str, Any]], current_code: str = "") -> str:
        """
        Generate a mock agent code based on user requirements.
        
        Args:
            messages: List of conversation messages
            current_code: Current Dana code to improve upon
            
        Returns:
            Mock Dana agent code
        """
        # Extract user requirements from all messages
        all_content = " ".join([msg.get('content', '') for msg in messages])
        requirements_lower = all_content.lower()
        
        logger.info(f"Analyzing requirements: {requirements_lower}")
        
        # If there's existing code, try to improve it based on new requirements
        if current_code:
            logger.info("Improving existing agent code based on new requirements")
            # For mock mode, we'll just return a new agent based on the latest requirements
            # In real LLM mode, this would analyze and improve the existing code
        
        # Simple keyword-based agent generation
        if "weather" in requirements_lower:
            # Check for specific cities mentioned
            cities = []
            if "tokyo" in requirements_lower:
                cities.append("Tokyo")
            if "new york" in requirements_lower or "nyc" in requirements_lower:
                cities.append("New York")
            if "san francisco" in requirements_lower or "sf" in requirements_lower:
                cities.append("San Francisco")
            if "london" in requirements_lower:
                cities.append("London")
            if "paris" in requirements_lower:
                cities.append("Paris")
            
            # If no specific cities mentioned, use a generic approach
            if not cities:
                cities = ["any city"]
            
            city_list = ", ".join(cities)
            
            return f'''"""Weather information agent for {city_list}."""

# Agent resources
web_search = use("web_search", {{"api_key": "env:WEB_SEARCH_API_KEY"}})

# Agent Card declaration
agent WeatherAgent:
    name : str = "Weather Information Agent"
    description : str = "Provides weather information and recommendations for {city_list}"
    resources : list = [web_search]

# Agent's problem solver
def solve(weather_agent : WeatherAgent, problem : str):
    return reason(f"Get weather information for: {{problem}}", resources=weather_agent.resources)'''
        
        elif "help" in requirements_lower or "assistant" in requirements_lower:
            return '''"""General assistant agent."""

# Agent Card declaration
agent AssistantAgent:
    name : str = "General Assistant Agent"
    description : str = "A helpful assistant that can answer questions and provide guidance"
    resources : list = []

# Agent's problem solver
def solve(assistant_agent : AssistantAgent, problem : str):
    return reason(f"I'm here to help! Let me assist you with: {{problem}}")'''
        
        elif "data" in requirements_lower or "analysis" in requirements_lower:
            return '''"""Data analysis agent."""

# Agent resources
data_processor = use("data_processor", {"format": "json"})

# Agent Card declaration
agent DataAgent:
    name : str = "Data Analysis Agent"
    description : str = "Analyzes data and provides insights"
    resources : list = [data_processor]

# Agent's problem solver
def solve(data_agent : DataAgent, problem : str):
    return reason(f"Analyze this data and provide insights: {{problem}}", resources=data_agent.resources)'''
        
        elif "email" in requirements_lower or "mail" in requirements_lower:
            return '''"""Email assistant agent."""

# Agent resources
email_client = use("email_client", {"provider": "gmail"})

# Agent Card declaration
agent EmailAgent:
    name : str = "Email Assistant Agent"
    description : str = "Helps with email composition, analysis, and management"
    resources : list = [email_client]

# Agent's problem solver
def solve(email_agent : EmailAgent, problem : str):
    return reason(f"Help me with email tasks: {{problem}}", resources=email_agent.resources)'''
        
        elif "calendar" in requirements_lower or "schedule" in requirements_lower:
            return '''"""Calendar assistant agent."""

# Agent resources
calendar_client = use("calendar_client", {"provider": "google"})

# Agent Card declaration
agent CalendarAgent:
    name : str = "Calendar Assistant Agent"
    description : str = "Helps with calendar management and scheduling"
    resources : list = [calendar_client]

# Agent's problem solver
def solve(calendar_agent : CalendarAgent, problem : str):
    return reason(f"Help me with calendar tasks: {{problem}}", resources=calendar_agent.resources)'''
        
        else:
            # Generate a more intelligent fallback based on the conversation
            if "question" in requirements_lower or "answer" in requirements_lower:
                return '''"""Question answering agent."""

# Agent Card declaration
agent QuestionAgent:
    name : str = "Question Answering Agent"
    description : str = "Answers questions on various topics"
    resources : list = []

# Agent's problem solver
def solve(question_agent : QuestionAgent, problem : str):
    return reason(f"Answer this question: {{problem}}")'''
            else:
                # Default template with more context
                return f'''"""Custom agent for your needs."""

# Agent Card declaration
agent CustomAgent:
    name : str = "Custom Assistant Agent"
    description : str = "An agent that can help with: {requirements_lower[:100]}..."
    resources : list = []

# Agent's problem solver
def solve(custom_agent : CustomAgent, problem : str):
    return reason(f"Help me with: {{problem}}")'''


# Global instance
_agent_generator: Optional[AgentGenerator] = None


async def get_agent_generator() -> AgentGenerator:
    """
    Get or create the global agent generator instance.
    
    Returns:
        AgentGenerator instance
    """
    global _agent_generator
    
    if _agent_generator is None:
        _agent_generator = AgentGenerator()
        success = await _agent_generator.initialize()
        if not success:
            logger.warning("Failed to initialize agent generator, will use fallback templates")
    
    return _agent_generator


async def generate_agent_code_from_messages(messages: List[Dict[str, Any]], current_code: str = "") -> str:
    """
    Generate Dana agent code from user conversation messages.
    
    Args:
        messages: List of conversation messages
        current_code: Current Dana code to improve upon (default empty string)
        
    Returns:
        Generated Dana code
    """
    generator = await get_agent_generator()
    return await generator.generate_agent_code(messages, current_code) 