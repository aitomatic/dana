from dana.api.services.intent_detection.intent_handlers.abstract_handler import AbstractHandler
from dana.api.services.knowledge_pack.structuring_handler.tools import (
    AskQuestionTool,
    ExploreKnowledgeTool,
    ModifyTreeTool,
    AttemptCompletionTool,
    ProposeKnowledgeStructureTool,
    RefineKnowledgeStructureTool,
    PreviewKnowledgeTopicTool,
)
from dana.api.core.schemas_v2 import HandlerConversation, HandlerMessage, SenderRole
from dana.api.core.schemas import DomainKnowledgeTree, DomainNode
from dana.api.services.intent_detection.intent_handlers.handler_utility import knowledge_ops_utils as ko_utils
from pathlib import Path
from dana.common.utils.misc import Misc
import logging
from dana.api.services.knowledge_pack.structuring_handler.prompts import TOOL_SELECTION_PROMPT
from dana.common.types import BaseRequest
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from collections.abc import Callable, Awaitable
from typing import Literal
import os
from typing import Any

logger = logging.getLogger(__name__)


class KPQuestionGenerationOrchestrator(AbstractHandler):
    def __init__(
        self,
        domain_knowledge_path: str,
        knowledge_status_path: str | None = None,
        llm: LLMResource | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
        tasks: list[str] | None = None,
        notifier: Callable[[str, str, Literal["init", "in_progress", "finish", "error"], float | None], Awaitable[None]] | None = None,
        **kwargs,
    ):
        base_path = Path(domain_knowledge_path).parent
        self.domain_knowledge_path = domain_knowledge_path
        self.knowledge_status_path = knowledge_status_path or os.path.join(str(base_path), "knowledge_status.json")
        self.llm = llm or LLMResource()
        self.domain = domain
        self.role = role
        self.tasks = tasks or ["Analyze Information", "Provide Insights", "Answer Questions"]
        self.storage_path = os.path.join(str(base_path), "knows")
        self.document_path = os.path.join(str(base_path), "docs")
        self.notifier = notifier
        self.tree_structure = self._load_tree_structure(domain_knowledge_path)
        self.tools = {}
        self._initialize_tools()

    def _load_tree_structure(self, domain_knowledge_path):
        _path = Path(domain_knowledge_path)
        if not _path.exists():
            tree = DomainKnowledgeTree(root=DomainNode(topic=self.domain, children=[]))
            ko_utils.save_tree(tree, domain_knowledge_path)
        else:
            tree = ko_utils.load_tree(domain_knowledge_path)
        return tree

    def _reload_tree_structure(self):
        """Reload the tree structure after modifications."""
        try:
            self.tree_structure = ko_utils.load_tree(self.domain_knowledge_path)
            logger.info("Tree structure reloaded from disk")

            # Update tools with the new tree structure
            if "explore_knowledge" in self.tools:
                self.tools["explore_knowledge"].tree_structure = self.tree_structure
            if "generate_knowledge" in self.tools:
                self.tools["generate_knowledge"].tree_structure = self.tree_structure
        except Exception as e:
            logger.error(f"Failed to reload tree structure: {e}")

    def _initialize_tools(self):
        # Core workflow tools
        self.tools.update(AskQuestionTool().as_dict())  # Unified tool for questions and approvals
        self.tools.update(
            ExploreKnowledgeTool(tree_structure=self.tree_structure, knowledge_status_path=self.knowledge_status_path).as_dict()
        )

        # Structure proposal tool
        self.tools.update(
            ProposeKnowledgeStructureTool(
                llm=self.llm,
                domain=self.domain,
                role=self.role,
            ).as_dict()
        )

        # Structure refinement tool
        self.tools.update(
            RefineKnowledgeStructureTool(
                llm=self.llm,
                domain=self.domain,
                role=self.role,
            ).as_dict()
        )

        # Knowledge preview tool
        self.tools.update(
            PreviewKnowledgeTopicTool(
                llm=self.llm,
                domain=self.domain,
                role=self.role,
                tasks=self.tasks,
            ).as_dict()
        )

        # Tree management
        self.tools.update(
            ModifyTreeTool(
                tree_structure=self.tree_structure,
                domain_knowledge_path=self.domain_knowledge_path,
                storage_path=self.storage_path,
                knowledge_status_path=self.knowledge_status_path,
                domain=self.domain,
                role=self.role,
                tasks=self.tasks,
                notifier=self.notifier,
            ).as_dict()
        )

        # Quality and completion tools
        self.tools.update(AttemptCompletionTool().as_dict())

    async def handle(self, request: HandlerConversation) -> dict[str, Any]:
        """
        Main stateless handler - runs tool loop until completion.

        Mock return:
        {
            "status": "success",
            "message": "Generated 10 knowledge artifacts",
            "conversation": [...],  # Full conversation with all tool results
            "final_result": {...},
            "tree_modified": bool,  # Indicates if tree was modified
            "updated_tree": {...}  # Only included if tree was modified
        }
        """
        # Initialize conversation with user request
        conversation = request.messages  # TODO : IMPROVE MANAGING CONVERSATION HISTORY

        if len(conversation) >= 10:  # FOR NOW, ONLY USE LAST 10 MESSAGES
            conversation = conversation[-10:]

        # Track if tree was modified
        tree_modified = False

        # Tool loop - max 15 iterations
        for _ in range(15):
            # Determine next tool from conversation
            tool_msg = await self._determine_next_tool(conversation)
            print("=" * 100)
            print(tool_msg.content)
            print("=" * 100)
            conversation.append(tool_msg)
            init = False
            try:
                tool_name, params, thinking_content = self._parse_xml_tool_call(tool_msg.content)
                if self.notifier:
                    await self.notifier(tool_name, thinking_content, "init", None)
                init = True
                tool_result_msg = await self._execute_tool(tool_name, params, thinking_content)
                if self.notifier:
                    await self.notifier(tool_name, tool_result_msg.content, "finish", 1.0)
                init = False
            except Exception as e:
                conversation.append(HandlerMessage(sender=SenderRole.USER, content=f"Error: {e}"))
                if self.notifier and init:
                    await self.notifier(tool_name, f"Error: {e}", "error", None)
                continue

            # Check if complete
            if isinstance(tool_msg, HandlerMessage) and tool_msg.content.strip().lower() == "complete":
                break

            # Check if this was a tree modification
            if "modify_tree" in tool_msg.content:
                tree_modified = True

            # Add result to conversation
            conversation.append(tool_result_msg)

            # Check if user input is required
            if tool_result_msg.require_user:
                return {
                    "status": "user_input_required",
                    "message": tool_result_msg.content,
                    "conversation": conversation,
                    "final_result": None,
                    "tree_modified": tree_modified,
                    "updated_tree": self.tree_structure if tree_modified else None,
                }

            # Check if workflow completed after tool execution
            if "attempt_completion" in tool_msg.content:
                break

        # Build final result
        result = {
            "status": "success",
            "message": conversation[-1].content,
            "conversation": conversation,
            "final_result": None,
            "tree_modified": tree_modified,
        }

        # Only include updated tree if it was modified
        if tree_modified:
            result["updated_tree"] = self.tree_structure

        return result

    async def _determine_next_tool(self, conversation: list[HandlerMessage]) -> HandlerMessage:
        """
        LLM decides next tool based purely on conversation history.

        Returns HandlerMessage with tool call XML or "complete"
        """
        # Convert conversation to string
        llm_conversation = []
        for message in conversation:
            if message.sender == "agent":
                message.sender = "assistant"
            llm_conversation.append({"role": message.sender, "content": message.content})

        tool_str = "\n\n".join([f"{tool}" for tool in self.tools.values()])

        system_prompt = TOOL_SELECTION_PROMPT.format(tools_str=tool_str, domain=self.domain, role=self.role, tasks=self.tasks)

        llm_request = BaseRequest(
            arguments={
                "messages": [
                    {"role": "system", "content": system_prompt},
                ]
                + llm_conversation,
                "temperature": 0.1,
                "max_tokens": 8000,
            }
        )

        response = await self.llm.query(llm_request)
        tool_call = Misc.get_response_content(response).strip()

        return HandlerMessage(role="assistant", content=tool_call, treat_as_tool=True)

    async def _execute_tool(self, tool_name: str, params: dict, thinking_content: str) -> HandlerMessage:
        """
        Execute the tool and return the result.
        """
        try:
            # Log thinking content for debugging
            if thinking_content:
                logger.debug(f"LLM thinking: {thinking_content}")

            # Check if tool exists
            if tool_name not in self.tools:
                error_msg = f"Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"
                logger.error(error_msg)
                return HandlerMessage(role="user", content=f"Error calling tool `{tool_name}`: {error_msg}")

            # Execute the tool
            tool = self.tools[tool_name]
            result = await tool.execute(**params)

            # Convert ToolResult to HandlerMessage
            content = result.result
            if tool_name in ("attempt_completion", "ask_question"):
                content = f"{content}"
            message_data = HandlerMessage(sender=SenderRole.USER, content=content, require_user=result.require_user, treat_as_tool=True)

            # If this was a modify_tree operation, reload the tree structure
            if tool_name == "modify_tree":
                self._reload_tree_structure()

            return message_data

        except Exception as e:
            error_msg = f"Failed to execute tool: {str(e)}"
            logger.error(error_msg)
            return HandlerMessage(sender=SenderRole.USER, content=f"Error: {error_msg}")
