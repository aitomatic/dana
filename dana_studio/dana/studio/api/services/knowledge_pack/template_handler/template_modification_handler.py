"""
Template Modification Handler for Interview Template Editing

A simplified conversational handler for reading and modifying interview templates
through natural language interactions. Focuses exclusively on template viewing
and direct text modifications without document reading or question generation.
"""

from dana.studio.api.services.intent_detection.intent_handlers.abstract_handler import AbstractHandler
from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.lang.common.types import BaseRequest
from dana.lang.common.utils.misc import Misc
from dana.studio.api.core.schemas import IntentDetectionRequest, MessageData
from dana.studio.api.core.schemas import SenderRole
from typing import Any, Literal, Awaitable, Callable
from dana.studio.api.services.knowledge_pack.template_handler.tools import (
    ViewTemplateTool,
    ReplaceInFileTool,
    AttemptCompletionTool,
    AskQuestionTool,
)
from dana.studio.api.services.knowledge_pack.template_handler.prompts import TEMPLATE_MODIFICATION_PROMPT
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TemplateModificationHandler(AbstractHandler):
    """
    Stateless template modification handler using conversation history as state.

    Flow:
    1. Each tool result is added as assistant message
    2. LLM reads full conversation to decide next action
    3. No complex state management needed
    4. Human approval happens via conversation

    Simplified to only support:
    - Viewing template sections
    - Modifying template content via search/replace
    - User interaction and clarifications
    - Workflow completion
    """

    def __init__(
        self,
        template_path: str,
        kp_id: int,
        llm: LLMResource | None = None,
        notifier: Callable[[str, str, Literal["init", "in_progress", "finish", "error"], float | None], Awaitable[None]] | None = None,
    ):
        self.template_path = template_path
        self.kp_id = kp_id
        self.llm = llm or LLMResource()
        self.notifier = notifier
        self.tools = {}
        self.db = None  # Database session set by API route
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize available tools for template modification (4 tools only)."""
        # Core workflow tools
        self.tools.update(AskQuestionTool().as_dict())
        self.tools.update(AttemptCompletionTool().as_dict())

        # Template-specific tools
        self.tools.update(ViewTemplateTool(template_path=str(self.template_path)).as_dict())
        self.tools.update(ReplaceInFileTool(template_path=str(self.template_path)).as_dict())

    async def handle(self, request: IntentDetectionRequest) -> dict[str, Any]:
        """
        Main stateless handler - runs tool loop until completion.

        Returns:
        {
            "status": "success" | "user_input_required",
            "message": "...",
            "conversation": [...],
            "template_modified": bool,
            "template_preview": str (if modified)
        }
        """
        # Initialize conversation with user request
        conversation = request.chat_history

        if len(conversation) >= 10:  # FOR NOW, ONLY USE LAST 10 MESSAGES
            conversation = conversation[-10:]

        # Check if view_template was already called
        has_view_template = any("<view_template>" in msg.content for msg in conversation)

        if not has_view_template:
            # Execute view_template tool with default parameters (view all)
            tool_msg = await self._execute_tool(tool_name="view_template", params={"section": "all"}, thinking_content="")

            # Create assistant message with tool call XML
            thinking_msg = MessageData(
                role=SenderRole.ASSISTANT,
                content="<thinking>Starting template modification. First, I need to view the current template to understand its structure and content.</thinking>\n\n<view_template>\n  <section>all</section>\n</view_template>",
                treat_as_tool=True,
            )

            # Append at the end of conversation
            conversation.append(thinking_msg)
            conversation.append(tool_msg)

        # Track if template was modified
        template_modified = False

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
                conversation.append(MessageData(role=SenderRole.USER, content=f"Error: {e}", treat_as_tool=True))
                if self.notifier and init:
                    await self.notifier(tool_name, f"Error: {e}", "error", None)
                continue

            # Check if complete
            if isinstance(tool_msg, MessageData) and tool_msg.content.strip().lower() == "complete":
                break

            # Check if this was a template modification
            if tool_name == "replace_in_template":
                template_modified = True

            # Add result to conversation
            conversation.append(tool_result_msg)

            # Check if user input is required
            if tool_result_msg.require_user:
                return {
                    "status": "user_input_required",
                    "message": tool_result_msg.content,
                    "conversation": conversation,
                    "template_modified": template_modified,
                }

            # Check if workflow completed after tool execution
            if "attempt_completion" in tool_msg.content:
                break

        # Build final result
        result = {
            "status": "success",
            "message": conversation[-1].content,
            "conversation": conversation,
            "template_modified": template_modified,
        }

        # Include template preview if modified
        if template_modified:
            try:
                result["template_preview"] = self._read_template()
            except Exception as e:
                logger.warning(f"Failed to read template preview: {e}")

        return result

    async def _determine_next_tool(self, conversation: list[MessageData]) -> MessageData:
        """
        LLM decides next tool based purely on conversation history.

        Returns MessageData with tool call XML or "complete"
        """
        # Convert conversation to string
        llm_conversation = []
        for message in conversation:
            if message.role == "agent":
                message.role = "assistant"
            llm_conversation.append({"role": message.role, "content": message.content})

        tool_str = "\n\n".join([f"{tool}" for tool in self.tools.values()])

        system_prompt = TEMPLATE_MODIFICATION_PROMPT.format(tools_str=tool_str, template_path=self.template_path)

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

        return MessageData(role=SenderRole.ASSISTANT, content=tool_call, treat_as_tool=True)

    async def _execute_tool(self, tool_name: str, params: dict, thinking_content: str) -> MessageData:
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
                return MessageData(role=SenderRole.USER, content=f"Error calling tool `{tool_name}`: {error_msg}")

            # Execute the tool
            tool = self.tools[tool_name]
            result = await tool.execute(**params)

            # Convert ToolResult to MessageData
            content = result.result
            if tool_name in ("attempt_completion", "ask_question"):
                content = f"{content}"

            if result.require_user:
                role = SenderRole.ASSISTANT  # Assistant will ask for user input
            elif tool_name == "view_template":
                role = SenderRole.ASSISTANT  # Assistant will show template content
            else:
                role = SenderRole.USER  # User will provide tool result

            message_data = MessageData(role=role, content=content, require_user=result.require_user, treat_as_tool=True)

            return message_data

        except Exception as e:
            error_msg = f"Failed to execute tool: {str(e)}"
            logger.error(error_msg)
            return MessageData(role=SenderRole.USER, content=f"Error: {error_msg}")

    def _read_template(self) -> str:
        """Read template content from file."""
        try:
            with open(self.template_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read template: {e}")
            return ""

    def _write_template(self, content: str, create_backup: bool = True) -> None:
        """Write template content to file with optional backup."""
        try:
            if create_backup and Path(self.template_path).exists():
                backup_path = f"{self.template_path}.bak"
                Path(self.template_path).copy(backup_path)
                logger.info(f"Created backup: {backup_path}")

            with open(self.template_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Template updated: {self.template_path}")
        except Exception as e:
            logger.error(f"Failed to write template: {e}")
            raise
