"""
Agent Manager for handling all agent-related operations with consistency.
"""

import json
import logging
import os
import re
import shutil
import time
import uuid
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from .agent_generator import (
    analyze_agent_capabilities,
    analyze_conversation_completeness,
    generate_agent_files_from_prompt,
)
from .schemas import AgentCapabilities, DanaFile, MultiFileProject


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
        self,
        messages: List[Dict[str, Any]],
        agent_id: Optional[int] = None,
        existing_agent_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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
            agent_requirements = self._merge_agent_requirements(
                agent_requirements, existing_agent_data
            )
        
        # Analyze conversation completeness
        conversation_analysis = await analyze_conversation_completeness(messages)
        
        # Generate intelligent response
        response_message = await self._generate_intelligent_response(
            messages, agent_requirements, conversation_analysis
        )
        
        # Determine readiness for code generation
        ready_for_code_generation = self._is_ready_for_code_generation(
            agent_requirements, conversation_analysis
        )
        
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
                "updated_at": datetime.now(UTC).isoformat()
            }
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
            "agent_metadata": agent_metadata
        }
    
    async def generate_agent_code(
        self,
        agent_metadata: Dict[str, Any],
        messages: List[Dict[str, Any]],
        prompt: str = ""
    ) -> Dict[str, Any]:
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
        
        # Generate code using the agent generator
        dana_code, syntax_error, multi_file_project = await generate_agent_files_from_prompt(
            prompt, messages, agent_metadata, True  # Always multi-file
        )
        
        if syntax_error:
            raise HTTPException(status_code=500, detail=f"Code generation failed: {syntax_error}")
        
        # Store files in the agent folder
        stored_files = await self._store_multi_file_project(
            agent_folder, agent_name, agent_description, multi_file_project
        )
        
        # Analyze capabilities from generated code
        capabilities = await analyze_agent_capabilities(
            dana_code, messages, multi_file_project
        )
        
        # Create multi-file project object
        multi_file_project_obj = self._create_multi_file_project_object(multi_file_project)
        
        # Update agent metadata
        agent_metadata.update({
            "generation_phase": "code_generated",
            "generated_code": dana_code,
            "stored_files": stored_files,
            "updated_at": datetime.now(UTC).isoformat()
        })
        
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
            "agent_metadata": agent_metadata
        }
    
    async def upload_knowledge_file(
        self,
        file_content: bytes,
        filename: str,
        agent_metadata: Dict[str, Any],
        conversation_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
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
            raise HTTPException(
                status_code=400,
                detail="Agent metadata must include a valid 'folder_path' for knowledge upload."
            )
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
        updated_context = conversation_context + [{
            "role": "user",
            "content": f"Uploaded knowledge file: {filename}"
        }]
        
        # Regenerate agent capabilities with new knowledge
        updated_capabilities = await self._regenerate_agent_with_knowledge(
            updated_context, agent_metadata, agent_folder, filename
        )
        
        # Check if ready for code generation
        ready_for_code_generation = await self._check_ready_for_code_generation(
            updated_context, agent_metadata
        )
        
        # Generate response about the upload
        upload_response = await self._generate_upload_response(
            filename, agent_folder, updated_capabilities, updated_context
        )
        
        # Update agent metadata
        agent_metadata.update({
            "knowledge_files": agent_metadata.get("knowledge_files", []) + [filename],
            "updated_at": datetime.now(UTC).isoformat()
        })
        
        return {
            "success": True,
            "file_path": str(file_path),
            "message": f"File {filename} uploaded successfully",
            "updated_capabilities": updated_capabilities,
            "generated_response": upload_response,
            "ready_for_code_generation": ready_for_code_generation,
            "agent_metadata": agent_metadata
        }
    
    async def update_agent_description(
        self,
        agent_metadata: Dict[str, Any],
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
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
        return await self.create_agent_description(
            all_messages, 
            agent_metadata.get("id"), 
            agent_metadata
        )
    
    def get_agent_folder(self, agent_id: int) -> Optional[Path]:
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
    
    async def _extract_agent_requirements(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract agent requirements from conversation messages."""
        # Import here to avoid circular imports
        from .routers.api import _extract_agent_requirements
        return await _extract_agent_requirements(messages)
    
    def _merge_agent_requirements(
        self, 
        new_requirements: Dict[str, Any], 
        existing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
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
        new_requirements.update({
            "capabilities": merged_capabilities,
            "knowledge_domains": merged_knowledge,
            "workflows": merged_workflows
        })
        
        # Use existing name/description if new ones are defaults
        if new_requirements.get("name") == "Custom Agent" and existing_requirements.get("name"):
            new_requirements["name"] = existing_requirements["name"]
        
        if new_requirements.get("description") == "A specialized agent for your needs" and existing_requirements.get("description"):
            new_requirements["description"] = existing_requirements["description"]
        
        return new_requirements
    
    async def _generate_intelligent_response(
        self, 
        messages: List[Dict[str, Any]], 
        agent_requirements: Dict[str, Any], 
        conversation_analysis: Dict[str, Any]
    ) -> str:
        """Generate intelligent response based on conversation context."""
        # Import here to avoid circular imports
        from .routers.api import _generate_intelligent_response
        return await _generate_intelligent_response(messages, agent_requirements, conversation_analysis)
    
    def _is_ready_for_code_generation(
        self, 
        agent_requirements: Dict[str, Any], 
        conversation_analysis: Dict[str, Any]
    ) -> bool:
        """Check if agent is ready for code generation."""
        needs_more_info = conversation_analysis.get("needs_more_info", False)
        has_name = bool(agent_requirements.get("name") and agent_requirements.get("name") != "Custom Agent")
        has_description = bool(agent_requirements.get("description") and agent_requirements.get("description") != "A specialized agent for your needs")
        has_capabilities = len(agent_requirements.get("capabilities", [])) > 0
        
        return not needs_more_info and has_name and has_description and has_capabilities
    
    async def _analyze_capabilities_for_description(self, messages: List[Dict[str, Any]]) -> Optional[AgentCapabilities]:
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
        self,
        agent_folder: Path,
        agent_name: str,
        agent_description: str,
        multi_file_project: Dict[str, Any]
    ) -> List[str]:
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
    
    def _create_multi_file_project_object(self, multi_file_project: Dict[str, Any]) -> MultiFileProject:
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
            with open(tools_file, "r", encoding="utf-8") as f:
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
        self,
        conversation_context: List[Dict[str, Any]],
        agent_metadata: Dict[str, Any],
        agent_folder: Path,
        uploaded_filename: str
    ) -> Optional[Dict[str, Any]]:
        """Regenerate agent capabilities with new knowledge."""
        # Import here to avoid circular imports
        from .routers.api import _regenerate_agent_with_knowledge
        return await _regenerate_agent_with_knowledge(
            conversation_context, agent_metadata, agent_folder, uploaded_filename
        )
    
    async def _check_ready_for_code_generation(
        self,
        conversation_context: List[Dict[str, Any]],
        agent_metadata: Dict[str, Any]
    ) -> bool:
        """Check if agent is ready for code generation after knowledge upload."""
        agent_requirements = await self._extract_agent_requirements(conversation_context)
        conversation_analysis = await analyze_conversation_completeness(conversation_context)
        
        has_name = bool(agent_requirements.get("name") and agent_requirements.get("name") != "Custom Agent")
        has_description = bool(agent_requirements.get("description") and agent_requirements.get("description") != "A specialized agent for your needs")
        has_capabilities = len(agent_requirements.get("capabilities", [])) > 0
        has_knowledge = len(conversation_context) > 2
        
        return (
            not conversation_analysis.get("needs_more_info", True) and
            has_name and
            has_description and
            has_capabilities and
            has_knowledge
        )
    
    async def _generate_upload_response(
        self,
        filename: str,
        agent_folder: Path,
        updated_capabilities: Optional[Dict[str, Any]],
        conversation_context: List[Dict[str, Any]]
    ) -> str:
        """Generate response about uploaded file."""
        # Import here to avoid circular imports
        from .routers.api import _generate_upload_response
        return await _generate_upload_response(filename, agent_folder, updated_capabilities, conversation_context)


# Global agent manager instance
_agent_manager = None


def get_agent_manager() -> AgentManager:
    """Get global agent manager instance."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager 