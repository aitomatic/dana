"""
Agent Manager for handling all agent-related operations with consistency.
"""

import logging
import re
import shutil
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any
from dana.common.types import BaseRequest

from fastapi import HTTPException

from .agent_generator import (
    analyze_agent_capabilities,
    analyze_conversation_completeness,
    generate_agent_files_from_prompt,
)
from dana.api.core.schemas import AgentCapabilities, DanaFile, MultiFileProject


class AgentManager:
    """
    Centralized manager for all agent-related operations.

    Handles:
    - Agent creation and lifecycle management
    - Phase 1: Description refinement
    - Phase 2: Code generation
    - Knowledge file management
    - Folder and file consistency
    - Agent metadata management
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agents_dir = Path("agents")
        self.agents_dir.mkdir(exist_ok=True)

    async def create_agent_description(
        self, messages: list[dict[str, Any]], agent_id: int | None = None, existing_agent_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Phase 1: Create or update agent description based on conversation.

        Args:
            messages: Conversation messages
            agent_id: Existing agent ID (if updating)
            existing_agent_data: Existing agent data (if updating)

        Returns:
            Agent description response with metadata
        """
        self.logger.info(f"Creating agent description with {len(messages)} messages")

        # Extract agent requirements from conversation
        agent_requirements = await self._extract_agent_requirements(messages)

        # Merge with existing data if provided
        if existing_agent_data:
            agent_requirements = self._merge_agent_requirements(agent_requirements, existing_agent_data)

        # Analyze conversation completeness
        conversation_analysis = await analyze_conversation_completeness(messages)

        # Generate intelligent response
        response_message = await self._generate_intelligent_response(messages, agent_requirements, conversation_analysis)

        # Determine readiness for code generation
        ready_for_code_generation = self._is_ready_for_code_generation(agent_requirements, conversation_analysis)

        # Generate or use existing agent ID and folder
        agent_name = agent_requirements.get("name", "Custom Agent")
        folder_path = None
        if existing_agent_data and existing_agent_data.get("folder_path"):
            folder_path = existing_agent_data["folder_path"]
            agent_id = existing_agent_data.get("id", agent_id)
            # Ensure the folder exists on disk
            agent_folder = Path(folder_path)
            agent_folder.mkdir(parents=True, exist_ok=True)
        else:
            if not agent_id:
                agent_id = int(time.time() * 1000)
            agent_folder = self._create_agent_folder(agent_id, agent_name)
            folder_path = str(agent_folder)

        # Create agent metadata
        agent_metadata = {
            "id": agent_id,
            "name": agent_name,
            "description": agent_requirements.get("description", "A specialized agent for your needs"),
            "folder_path": folder_path,
            "generation_phase": "description",
            "agent_description_draft": agent_requirements,
            "generation_metadata": {
                "conversation_context": messages,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            },
        }

        # Analyze capabilities
        capabilities = await self._analyze_capabilities_for_description(messages)

        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "agent_description": agent_requirements.get("description"),
            "agent_folder": folder_path,
            "capabilities": capabilities,
            "ready_for_code_generation": ready_for_code_generation,
            "needs_more_info": conversation_analysis.get("needs_more_info", False),
            "follow_up_message": response_message if conversation_analysis.get("needs_more_info", False) else None,
            "suggested_questions": conversation_analysis.get("suggested_questions", []),
            "agent_metadata": agent_metadata,
        }

    async def generate_agent_code(self, agent_metadata: dict[str, Any], messages: list[dict[str, Any]], prompt: str = "") -> dict[str, Any]:
        """
        Phase 2: Generate agent code and store in the agent folder.

        Args:
            agent_metadata: Complete agent metadata from Phase 1
            messages: Conversation messages
            prompt: Specific prompt for code generation

        Returns:
            Code generation response with file paths
        """
        self.logger.info(f"Generating agent code for agent {agent_metadata.get('id')}")

        agent_folder = Path(agent_metadata.get("folder_path"))
        agent_name = agent_metadata.get("name")
        agent_description = agent_metadata.get("description")

        # Detect docs/knows folders
        has_docs_folder = (agent_folder / "docs").exists()
        has_knows_folder = (agent_folder / "knows").exists()

        # Generate code using the agent generator, passing folder flags in the prompt
        dana_code, syntax_error, multi_file_project = await generate_agent_files_from_prompt(
            prompt,
            messages,
            agent_metadata,
            True,  # Always multi-file
            has_docs_folder=has_docs_folder,
            has_knows_folder=has_knows_folder,
        )

        if syntax_error:
            raise HTTPException(status_code=500, detail=f"Code generation failed: {syntax_error}")

        # Store files in the agent folder
        stored_files = await self._store_multi_file_project(agent_folder, agent_name, agent_description, multi_file_project)

        # Analyze capabilities from generated code
        capabilities = await analyze_agent_capabilities(dana_code, messages, multi_file_project)

        # Create multi-file project object
        multi_file_project_obj = self._create_multi_file_project_object(multi_file_project)

        # Update agent metadata
        agent_metadata.update(
            {
                "generation_phase": "code_generated",
                "generated_code": dana_code,
                "stored_files": stored_files,
                "updated_at": datetime.now(UTC).isoformat(),
            }
        )

        return {
            "success": True,
            "dana_code": dana_code,
            "agent_name": agent_name,
            "agent_description": agent_description,
            "capabilities": capabilities,
            "auto_stored_files": stored_files,
            "multi_file_project": multi_file_project_obj,
            "agent_id": agent_metadata.get("id"),
            "agent_folder": str(agent_folder),
            "phase": "code_generated",
            "ready_for_code_generation": True,
            "agent_metadata": agent_metadata,
        }

    async def upload_knowledge_file(
        self, file_content: bytes, filename: str, agent_metadata: dict[str, Any], conversation_context: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Upload and store knowledge file for an agent.

        Args:
            file_content: File content as bytes
            filename: Name of the file
            agent_metadata: Agent metadata
            conversation_context: Current conversation context

        Returns:
            Upload response with updated capabilities
        """
        self.logger.info(f"Uploading knowledge file {filename} for agent {agent_metadata.get('id')}")
        print(f"Uploading knowledge file {filename} for agent {agent_metadata.get('id')}")
        print(f"Agent metadata: {agent_metadata}")

        agent_folder_path_str = agent_metadata.get("folder_path")
        if not agent_folder_path_str:
            raise HTTPException(status_code=400, detail="Agent metadata must include a valid 'folder_path' for knowledge upload.")
        agent_folder = Path(agent_folder_path_str)

        # Create docs folder
        docs_folder = agent_folder / "docs"
        docs_folder.mkdir(exist_ok=True)

        # Save the file
        file_path = docs_folder / filename
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Update tools.na with RAG resource
        await self._update_tools_with_rag(agent_folder)

        # Clear RAG cache to force re-indexing
        await self._clear_rag_cache(agent_folder)

        # Add upload message to conversation context
        updated_context = conversation_context + [{"role": "user", "content": f"Uploaded knowledge file: {filename}"}]

        # Regenerate agent capabilities with new knowledge
        updated_capabilities = await self._regenerate_agent_with_knowledge(updated_context, agent_metadata, agent_folder, filename)

        # Check if ready for code generation
        ready_for_code_generation = await self._check_ready_for_code_generation(updated_context, agent_metadata)

        # Update agent metadata with the correct ready_for_code_generation value
        if updated_capabilities:
            updated_capabilities["ready_for_code_generation"] = ready_for_code_generation

        # Generate response about the upload
        upload_response = await self._generate_upload_response(filename, agent_folder, updated_capabilities, updated_context)

        # Update agent metadata
        agent_metadata.update(
            {"knowledge_files": agent_metadata.get("knowledge_files", []) + [filename], "updated_at": datetime.now(UTC).isoformat()}
        )

        # Extract the capabilities in the format expected by frontend
        frontend_capabilities = None
        if updated_capabilities and isinstance(updated_capabilities, dict):
            capabilities = updated_capabilities.get("capabilities", {})
            if isinstance(capabilities, dict):
                frontend_capabilities = {
                    "summary": capabilities.get("summary", ""),
                    "knowledge": capabilities.get("knowledge", []),
                    "workflow": capabilities.get("workflow", []),
                    "tools": capabilities.get("tools", []),
                }
            else:
                # Fallback if capabilities is not in expected format
                frontend_capabilities = {
                    "summary": "Enhanced agent capabilities with document processing",
                    "knowledge": [
                        f"**Document Processing**: Process and analyze {filename}",
                        "**Knowledge Retrieval**: Access information from uploaded documents",
                    ],
                    "workflow": [
                        "**Input Reception**: Receive and process user query",
                        "**Document Analysis**: Analyze relevant documents using RAG system",
                        "**Response Generation**: Generate informed responses based on document knowledge",
                    ],
                    "tools": [
                        "**RAG System**: Retrieve and analyze document content",
                        "**Dana Reasoning Engine**: Process and reason about information",
                    ],
                }

        return {
            "success": True,
            "file_path": str(file_path),
            "message": f"File {filename} uploaded successfully",
            "updated_capabilities": frontend_capabilities,
            "generated_response": upload_response,
            "ready_for_code_generation": ready_for_code_generation,
            "agent_metadata": agent_metadata,
        }

    async def update_agent_description(self, agent_metadata: dict[str, Any], messages: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Update agent description during Phase 1.

        Args:
            agent_metadata: Current agent metadata
            messages: New conversation messages

        Returns:
            Updated agent description response
        """
        self.logger.info(f"Updating agent description for agent {agent_metadata.get('id')}")

        # Merge existing conversation with new messages
        existing_context = agent_metadata.get("generation_metadata", {}).get("conversation_context", [])
        all_messages = existing_context + messages

        # Create new description
        return await self.create_agent_description(all_messages, agent_metadata.get("id"), agent_metadata)

    def get_agent_folder(self, agent_id: int) -> Path | None:
        """
        Get agent folder by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent folder path or None if not found
        """
        for folder in self.agents_dir.iterdir():
            if folder.is_dir() and folder.name.startswith(f"agent_{agent_id}_"):
                return folder
        return None

    def _create_agent_folder(self, agent_id: int, agent_name: str) -> Path:
        """Create agent folder with consistent naming."""
        sanitized_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", agent_name.lower())
        folder_name = f"agent_{agent_id}_{sanitized_name}"
        agent_folder = self.agents_dir / folder_name
        agent_folder.mkdir(exist_ok=True)
        return agent_folder

    async def _extract_agent_requirements(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract agent requirements from conversation messages using LLM."""
        try:
            # Use LLM to intelligently extract agent requirements
            from .agent_generator import get_agent_generator

            agent_generator = await get_agent_generator()

            if agent_generator and agent_generator.llm_resource:
                # Create a prompt for extracting agent requirements
                conversation_text = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in messages])

                prompt = f"""
You are an expert at analyzing conversations and extracting agent requirements.

CONVERSATION:
{conversation_text}

TASK:
Extract the agent requirements from this conversation. Pay special attention to:
1. The agent's name (if mentioned)
2. The agent's purpose and description
3. Key capabilities the user wants
4. Knowledge domains the agent should have
5. Workflows the agent should perform

RESPONSE FORMAT (JSON):
{{
    "name": "Extracted agent name (be specific, don't use generic names like 'Custom Agent')",
    "description": "Clear description of what the agent does",
    "capabilities": ["capability1", "capability2", "capability3"],
    "knowledge_domains": ["domain1", "domain2"],
    "workflows": ["workflow1", "workflow2"]
}}

IMPORTANT:
- If the user mentions a specific name (like "Georgia", "Alex", "Helper", etc.), use that name
- If no specific name is mentioned, create a descriptive name based on the agent's purpose
- Avoid generic names like "Custom Agent" or "Assistant"
- Make the description specific and actionable
- Extract real capabilities from the conversation
"""

                # Create request for LLM
                from dana.common.types import BaseRequest

                request = BaseRequest(arguments={"prompt": prompt, "messages": [{"role": "user", "content": prompt}]})

                response = await agent_generator.llm_resource.query(request)

                if response.success:
                    # Extract the response content
                    content = response.content
                    if isinstance(content, dict):
                        if "choices" in content:
                            llm_response = content["choices"][0]["message"]["content"]
                        elif "content" in content:
                            llm_response = content["content"]
                        else:
                            llm_response = str(content)
                    else:
                        llm_response = str(content)

                    # Try to parse JSON response
                    try:
                        import json

                        # Extract JSON from the response (handle markdown code blocks)
                        if "```json" in llm_response:
                            json_start = llm_response.find("```json") + 7
                            json_end = llm_response.find("```", json_start)
                            json_str = llm_response[json_start:json_end].strip()
                        elif "```" in llm_response:
                            json_start = llm_response.find("```") + 3
                            json_end = llm_response.find("```", json_start)
                            json_str = llm_response[json_start:json_end].strip()
                        else:
                            json_str = llm_response.strip()

                        requirements = json.loads(json_str)

                        # Ensure required fields are present
                        requirements.setdefault("name", "Custom Agent")
                        requirements.setdefault("description", "A specialized agent for your needs")
                        requirements.setdefault("capabilities", [])
                        requirements.setdefault("knowledge_domains", [])
                        requirements.setdefault("workflows", [])

                        self.logger.info(f"LLM extracted requirements: {requirements}")
                        print("--------------------------------")
                        print("LLM EXTRACTED AGENT REQUIREMENTS:")
                        print(f"  Name: {requirements.get('name')}")
                        print(f"  Description: {requirements.get('description')}")
                        print(f"  Capabilities: {requirements.get('capabilities')}")
                        print("--------------------------------")
                        return requirements

                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Failed to parse LLM response as JSON: {e}")
                        self.logger.warning(f"LLM response: {llm_response}")

        except Exception as e:
            self.logger.warning(f"Failed to use LLM for requirements extraction: {e}")

        # Fallback to simple extraction based on conversation content
        all_content = ""
        for msg in messages:
            if msg.get("role") == "user":
                all_content += " " + msg.get("content", "")

        content_lower = all_content.lower()

        # Extract basic requirements
        requirements = {
            "name": "Custom Agent",
            "description": "A specialized agent for your needs",
            "capabilities": [],
            "knowledge_domains": [],
            "workflows": [],
        }

        # Simple keyword-based extraction as fallback
        if "weather" in content_lower:
            requirements["name"] = "Weather Agent"
            requirements["description"] = "Provides weather information and recommendations"
            requirements["capabilities"] = ["weather lookup", "forecasting", "recommendations"]
        elif "data" in content_lower or "analysis" in content_lower:
            requirements["name"] = "Data Analysis Agent"
            requirements["description"] = "Analyzes data and provides insights"
            requirements["capabilities"] = ["data processing", "statistical analysis", "visualization"]
        elif "document" in content_lower or "file" in content_lower:
            requirements["name"] = "Document Processing Agent"
            requirements["description"] = "Processes and analyzes documents"
            requirements["capabilities"] = ["document parsing", "text extraction", "content analysis"]
        elif "email" in content_lower:
            requirements["name"] = "Email Assistant Agent"
            requirements["description"] = "Assists with email composition and management"
            requirements["capabilities"] = ["email composition", "template management", "communication"]
        elif "help" in content_lower or "assistant" in content_lower:
            requirements["name"] = "General Assistant Agent"
            requirements["description"] = "A helpful assistant for various tasks"
            requirements["capabilities"] = ["general assistance", "task management", "information retrieval"]

        return requirements

    def _merge_agent_requirements(self, new_requirements: dict[str, Any], existing_data: dict[str, Any]) -> dict[str, Any]:
        """Merge new requirements with existing agent data."""
        existing_requirements = existing_data.get("agent_description_draft", {})

        # Merge capabilities, knowledge domains, and workflows
        existing_capabilities = existing_requirements.get("capabilities", [])
        new_capabilities = new_requirements.get("capabilities", [])
        merged_capabilities = list(set(existing_capabilities + new_capabilities))

        existing_knowledge = existing_requirements.get("knowledge_domains", [])
        new_knowledge = new_requirements.get("knowledge_domains", [])
        merged_knowledge = list(set(existing_knowledge + new_knowledge))

        existing_workflows = existing_requirements.get("workflows", [])
        new_workflows = new_requirements.get("workflows", [])
        merged_workflows = list(set(existing_workflows + new_workflows))

        # Update requirements with merged data
        new_requirements.update({"capabilities": merged_capabilities, "knowledge_domains": merged_knowledge, "workflows": merged_workflows})

        # Use existing name/description if new ones are defaults
        if new_requirements.get("name") == "Custom Agent" and existing_requirements.get("name"):
            new_requirements["name"] = existing_requirements["name"]

        if new_requirements.get("description") == "A specialized agent for your needs" and existing_requirements.get("description"):
            new_requirements["description"] = existing_requirements["description"]

        return new_requirements

    async def _generate_intelligent_response(
        self, messages: list[dict[str, Any]], agent_requirements: dict[str, Any], conversation_analysis: dict[str, Any]
    ) -> str:
        """Generate intelligent response based on conversation context."""
        # Simple response generation based on conversation analysis
        if conversation_analysis.get("needs_more_info", False):
            agent_name = agent_requirements.get("name", "Custom Agent")
            return f"I'd like to understand more about your requirements for the {agent_name}. Could you provide more specific details about what you need this agent to do?"

        return "I have enough information to proceed with agent generation."

    def _is_ready_for_code_generation(self, agent_requirements: dict[str, Any], conversation_analysis: dict[str, Any]) -> bool:
        """Check if agent is ready for code generation."""
        needs_more_info = conversation_analysis.get("needs_more_info", False)
        has_name = bool(agent_requirements.get("name") and agent_requirements.get("name") != "Custom Agent")
        has_description = bool(
            agent_requirements.get("description") and agent_requirements.get("description") != "A specialized agent for your needs"
        )
        has_capabilities = len(agent_requirements.get("capabilities", [])) > 0

        return not needs_more_info and has_name and has_description and has_capabilities

    async def _analyze_capabilities_for_description(self, messages: list[dict[str, Any]]) -> AgentCapabilities | None:
        """Analyze capabilities for Phase 1 description."""
        try:
            capabilities_data = await analyze_agent_capabilities("", messages, None)
            return AgentCapabilities(
                summary=capabilities_data.get("summary"),
                knowledge=capabilities_data.get("knowledge", []),
                workflow=capabilities_data.get("workflow", []),
                tools=capabilities_data.get("tools", []),
            )
        except Exception as e:
            self.logger.warning(f"Failed to analyze capabilities: {e}")
            return None

    async def _store_multi_file_project(
        self, agent_folder: Path, agent_name: str, agent_description: str, multi_file_project: dict[str, Any]
    ) -> list[str]:
        """Store multi-file project in agent folder."""
        stored_files = []

        for file_info in multi_file_project.get("files", []):
            filename = file_info["filename"]
            content = file_info["content"]

            file_path = agent_folder / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            stored_files.append(str(file_path))

        self.logger.info(f"Stored {len(stored_files)} files in {agent_folder}")
        return stored_files

    def _create_multi_file_project_object(self, multi_file_project: dict[str, Any]) -> MultiFileProject:
        """Create MultiFileProject object from dictionary."""
        dana_files = [
            DanaFile(
                filename=file_info["filename"],
                content=file_info["content"],
                file_type=file_info["file_type"],
                description=file_info.get("description"),
                dependencies=file_info.get("dependencies", []),
            )
            for file_info in multi_file_project["files"]
        ]

        return MultiFileProject(
            name=multi_file_project["name"],
            description=multi_file_project["description"],
            files=dana_files,
            main_file=multi_file_project["main_file"],
            structure_type=multi_file_project.get("structure_type", "complex"),
        )

    async def _update_tools_with_rag(self, agent_folder: Path):
        """Update tools.na with RAG resource declaration."""
        tools_file = agent_folder / "tools.na"
        rag_declaration = 'rag_resource = use("rag", sources=["./docs"])'

        if tools_file.exists():
            with open(tools_file, encoding="utf-8") as f:
                content = f.read()

            if rag_declaration not in content:
                content = re.sub(r"^.*rag_resource\s*=.*$", "", content, flags=re.MULTILINE)
                if not content.endswith("\n"):
                    content += "\n"
                content += rag_declaration + "\n"

                with open(tools_file, "w", encoding="utf-8") as f:
                    f.write(content)
        else:
            with open(tools_file, "w", encoding="utf-8") as f:
                f.write(rag_declaration + "\n")

    async def _clear_rag_cache(self, agent_folder: Path):
        """Clear RAG cache to force re-indexing."""
        rag_cache_dir = agent_folder / ".cache"
        if rag_cache_dir.exists() and rag_cache_dir.is_dir():
            shutil.rmtree(rag_cache_dir)
            self.logger.info(f"Cleared RAG cache at {rag_cache_dir}")

    async def _regenerate_agent_with_knowledge(
        self, conversation_context: list[dict[str, Any]], agent_metadata: dict[str, Any], agent_folder: Path, uploaded_filename: str
    ) -> dict[str, Any] | None:
        """Regenerate agent capabilities with new knowledge using LLM."""
        try:
            # Update agent metadata with new knowledge
            agent_metadata["knowledge_files"] = agent_metadata.get("knowledge_files", []) + [uploaded_filename]
            agent_metadata["updated_at"] = datetime.now(UTC).isoformat()

            # Get existing agent information
            existing_name = agent_metadata.get("name", agent_metadata.get("agent_name", "Custom Agent"))
            existing_description = agent_metadata.get(
                "description", agent_metadata.get("agent_description", "A specialized agent for your needs")
            )

            # Debug: Check if capabilities are in agent_metadata
            if "capabilities" in agent_metadata:
                print("✅ Capabilities found in agent_metadata:")
                print(f"  capabilities: {agent_metadata['capabilities']}")
            else:
                print("❌ No capabilities found in agent_metadata")
            print("--------------------------------")

            # Try to get capabilities from different possible locations
            existing_capabilities = {}
            if "capabilities" in agent_metadata:
                existing_capabilities = agent_metadata["capabilities"]
            elif "agent_description_draft" in agent_metadata:
                draft = agent_metadata["agent_description_draft"]
                if isinstance(draft, dict):
                    existing_capabilities = {
                        "summary": f"Agent capabilities from {existing_name}",
                        "knowledge": draft.get("capabilities", []),
                        "workflow": draft.get("workflows", []),
                        "tools": ["Dana Reasoning Engine"],
                    }
            elif "agent_data" in agent_metadata:
                agent_data = agent_metadata["agent_data"]
                if isinstance(agent_data, dict) and "agent_description_draft" in agent_data:
                    draft = agent_data["agent_description_draft"]
                    if isinstance(draft, dict):
                        existing_capabilities = {
                            "summary": f"Agent capabilities from {existing_name}",
                            "knowledge": draft.get("capabilities", []),
                            "workflow": draft.get("workflows", []),
                            "tools": ["Dana Reasoning Engine"],
                        }

            # Generate new summary using the same approach as /describe API
            new_summary_text = await self._generate_consistent_summary_with_knowledge(
                existing_name, existing_description, existing_capabilities, uploaded_filename, conversation_context
            )

            print("--------------------------------")
            print("SUMMARY UPDATE COMPLETE")
            print(f"  Agent: {existing_name}")
            print(f"  Summary: {new_summary_text[:100]}...")
            print("--------------------------------")

            # Update agent metadata with LLM-generated summary
            agent_metadata.update(
                {
                    "name": existing_name,
                    "agent_name": existing_name,
                    "description": existing_description,
                    "agent_description": existing_description,
                    "capabilities": {
                        "summary": new_summary_text,
                        "knowledge": existing_capabilities.get("knowledge", []) + [f"Document processing: {uploaded_filename}"],
                        "workflow": existing_capabilities.get("workflow", []) + ["Document analysis using RAG system"],
                        "tools": existing_capabilities.get("tools", []) + ["RAG System"],
                    },
                    "ready_for_code_generation": True,
                }
            )

            # Fix duplicate knowledge files
            if "knowledge_files" in agent_metadata:
                knowledge_files = agent_metadata["knowledge_files"]
                if isinstance(knowledge_files, list):
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_files = []
                    for file in knowledge_files:
                        if file not in seen:
                            seen.add(file)
                            unique_files.append(file)
                    agent_metadata["knowledge_files"] = unique_files

            return agent_metadata

        except Exception as e:
            self.logger.error(f"Error regenerating agent with knowledge: {e}")
            # Fallback to simple update
            if "capabilities" not in agent_metadata:
                agent_metadata["capabilities"] = {}
            if isinstance(agent_metadata["capabilities"], dict):
                if "knowledge" not in agent_metadata["capabilities"]:
                    agent_metadata["capabilities"]["knowledge"] = []
                agent_metadata["capabilities"]["knowledge"].append(f"Document processing: {uploaded_filename}")
            elif isinstance(agent_metadata["capabilities"], list):
                if "knowledge processing" not in agent_metadata["capabilities"]:
                    agent_metadata["capabilities"].append("knowledge processing")
            return agent_metadata

    async def _generate_consistent_summary_with_knowledge(
        self,
        existing_name: str,
        existing_description: str,
        existing_capabilities: dict[str, Any],
        uploaded_filename: str,
        conversation_context: list[dict[str, Any]],
    ) -> str:
        """Generate new agent summary that incorporates new knowledge."""
        print("--------------------------------")
        print("Generating consistent summary with knowledge")
        print("existing_name: ", existing_name)
        print("existing_description: ", existing_description)
        print("existing_capabilities: ", existing_capabilities)
        print("uploaded_filename: ", uploaded_filename)
        print("conversation_context: ", conversation_context)
        print("--------------------------------")

        try:
            # Use LLM to regenerate summary with new knowledge
            from .agent_generator import get_agent_generator

            agent_generator = await get_agent_generator()

            if agent_generator and agent_generator.llm_resource:
                # Get existing summary text
                old_summary_text = ""
                if existing_capabilities and isinstance(existing_capabilities, dict):
                    old_summary_text = existing_capabilities.get("summary", "")

                # Simple prompt focused only on regenerating the summary
                prompt = f"""
You are tasked with regenerating an agent summary to incorporate new knowledge.

**Existing Agent Summary:**
{old_summary_text}

**New Knowledge Added:**
Document: {uploaded_filename}

**Existing Agent Information:**
- Name: {existing_name}
- Description: {existing_description}

**Task:**
Generate an updated summary that incorporates the new knowledge from '{uploaded_filename}' while preserving the existing structure and information.

**Requirements:**
1. Keep the existing summary format and structure
2. Preserve all existing information
3. Add new capabilities related to the uploaded document
4. Enhance the summary to reflect the agent's ability to process and analyze the new document

**Response:**
Return ONLY the updated summary text. Do not include any JSON formatting, markdown code blocks, or additional text.
"""

                # Create request for LLM
                from dana.common.types import BaseRequest

                request = BaseRequest(arguments={"prompt": prompt, "messages": [{"role": "user", "content": prompt}]})

                response = await agent_generator.llm_resource.query(request)

                if response.success:
                    # Extract the response content
                    content = response.content
                    if isinstance(content, dict):
                        if "choices" in content:
                            llm_response = content["choices"][0]["message"]["content"]
                        elif "content" in content:
                            llm_response = content["content"]
                        else:
                            llm_response = str(content)
                    else:
                        llm_response = str(content)

                    # Clean up the response to get just the summary text
                    summary_text = llm_response.strip()

                    # Remove markdown code blocks if present
                    if summary_text.startswith("```") and summary_text.endswith("```"):
                        summary_text = summary_text[3:-3].strip()
                    elif summary_text.startswith("```json") and "```" in summary_text[7:]:
                        json_end = summary_text.find("```", 7)
                        summary_text = summary_text[7:json_end].strip()

                    print("--------------------------------")
                    print("LLM generated summary:")
                    print(f"  Summary: {summary_text[:100]}...")
                    print("--------------------------------")

                    return summary_text

            # Fallback: Return a simple enhanced summary
            enhanced_summary = (
                f"{old_summary_text}\n\nEnhanced with knowledge from {uploaded_filename} for document processing and analysis capabilities."
            )
            return enhanced_summary

        except Exception as e:
            self.logger.error(f"Error generating consistent summary: {e}")
            # Fallback: Return a simple enhanced summary
            old_summary_text = ""
            if existing_capabilities and isinstance(existing_capabilities, dict):
                old_summary_text = existing_capabilities.get("summary", "")
            enhanced_summary = (
                f"{old_summary_text}\n\nEnhanced with knowledge from {uploaded_filename} for document processing and analysis capabilities."
            )
            return enhanced_summary

    async def _generate_llm_summary_with_knowledge(
        self,
        existing_name: str,
        existing_description: str,
        existing_capabilities: dict[str, Any],
        uploaded_filename: str,
        conversation_context: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate new agent summary using LLM that combines existing info with new knowledge."""
        print("--------------------------------")
        print("Generating LLM summary with knowledge")
        print("existing_name: ", existing_name)
        print("existing_description: ", existing_description)
        print("existing_capabilities: ", existing_capabilities)
        print("uploaded_filename: ", uploaded_filename)
        print("conversation_context: ", conversation_context)
        print("--------------------------------")
        try:
            # Create a focused prompt for LLM
            prompt = f"""
You are an expert at updating agent descriptions and capabilities when new knowledge is added.

EXISTING AGENT INFORMATION:
- Name: {existing_name}
- Description: {existing_description}

EXISTING CAPABILITIES:
{self._format_existing_capabilities(existing_capabilities)}

NEW KNOWLEDGE ADDED:
- Document: {uploaded_filename}

CONVERSATION CONTEXT:
{self._format_conversation_context(conversation_context)}

TASK:
Generate an updated agent summary that combines the existing capabilities with new knowledge from '{uploaded_filename}'.

REQUIREMENTS:
1. Keep the existing agent name unless it needs to be more specific
2. Enhance the description to mention the new document and how it improves the agent's capabilities
3. Create a comprehensive capabilities summary that includes both existing and new capabilities
4. Format all capabilities in markdown style with **bold** headers
5. Generate a follow-up message explaining how to use the new knowledge
6. Suggest relevant questions users can ask about the new document

RESPONSE FORMAT (JSON):
{{
    "name": "Updated agent name",
    "description": "Enhanced description that includes the new knowledge",
    "capabilities": {{
        "summary": "Comprehensive capability summary including existing and new knowledge",
        "knowledge": [
            "**Existing Knowledge**: [List existing knowledge capabilities]",
            "**Document Processing**: Process and analyze {uploaded_filename}",
            "**Knowledge Retrieval**: Access information from uploaded documents",
            "**Content Analysis**: Extract insights and answer questions about document content"
        ],
        "workflow": [
            "**Existing Workflow**: [List existing workflow capabilities]",
            "**Document Analysis**: Analyze relevant documents using RAG system",
            "**Response Generation**: Generate informed responses based on document knowledge"
        ],
        "tools": [
            "**Existing Tools**: [List existing tools]",
            "**RAG System**: Retrieve and analyze document content",
            "**Document Processor**: Handle various document formats"
        ]
    }},
    "follow_up_message": "Guidance on how to use the new knowledge",
    "suggested_questions": [
        "What information is available in {uploaded_filename}?",
        "Can you analyze the content of {uploaded_filename}?",
        "What insights can you provide from {uploaded_filename}?"
    ],
    "ready_for_code_generation": true
}}

IMPORTANT: 
- Format all capability items in markdown style with **bold** headers
- Include both existing capabilities and new document processing capabilities
- Create a comprehensive summary that reflects the agent's enhanced capabilities
"""

            print("--------------------------------")
            print(prompt)

            print("--------------------------------")
            # Use the agent generator's LLM to generate the summary
            from .agent_generator import get_agent_generator

            agent_generator = await get_agent_generator()

            if agent_generator and agent_generator.llm_resource:
                # Create request for LLM

                request = BaseRequest(arguments={"prompt": prompt, "messages": [{"role": "user", "content": prompt}]})

                response = await agent_generator.llm_resource.query(request)

                if response.success:
                    # Extract the response content
                    content = response.content
                    if isinstance(content, dict):
                        if "choices" in content:
                            llm_response = content["choices"][0]["message"]["content"]
                        elif "content" in content:
                            llm_response = content["content"]
                        else:
                            llm_response = str(content)
                    else:
                        llm_response = str(content)

                    # Try to parse JSON response
                    try:
                        import json

                        # Extract JSON from the response (handle markdown code blocks)
                        if "```json" in llm_response:
                            json_start = llm_response.find("```json") + 7
                            json_end = llm_response.find("```", json_start)
                            json_str = llm_response[json_start:json_end].strip()
                        elif "```" in llm_response:
                            json_start = llm_response.find("```") + 3
                            json_end = llm_response.find("```", json_start)
                            json_str = llm_response[json_start:json_end].strip()
                        else:
                            json_str = llm_response.strip()

                        summary_data = json.loads(json_str)

                        # Ensure required fields are present
                        summary_data.setdefault("name", existing_name)
                        summary_data.setdefault("description", existing_description)
                        summary_data.setdefault("capabilities", existing_capabilities)
                        summary_data.setdefault("follow_up_message", "")
                        summary_data.setdefault("suggested_questions", [])
                        summary_data.setdefault("ready_for_code_generation", True)

                        return summary_data

                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse LLM JSON response: {e}")
                        self.logger.error(f"LLM response: {llm_response}")
                        print(f"Failed to parse LLM JSON response: {e}")
                        print(f"LLM response: {llm_response}")
                        # Fallback to simple enhancement
                        return self._fallback_summary_enhancement(
                            existing_name, existing_description, existing_capabilities, uploaded_filename
                        )
                else:
                    self.logger.error(f"LLM query failed: {response.error}")
                    print(f"LLM query failed: {response.error}")
                    return self._fallback_summary_enhancement(existing_name, existing_description, existing_capabilities, uploaded_filename)
            else:
                self.logger.warning("LLM resource not available, using fallback enhancement")
                print("LLM resource not available, using fallback enhancement")
                return self._fallback_summary_enhancement(existing_name, existing_description, existing_capabilities, uploaded_filename)

        except Exception as e:
            self.logger.error(f"Error generating LLM summary: {e}")
            print(f"Error generating LLM summary: {e}")
            return self._fallback_summary_enhancement(existing_name, existing_description, existing_capabilities, uploaded_filename)

    def _format_conversation_context(self, conversation_context: list[dict[str, Any]]) -> str:
        """Format conversation context for LLM prompt."""
        formatted = []
        for msg in conversation_context:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    def _format_existing_capabilities(self, existing_capabilities: dict[str, Any]) -> str:
        """Format existing capabilities for LLM prompt."""
        if not existing_capabilities:
            return "No existing capabilities found."

        formatted = []
        if isinstance(existing_capabilities, dict):
            for category, items in existing_capabilities.items():
                if category == "summary":
                    formatted.append(f"SUMMARY: {items}")
                elif isinstance(items, list) and items:
                    formatted.append(f"{category.upper()}:")
                    for item in items:
                        # Clean up the item if it's already in markdown format
                        if item.startswith("**") and ":" in item:
                            formatted.append(f"  - {item}")
                        else:
                            # Convert to markdown format if not already
                            formatted.append(f"  - **{category.title()}**: {item}")
                elif items:
                    formatted.append(f"{category.upper()}: {items}")
        elif isinstance(existing_capabilities, list):
            formatted.append("CAPABILITIES:")
            for item in existing_capabilities:
                formatted.append(f"  - {item}")
        else:
            formatted.append(f"CAPABILITIES: {existing_capabilities}")

        return "\n".join(formatted) if formatted else "No existing capabilities found."

    def _fallback_summary_enhancement(
        self, existing_name: str, existing_description: str, existing_capabilities: dict[str, Any], uploaded_filename: str
    ) -> dict[str, Any]:
        """Fallback summary enhancement when LLM is not available."""
        enhanced_description = f"{existing_description} The agent has been enhanced with knowledge from '{uploaded_filename}' to provide more comprehensive and accurate responses."

        # Merge existing capabilities with new knowledge capabilities
        enhanced_capabilities = self._merge_capabilities_with_knowledge(existing_capabilities, uploaded_filename)

        return {
            "name": existing_name,
            "description": enhanced_description,
            "capabilities": enhanced_capabilities,
            "follow_up_message": f"The agent '{existing_name}' now has access to '{uploaded_filename}'. You can ask questions about this document or request the agent to analyze its content.",
            "suggested_questions": [
                f"What information is available in {uploaded_filename}?",
                f"Can you analyze the content of {uploaded_filename}?",
                f"What insights can you provide from {uploaded_filename}?",
            ],
            "ready_for_code_generation": True,
        }

    def _merge_capabilities_with_knowledge(self, existing_capabilities: dict[str, Any], uploaded_filename: str) -> dict[str, Any]:
        """Merge existing capabilities with new knowledge capabilities."""
        # Start with existing capabilities
        merged_capabilities = existing_capabilities.copy() if isinstance(existing_capabilities, dict) else {}

        # Ensure all required fields exist
        if "summary" not in merged_capabilities:
            merged_capabilities["summary"] = "Enhanced agent capabilities"
        if "knowledge" not in merged_capabilities:
            merged_capabilities["knowledge"] = []
        if "workflow" not in merged_capabilities:
            merged_capabilities["workflow"] = []
        if "tools" not in merged_capabilities:
            merged_capabilities["tools"] = []

        # Add new knowledge capabilities
        new_knowledge = [
            f"**Document Processing**: Process and analyze {uploaded_filename}",
            "**Knowledge Retrieval**: Access information from uploaded documents",
            "**Content Analysis**: Extract insights and answer questions about document content",
        ]

        # Merge knowledge capabilities (avoid duplicates)
        existing_knowledge = merged_capabilities.get("knowledge", [])
        if isinstance(existing_knowledge, list):
            for item in new_knowledge:
                if item not in existing_knowledge:
                    existing_knowledge.append(item)
        else:
            existing_knowledge = new_knowledge
        merged_capabilities["knowledge"] = existing_knowledge

        # Add new workflow capabilities if not present
        new_workflow = [
            "**Document Analysis**: Analyze relevant documents using RAG system",
            "**Response Generation**: Generate informed responses based on document knowledge",
        ]

        existing_workflow = merged_capabilities.get("workflow", [])
        if isinstance(existing_workflow, list):
            for item in new_workflow:
                if item not in existing_workflow:
                    existing_workflow.append(item)
        else:
            existing_workflow = new_workflow
        merged_capabilities["workflow"] = existing_workflow

        # Add new tools if not present
        new_tools = ["**RAG System**: Retrieve and analyze document content", "**Document Processor**: Handle various document formats"]

        existing_tools = merged_capabilities.get("tools", [])
        if isinstance(existing_tools, list):
            for item in new_tools:
                if item not in existing_tools:
                    existing_tools.append(item)
        else:
            existing_tools = new_tools
        merged_capabilities["tools"] = existing_tools

        # Update summary
        merged_capabilities["summary"] = (
            f"This agent specializes in providing tailored assistance, now with enhanced capabilities for understanding and applying knowledge from {uploaded_filename}."
        )

        return merged_capabilities

    def _enhance_description_with_knowledge(self, existing_description: str, filename: str, requirements: dict[str, Any]) -> str:
        """Enhance existing description with new knowledge information."""
        if existing_description == "A specialized agent for your needs":
            # If it's the default description, create a more specific one
            return f"A specialized agent that can process and analyze the document '{filename}' to provide informed responses and insights."

        # Enhance existing description
        knowledge_enhancement = (
            f" The agent has been enhanced with knowledge from '{filename}' to provide more comprehensive and accurate responses."
        )

        # Avoid duplication
        if filename not in existing_description:
            return existing_description + knowledge_enhancement
        else:
            return existing_description

    def _enhance_capabilities_with_knowledge(self, existing_capabilities: Any, filename: str) -> dict[str, Any]:
        """Enhance existing capabilities with knowledge processing."""
        return self._merge_capabilities_with_knowledge(existing_capabilities, filename)

    def _generate_knowledge_follow_up(self, filename: str, requirements: dict[str, Any]) -> str:
        """Generate follow-up message about the new knowledge."""
        agent_name = requirements.get("name", "the agent")
        return f"The agent '{agent_name}' now has access to '{filename}'. You can ask questions about this document or request the agent to analyze its content. The agent will use this knowledge to provide more informed and accurate responses."

    async def _check_ready_for_code_generation(self, conversation_context: list[dict[str, Any]], agent_metadata: dict[str, Any]) -> bool:
        """Check if agent is ready for code generation after knowledge upload."""
        agent_requirements = await self._extract_agent_requirements(conversation_context)
        conversation_analysis = await analyze_conversation_completeness(conversation_context)

        has_name = bool(agent_requirements.get("name") and agent_requirements.get("name") != "Custom Agent")
        has_description = bool(
            agent_requirements.get("description") and agent_requirements.get("description") != "A specialized agent for your needs"
        )
        has_capabilities = len(agent_requirements.get("capabilities", [])) > 0
        has_knowledge = len(conversation_context) > 2

        return (
            not conversation_analysis.get("needs_more_info", True) and has_name and has_description and has_capabilities and has_knowledge
        )

    async def _generate_upload_response(
        self, filename: str, agent_folder: Path, updated_capabilities: dict[str, Any] | None, conversation_context: list[dict[str, Any]]
    ) -> str:
        """Generate response about uploaded file."""
        try:
            if updated_capabilities and isinstance(updated_capabilities, dict):
                # Generate a comprehensive response based on the updated agent capabilities
                agent_name = updated_capabilities.get("agent_name", updated_capabilities.get("name", "the agent"))
                agent_description = updated_capabilities.get("agent_description", updated_capabilities.get("description", ""))
                follow_up_message = updated_capabilities.get("follow_up_message", "")

                response_parts = [f"✅ Successfully uploaded '{filename}' to {agent_name}'s knowledge base."]

                # Add description update if it changed
                if agent_description and agent_description != "A specialized agent for your needs":
                    if "enhanced with knowledge" in agent_description or filename in agent_description:
                        response_parts.append(f"📝 Updated agent description: {agent_description}")

                # Add capabilities information
                capabilities = updated_capabilities.get("capabilities", {})
                if isinstance(capabilities, dict) and capabilities.get("knowledge"):
                    knowledge_items = capabilities["knowledge"]
                    if knowledge_items:
                        response_parts.append(f"🧠 Enhanced capabilities: {', '.join(knowledge_items)}")

                # Add follow-up guidance
                if follow_up_message:
                    response_parts.append(f"💡 {follow_up_message}")
                else:
                    response_parts.append("💡 The agent can now process and analyze this document to provide more informed responses.")

                return " ".join(response_parts)
            else:
                return f"✅ Successfully uploaded '{filename}' to the agent's knowledge base."

        except Exception as e:
            self.logger.error(f"Error generating upload response: {e}")
            return f"✅ Successfully uploaded '{filename}' to the agent's knowledge base."


# Global agent manager instance
_agent_manager = None


def get_agent_manager() -> AgentManager:
    """Get global agent manager instance."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager
