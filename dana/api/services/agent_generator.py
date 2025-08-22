"""
Agent Generator Module

This module processes user messages and generates appropriate Dana code for agent creation.
It uses LLM to understand user requirements and generate suitable agent templates.
"""

import logging
import os
from typing import Any

from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.common.types import BaseRequest
from dana.core.lang.dana_sandbox import DanaSandbox

from .code_handler import CodeHandler

logger = logging.getLogger(__name__)


class AgentGenerator:
    """
    Generates Dana agent code from user conversation messages.
    """

    def __init__(self, llm_config: dict[str, Any] | None = None):
        """
        Initialize the agent generator.

        Args:
            llm_config: Optional LLM configuration
        """
        self.llm_config = llm_config or {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 2000}

        # Initialize LLM resource with better error handling
        try:
            self.llm_resource = LegacyLLMResource(
                name="agent_generator_llm", description="LLM for generating Dana agent code", config=self.llm_config
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

    async def generate_agent_code(
        self, messages: list[dict[str, Any]], current_code: str = "", multi_file: bool = False
    ) -> tuple[str, str | None, dict[str, Any], dict[str, Any] | None]:
        """
        Generate Dana agent code from user conversation messages.

        Args:
            messages: List of conversation messages with 'role' and 'content' fields
            current_code: Current Dana code to improve upon (default empty string)
            multi_file: Whether to generate multi-file structure

        Returns:
            Tuple of (Generated Dana code as string, error message or None, conversation analysis, multi-file project or None)
        """
        # First, analyze if we need more information
        conversation_analysis = await analyze_conversation_completeness(messages)

        # Check if mock mode is enabled
        if os.environ.get("DANA_MOCK_AGENT_GENERATION", "").lower() == "true":
            logger.info("Using mock agent generation mode")
            return generate_mock_agent_code(messages, current_code), None, conversation_analysis, None

        try:
            # Check if LLM resource is available
            if self.llm_resource is None:
                logger.warning("LLMResource is not available, using fallback template")
                return CodeHandler.get_fallback_template(), None, conversation_analysis, None

            # Check if LLM is properly initialized
            if not hasattr(self.llm_resource, "_is_available") or not self.llm_resource._is_available:
                logger.warning("LLMResource is not available, using fallback template")
                return CodeHandler.get_fallback_template(), None, conversation_analysis, None

            # Extract user requirements and intentions using LLM
            user_intentions = await self._extract_user_intentions(messages, current_code)
            logger.info(f"Extracted user intentions: {user_intentions[:100]}...")

            # Create prompt for LLM based on current code and new intentions
            if multi_file:
                prompt = get_multi_file_agent_generation_prompt(user_intentions, current_code)
            else:
                prompt = self._create_generation_prompt(user_intentions, current_code, multi_file)
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

                # Handle multi-file response
                if multi_file and "FILE_START:" in generated_code:
                    multi_file_project = CodeHandler.parse_multi_file_response(generated_code)
                    # Extract main file content for backward compatibility
                    main_file_content = ""
                    for file_info in multi_file_project["files"]:
                        if file_info["filename"] == multi_file_project["main_file"]:
                            main_file_content = file_info["content"]
                            break

                    if main_file_content:
                        return main_file_content, None, conversation_analysis, multi_file_project
                    else:
                        logger.warning("No main file found in multi-file response")
                        return CodeHandler.get_fallback_template(), None, conversation_analysis, None

                # Clean up the generated code (single file)
                cleaned_code = CodeHandler.clean_generated_code(generated_code)
                logger.info(f"Cleaned code length: {len(cleaned_code)}")

                # FINAL FALLBACK: Ensure Dana code is returned
                if cleaned_code and "agent " in cleaned_code:
                    return cleaned_code, None, conversation_analysis, None
                else:
                    logger.warning("Generated code is empty or not Dana code, using fallback template")
                    return CodeHandler.get_fallback_template(), None, conversation_analysis, None
            else:
                logger.error(f"LLM generation failed: {response.error}")
                return CodeHandler.get_fallback_template(), None, conversation_analysis, None

        except Exception as e:
            logger.error(f"Error generating agent code: {e}")
            return CodeHandler.get_fallback_template(), str(e), conversation_analysis, None

    async def _extract_user_intentions(self, messages: list[dict[str, Any]], current_code: str = "") -> str:
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

            request = BaseRequest(arguments={"messages": [{"role": "user", "content": intention_prompt}]})

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

    def _extract_requirements(self, messages: list[dict[str, Any]]) -> str:
        """
        Extract user requirements from conversation messages (fallback method).

        Args:
            messages: List of conversation messages

        Returns:
            Extracted requirements as string
        """
        requirements = []

        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")

            if role == "user" and content:
                requirements.append(content)

        return "\n".join(requirements)

    def _create_generation_prompt(self, intentions: str, current_code: str = "", multi_file: bool = False) -> str:
        """
        Create a prompt for the LLM to generate Dana agent code.

        Args:
            intentions: User intentions extracted by LLM
            current_code: Current Dana code to improve upon
            multi_file: Whether to generate multi-file structure

        Returns:
            Formatted prompt for LLM
        """
        if multi_file:
            # Multi-file generation prompt
            prompt = get_multi_file_agent_generation_prompt(intentions, current_code)
        elif current_code:
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

IMPORTANT: Do NOT use ```python code blocks. This is Dana language code, not Python. Use ```dana or no code blocks at all.
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

IMPORTANT: Do NOT use ```python code blocks. This is Dana language code, not Python. Use ```dana or no code blocks at all.
"""
        return prompt

    async def cleanup(self):
        """Clean up resources."""
        if self.llm_resource:
            await self.llm_resource.cleanup()
        logger.info("Agent Generator cleaned up")


# Global instance
_agent_generator: AgentGenerator | None = None


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


async def generate_agent_code_from_messages(
    messages: list[dict[str, Any]], current_code: str = "", multi_file: bool = False
) -> tuple[str, str | None, dict[str, Any], dict[str, Any] | None]:
    """
    Generate Dana agent code from user conversation messages.

    Args:
        messages: List of conversation messages
        current_code: Current Dana code to improve upon (default empty string)
        multi_file: Whether to generate multi-file structure

    Returns:
        Tuple of (Generated Dana code, error message or None, conversation analysis, multi-file project or None)
    """
    generator = await get_agent_generator()
    result = await generator.generate_agent_code(messages, current_code, multi_file)
    if isinstance(result, tuple) and len(result) == 4:
        return result  # (code, error, analysis, multi_file_project)
    elif isinstance(result, tuple) and len(result) == 3:
        return result[0], result[1], result[2], None  # backward compatibility
    elif isinstance(result, tuple) and len(result) == 2:
        return result[0], result[1], {}, None  # backward compatibility
    return result, None, {}, None


async def generate_agent_code_na(messages: list[dict[str, Any]], current_code: str = "") -> tuple[str, str | None]:
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
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".na", delete=False) as temp_file:
            temp_file.write(na_code)
            temp_file_path = temp_file.name

        try:
            # Execute the .na file using DanaSandbox.quick_run with file path
            result = DanaSandbox.execute_file_once(file_path=temp_file_path)

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
                        error_msg = str(test_result.error) if hasattr(test_result, "error") else "Unknown syntax error"
                        logger.warning(f"Generated code has errors: {error_msg}")
                        # Try to fix the code using a Dana agent
                        fixed_code = await _fix_generated_code_with_agent(generated_code, error_msg, messages)
                        if fixed_code:
                            return fixed_code, None
                        else:
                            logger.warning("Failed to fix code, using fallback template")
                            return CodeHandler.get_fallback_template(), None
                else:
                    logger.warning("Generated code is empty or not Dana code, using fallback template")
                    return CodeHandler.get_fallback_template(), None
            else:
                logger.error(f"NA execution failed: {result.error}")
                # Try to generate a simple fallback agent based on user intention
                try:
                    fallback_code = _generate_simple_fallback_agent(messages)
                    return fallback_code, None
                except Exception as fallback_error:
                    logger.error(f"Fallback generation also failed: {fallback_error}")
                    return CodeHandler.get_fallback_template(), str(result.error)

        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temporary file: {cleanup_error}")

    except Exception as e:
        logger.error(f"Error generating agent code with NA: {e}")
        return CodeHandler.get_fallback_template(), str(e)


def _create_agent_generator_na_code(messages: list[dict[str, Any]], current_code: str) -> str:
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
    current_code_str = current_code.replace('"', '\\"').replace("\n", "\\n")

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

Generate only the Dana code, no explanations or markdown formatting. Make sure all strings are properly quoted and all syntax is valid Dana.

IMPORTANT: Do NOT use ```python code blocks. This is Dana language code, not Python. Use ```dana or no code blocks at all."""

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
        import os
        import tempfile

        # Write the code to a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".na", delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        try:
            # Test the code using DanaSandbox.quick_run
            result = DanaSandbox.execute_file_once(file_path=temp_file_path)
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


async def _fix_generated_code_with_agent(code: str, error: str, messages: list[dict[str, Any]]) -> str:
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
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".na", delete=False) as temp_file:
            temp_file.write(fixer_code)
            temp_file_path = temp_file.name

        try:
            # Execute the code fixer
            result = DanaSandbox.execute_file_once(file_path=temp_file_path)

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


def _create_code_fixer_na_code(code: str, error: str, messages: list[dict[str, Any]]) -> str:
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
    code_str = code.replace('"', '\\"').replace("\n", "\\n")
    # Convert error to string and escape it properly - use a simpler approach
    str(error).replace('"', '\\"').replace("'", "\\'").replace("\n", "\\n")
    str(messages).replace('"', '\\"')

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

Generate only the corrected Dana code, no explanations or markdown formatting. Make sure all strings are properly quoted and all syntax is valid Dana.

IMPORTANT: Do NOT use ```python code blocks. This is Dana language code, not Python. Use ```dana or no code blocks at all."""

    fixed_code = reason(prompt)
    return fixed_code

# Execute the code fixer
result = solve(CodeFixerAgent(), "Fix the Dana code")
result
'''


def _generate_simple_fallback_agent(messages: list[dict[str, Any]]) -> str:
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

# Use solve() in your application
# example_input = "Hello, how can you help me?"
# response = solve({agent_name}(), example_input)'''


async def analyze_conversation_completeness(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze if the conversation has enough information to generate a meaningful agent.

    Args:
        messages: List of conversation messages

    Returns:
        Dictionary with analysis results including whether more info is needed
    """
    try:
        # Extract user messages only
        user_messages = [msg.get("content", "") for msg in messages if msg.get("role") == "user"]
        conversation_text = " ".join(user_messages).lower()

        # Check for vague or insufficient requests
        vague_indicators = ["help", "assistant", "agent", "create", "make", "build", "something", "anything"]

        specific_indicators = [
            "weather",
            "data",
            "analysis",
            "email",
            "calendar",
            "document",
            "research",
            "finance",
            "customer",
            "sales",
            "support",
            "translate",
            "schedule",
            "appointment",
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
            follow_up_message = "I'm Dana, and I'd love to help you train Georgia! To build something that's truly useful for you, could you tell me more about what you'd like Georgia to do? The more specific you can be, the better I can tailor her training to your needs."

            suggested_questions = [
                "What specific task should Georgia help you with?",
                "What kind of data or information will Georgia work with?",
                "Who will be using Georgia and in what context?",
                "Do you have any existing tools or systems Georgia should integrate with?",
            ]

        # Check for unclear domain or purpose
        elif "help" in conversation_text and specific_count == 0:
            needs_more_info = True
            follow_up_message = "I can help you train Georgia! What specific area would you like Georgia to assist with? For example, are you looking for help with business processes, data analysis, communication, or something else?"

            suggested_questions = [
                "What's the main purpose for Georgia?",
                "What industry or domain is this for?",
                "What are the key features you need Georgia to have?",
            ]

        # Check for missing technical details if it's a complex request
        elif any(term in conversation_text for term in ["integration", "api", "database", "system"]) and "how" not in conversation_text:
            needs_more_info = True
            follow_up_message = "I can see you want to train Georgia with some technical integrations. To build this properly, I'll need some more details about your technical requirements."

            suggested_questions = [
                "What APIs or systems should Georgia connect to?",
                "What data formats will you be working with?",
                "Are there any specific authentication requirements?",
                "What's your preferred way of receiving results?",
            ]

        return {
            "needs_more_info": needs_more_info,
            "follow_up_message": follow_up_message,
            "suggested_questions": suggested_questions,
            "analysis": {
                "word_count": word_count,
                "vague_count": vague_count,
                "specific_count": specific_count,
                "conversation_text": conversation_text[:100] + "..." if len(conversation_text) > 100 else conversation_text,
            },
        }

    except Exception as e:
        logger.error(f"Error analyzing conversation completeness: {e}")
        return {"needs_more_info": False, "follow_up_message": None, "suggested_questions": [], "analysis": {"error": str(e)}}


async def analyze_agent_capabilities(
    dana_code: str, messages: list[dict[str, Any]], multi_file_project: dict[str, Any] = None
) -> dict[str, Any]:
    """
    Analyze the generated Dana code and conversation to extract agent capabilities using LLM.

    Args:
        dana_code: Generated Dana agent code (main file content)
        messages: Original conversation messages
        multi_file_project: Multi-file project data if available

    Returns:
        Dictionary containing summary, knowledge, workflow, and tools
    """
    try:
        # Extract conversation context
        conversation_text = "\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in messages])

        # For multi-file projects, get additional context from all files
        all_code_content = dana_code
        if multi_file_project and multi_file_project.get("files"):
            # Combine all file contents for comprehensive analysis
            all_files_content = []
            for file_info in multi_file_project["files"]:
                all_files_content.append(f"# File: {file_info['filename']}\n{file_info['content']}")
            all_code_content = "\n\n".join(all_files_content)

        # Try to use LLM to analyze the agent capabilities
        try:
            # Create LLM resource with proper configuration
            llm_config = {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 2000}
            llm = LegacyLLMResource(
                name="agent_capabilities_analyzer", description="LLM for analyzing Dana agent capabilities", config=llm_config
            )

            # Initialize the LLM resource
            await llm.initialize()

            # Check if LLM is available before proceeding
            if not hasattr(llm, "_is_available") or not llm._is_available:
                logger.warning("LLM resource is not available, falling back to manual analysis")
                raise Exception("LLM not available")

            analysis_prompt = f"""
Analyze the following Dana agent code and conversation context to generate a focused, accurate summary.

**Conversation Context:**
{conversation_text}

**Dana Agent Code:**
{all_code_content}

Generate a brief, focused markdown summary that includes ONLY information that actually exists in the code or conversation:

1. **Agent Overview**: Name and description (only if explicitly defined)
2. **Core Capabilities**: What the agent can actually do based on the code
3. **Knowledge Sources**: What knowledge bases or documents it actually uses (only if present in code)
4. **Workflow Process**: How the agent actually works (only if defined in code)

IMPORTANT RULES:
- Only include information that is explicitly present in the code or conversation
- Do NOT generate information about future integrations or capabilities
- Do NOT include generic capabilities that aren't specifically implemented
- Do NOT mention tools or integrations unless they are actually used in the code
- Keep the summary concise and factual
- If a section has no relevant information, omit it entirely

Focus on analyzing:
- What the agent actually does based on the code structure
- What resources it actually uses (RAG, LLM, etc.)
- What functions and workflows are actually implemented
- What knowledge domains are actually referenced
- Do not include the headline
- Do not mention Dana Code or Conversation Context in the summary

Generate a brief, accurate summary that reflects the current state of the agent, not future possibilities.
"""

            # Create a request for the LLM
            request = BaseRequest(arguments={"prompt": analysis_prompt, "messages": [{"role": "user", "content": analysis_prompt}]})

            result = await llm.query(request)

            if result and result.success:
                # Extract content from response
                markdown_summary = ""
                if hasattr(result, "content") and result.content:
                    if isinstance(result.content, dict):
                        # Handle OpenAI-style response format
                        if "choices" in result.content:
                            markdown_summary = result.content["choices"][0]["message"]["content"]
                        elif "response" in result.content:
                            markdown_summary = result.content["response"]
                        elif "content" in result.content:
                            markdown_summary = result.content["content"]
                    elif isinstance(result.content, str):
                        markdown_summary = result.content

                if markdown_summary:
                    logger.info("Successfully generated agent capabilities summary using LLM")
                    # Extract basic structured data for backward compatibility
                    capabilities = {
                        "summary": markdown_summary,
                        "knowledge": _extract_knowledge_domains_from_code(all_code_content, conversation_text),
                        "workflow": _extract_workflow_steps_from_code(all_code_content, conversation_text),
                        "tools": _extract_agent_tools_from_code(all_code_content),
                    }
                    return capabilities
                else:
                    logger.warning("LLM returned empty response, falling back to manual analysis")
                    raise Exception("Empty LLM response")
            else:
                logger.warning(f"LLM analysis failed: {result.error if hasattr(result, 'error') else 'Unknown error'}")
                raise Exception("LLM query failed")

        except Exception as llm_error:
            logger.warning(f"LLM analysis failed ({llm_error}), falling back to manual analysis")
            # Fallback to manual analysis if LLM fails
            capabilities = {
                "summary": _extract_summary_from_code_and_conversation(dana_code, conversation_text),
                "knowledge": _extract_knowledge_domains_from_code(all_code_content, conversation_text),
                "workflow": _extract_workflow_steps_from_code(all_code_content, conversation_text),
                "tools": _extract_agent_tools_from_code(all_code_content),
            }
            return capabilities

    except Exception as e:
        logger.error(f"Error analyzing agent capabilities: {e}")
        return {"summary": "Unable to analyze agent capabilities", "knowledge": [], "workflow": [], "tools": []}


def _extract_summary_from_code_and_conversation(dana_code: str, conversation_text: str) -> str:
    """Extract a comprehensive markdown summary of what the agent does based on actual code."""
    # Extract agent name and description from code
    lines = dana_code.split("\n")
    agent_name = None
    agent_description = None

    for line in lines:
        if line.strip().startswith("agent ") and line.strip().endswith(":"):
            # Extract agent name
            agent_name = line.strip().replace("agent ", "").replace(":", "").strip()
        elif "description : str =" in line:
            agent_description = line.split("=")[1].strip().strip('"')
            break

    # Analyze what the agent actually does based on the solve function
    solve_function_content = _extract_solve_function_content(dana_code)

    # Build comprehensive markdown summary
    markdown_summary = []

    # Header with agent name
    if agent_name:
        markdown_summary.append(f"# {agent_name}")
    else:
        markdown_summary.append("# Dana Agent")

    # Description section
    if agent_description:
        markdown_summary.append(f"\n## Overview\n{agent_description}")
    else:
        markdown_summary.append("\n## Overview\nA specialized Dana agent that provides intelligent assistance.")

    # Analyze actual capabilities from solve function
    capabilities = []
    if "reason(" in solve_function_content:
        if "resources=" in solve_function_content:
            capabilities.append("uses knowledge base for informed responses")
        else:
            capabilities.append("uses AI reasoning for problem-solving")

    # Check for resource usage
    if 'use("rag"' in dana_code:
        capabilities.append("can access and retrieve information from documents")

    # Domain-specific capabilities
    domain_capabilities = []
    if "weather" in solve_function_content.lower():
        domain_capabilities.append("provides weather information and forecasts")
    if "data" in solve_function_content.lower() or "analysis" in solve_function_content.lower():
        domain_capabilities.append("performs data analysis and insights")
    if "email" in solve_function_content.lower():
        domain_capabilities.append("assists with email composition and management")
    if "calendar" in solve_function_content.lower() or "schedule" in solve_function_content.lower():
        domain_capabilities.append("helps with scheduling and time management")
    if "document" in solve_function_content.lower() or "file" in solve_function_content.lower():
        domain_capabilities.append("processes and analyzes documents")
    if "finance" in solve_function_content.lower() or "money" in solve_function_content.lower():
        domain_capabilities.append("provides financial advice and guidance")

    # Core capabilities section - only include if actually present
    if capabilities or domain_capabilities:
        markdown_summary.append("\n## Core Capabilities")
        all_capabilities = capabilities + domain_capabilities
        for capability in all_capabilities:
            markdown_summary.append(f"- {capability.capitalize()}")

    # Knowledge sources section - only include if actually present in code
    knowledge_sources = _extract_knowledge_domains_from_code(dana_code, conversation_text)
    if knowledge_sources and any(source.strip() for source in knowledge_sources):
        markdown_summary.append("\n## Knowledge Sources")
        for source in knowledge_sources:
            if source.strip():  # Only include non-empty sources
                markdown_summary.append(f"- {source}")

    # Workflow section - only include if actually defined
    workflow_steps = _extract_workflow_steps_from_code(dana_code, conversation_text)
    if workflow_steps and any(step.strip() for step in workflow_steps):
        markdown_summary.append("\n## Workflow Process")
        for i, step in enumerate(workflow_steps, 1):
            if step.strip():  # Only include non-empty steps
                markdown_summary.append(f"{i}. {step}")

    # Tools section - only include if actually used in code
    tools = _extract_agent_tools_from_code(dana_code)
    if tools and any(tool.strip() for tool in tools):
        markdown_summary.append("\n## Tools & Integrations")
        for tool in tools:
            if tool.strip():  # Only include non-empty tools
                markdown_summary.append(f"- {tool}")

    # Technical specifications
    markdown_summary.append("\n## Technical Specifications")

    # Check for data structures
    if "struct " in dana_code:
        markdown_summary.append("- **Data Structures**: Custom Dana structs for data handling")

    # Check for workflow patterns
    if "workflow =" in dana_code:
        markdown_summary.append("- **Architecture**: Pipeline-based workflow processing")

    # Check for multi-file structure
    if "from " in dana_code and "import " in dana_code:
        markdown_summary.append("- **Structure**: Multi-file modular architecture")

    # Check for reasoning usage
    if "reason(" in dana_code:
        markdown_summary.append("- **AI Integration**: Uses Dana's built-in reasoning capabilities")

    return "\n".join(markdown_summary)


def _extract_knowledge_domains_from_code(dana_code: str, conversation_text: str) -> list[str]:
    """Extract knowledge domains the agent can work with based on actual code."""
    domains = []

    # Analyze code for RAG resources and their sources
    if 'use("rag"' in dana_code:
        domains.append("Document-based knowledge retrieval")

        # Extract specific sources if mentioned
        import re

        sources_match = re.search(r"sources=\[([^\]]+)\]", dana_code)
        if sources_match:
            sources = sources_match.group(1)
            if "pdf" in sources.lower():
                domains.append("PDF document analysis")
            if "txt" in sources.lower():
                domains.append("Text file processing")
            if "md" in sources.lower():
                domains.append("Markdown documentation")
            if "guide" in sources.lower():
                domains.append("Reference guides and manuals")

    # Analyze agent name and description for domain expertise
    agent_name = _extract_agent_name_from_code(dana_code)
    agent_description = _extract_agent_description_from_code(dana_code)

    code_content = f"{agent_name} {agent_description}".lower()

    # Extract domains based on actual agent characteristics
    if "weather" in code_content:
        domains.append("Weather and climate information")
    if "data" in code_content or "analysis" in code_content:
        domains.append("Data analysis and statistics")
    if "email" in code_content:
        domains.append("Email communication and management")
    if "calendar" in code_content or "schedule" in code_content:
        domains.append("Time management and scheduling")
    if "document" in code_content or "file" in code_content:
        domains.append("Document processing and analysis")
    if "research" in code_content or "knowledge" in code_content:
        domains.append("Research and information gathering")
    if "finance" in code_content or "money" in code_content or "investment" in code_content:
        domains.append("Personal finance and investment")
    if "code" in code_content or "programming" in code_content:
        domains.append("Software development and programming")
    if "health" in code_content or "medical" in code_content:
        domains.append("Health and wellness information")
    if "travel" in code_content:
        domains.append("Travel planning and recommendations")
    if "customer" in code_content or "support" in code_content:
        domains.append("Customer service and support")
    if "sales" in code_content or "marketing" in code_content:
        domains.append("Sales and marketing assistance")

    # Only return domains if we actually found specific ones
    # Don't add generic defaults that don't exist in the code
    return domains


def _extract_workflow_steps_from_code(dana_code: str, conversation_text: str) -> list[str]:
    """Extract the typical workflow steps the agent follows based on actual code."""
    workflow = []

    # Analyze the solve function to understand actual workflow
    solve_function_content = _extract_solve_function_content(dana_code)

    # Check for workflow patterns in the code
    if "workflow =" in dana_code:
        # Extract workflow from multi-file structure
        workflow.append("**Input Processing**: Accept and validate user query")

        # Look for pipeline operators to understand workflow
        if "|" in dana_code:
            workflow.append("**Pipeline Processing**: Execute sequential workflow stages")

        # Analyze individual workflow steps
        if "process_request" in dana_code:
            workflow.append("**Request Analysis**: Parse and categorize user request")

        if "generate_response" in dana_code:
            workflow.append("**Response Generation**: Create appropriate response")

        if "reason(" in solve_function_content:
            workflow.append("**AI Reasoning**: Apply intelligent analysis to generate solutions")

        workflow.append("**Output Delivery**: Return formatted response to user")

    else:
        # Single-file agent workflow
        workflow.append("**Input Reception**: Receive and process user query")

        # Analyze the solve function for specific processing steps
        if "resources=" in solve_function_content:
            workflow.append("**Knowledge Retrieval**: Query knowledge base for relevant information")
            workflow.append("**Context Integration**: Apply reasoning with retrieved context")
            workflow.append("**Response Generation**: Generate informed response based on knowledge base")
        elif "reason(" in solve_function_content:
            workflow.append("**AI Processing**: Apply AI reasoning to understand the problem")
            workflow.append("**Solution Generation**: Generate appropriate response or solution")

    # Add domain-specific workflow steps based on agent characteristics
    agent_name = _extract_agent_name_from_code(dana_code)
    agent_description = _extract_agent_description_from_code(dana_code)

    code_content = f"{agent_name} {agent_description} {solve_function_content}".lower()

    # Insert specific processing steps based on agent type
    if "weather" in code_content:
        workflow.insert(-1, "**Weather Analysis**: Analyze weather patterns and conditions")
    elif "data" in code_content or "analysis" in code_content:
        workflow.insert(-1, "2. Process and analyze data patterns")
        workflow.append("4. Present insights and recommendations")
    elif "document" in code_content or "file" in code_content:
        workflow.insert(-1, "2. Process and analyze document content")
    elif "email" in code_content:
        workflow.insert(-1, "2. Analyze email context and requirements")
        workflow.append("4. Format response appropriately for email context")
    elif "calendar" in code_content or "schedule" in code_content:
        workflow.insert(-1, "2. Analyze scheduling requirements and constraints")
    elif "finance" in code_content or "money" in code_content:
        workflow.insert(-1, "2. Analyze financial situation and requirements")
        workflow.append("4. Provide personalized financial recommendations")

    # Only return workflow if we actually found specific steps
    # Don't add generic defaults that don't exist in the code
    return workflow


def _extract_agent_tools_from_code(dana_code: str) -> list[str]:
    """Extract tools and capabilities available to the agent based on actual code."""
    tools = []

    # Core Dana capabilities that are always present
    tools.append("**Dana Reasoning Engine**: Built-in AI reasoning capabilities via `reason()` function")

    # Check for specific resources and their capabilities
    if 'use("rag"' in dana_code:
        tools.append("**RAG System**: Retrieval-Augmented Generation for document-based knowledge")
        tools.append("**Document Search**: Advanced search and retrieval from knowledge base")
        tools.append("**Knowledge Querying**: Semantic search across indexed documents")

        # Extract specific source types
        import re

        sources_match = re.search(r"sources=\[([^\]]+)\]", dana_code)
        if sources_match:
            sources = sources_match.group(1)
            if "pdf" in sources.lower():
                tools.append("**PDF Processing**: Extract and analyze PDF document content")
            if "txt" in sources.lower():
                tools.append("**Text Analysis**: Process and analyze plain text files")
            if "md" in sources.lower():
                tools.append("**Markdown Parser**: Parse and process markdown documentation")

    # Check for database integrations
    if 'use("database"' in dana_code:
        tools.append("**Database Integration**: Connect to and query external databases")

    # Check for API integrations
    if 'use("api"' in dana_code:
        tools.append("**API Integration**: Connect to external APIs and services")

    # Check for workflow pipeline capabilities
    if "workflow =" in dana_code and "|" in dana_code:
        tools.append("**Pipeline Processing**: Sequential workflow execution with pipe operators")

    # Check for data structure capabilities
    if "struct " in dana_code:
        tools.append("**Data Structures**: Custom Dana structs for structured data handling")

    # Check for custom functions (beyond solve)
    custom_functions = []
    lines = dana_code.split("\n")
    for line in lines:
        if line.strip().startswith("def ") and "solve(" not in line:
            func_name = line.strip().split("(")[0].replace("def ", "")
            custom_functions.append(func_name)

    if custom_functions:
        tools.append(f"**Custom Functions**: Specialized utility functions ({', '.join(custom_functions)})")

    # Check for imports that indicate additional capabilities
    imports = []
    for line in lines:
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            imports.append(line.strip())

    if imports:
        external_tools = []
        for imp in imports:
            if "json" in imp:
                external_tools.append("JSON data processing")
            elif "os" in imp:
                external_tools.append("System operations")
            elif "datetime" in imp:
                external_tools.append("Date and time handling")
            elif "requests" in imp:
                external_tools.append("HTTP requests")
            elif "pandas" in imp:
                external_tools.append("Data analysis with Pandas")
            elif "numpy" in imp:
                external_tools.append("Numerical computing")

        if external_tools:
            tools.append(f"**External Libraries**: {', '.join(external_tools)}")

    # Check for error handling
    if "try:" in dana_code or "except:" in dana_code:
        tools.append("Error handling and recovery")

    # Check for data structures
    if "list" in dana_code and "resources : list" not in dana_code:
        tools.append("List data processing")
    if "dict" in dana_code:
        tools.append("Dictionary data manipulation")

    # Check for private variables (state management)
    if "private:" in dana_code:
        tools.append("State management")

    # Analyze agent-specific capabilities based on agent type
    agent_name = _extract_agent_name_from_code(dana_code)
    agent_description = _extract_agent_description_from_code(dana_code)

    code_content = f"{agent_name} {agent_description}".lower()

    if "weather" in code_content:
        tools.append("Weather data interpretation")
    elif "data" in code_content or "analysis" in code_content:
        tools.append("Data analysis and visualization")
        tools.append("Statistical computation")
    elif "email" in code_content:
        tools.append("Email composition assistance")
        tools.append("Communication optimization")
    elif "calendar" in code_content or "schedule" in code_content:
        tools.append("Time management algorithms")
        tools.append("Scheduling optimization")
    elif "finance" in code_content or "money" in code_content:
        tools.append("Financial calculation")
        tools.append("Investment analysis")
    elif "document" in code_content or "file" in code_content:
        tools.append("Document parsing and analysis")
        tools.append("Content extraction")

    # Only return tools that are actually present in the code
    # Don't add generic capabilities that aren't specifically implemented
    return list(set(tools))  # Remove duplicates


def _extract_solve_function_content(dana_code: str) -> str:
    """Extract the content of the solve function from Dana code."""
    lines = dana_code.split("\n")
    solve_content = []
    in_solve_function = False

    for line in lines:
        if "def solve(" in line:
            in_solve_function = True
            solve_content.append(line)
            continue
        elif in_solve_function:
            if line.strip() and not line.startswith("    "):
                break
            solve_content.append(line)

    return "\n".join(solve_content)


def _extract_agent_name_from_code(dana_code: str) -> str:
    """Extract the agent name from Dana code."""
    lines = dana_code.split("\n")
    for line in lines:
        if line.strip().startswith("agent ") and line.strip().endswith(":"):
            return line.strip().replace("agent ", "").replace(":", "").strip()
    return ""


def _extract_agent_description_from_code(dana_code: str) -> str:
    """Extract the agent description from Dana code."""
    lines = dana_code.split("\n")
    for line in lines:
        if "description : str =" in line:
            return line.split("=")[1].strip().strip('"')
    return ""


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

# Use solve() in your application
# example_input = "Hello, how can you help me?"
# response = solve(BasicAgent(), example_input)'''


async def generate_agent_files_from_prompt(
    prompt: str,
    messages: list[dict[str, Any]],
    agent_summary: dict[str, Any],
    multi_file: bool = False,
    has_docs_folder: bool = False,
    has_knows_folder: bool = False,
) -> tuple[str, str | None, dict[str, Any] | None]:
    """
    Generate Dana agent files from a specific prompt, conversation messages, and agent summary.

    This function is designed for Phase 2 of the agent generation flow, where we have
    a refined agent description and want to generate the actual .na files.

    Args:
        prompt: Specific prompt for generating the agent files
        messages: List of conversation messages with 'role' and 'content' fields
        agent_summary: Dictionary containing agent description, capabilities, etc.
        multi_file: Whether to generate multi-file structure

    Returns:
        Tuple of (Generated Dana code as string, error message or None, multi-file project or None)
    """
    logger.info("Generating agent files from prompt for Phase 2")

    try:
        # Check if mock mode is enabled
        if os.environ.get("DANA_MOCK_AGENT_GENERATION", "").lower() == "true":
            logger.info("Using mock agent generation mode for Phase 2")
            return generate_mock_agent_code(messages, ""), None, None

        # Get agent generator instance
        generator = await get_agent_generator()

        # Check if LLM resource is available
        if generator.llm_resource is None:
            logger.warning("LLMResource is not available, using fallback template")
            return CodeHandler.get_fallback_template(), None, None

        # Check if LLM is properly initialized
        if not hasattr(generator.llm_resource, "_is_available") or not generator.llm_resource._is_available:
            logger.warning("LLMResource is not available, using fallback template")
            return CodeHandler.get_fallback_template(), None, None

        # Create enhanced prompt with context
        enhanced_prompt = _create_phase_2_prompt(prompt, messages, agent_summary, multi_file, has_docs_folder, has_knows_folder)
        print(f"Enhanced Phase 2 prompt: {enhanced_prompt}")
        logger.debug(f"Enhanced Phase 2 prompt: {enhanced_prompt[:200]}...")

        # Generate code using LLM
        request = BaseRequest(arguments={"prompt": enhanced_prompt, "messages": [{"role": "user", "content": enhanced_prompt}]})
        logger.info("Sending Phase 2 request to LLM...")

        response = await generator.llm_resource.query(request)
        logger.info(f"LLM response success: {response.success}")
        print("--------------------------------")
        print("LLM Success: ", response.success)
        print(f"LLM response: {response}")
        print(f"LLM response content: {response.content}")
        print("--------------------------------")

        if response.success:
            generated_code = response.content.get("choices", "")[0].get("message", {}).get("content", "")
            print("--------------------------------")
            print("Generated code: ", generated_code)
            print("--------------------------------")
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

            logger.info(f"Generated Phase 2 code length: {len(generated_code)}")

            # Handle multi-file response (always the case)
            logger.info("Parsing multi-file response...")
            multi_file_project = CodeHandler.parse_multi_file_response(generated_code)
            logger.info(f"Parsed multi-file project: {multi_file_project}")

            # Extract main file content for backward compatibility
            main_file_content = ""
            for file_info in multi_file_project["files"]:
                if file_info["filename"] == multi_file_project["main_file"]:
                    main_file_content = file_info["content"]
                    break

            print("--------------------------------")
            print("Multi-file project: ", multi_file_project)
            print("--------------------------------")

            if main_file_content:
                print("--------------------------------")
                print("Main file content: ", main_file_content)
                print("--------------------------------")
                logger.info(f"Returning multi-file project with {len(multi_file_project['files'])} files")
                return main_file_content, None, multi_file_project
            else:
                logger.warning("No main file found in multi-file response")
                print("--------------------------------")
                print("No main file found in multi-file response")
                print("--------------------------------")
                return CodeHandler.get_fallback_template(), None, None
        else:
            logger.error(f"LLM generation failed for Phase 2: {response.error}")
            print("--------------------------------")
            print("LLM generation failed for Phase 2: ", response.error)
            print("--------------------------------")
            return CodeHandler.get_fallback_template(), None, None

    except Exception as e:
        logger.error(f"Error generating Phase 2 agent code: {e}")
        logger.exception(e)
        return CodeHandler.get_fallback_template(), str(e), None


def _create_phase_2_prompt(
    prompt: str,
    messages: list[dict[str, Any]],
    agent_summary: dict[str, Any],
    multi_file: bool,
    has_docs_folder: bool = False,
    has_knows_folder: bool = False,
) -> str:
    """
    Create an enhanced prompt for Phase 2 agent generation.

    Args:
        prompt: The specific prompt for generating agent files
        messages: Conversation messages for context
        agent_summary: Agent description and capabilities
        multi_file: Whether to generate multi-file structure

    Returns:
        Enhanced prompt string
    """
    # Extract conversation context
    conversation_text = "\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in messages])

    # Extract agent information
    agent_name = agent_summary.get("name", "Custom Agent")
    agent_description = agent_summary.get("description", "A specialized agent for your needs")
    capabilities = agent_summary.get("capabilities", {})
    agent_summary_description = capabilities.get("summary", "")
    knowledge_domains = capabilities.get("knowledge", [])
    workflow_steps = capabilities.get("workflow", [])
    tools = capabilities.get("tools", [])

    agent_class = agent_name.replace(" ", "")
    # Try to get docs files from agent_summary if available
    docs_files = agent_summary.get("docs_files") or agent_summary.get("knowledge_files") or []
    if not isinstance(docs_files, list):
        docs_files = []

    # Create context section
    context_section = f"""
AGENT SUMMARY:
- Name: {agent_name}
- Description: {agent_description}
- Knowledge Domains: {", ".join(knowledge_domains) if knowledge_domains else "None specified"}
- Workflow Steps: {", ".join(workflow_steps) if workflow_steps else "None specified"}
- Tools: {", ".join(tools) if tools else "None specified"}
- Summary: {agent_summary_description}

CONVERSATION CONTEXT:
{conversation_text}

SPECIFIC REQUIREMENTS:
{prompt}
"""

    main_na = f"""
from workflows import workflow
from common import RetrievalPackage

agent {agent_class}:
    name: str = "{agent_name}"
    description: str = "Get from agent description and summary"


def solve(self : {agent_class}, query: str) -> str:
    package = RetrievalPackage(query=query)
    return workflow(package)

this_agent = {agent_class}()
"""

    methods_na = """
from knowledge import knowledge
from knowledge import doc
from common import QUERY_GENERATION_PROMPT
from common import QUERY_DECISION_PROMPT
from common import ANSWER_PROMPT
from common import RetrievalPackage

def search_document(package: RetrievalPackage) -> RetrievalPackage:
    query = package.refined_query
    package.retrieval_result = str(doc.query(query))
    return package

def refine_query(package: RetrievalPackage) -> RetrievalPackage:
    package.refined_query = reason(QUERY_GENERATION_PROMPT.format(user_input=package.query, context=package.context, filenames=doc.filenames), temperature=0.1)
    return package

def get_answer(package: RetrievalPackage) -> str:
    prompt = ANSWER_PROMPT.format(user_input=package.query, retrieved_docs=package.retrieval_result, context=package.context, original_problem=package.original_problem)
    return reason(prompt, resources=[knowledge], temperature=0.1)
"""

    workflows_na = """
from methods import refine_query
from methods import search_document
from methods import get_answer

workflow = refine_query | search_document | get_answer
"""

    # Build knowledge.na with rag_resource and comments about docs files
    knowledges_na_lines = [
        '"""',
        "Knowledge sources for this agent. The following files are available in the ./docs folder:",
    ]
    if docs_files:
        for f in docs_files:
            knowledges_na_lines.append(f"- {f}")
    else:
        knowledges_na_lines.append("- (No files currently listed. Add files to ./docs to make them available.)")
    if not has_docs_folder:
        knowledges_na_lines.append("- (No files currently listed. Add files to ./docs to make them available.)")
    if not has_knows_folder:
        knowledges_na_lines.append("- (No files currently listed. Add files to ./knows to make them available.)")
    knowledges_na_lines.append('"""\n')
    if has_docs_folder:
        knowledges_na_lines.append('doc = use("rag", sources=["./docs"])')
    if has_knows_folder:
        knowledges_na_lines.append('knowledge = use("rag", sources=["./knows"])')
    knowledges_na = "\n".join(knowledges_na_lines)

    tools_na = ""  # No rag_resource here; left intentionally empty or for other tools

    common_na = '''

struct RetrievalPackage:
   query: str
   refined_query: str = ""
   should_use_rag: bool = False
   retrieval_result: str = "<empty>"
   context: str = ""
   original_problem: str = ""
    
QUERY_GENERATION_PROMPT = """
You are **QuerySmith**, an expert search-query engineer for a Retrieval-Augmented Generation (RAG) pipeline.

────────────────────────────────────────────────────────────
GOAL  
Return **one** concise search query (≤ 12 tokens) that retrieves ONLY information **missing** from the Current Context and most relevant to the topics hinted at by the available filenames.

────────────────────────────────────────────────────────────
INPUTS  
• USER_REQUEST – the user’s current question.  
• CURRENT_CONTEXT – any information already known.  
• AVAILABLE_FILES – *optional* list of filenames (with extensions) that suggest additional topics.

────────────────────────────────────────────────────────────
WORKFLOW  

0. **Context Sufficiency Test**  
   • If CURRENT_CONTEXT already answers USER_REQUEST completely, output a blank line and stop.

1. **Filename Topic Mining**  
   • Strip extensions from AVAILABLE_FILES.  
   • Split remaining names on delimiters (space, underscore, dash).  
   • Retain meaningful topic words/phrases; ignore ordinals, dates, version tags.

2. **Gap-Focused Concept Extraction**  
   • From USER_REQUEST, pull entities, actions, qualifiers **not covered** in CURRENT_CONTEXT.  
   • Add relevant topic words mined in Step 1 that fill these gaps.

3. **Term Refinement**  
   • Keep the most discriminative nouns/verbs; drop stop-words and redundancies.  
   • Substitute stronger, widely-used synonyms when they improve recall.

4. **Context Packing**  
   • Order terms by importance; wrap multi-word entities in quotes.

5. **Final Polish**  
   • Convert to lowercase; no punctuation except quotes; ≤ 12 tokens; **no** explanatory text.

────────────────────────────────────────────────────────────
OUTPUT  
Return **only** the final query string on a single line (or a blank line if Step 0 triggered).  
No markdown, labels, or commentary.

────────────────────────────────────────────────────────────
CURRENT_CONTEXT:
{context}

AVAILABLE_FILES:
{filenames}

USER_REQUEST:
{user_input}
"""
    

QUERY_DECISION_PROMPT = """
You are **RetrievalGate**, a binary decision agent guarding a Retrieval-Augmented Generation (RAG) pipeline.

Task  
Analyze the USER_REQUEST below and decide whether external document retrieval is required to answer it accurately.

Decision Rules  
1. External-Knowledge Need – Does the request demand up-to-date facts, statistics, citations, or niche info unlikely to be in the model's parameters?  
2. Internal Sufficiency – Could the model satisfy the request with its own reasoning, creativity, or general knowledge?  
3. Explicit User Cue – If the user explicitly asks to "look up," "cite," "fetch," "search," or mentions a source/corpus, retrieval is required.  
4. Ambiguity Buffer – When uncertain, default to retrieval (erring on completeness).

Output Format  
Return **only** one lowercase Boolean literal on a single line:  
- `true`  → retrieval is needed  
- `false` → retrieval is not needed

---

USER_REQUEST: 
{user_input}
"""

ANSWER_PROMPT = """
You are **RAGResponder**, an expert answer-composer for a Retrieval-Augmented Generation (RAG) pipeline.

────────────────────────────────────────────────────────────
INPUTS
• ORIGINAL_PROBLEM – the user’s original question.
• USER_REQUEST – the user’s current question.  
• CURRENT_CONTEXT – *optional* conversation or system knowledge already at hand.  
• RETRIEVED_DOCS – *optional* list of objects, each with:
    · doc_id      · metadata  
    · content

────────────────────────────────────────────────────────────
OBJECTIVE  
Provide one clear, complete answer that satisfies USER_REQUEST while avoiding redundancy.

────────────────────────────────────────────────────────────
WORKFLOW  

0. **Context Sufficiency Test**  
   • If CURRENT_CONTEXT fully answers USER_REQUEST, use it and skip Steps 1-3.  

1. **Context Integration**  
   • Read CURRENT_CONTEXT first; extract any directly relevant facts.  
   • Treat these facts as authoritative and **do not cite** them.

2. **Retrieval Grounding (if needed)**  
   • If gaps remain, scan RETRIEVED_DOCS in ranked order.  
   • Pull only the information that fills those gaps.  
   • Cite each borrowed fact inline as **[doc_id]**.

3. **Knowledge Fallback**  
   • If unanswered aspects persist after Step 2, rely on internal knowledge.  
   • Answer confidently but avoid invented specifics.

4. **Answer Composition**  
   • Merge insights from all sources into a cohesive response.  
   • Prefer short paragraphs, bullets, or headings for readability.  
   • Maintain a neutral, informative tone unless the user requests otherwise.

5. **Citation Rules**  
   • Cite **every** external fact from RETRIEVED_DOCS with its matching [doc_id].  
   • Do **not** cite CURRENT_CONTEXT or internal knowledge.  
   • Never mention retrieval scores or quote raw snippets verbatim.

────────────────────────────────────────────────────────────
OUTPUT  
Return **only** the answer text—no markdown fences, JSON, or extra labels.  
Citations must appear inline in square brackets, e.g.:  
    Solar capacity rose 24 % in 2024 [energy_outlook_2025].

────────────────────────────────────────────────────────────
CURRENT_CONTEXT:
{context}

RETRIEVED_DOCS:
{retrieved_docs}

ORIGINAL_PROBLEM:
{original_problem}

USER_REQUEST:
{user_input}
"""

PLAN_PROMPT = """
You are a seasoned strategist and project-planning expert.

Objective  
Create a concise, actionable plan that leads directly to a complete answer to the user’s problem.

Workflow  
1. **Assess Complexity**  
   • Read the **Problem**.  
   • Decide if it is **simple** (one clear, low-risk action) or **complex** (multiple coordinated actions).  

2. **Build the Plan**  
   • **Simple** → Return a one-object JSON array:  
     {{ "step": 1, "action": <concise action>, "successMetric": <evidence problem solved> }}  

   • **Complex** → Return a 3-7-object JSON array. Each object must include:  
     {{
       "step": <number>,  
       "goal": <sub-goal bringing solution closer>,  
       "action": <specific next action>,  
       "dataRequired": [<data needed>],  
       "successMetric": <evidence step achieved>  
     }}  
   • Each step must move the solution measurably closer to fully answering the **Problem**.  
   • Use outputs from earlier steps when helpful, but only if they add clarity. 

   **Granularity Rules**  
   • **Atomicity test:** If one action hides multiple calculations or deliverables, split it into additional steps.  
     – Example red flags: “analyze,” “develop strategy,” “calculate cash flow.”  
   • Break broad finance tasks (e.g., cash-flow analysis) into their logical sub-components (e.g., operating cash flow, free cash flow, cash-conversion cycle).  
   • Keep 3-7 total steps; merge only if truly indivisible. 

3. **Formatting Rules**  
   • Output **only** the JSON array—no extra text.  
   • Use camelCase keys exactly as shown.  
   • Keep all string values ≤ 20 words.  
   • If no data are needed, use an empty list [] for **dataRequired**.

**Input Template (for the user):**  
> **Problem:** {problem}

**Output Examples**  
*Simple*  
```json
[
  {{
    "step": 1,
    "action": "Contact the vendor and request an updated invoice",
    "successMetric": "Corrected invoice received"
  }}
]
````

*Complex*

```json
[
  {{
    "step": 1,
    "goal": "Clarify scope",
    "action": "Confirm current quarterly revenue",
    "dataRequired": ["latest revenue report"],
    "successMetric": "Baseline revenue documented"
  }},
  {{
    "step": 2,
    "goal": "Project next-year revenue",
    "action": "Apply 20% quarterly growth rate",
    "dataRequired": ["baseline revenue", "growth rate"],
    "successMetric": "Projected revenue calculated"
  }},
  {{
    "step": 3,
    "goal": "Estimate operating cash flow",
    "action": "Compute OCF from projected revenue",
    "dataRequired": ["projected revenue", "operating margin"],
    "successMetric": "OCF estimated"
  }},
  {{
    "step": 4,
    "goal": "Estimate free cash flow",
    "action": "Subtract capex from OCF",
    "dataRequired": ["OCF", "planned capex"],
    "successMetric": "FCF estimated"
  }},
  {{
    "step": 5,
    "goal": "Analyze cash conversion cycle",
    "action": "Calculate CCC for next year",
    "dataRequired": ["DSO", "DIO", "DPO"],
    "successMetric": "CCC calculated"
  }},
  {{
    "step": 6,
    "goal": "Determine cash need",
    "action": "Combine FCF and CCC impacts",
    "dataRequired": ["FCF", "CCC", "current cash"],
    "successMetric": "Cash requirement finalized"
  }}
]

```
"""

'''

    # Prompt assembly
    prompt = f"""
You are Dana, an expert Dana language developer. Based on the provided summary, conversation context, and specific requirements, generate a complete multi-file training project for Georgia.

{context_section}

IMPORTANT: You MUST generate EXACTLY 6 files: main.na, workflows.na, methods.na, common.na, knowledge.na, and tools.na. Even if some files only contain comments, all 6 files must be present.

The main agent declaration must use the exact name: {agent_name} (do not invent a new name). Remember, you are Dana training Georgia.

Use the following as templates for each file. Adapt the agent/function names and details to match the agent description and requirements, but follow the structure and style shown. The rag_resource must be defined in knowledge.na, not tools.na.

---
main.na (example):
{main_na}
---
methods.na (example):
{methods_na}
---
workflows.na (example):
{workflows_na}
---
knowledge.na (example):
{knowledges_na}
---
tools.na (example):
{tools_na}
---
common.na (example):
{common_na}
---

RESPONSE FORMAT:
You MUST return a valid JSON object with the following structure:
{{
  "main.na": "content of main.na file",
  "workflows.na": "content of workflows.na file", 
  "methods.na": "content of methods.na file",
  "common.na": "content of common.na file",
  "knowledge.na": "content of knowledge.na file",
  "tools.na": "content of tools.na file"
}}

IMPORTANT: 
- Generate ONLY a valid JSON object - NO markdown code blocks, NO ```json, NO explanatory text!
- The JSON values must contain pure Dana code content for each file
- Ensure all string values are properly escaped (quotes, newlines, etc.)
- All 6 files must be present in the JSON object

Use the agent summary and conversation context to ensure the generated code matches the intended functionality and requirements.

Generate only the JSON object, no explanations or markdown formatting.
"""
    return prompt


# Missing functions that were previously imported from deleted files


def get_multi_file_agent_generation_prompt(intentions: str, current_code: str = "", has_docs_folder: bool = False) -> str:
    """
    Returns the multi-file agent generation prompt for the LLM.
    """
    rag_import_block = "from tools import rag_resource\n"
    rag_search_block = "    package.retrieval_result = str(rag_resource.query(query))"

    return f'''
You are Dana, an expert Dana language developer. Based on the user's intentions, generate a training project for Georgia that follows the modular, workflow-based pattern.

User Intentions:
{intentions}

IMPORTANT: You MUST generate EXACTLY 6 files: main.na, workflows.na, methods.na, common.na, knowledge.na, and tools.na. Even if some files only contain comments, all 6 files must be present.

Generate a multi-file Dana training project for Georgia with the following structure, following the established patterns:

1. **main.na**        - Main agent definition and orchestration (entrypoint)
2. **workflows.na**   - Workflow orchestration using pipe operators
3. **methods.na**     - Core processing methods and utilities
4. **common.na**      - Shared data structures, prompt templates, and constants (must include structs and constants)
5. **knowledge.na**  - Knowledge base/resource configurations (describe or define knowledge sources, or explain if not needed)
6. **tools.na**       - Tool/resource definitions and integrations (always define rag_resource for ./docs)

RESPONSE FORMAT:
You MUST generate ALL 6 files in this exact format with FILE_START and FILE_END markers. Do not skip any files.
IMPORTANT: Generate ONLY pure Dana code between the markers - NO markdown code blocks, NO ```python, NO ```dana, NO explanatory text!

FILE_START:main.na
from workflows import workflow
from common import RetrievalPackage

agent RetrievalExpertAgent:
    name: str = "RetrievalExpertAgent"
    description: str = "A retrieval expert agent that can answer questions about documents"

def solve(self : RetrievalExpertAgent, query: str) -> str:
    package = RetrievalPackage(query=query)
    return workflow(package)

this_agent = RetrievalExpertAgent()

FILE_END:main.na

FILE_START:workflows.na
from methods import should_use_rag
from methods import refine_query
from methods import search_document
from methods import get_answer

workflow = should_use_rag | refine_query | search_document | get_answer
FILE_END:workflows.na

FILE_START:methods.na
{rag_import_block}from common import QUERY_GENERATION_PROMPT
from common import QUERY_DECISION_PROMPT
from common import ANSWER_PROMPT
from common import RetrievalPackage

def search_document(package: RetrievalPackage) -> RetrievalPackage:
    query = package.query
    if package.refined_query != "":
        query = package.refined_query
{rag_search_block}
    return package

def refine_query(package: RetrievalPackage) -> RetrievalPackage:
    if package.should_use_rag:
        package.refined_query = reason(QUERY_GENERATION_PROMPT.format(user_input=package.query))
    return package

def should_use_rag(package: RetrievalPackage) -> RetrievalPackage:
    package.should_use_rag = reason(QUERY_DECISION_PROMPT.format(user_input=package.query))
    return package

def get_answer(package: RetrievalPackage) -> str:
    prompt = ANSWER_PROMPT.format(user_input=package.query, retrieved_docs=package.retrieval_result)
    return reason(prompt)
FILE_END:methods.na

FILE_START:common.na
QUERY_GENERATION_PROMPT = """
You are **QuerySmith**, an expert search-query engineer for a Retrieval-Augmented Generation (RAG) pipeline.

**Task**  
Given the USER_REQUEST below, craft **one** concise query string (≤ 12 tokens) that will maximize recall of the most semantically relevant documents.

**Process**  
1. **Extract Core Concepts** – identify the main entities, actions, and qualifiers.  
2. **Select High-Signal Terms** – keep nouns/verbs with the strongest discriminative power; drop stop-words and vague modifiers.  
3. **Synonym Check** – if a well-known synonym outperforms the original term in typical search engines, substitute it.  
4. **Context Packing** – arrange terms from most to least important; group multi-word entities in quotes ("like this").  
5. **Final Polish** – ensure the string is lowercase, free of punctuation except quotes, and contains **no** explanatory text.

**Output Format**  
Return **only** the final query string on a single line. No markdown, labels, or additional commentary.

---

USER_REQUEST: 
{{user_input}}
"""

QUERY_DECISION_PROMPT = """
You are **RetrievalGate**, a binary decision agent guarding a Retrieval-Augmented Generation (RAG) pipeline.

Task  
Analyze the USER_REQUEST below and decide whether external document retrieval is required to answer it accurately.

Decision Rules  
1. External-Knowledge Need – Does the request demand up-to-date facts, statistics, citations, or niche info unlikely to be in the model's parameters?  
2. Internal Sufficiency – Could the model satisfy the request with its own reasoning, creativity, or general knowledge?  
3. Explicit User Cue – If the user explicitly asks to "look up," "cite," "fetch," "search," or mentions a source/corpus, retrieval is required.  
4. Ambiguity Buffer – When uncertain, default to retrieval (erring on completeness).

Output Format  
Return **only** one lowercase Boolean literal on a single line:  
- `true`  → retrieval is needed  
- `false` → retrieval is not needed

---

USER_REQUEST: 
{{user_input}}
"""

ANSWER_PROMPT = """
You are **RAGResponder**, an expert answer-composer for a Retrieval-Augmented Generation pipeline.

────────────────────────────────────────
INPUTS
• USER_REQUEST: The user's natural-language question.  
• RETRIEVED_DOCS: *Optional* — multiple objects, each with:
    - metadata
    - content
  If no external retrieval was performed, RETRIEVED_DOCS will be empty.

────────────────────────────────────────
TASK  
Produce a single, well-structured answer that satisfies USER_REQUEST.

────────────────────────────────────────
GUIDELINES  
1. **Grounding Strategy**  
   • If RETRIEVED_DOCS is **non-empty**, read the top-scoring snippets first.  
   • Extract only the facts truly relevant to the question.  
   • Integrate those facts into your reasoning and cite them inline as **[doc_id]**.

2. **Fallback Strategy**  
   • If RETRIEVED_DOCS is **empty**, rely on your internal knowledge.  
   • Answer confidently but avoid invented specifics (no hallucinations).

3. **Citation Rules**  
   • Cite **every** external fact or quotation with its matching [doc_id].  
   • Do **not** cite when drawing solely from internal knowledge.  
   • Never reference retrieval *scores* or expose raw snippets.

4. **Answer Quality**  
   • Prioritize clarity, accuracy, and completeness.  
   • Use short paragraphs, bullets, or headings if it helps readability.  
   • Maintain a neutral, informative tone unless the user requests otherwise.

────────────────────────────────────────
OUTPUT FORMAT  
Return **only** the answer text—no markdown fences, JSON, or additional labels.
Citations must appear inline in square brackets, e.g.:
    Solar power capacity grew by 24 % in 2024 [energy_outlook_2025].

────────────────────────────────────────
USER_REQUEST: 
{{user_input}}
RETRIEVED_DOCS: 
{{retrieved_docs}}
"""

struct RetrievalPackage:
    query: str
    refined_query: str = ""
    should_use_rag: bool = False
    retrieval_result: str = "<empty>"
FILE_END:common.na

FILE_START:knowledge.na
"""Knowledge base/resource configurations.

Knowledge Description:
- Describe the knowledge sources, databases, RAG resources, and their roles in the agent.
- If no knowledge sources are needed, explain why the agent works without them.
"""

# Example knowledge resource definitions (include only if needed):
# knowledge_base = use("rag", sources=["./docs"])
# database = use("database", connection_string="...")
# api_knowledge = use("api", endpoint="...")

FILE_END:knowledge.na

FILE_START:tools.na
"""Tool/resource definitions and integrations."""

# Define rag_resource for document retrieval
rag_resource = use("rag", sources=["./docs"])

FILE_END:tools.na
'''


def generate_mock_agent_code(messages, current_code=""):
    """
    Generate mock Dana agent code based on user requirements for testing or mock mode.
    Args:
        messages: List of conversation messages
        current_code: Current Dana code to improve upon (default empty string)
    Returns:
        Mock Dana agent code as a string
    """
    # Extract requirements from messages
    all_content = ""
    for msg in messages:
        if msg.get("role") == "user":
            all_content = all_content + " " + msg.get("content", "")
    requirements_lower = all_content.lower()

    # Simple keyword-based agent generation
    if "weather" in requirements_lower:
        # Weather agents don't typically need RAG - they can use general knowledge
        return '''"""Weather information agent."""

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
    elif "email" in requirements_lower:
        # Email agents need RAG for email templates and best practices
        return '''"""Email assistant agent."""

# Agent resources for email knowledge
email_knowledge = use("rag", sources=["email_templates.md", "communication_best_practices.pdf"])

# Agent Card declaration
agent EmailAgent:
    name : str = "Email Assistant Agent"
    description : str = "Assists with email composition and communication"
    resources : list = [email_knowledge]

# Agent's problem solver
def solve(email_agent : EmailAgent, problem : str):
    return reason(f"Help with email: {{problem}}", resources=email_agent.resources)'''
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
        return '''"""Custom assistant agent."""

# Agent Card declaration
agent CustomAgent:
    name : str = "Custom Assistant Agent"
    description : str = "An agent that can help with various tasks"
    resources : list = []

# Agent's problem solver
def solve(custom_agent : CustomAgent, problem : str):
    return reason(f"Help me with: {{problem}}")'''
