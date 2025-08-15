"""
Agent Service Module

This module provides business logic for agent generation, management, and capabilities analysis.
Consolidates functionality from server/agent_generator.py and domains/agents/generator/service.py.
"""

import logging
import os
from typing import Any

from dana.api.services.code_handler import CodeHandler
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.common.types import BaseRequest

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service for agent generation and management.
    Provides business logic for creating, analyzing, and managing Dana agents.
    """

    def __init__(self, llm_config: dict[str, Any] | None = None):
        """
        Initialize the agent service.

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
            logger.info("Agent Service initialized successfully")
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
        conversation_analysis = await self.analyze_conversation_completeness(messages)

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

    async def generate_agent_files_from_prompt(
        self, prompt: str, messages: list[dict[str, Any]], agent_summary: dict[str, Any], multi_file: bool = False
    ) -> tuple[str, str | None, dict[str, Any] | None]:
        """
        Generate Dana agent files from a specific prompt, conversation messages, and agent summary.

        This function is designed for Phase 2 of the agent generation flow.

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

            # Check if LLM resource is available
            if self.llm_resource is None:
                logger.warning("LLMResource is not available, using fallback template")
                return CodeHandler.get_fallback_template(), None, None

            # Check if LLM is properly initialized
            if not hasattr(self.llm_resource, "_is_available") or not self.llm_resource._is_available:
                logger.warning("LLMResource is not available, using fallback template")
                return CodeHandler.get_fallback_template(), None, None

            # Create enhanced prompt with context
            enhanced_prompt = self._create_phase_2_prompt(prompt, messages, agent_summary, multi_file)
            logger.debug(f"Enhanced Phase 2 prompt: {enhanced_prompt[:200]}...")

            # Generate code using LLM
            request = BaseRequest(arguments={"prompt": enhanced_prompt, "messages": [{"role": "user", "content": enhanced_prompt}]})
            logger.info("Sending Phase 2 request to LLM...")

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

                logger.info(f"Generated Phase 2 code length: {len(generated_code)}")

                # Handle multi-file response (always the case)
                logger.info("Parsing multi-file response...")
                multi_file_project = CodeHandler.parse_multi_file_response(generated_code)

                # Extract main file content for backward compatibility
                main_file_content = ""
                for file_info in multi_file_project["files"]:
                    if file_info["filename"] == multi_file_project["main_file"]:
                        main_file_content = file_info["content"]
                        break

                if main_file_content:
                    logger.info(f"Returning multi-file project with {len(multi_file_project['files'])} files")
                    return main_file_content, None, multi_file_project
                else:
                    logger.warning("No main file found in multi-file response")
                    return CodeHandler.get_fallback_template(), None, None
            else:
                logger.error(f"LLM generation failed for Phase 2: {response.error}")
                return CodeHandler.get_fallback_template(), None, None

        except Exception as e:
            logger.error(f"Error generating Phase 2 agent code: {e}")
            return CodeHandler.get_fallback_template(), str(e), None

    async def analyze_agent_capabilities(
        self, dana_code: str, messages: list[dict[str, Any]], multi_file_project: dict[str, Any] = None
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
            conversation_text = "\\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in messages])

            # For multi-file projects, get additional context from all files
            all_code_content = dana_code
            if multi_file_project and multi_file_project.get("files"):
                # Combine all file contents for comprehensive analysis
                all_files_content = []
                for file_info in multi_file_project["files"]:
                    all_files_content.append(f"# File: {file_info['filename']}\\n{file_info['content']}")
                all_code_content = "\\n\\n".join(all_files_content)

            # Try to use LLM to analyze the agent capabilities
            try:
                # Check if LLM is available before proceeding
                if not hasattr(self.llm_resource, "_is_available") or not self.llm_resource._is_available:
                    logger.warning("LLM resource is not available, falling back to manual analysis")
                    raise Exception("LLM not available")

                # Create analysis prompt
                analysis_prompt = self._create_capabilities_analysis_prompt(conversation_text, all_code_content)

                # Create a request for the LLM
                request = BaseRequest(arguments={"prompt": analysis_prompt, "messages": [{"role": "user", "content": analysis_prompt}]})

                result = await self.llm_resource.query(request)

                if result and result.success:
                    # Extract content from response
                    markdown_summary = self._extract_response_content(result)

                    if markdown_summary:
                        logger.info("Successfully generated agent capabilities summary using LLM")
                        # Extract basic structured data for backward compatibility
                        capabilities = {
                            "summary": markdown_summary,
                            "knowledge": self._extract_knowledge_domains_from_code(all_code_content, conversation_text),
                            "workflow": self._extract_workflow_steps_from_code(all_code_content, conversation_text),
                            "tools": self._extract_agent_tools_from_code(all_code_content),
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
                    "summary": self._extract_summary_from_code_and_conversation(dana_code, conversation_text),
                    "knowledge": self._extract_knowledge_domains_from_code(all_code_content, conversation_text),
                    "workflow": self._extract_workflow_steps_from_code(all_code_content, conversation_text),
                    "tools": self._extract_agent_tools_from_code(all_code_content),
                }
                return capabilities

        except Exception as e:
            logger.error(f"Error analyzing agent capabilities: {e}")
            return {"summary": "Unable to analyze agent capabilities", "knowledge": [], "workflow": [], "tools": []}

    async def analyze_conversation_completeness(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
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

    async def cleanup(self):
        """Clean up resources."""
        if self.llm_resource:
            await self.llm_resource.cleanup()
        logger.info("Agent Service cleaned up")

    # Private helper methods
    async def _extract_user_intentions(self, messages: list[dict[str, Any]], current_code: str = "") -> str:
        """Extract user intentions from conversation messages using LLM."""
        try:
            conversation_text = "\\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in messages])

            if current_code:
                intention_prompt = f"""
Analyze the following conversation and the current Dana agent code to extract the user's intentions for improving or modifying the agent.

Current Dana Agent Code:
{current_code}

Conversation:
{conversation_text}

Extract and summarize the user's intentions in a clear, concise way that can be used to improve the existing Dana agent code.
"""
            else:
                intention_prompt = f"""
Analyze the following conversation and extract the user's intentions for creating a new Dana agent.

Conversation:
{conversation_text}

Extract and summarize the user's intentions in a clear, concise way that can be used to generate appropriate Dana agent code.
"""

            request = BaseRequest(arguments={"messages": [{"role": "user", "content": intention_prompt}]})
            response = await self.llm_resource.query(request)

            if response.success:
                intention = response.content.get("choices", "")[0].get("message", {}).get("content", "")
                if not intention:
                    return self._extract_requirements(messages)
                return intention
            else:
                return self._extract_requirements(messages)

        except Exception as e:
            logger.error(f"Error extracting user intentions: {e}")
            return self._extract_requirements(messages)

    def _extract_requirements(self, messages: list[dict[str, Any]]) -> str:
        """Fallback method to extract user requirements from conversation messages."""
        requirements = []
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            if role == "user" and content:
                requirements.append(content)
        return "\\n".join(requirements)

    def _create_generation_prompt(self, intentions: str, current_code: str = "", multi_file: bool = False) -> str:
        """Create a prompt for the LLM to generate Dana agent code."""
        if multi_file:
            return get_multi_file_agent_generation_prompt(intentions, current_code)

        # Single file generation logic here
        if current_code:
            return f"""
You are an expert Dana language developer. Based on the user's intentions and the existing Dana agent code, improve or modify the agent to better meet their needs.

User Intentions:
{intentions}

Current Dana Agent Code:
{current_code}

Generate improved Dana code that better matches the user's intentions.
"""
        else:
            return f"""
You are an expert Dana language developer. Based on the following user intentions, generate a simple and focused Dana agent code.

User Intentions:
{intentions}

Generate a simple Dana agent that meets the user's requirements.
"""

    def _create_phase_2_prompt(self, prompt: str, messages: list[dict[str, Any]], agent_summary: dict[str, Any], multi_file: bool) -> str:
        """Create an enhanced prompt for Phase 2 agent generation."""
        # Implementation from the original file
        conversation_text = "\\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" for msg in messages])

        agent_name = agent_summary.get("name", "Custom Agent")
        agent_description = agent_summary.get("description", "A specialized agent for your needs")

        enhanced_prompt = f"""
You are Dana, an expert Dana language developer. Generate a complete multi-file training project for Georgia.

AGENT SUMMARY:
- Name: {agent_name}
- Description: {agent_description}

CONVERSATION CONTEXT:
{conversation_text}

SPECIFIC REQUIREMENTS:
{prompt}

Generate a complete multi-file Dana agent with all required files.
"""
        return enhanced_prompt

    def _create_capabilities_analysis_prompt(self, conversation_text: str, all_code_content: str) -> str:
        """Create a prompt for analyzing agent capabilities."""
        return f"""
Analyze the following Dana agent code and conversation context to generate a focused, accurate summary.

**Conversation Context:**
{conversation_text}

**Dana Agent Code:**
{all_code_content}

Generate a brief, focused markdown summary of the agent's actual capabilities.
"""

    def _extract_response_content(self, result) -> str:
        """Extract content from LLM response."""
        if hasattr(result, "content") and result.content:
            if isinstance(result.content, dict):
                if "choices" in result.content:
                    return result.content["choices"][0]["message"]["content"]
                elif "response" in result.content:
                    return result.content["response"]
                elif "content" in result.content:
                    return result.content["content"]
            elif isinstance(result.content, str):
                return result.content
        return ""

    def _extract_summary_from_code_and_conversation(self, dana_code: str, conversation_text: str) -> str:
        """Extract a summary from code and conversation."""
        # Simplified version of the original method
        lines = dana_code.split("\\n")
        agent_name = None
        agent_description = None

        for line in lines:
            if line.strip().startswith("agent ") and line.strip().endswith(":"):
                agent_name = line.strip().replace("agent ", "").replace(":", "").strip()
            elif "description : str =" in line:
                agent_description = line.split("=")[1].strip().strip('"')
                break

        summary = f"# {agent_name or 'Dana Agent'}\\n\\n"
        if agent_description:
            summary += f"## Overview\\n{agent_description}\\n\\n"
        else:
            summary += "## Overview\\nA specialized Dana agent.\\n\\n"

        return summary

    def _extract_knowledge_domains_from_code(self, dana_code: str, conversation_text: str) -> list[str]:
        """Extract knowledge domains from code."""
        domains = []
        if 'use("rag"' in dana_code:
            domains.append("Document-based knowledge retrieval")
        return domains

    def _extract_workflow_steps_from_code(self, dana_code: str, conversation_text: str) -> list[str]:
        """Extract workflow steps from code."""
        workflow = []
        if "workflow =" in dana_code:
            workflow.append("Input Processing")
            workflow.append("Pipeline Processing")
            workflow.append("Output Delivery")
        return workflow

    def _extract_agent_tools_from_code(self, dana_code: str) -> list[str]:
        """Extract tools from code."""
        tools = ["Dana Reasoning Engine"]
        if 'use("rag"' in dana_code:
            tools.append("RAG System")
        return tools


# Global service instance
_agent_service: AgentService | None = None


async def get_agent_service() -> AgentService:
    """Get or create the global agent service instance."""
    global _agent_service

    if _agent_service is None:
        _agent_service = AgentService()
        success = await _agent_service.initialize()
        if not success:
            logger.warning("Failed to initialize agent service, will use fallback templates")

    return _agent_service


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
