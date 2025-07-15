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
from dana.core.lang.dana_sandbox import DanaSandbox

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
    
    async def generate_agent_code(self, messages: List[Dict[str, Any]], current_code: str = "") -> tuple[str, str | None, Dict[str, Any]]:
        """
        Generate Dana agent code from user conversation messages.
        
        Args:
            messages: List of conversation messages with 'role' and 'content' fields
            current_code: Current Dana code to improve upon (default empty string)
            
        Returns:
            Tuple of (Generated Dana code as string, error message or None, conversation analysis)
        """
        # First, analyze if we need more information
        conversation_analysis = await analyze_conversation_completeness(messages)
        
        # Check if mock mode is enabled
        if os.environ.get("DANA_MOCK_AGENT_GENERATION", "").lower() == "true":
            logger.info("Using mock agent generation mode")
            return self._generate_mock_agent_code(messages, current_code), None, conversation_analysis
        
        try:
            # Check if LLM resource is available
            if self.llm_resource is None:
                logger.warning("LLMResource is not available, using fallback template")
                return self._get_fallback_template(), None, conversation_analysis
            
            # Check if LLM is properly initialized
            if not hasattr(self.llm_resource, '_is_available') or not self.llm_resource._is_available:
                logger.warning("LLMResource is not available, using fallback template")
                return self._get_fallback_template(), None, conversation_analysis
            
            # Extract user requirements and intentions using LLM
            user_intentions = await self._extract_user_intentions(messages, current_code)
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
                
                # FINAL FALLBACK: Ensure Dana code is returned
                if cleaned_code and "agent " in cleaned_code:
                    
                    return cleaned_code, None, conversation_analysis
                else:
                    logger.warning("Generated code is empty or not Dana code, using fallback template")
                    return self._get_fallback_template(), None, conversation_analysis
            else:
                logger.error(f"LLM generation failed: {response.error}")
                return self._get_fallback_template(), None, conversation_analysis
                
        except Exception as e:
            logger.error(f"Error generating agent code: {e}")
            return self._get_fallback_template(), str(e), conversation_analysis
    
    async def _extract_user_intentions(self, messages: List[Dict[str, Any]], current_code: str = "") -> str:
        """
        Use LLM to extract user intentions from conversation messages.
        
        Args:
            messages: List of conversation messages
            current_code: Current Dana code to provide context for intention extraction
            
        Returns:
            Extracted user intentions as string
        """
        try:
            # Create a prompt to extract intentions
            conversation_text = "\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in messages])
            
            if current_code:
                intention_prompt = f"""
Analyze the following conversation and the current Dana agent code to extract the user's intentions for improving or modifying the agent. Focus on:
1. What changes or improvements they want to make
2. What functionality they want to add or modify
3. Any specific requirements or constraints
4. How the current code should be enhanced

Current Dana Agent Code:
{current_code}

Conversation:
{conversation_text}

Extract and summarize the user's intentions in a clear, concise way that can be used to improve the existing Dana agent code. Consider what aspects of the current code need to be changed or enhanced.
"""
            else:
                intention_prompt = f"""
Analyze the following conversation and extract the user's intentions for creating a new Dana agent. Focus on:
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
2. Add RAG resources ONLY if the user needs document/knowledge retrieval capabilities
3. Update the solve function
4. Change the agent name and description
5. Keep the improvements focused and simple

Use this template structure:

```dana
\"\"\"[Brief description of what the agent does].\"\"\"

# Agent resources (ONLY if document/knowledge retrieval is needed)
[resource_name] = use("rag", sources=[list_of_document_paths_or_urls])

# Agent Card declaration
agent [AgentName]:
    name : str = "[Descriptive Agent Name]"
    description : str = "[Brief description of what the agent does]"
    resources : list = [resource_name]  # only if RAG resources are used

# Agent's problem solver
def solve([agent_name] : [AgentName], problem : str):
    return reason(f"[How to handle the problem]", resources=[agent_name].resources if [agent_name].resources else None)
```

Available resources:
- RAG resource: use("rag", sources=[list_of_document_paths_or_urls]) - ONLY for document retrieval and knowledge base access

IMPORTANT: Only use RAG resources if the user specifically needs:
- Document processing or analysis
- Knowledge base access
- Information retrieval from files or web pages
- Context-aware responses based on documents

For simple agents that just answer questions or perform basic tasks, do NOT use any resources.

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
3. Includes RAG resources ONLY if document/knowledge retrieval is needed
4. Has a simple solve function that handles the user's requirements
5. Uses proper Dana syntax and patterns
6. Keeps it simple and focused

Use this template structure:

```dana
\"\"\"[Brief description of what the agent does].\"\"\"


# Agent Card declaration
agent [AgentName]:
    name : str = "[Descriptive Agent Name]"
    description : str = "[Brief description of what the agent does]"
    resources : list = []  # only if RAG resources are used

# Agent's problem solver
def solve([agent_name] : [AgentName], problem : str):
    return reason(f"[How to handle the problem]")
```

Available resources:
- RAG resource: use("rag", sources=[list_of_document_paths_or_urls]) - ONLY for document retrieval and knowledge base access

IMPORTANT: Only use RAG resources if the user specifically needs:
- Document processing or analysis
- Knowledge base access
- Information retrieval from files or web pages
- Context-aware responses based on documents

For simple agents that just answer questions or perform basic tasks, do NOT use any resources.

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

# Agent Card declaration
agent BasicAgent:
    name : str = "Basic Agent"
    description : str = "A basic agent that can handle general queries."

# Agent's problem solver
def solve(basic_agent : BasicAgent, problem : str):
    """Solve a problem using reasoning."""
    return reason(f"Help me to answer the question: {problem}")

# Example usage
example_input = "Hello, how can you help me?"
print(solve(BasicAgent(), example_input))'''
    
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
            # Weather agents don't typically need RAG - they can use general knowledge
            return f'''"""Weather information agent."""

# Agent Card declaration
agent WeatherAgent:
    name : str = "Weather Information Agent"
    description : str = "Provides weather information and recommendations"
    resources : list = []

# Agent's problem solver
def solve(weather_agent : WeatherAgent, problem : str):
    return reason(f"Get weather information for: {{problem}}")'''
        
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
            # Data analysis might need RAG for statistical methods and guides
            return '''"""Data analysis agent."""

# Agent resources for data analysis knowledge
data_knowledge = use("rag", sources=["data_analysis_guide.md", "statistical_methods.pdf"])

# Agent Card declaration
agent DataAgent:
    name : str = "Data Analysis Agent"
    description : str = "Analyzes data and provides insights using knowledge base"
    resources : list = [data_knowledge]

# Agent's problem solver
def solve(data_agent : DataAgent, problem : str):
    return reason(f"Analyze this data and provide insights: {{problem}}", resources=data_agent.resources)'''
        
        elif "email" in requirements_lower or "mail" in requirements_lower:
            # Email assistance might need templates and guides
            return '''"""Email assistant agent."""

# Agent resources for email assistance
email_knowledge = use("rag", sources=["email_templates.txt", "communication_guide.pdf"])

# Agent Card declaration
agent EmailAgent:
    name : str = "Email Assistant Agent"
    description : str = "Helps with email composition, analysis, and management"
    resources : list = [email_knowledge]

# Agent's problem solver
def solve(email_agent : EmailAgent, problem : str):
    return reason(f"Help me with email tasks: {{problem}}", resources=email_agent.resources)'''
        
        elif "calendar" in requirements_lower or "schedule" in requirements_lower:
            # Calendar management might need scheduling guides
            return '''"""Calendar assistant agent."""

# Agent resources for calendar management
calendar_knowledge = use("rag", sources=["scheduling_guide.md", "time_management.pdf"])

# Agent Card declaration
agent CalendarAgent:
    name : str = "Calendar Assistant Agent"
    description : str = "Helps with calendar management and scheduling"
    resources : list = [calendar_knowledge]

# Agent's problem solver
def solve(calendar_agent : CalendarAgent, problem : str):
    return reason(f"Help me with calendar tasks: {{problem}}", resources=calendar_agent.resources)'''
        
        elif "document" in requirements_lower or "file" in requirements_lower or "pdf" in requirements_lower:
            # Document processing definitely needs RAG
            return '''"""Document processing agent."""

# Agent resources for document processing
document_knowledge = use("rag", sources=["document_processing_guide.md", "file_formats.pdf"])

# Agent Card declaration
agent DocumentAgent:
    name : str = "Document Processing Agent"
    description : str = "Processes and analyzes documents and files"
    resources : list = [document_knowledge]

# Agent's problem solver
def solve(document_agent : DocumentAgent, problem : str):
    return reason(f"Help me process this document: {{problem}}", resources=document_agent.resources)'''
        
        elif "knowledge" in requirements_lower or "research" in requirements_lower or "information" in requirements_lower:
            # Knowledge/research agents need RAG
            return '''"""Knowledge and research agent."""

# Agent resources for knowledge base
knowledge_base = use("rag", sources=["general_knowledge.txt", "research_database.pdf"])

# Agent Card declaration
agent KnowledgeAgent:
    name : str = "Knowledge and Research Agent"
    description : str = "Provides information and research capabilities using knowledge base"
    resources : list = [knowledge_base]

# Agent's problem solver
def solve(knowledge_agent : KnowledgeAgent, problem : str):
    return reason(f"Research and provide information about: {{problem}}", resources=knowledge_agent.resources)'''
        
        else:
            # Generate a more intelligent fallback based on the conversation
            if "question" in requirements_lower or "answer" in requirements_lower:
                # Simple Q&A doesn't need RAG
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
                # Default template without resources for simple tasks
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


async def generate_agent_code_from_messages(messages: List[Dict[str, Any]], current_code: str = "") -> tuple[str, str | None, Dict[str, Any]]:
    """
    Generate Dana agent code from user conversation messages.
    
    Args:
        messages: List of conversation messages
        current_code: Current Dana code to improve upon (default empty string)
        
    Returns:
        Tuple of (Generated Dana code, error message or None, conversation analysis)
    """
    generator = await get_agent_generator()
    result = await generator.generate_agent_code(messages, current_code)
    if isinstance(result, tuple) and len(result) == 3:
        return result  # (code, error, analysis)
    elif isinstance(result, tuple) and len(result) == 2:
        return result[0], result[1], {}  # backward compatibility
    return result, None, {}


async def generate_agent_code_na(messages: List[Dict[str, Any]], current_code: str = "") -> tuple[str, str | None]:
    """
    Generate Dana agent code using a .na file executed with DanaSandbox.quick_run.
    If the generated code has errors, it calls another Dana agent to fix it.
    
    Args:
        messages: List of conversation messages with 'role' and 'content' fields
        current_code: Current Dana code to improve upon (default empty string)
        
    Returns:
        Tuple of (Generated Dana code as string, error message or None)
    """
    try:
        # Create the .na file content with injected messages and current_code
        na_code = _create_agent_generator_na_code(messages, current_code)
        
        # Write the code to a temporary file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.na', delete=False) as temp_file:
            temp_file.write(na_code)
            temp_file_path = temp_file.name
        
        try:
            # Execute the .na file using DanaSandbox.quick_run with file path
            result = DanaSandbox.quick_run(file_path=temp_file_path)
            
            if result.success:
                generated_code = result.result
                # Strip leading/trailing triple quotes and whitespace
                if generated_code:
                    code = generated_code.strip()
                    if code.startswith('"""') and code.endswith('"""'):
                        code = code[3:-3].strip()
                    generated_code = code
                if generated_code and "agent " in generated_code:
                    # Test the generated code for syntax errors
                    test_result = _test_generated_code(generated_code)
                    if test_result.success:
                        return generated_code, None
                    else:
                        error_msg = str(test_result.error) if hasattr(test_result, 'error') else "Unknown syntax error"
                        logger.warning(f"Generated code has errors: {error_msg}")
                        # Try to fix the code using a Dana agent
                        fixed_code = await _fix_generated_code_with_agent(generated_code, error_msg, messages)
                        if fixed_code:
                            return fixed_code, None
                        else:
                            logger.warning("Failed to fix code, using fallback template")
                            return _get_fallback_template(), None
                else:
                    logger.warning("Generated code is empty or not Dana code, using fallback template")
                    return _get_fallback_template(), None
            else:
                logger.error(f"NA execution failed: {result.error}")
                # Try to generate a simple fallback agent based on user intention
                try:
                    fallback_code = _generate_simple_fallback_agent(messages)
                    return fallback_code, None
                except Exception as fallback_error:
                    logger.error(f"Fallback generation also failed: {fallback_error}")
                    return _get_fallback_template(), str(result.error)
                
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temporary file: {cleanup_error}")
            
    except Exception as e:
        logger.error(f"Error generating agent code with NA: {e}")
        return _get_fallback_template(), str(e)


def _create_agent_generator_na_code(messages: List[Dict[str, Any]], current_code: str) -> str:
    """
    Create the .na code that will generate Dana agents using reason() function.
    
    Args:
        messages: List of conversation messages
        current_code: Current Dana code to improve upon
        
    Returns:
        Dana code as string with injected data
    """
    # Inject the messages and current_code into the .na code
    messages_str = str(messages).replace('"', '\\"')
    current_code_str = current_code.replace('"', '\\"').replace('\n', '\\n')
    
    return f'''"""Agent Generator NA Code

This .na file contains the logic for generating Dana agents based on conversation messages.
"""

# Injected conversation messages
messages = {messages_str}

# Injected current Dana code
current_code = """{current_code_str}"""

# Extract user intentions from conversation
def extract_intentions(messages: list) -> str:
    """Extract user intentions from conversation messages."""
    all_content = ""
    for msg in messages:
        if msg.get("role") == "user":
            all_content = all_content + " " + msg.get("content", "")
    
    # Simple keyword-based intention extraction
    content_lower = all_content.lower()
    
    if "weather" in content_lower:
        return "weather information agent"
    elif "help" in content_lower or "assistant" in content_lower:
        return "general assistant agent"
    elif "data" in content_lower or "analysis" in content_lower:
        return "data analysis agent"
    elif "email" in content_lower or "mail" in content_lower:
        return "email assistant agent"
    elif "calendar" in content_lower or "schedule" in content_lower:
        return "calendar assistant agent"
    elif "document" in content_lower or "file" in content_lower or "pdf" in content_lower:
        return "document processing agent"
    elif "knowledge" in content_lower or "research" in content_lower or "information" in content_lower:
        return "knowledge and research agent"
    elif "question" in content_lower or "answer" in content_lower:
        return "question answering agent"
    elif "finance" in content_lower or "money" in content_lower or "budget" in content_lower or "investment" in content_lower:
        return "personal finance advisor agent"
    else:
        return "custom assistant agent"

# Generate agent code using reason() function
def generate_agent_code(messages: list, current_code: str) -> str:
    """Generate Dana agent code using reason() function."""
    
    # Extract user intentions first
    user_intention = extract_intentions(messages)
    
    # Create prompt for reason() function
    prompt = f"""Based on the user's intention to create a {{user_intention}}, generate a complete Dana agent code.

User intention: {{user_intention}}
Current code (if any): {{current_code}}

Generate a complete, working Dana agent code that:
1. Has a descriptive name and description based on the intention
2. Uses the 'agent' keyword syntax (not system:agent_name)
3. Includes RAG resources ONLY if document/knowledge retrieval is needed
4. Has a simple solve function that handles the user's requirements
5. Uses proper Dana syntax and patterns
6. Keeps it simple and focused

CRITICAL DANA SYNTAX RULES:
- Agent names must be unquoted: agent PersonalFinanceAgent (NOT agent "PersonalFinanceAgent")
- String values must be quoted: name : str = "Personal Finance Agent"
- Function parameters must be unquoted: def solve(agent_name : AgentName, problem : str)
- Use proper Dana syntax throughout
- **All function definitions (like def solve(...)) must be outside the agent block. The agent block should only contain attribute assignments.**

EXACT TEMPLATE TO FOLLOW:
```dana
\"\"\"[Brief description of what the agent does].\"\"\"

# Agent Card declaration
agent [AgentName]:
    name : str = "[Descriptive Agent Name]"
    description : str = "[Brief description of what the agent does]"
    resources : list = []

# Agent's problem solver
def solve([agent_name] : [AgentName], problem : str):
    return reason(f"[How to handle the problem]")
```

IMPORTANT: Generate ONLY valid Dana code with:
- Proper agent declaration syntax (agent Name, not agent "Name")
- Valid string literals (use double quotes for values)
- Proper function definitions OUTSIDE the agent block
- Correct Dana syntax throughout

Available resources:
- RAG resource: use("rag", sources=[list_of_document_paths_or_urls]) - ONLY for document retrieval and knowledge base access

IMPORTANT: Only use RAG resources if the user specifically needs:
- Document processing or analysis
- Knowledge base access
- Information retrieval from files or web pages
- Context-aware responses based on documents

For simple agents that just answer questions or perform basic tasks, do NOT use any resources.

Generate only the Dana code, no explanations or markdown formatting. Make sure all strings are properly quoted and all syntax is valid Dana."""

    # Use reason() function to generate the agent code
    generated_code = reason(prompt)
    
    return generated_code

# Execute the main function with injected data
result = generate_agent_code(messages, current_code)
result
'''





def _test_generated_code(code: str) -> Any:
    """
    Test the generated Dana code for syntax errors.
    
    Args:
        code: Dana code to test
        
    Returns:
        ExecutionResult with success/error information
    """
    try:
        import tempfile
        import os
        
        # Write the code to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.na', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name
        
        try:
            # Test the code using DanaSandbox.quick_run
            result = DanaSandbox.quick_run(file_path=temp_file_path)
            return result
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
                
    except Exception as e:
        # Return a mock result indicating failure
        class MockResult:
            def __init__(self, success: bool, error: str):
                self.success = success
                self.error = error
        return MockResult(False, str(e))


async def _fix_generated_code_with_agent(code: str, error: str, messages: List[Dict[str, Any]]) -> str:
    """
    Use a Dana agent to fix the generated code.
    
    Args:
        code: The generated code with errors
        error: The error message
        messages: Original conversation messages for context
        
    Returns:
        Fixed Dana code or empty string if fixing failed
    """
    try:
        # Create a code fixing agent using Dana
        fixer_code = _create_code_fixer_na_code(code, error, messages)
        
        # Write the fixer code to a temporary file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.na', delete=False) as temp_file:
            temp_file.write(fixer_code)
            temp_file_path = temp_file.name
        
        try:
            # Execute the code fixer
            result = DanaSandbox.quick_run(file_path=temp_file_path)
            
            if result.success and result.result:
                # Test the fixed code
                test_result = _test_generated_code(result.result)
                if test_result.success:
                    return result.result
                else:
                    logger.warning(f"Fixed code still has errors: {test_result.error}")
                    return ""
            else:
                logger.warning("Code fixer failed to generate fixed code")
                return ""
                
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temporary file: {cleanup_error}")
                
    except Exception as e:
        logger.error(f"Error fixing generated code: {e}")
        # Try to generate a simple fallback agent instead
        try:
            return _generate_simple_fallback_agent(messages)
        except Exception as fallback_error:
            logger.error(f"Fallback generation also failed: {fallback_error}")
            return ""


def _create_code_fixer_na_code(code: str, error: str, messages: List[Dict[str, Any]]) -> str:
    """
    Create the .na code for a code fixing agent.
    
    Args:
        code: The generated code with errors
        error: The error message
        messages: Original conversation messages for context
        
    Returns:
        Dana code for the code fixing agent
    """
    # Inject the data into the .na code
    code_str = code.replace('"', '\\"').replace('\n', '\\n')
    # Convert error to string and escape it properly - use a simpler approach
    error_str = str(error).replace('"', '\\"').replace("'", "\\'").replace('\n', '\\n')
    messages_str = str(messages).replace('"', '\\"')
    
    return f'''"""Code Fixer Agent

This .na file contains a Dana agent that fixes Dana code with syntax errors.
"""

# Injected data
original_code = """{code_str}"""

# Code fixing agent
agent CodeFixerAgent:
    name : str = "Dana Code Fixer Agent"
    description : str = "Fixes Dana code syntax errors and improves code quality"
    resources : list = []

def solve(code_fixer : CodeFixerAgent, problem : str):
    """Fix Dana code with syntax errors."""
    
    prompt = f"""You are an expert Dana language developer. Fix the following Dana code that has syntax errors.

Original Code:
{{original_code}}

Please fix the Dana code by:
1. Correcting any syntax errors
2. Ensuring proper Dana syntax and patterns
3. Maintaining the intended functionality
4. Using proper agent declaration syntax
5. Ensuring all functions are properly defined
6. Fixing any variable scope issues
7. Ensuring proper resource usage if any
8. Making sure all strings are properly quoted with double quotes
9. Ensuring all syntax is valid Dana

CRITICAL DANA SYNTAX RULES:
- Agent names must be unquoted: agent PersonalFinanceAgent (NOT agent "PersonalFinanceAgent")
- String values must be quoted: name : str = "Personal Finance Agent"
- Function parameters must be unquoted: def solve(agent_name : AgentName, problem : str)
- Use proper Dana syntax throughout
- **All function definitions (like def solve(...)) must be outside the agent block. The agent block should only contain attribute assignments.**

EXACT TEMPLATE TO FOLLOW:
```dana
\"\"\"[Brief description of what the agent does].\"\"\"

# Agent Card declaration
agent [AgentName]:
    name : str = "[Descriptive Agent Name]"
    description : str = "[Brief description of what the agent does]"
    resources : list = []

# Agent's problem solver
def solve([agent_name] : [AgentName], problem : str):
    return reason(f"[How to handle the problem]")
```

IMPORTANT: Generate ONLY valid Dana code with:
- Proper agent declaration syntax (agent Name, not agent "Name")
- Valid string literals (use double quotes for values)
- Proper function definitions OUTSIDE the agent block
- Correct Dana syntax throughout

Generate only the corrected Dana code, no explanations or markdown formatting. Make sure all strings are properly quoted and all syntax is valid Dana."""

    fixed_code = reason(prompt)
    return fixed_code

# Execute the code fixer
result = solve(CodeFixerAgent(), "Fix the Dana code")
result
'''


def _generate_simple_fallback_agent(messages: List[Dict[str, Any]]) -> str:
    """
    Generate a simple fallback agent based on user messages.
    
    Args:
        messages: List of conversation messages
        
    Returns:
        Simple Dana agent code
    """
    # Extract user intention from messages
    all_content = ""
    for msg in messages:
        if msg.get("role") == "user":
            all_content = all_content + " " + msg.get("content", "")
    
    content_lower = all_content.lower()
    
    # Determine agent type based on keywords
    if "weather" in content_lower:
        agent_name = "WeatherAgent"
        agent_title = "Weather Information Agent"
        description = "Provides weather information and recommendations"
    elif "help" in content_lower or "assistant" in content_lower:
        agent_name = "AssistantAgent"
        agent_title = "General Assistant Agent"
        description = "A helpful assistant that can answer questions and provide guidance"
    elif "data" in content_lower or "analysis" in content_lower:
        agent_name = "DataAgent"
        agent_title = "Data Analysis Agent"
        description = "Analyzes data and provides insights"
    elif "email" in content_lower or "mail" in content_lower:
        agent_name = "EmailAgent"
        agent_title = "Email Assistant Agent"
        description = "Helps with email composition and management"
    elif "calendar" in content_lower or "schedule" in content_lower:
        agent_name = "CalendarAgent"
        agent_title = "Calendar Assistant Agent"
        description = "Helps with calendar management and scheduling"
    elif "document" in content_lower or "file" in content_lower:
        agent_name = "DocumentAgent"
        agent_title = "Document Processing Agent"
        description = "Processes and analyzes documents and files"
    elif "knowledge" in content_lower or "research" in content_lower:
        agent_name = "KnowledgeAgent"
        agent_title = "Knowledge and Research Agent"
        description = "Provides information and research capabilities"
    elif "question" in content_lower or "answer" in content_lower:
        agent_name = "QuestionAgent"
        agent_title = "Question Answering Agent"
        description = "Answers questions on various topics"
    elif "finance" in content_lower or "money" in content_lower or "budget" in content_lower or "investment" in content_lower:
        agent_name = "FinanceAgent"
        agent_title = "Personal Finance Advisor Agent"
        description = "Provides personal finance advice, budgeting tips, and investment guidance"
    else:
        agent_name = "CustomAgent"
        agent_title = "Custom Assistant Agent"
        description = "An agent that can help with various tasks"
    
    return f'''"""Simple {agent_title}."""

# Agent Card declaration
agent {agent_name}:
    name : str = "{agent_title}"
    description : str = "{description}"
    resources : list = []

# Agent's problem solver
def solve({agent_name.lower()} : {agent_name}, problem : str):
    return reason(f"Help me with: {{problem}}")

# Example usage
example_input = "Hello, how can you help me?"
print(solve({agent_name}(), example_input))'''


async def analyze_conversation_completeness(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze if the conversation has enough information to generate a meaningful agent.
    
    Args:
        messages: List of conversation messages
        
    Returns:
        Dictionary with analysis results including whether more info is needed
    """
    try:
        # Extract user messages only
        user_messages = [msg.get('content', '') for msg in messages if msg.get('role') == 'user']
        conversation_text = ' '.join(user_messages).lower()
        
        # Check for vague or insufficient requests
        vague_indicators = [
            'help', 'assistant', 'agent', 'create', 'make', 'build', 'something', 'anything'
        ]
        
        specific_indicators = [
            'weather', 'data', 'analysis', 'email', 'calendar', 'document', 'research',
            'finance', 'customer', 'sales', 'support', 'translate', 'schedule', 'appointment'
        ]
        
        # Calculate vagueness score
        vague_count = sum(1 for indicator in vague_indicators if indicator in conversation_text)
        specific_count = sum(1 for indicator in specific_indicators if indicator in conversation_text)
        word_count = len(conversation_text.split())
        
        # Determine if more information is needed
        needs_more_info = False
        follow_up_message = ""
        suggested_questions = []
        
        # Too vague if mostly generic terms and few specific terms
        if word_count < 10 or (vague_count > specific_count and word_count < 20):
            needs_more_info = True
            follow_up_message = "I'd love to help you create a Dana agent! To build something that's truly useful for you, could you tell me more about what you'd like this agent to do? The more specific you can be, the better I can tailor it to your needs."
            
            suggested_questions = [
                "What specific task should this agent help you with?",
                "What kind of data or information will the agent work with?",
                "Who will be using this agent and in what context?",
                "Do you have any existing tools or systems it should integrate with?"
            ]
        
        # Check for unclear domain or purpose
        elif 'help' in conversation_text and specific_count == 0:
            needs_more_info = True
            follow_up_message = "I can help you create an agent! What specific area would you like the agent to assist with? For example, are you looking for help with business processes, data analysis, communication, or something else?"
            
            suggested_questions = [
                "What's the main purpose of this agent?",
                "What industry or domain is this for?",
                "What are the key features you need?"
            ]
        
        # Check for missing technical details if it's a complex request
        elif any(term in conversation_text for term in ['integration', 'api', 'database', 'system']) and 'how' not in conversation_text:
            needs_more_info = True
            follow_up_message = "I can see you want to create an agent with some technical integrations. To build this properly, I'll need some more details about your technical requirements."
            
            suggested_questions = [
                "What APIs or systems should the agent connect to?",
                "What data formats will you be working with?",
                "Are there any specific authentication requirements?",
                "What's your preferred way of receiving results?"
            ]
        
        return {
            "needs_more_info": needs_more_info,
            "follow_up_message": follow_up_message,
            "suggested_questions": suggested_questions,
            "analysis": {
                "word_count": word_count,
                "vague_count": vague_count,
                "specific_count": specific_count,
                "conversation_text": conversation_text[:100] + "..." if len(conversation_text) > 100 else conversation_text
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing conversation completeness: {e}")
        return {
            "needs_more_info": False,
            "follow_up_message": None,
            "suggested_questions": [],
            "analysis": {"error": str(e)}
        }


async def analyze_agent_capabilities(dana_code: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the generated Dana code and conversation to extract agent capabilities.
    
    Args:
        dana_code: Generated Dana agent code
        messages: Original conversation messages
        
    Returns:
        Dictionary containing summary, knowledge, workflow, and tools
    """
    try:
        # Extract conversation context
        conversation_text = "\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in messages])
        
        # Basic analysis from code structure
        capabilities = {
            "summary": _extract_summary_from_code_and_conversation(dana_code, conversation_text),
            "knowledge": _extract_knowledge_domains(dana_code, conversation_text),
            "workflow": _extract_workflow_steps(dana_code, conversation_text), 
            "tools": _extract_agent_tools(dana_code)
        }
        
        return capabilities
        
    except Exception as e:
        logger.error(f"Error analyzing agent capabilities: {e}")
        return {
            "summary": "Unable to analyze agent capabilities",
            "knowledge": [],
            "workflow": [],
            "tools": []
        }


def _extract_summary_from_code_and_conversation(dana_code: str, conversation_text: str) -> str:
    """Extract a comprehensive summary of what the agent does."""
    # Try to get description from agent code first
    lines = dana_code.split('\n')
    agent_description = None
    
    for line in lines:
        if 'description : str =' in line:
            agent_description = line.split('=')[1].strip().strip('"')
            break
    
    # Analyze conversation to understand user intent
    conversation_lower = conversation_text.lower()
    
    # Create a comprehensive summary
    if agent_description:
        base_summary = agent_description
    else:
        base_summary = "A Dana agent"
    
    # Add context from conversation
    context_keywords = []
    if "weather" in conversation_lower:
        context_keywords.append("weather information")
    if "data" in conversation_lower or "analysis" in conversation_lower:
        context_keywords.append("data analysis")
    if "email" in conversation_lower:
        context_keywords.append("email assistance")
    if "calendar" in conversation_lower or "schedule" in conversation_lower:
        context_keywords.append("scheduling")
    if "document" in conversation_lower or "file" in conversation_lower:
        context_keywords.append("document processing")
    if "research" in conversation_lower or "knowledge" in conversation_lower:
        context_keywords.append("research and knowledge")
    if "finance" in conversation_lower or "money" in conversation_lower:
        context_keywords.append("financial advice")
    
    if context_keywords:
        summary = f"{base_summary}. Specializes in {', '.join(context_keywords)}."
    else:
        summary = f"{base_summary}. Provides general assistance and reasoning capabilities."
    
    return summary


def _extract_knowledge_domains(dana_code: str, conversation_text: str) -> List[str]:
    """Extract knowledge domains the agent can work with."""
    domains = []
    
    # Analyze code for RAG resources
    if 'use("rag"' in dana_code:
        domains.append("Document-based knowledge retrieval")
        
    # Analyze conversation for domain expertise
    conversation_lower = conversation_text.lower()
    
    if "weather" in conversation_lower:
        domains.append("Weather and climate information")
    if "data" in conversation_lower or "analysis" in conversation_lower:
        domains.append("Data analysis and statistics")
    if "email" in conversation_lower:
        domains.append("Email communication and management")
    if "calendar" in conversation_lower or "schedule" in conversation_lower:
        domains.append("Time management and scheduling")
    if "document" in conversation_lower or "file" in conversation_lower:
        domains.append("Document processing and analysis")
    if "research" in conversation_lower or "knowledge" in conversation_lower:
        domains.append("Research and information gathering")
    if "finance" in conversation_lower or "money" in conversation_lower or "investment" in conversation_lower:
        domains.append("Personal finance and investment")
    if "code" in conversation_lower or "programming" in conversation_lower:
        domains.append("Software development and programming")
    if "health" in conversation_lower or "medical" in conversation_lower:
        domains.append("Health and wellness information")
    if "travel" in conversation_lower:
        domains.append("Travel planning and recommendations")
    
    # Default general knowledge if no specific domains found
    if not domains:
        domains.append("General knowledge and reasoning")
    
    return domains


def _extract_workflow_steps(dana_code: str, conversation_text: str) -> List[str]:
    """Extract the typical workflow steps the agent follows."""
    workflow = []
    
    # Analyze the solve function to understand workflow
    lines = dana_code.split('\n')
    in_solve_function = False
    
    for line in lines:
        if 'def solve(' in line:
            in_solve_function = True
            workflow.append("1. Receive user input/problem")
            continue
        elif in_solve_function:
            if line.strip() and not line.startswith('    '):
                break
            if 'reason(' in line:
                workflow.append("2. Apply reasoning to understand the problem")
                workflow.append("3. Generate appropriate response or solution")
            elif 'resources=' in line:
                workflow.append("2. Query knowledge base for relevant information")
    
    # Add common workflow steps based on agent type
    conversation_lower = conversation_text.lower()
    
    if "document" in conversation_lower or "file" in conversation_lower:
        if "2. Process and analyze document content" not in workflow:
            workflow.insert(-1, "2. Process and analyze document content")
    
    if "data" in conversation_lower or "analysis" in conversation_lower:
        if "2. Analyze data patterns and trends" not in workflow:
            workflow.insert(-1, "2. Analyze data patterns and trends")
            workflow.append("4. Present insights and recommendations")
    
    if "email" in conversation_lower:
        workflow.append("4. Format response appropriately for email context")
    
    # Default workflow if nothing specific found
    if not workflow:
        workflow = [
            "1. Receive user query or request",
            "2. Apply reasoning to understand the context",
            "3. Generate helpful response or guidance"
        ]
    
    return workflow


def _extract_agent_tools(dana_code: str) -> List[str]:
    """Extract tools and capabilities available to the agent."""
    tools = []
    
    # Core Dana capabilities
    tools.append("Reasoning engine (reason function)")
    
    # Check for specific resources
    if 'use("rag"' in dana_code:
        tools.append("RAG (Retrieval-Augmented Generation)")
        tools.append("Document search and retrieval")
    
    # Check for common function patterns
    if 'def ' in dana_code and 'solve(' not in dana_code:
        tools.append("Custom utility functions")
    
    # Check for imports that indicate additional capabilities
    if 'import' in dana_code:
        tools.append("External library integration")
    
    # Check for error handling
    if 'try:' in dana_code or 'except:' in dana_code:
        tools.append("Error handling and recovery")
    
    # Check for data structures
    if 'list' in dana_code or 'dict' in dana_code:
        tools.append("Data structure manipulation")
    
    # Check for private variables (state management)
    if 'private:' in dana_code:
        tools.append("State management")
    
    # Always include basic capabilities
    tools.extend([
        "Natural language processing",
        "Context understanding",
        "Response generation"
    ])
    
    return list(set(tools))  # Remove duplicates


def _get_fallback_template() -> str:
    """
    Get a fallback template when generation fails.
    
    Returns:
        Basic Dana agent template
    """
    return '''"""Basic Agent Template."""

# Agent Card declaration
agent BasicAgent:
    name : str = "Basic Agent"
    description : str = "A basic agent that can handle general queries."

# Agent's problem solver
def solve(basic_agent : BasicAgent, problem : str):
    """Solve a problem using reasoning."""
    return reason(f"Help me to answer the question: {problem}")

# Example usage
example_input = "Hello, how can you help me?"
print(solve(BasicAgent(), example_input))''' 