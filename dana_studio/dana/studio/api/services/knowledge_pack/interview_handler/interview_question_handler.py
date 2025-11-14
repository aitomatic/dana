"""
Interview Question Handler for generating next interview questions.

A specialized handler focused on generating questions based on conversation
history and current note state, with document search capabilities.
"""

from dana.studio.api.services.intent_detection.intent_handlers.abstract_handler import AbstractHandler
from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.lang.common.types import BaseRequest
from dana.lang.common.utils.misc import Misc
from dana.studio.api.core.schemas import IntentDetectionRequest, MessageData
from dana.studio.api.core.schemas import SenderRole
from dana.lang.common.sys_resource.rag.rag_resource_v2 import RAGResourceV2
from typing import Any
import logging

from dana.studio.api.services.knowledge_pack.interview_handler.tools import (
    ViewNoteTool,
    AskQuestionTool,
    DocumentSearchTool,
    AttemptCompletionTool,
)
from dana.studio.api.services.knowledge_pack.interview_handler.prompts import INTERVIEW_QUESTION_GENERATION_PROMPT

logger = logging.getLogger(__name__)


class InterviewQuestionHandler(AbstractHandler):
    """
    LLM-driven question generation handler for interview sessions.

    Flow:
    1. Verify note state (using provided note content)
    2. Search documents for context (if needed)
    3. Generate next question based on conversation and note
    4. Handle completion or meta-questions
    """

    def __init__(
        self,
        session_dir: str,
        template_path: str,
        rag_resource: RAGResourceV2,
        llm: LLMResource | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
    ):
        self.session_dir = session_dir
        self.note_path = f"{session_dir}/interview_notes.md"
        self.template_path = template_path
        self.rag_resource = rag_resource
        self.domain = domain
        self.role = role
        self.llm = llm or LLMResource()
        self.tools = {}

        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize question generation tools."""
        self.tools.update(ViewNoteTool(self.note_path).as_dict())
        self.tools.update(AskQuestionTool().as_dict())
        self.tools.update(DocumentSearchTool(self.rag_resource).as_dict())
        self.tools.update(AttemptCompletionTool().as_dict())

    async def handle(
        self,
        request: IntentDetectionRequest,
        current_note_content: str,  # Always provided
    ) -> dict[str, Any]:
        """
        Main handler - generates next question based on conversation and note.

        Args:
            request: Intent detection request with conversation history
            current_note_content: Current interview note content (read-only)

        Returns:
        {
            "status": "user_input_required" | "success",
            "message": str,  # Question or completion message
            "conversation": [...],
            "workflow_completed": bool
        }
        """
        # Initialize conversation with user request
        conversation = request.chat_history

        if len(conversation) >= 4:  # FOR NOW, ONLY USE LAST 10 MESSAGES
            conversation = conversation[-4:]

        # Track if workflow was completed
        workflow_completed = False

        # Add current note content to conversation context for LLM
        # This allows the LLM to use note state without reading file
        note_context_msg = MessageData(
            role=SenderRole.USER,
            content=f"[Current Interview Note State]\n{current_note_content}",
            treat_as_tool=True,
        )
        # Insert note context at the beginning of conversation for context
        conversation_with_note = [note_context_msg] + conversation

        # Tool loop - max 15 iterations
        for _ in range(15):
            # Determine next tool from conversation (with note context)
            tool_msg = await self._determine_next_tool(conversation_with_note)
            conversation_with_note.append(tool_msg)

            print("=" * 100)
            print(tool_msg.content)

            try:
                tool_name, params, thinking_content = self._parse_xml_tool_call(tool_msg.content)
                tool_result_msg = await self._execute_tool(tool_name, params, thinking_content, conversation_with_note)
                print("-" * 100)
                print(tool_result_msg.content)
            except Exception as e:
                conversation_with_note.append(MessageData(role=SenderRole.USER, content=f"Error: {e}", treat_as_tool=True))
                continue

            # Check if complete
            if isinstance(tool_msg, MessageData) and tool_msg.content.strip().lower() == "complete":
                break

            # Check if this was a completion
            if tool_name in ["attempt_completion"]:
                workflow_completed = True

            # Add result to conversation
            conversation_with_note.append(tool_result_msg)

            # Check if user input is required
            if tool_result_msg.require_user:
                # Remove note context message from final conversation
                final_conversation = [msg for msg in conversation_with_note if msg != note_context_msg]
                return {
                    "status": "user_input_required",
                    "message": tool_result_msg.content,
                    "conversation": final_conversation,
                    "workflow_completed": workflow_completed,
                }

            # Check if workflow completed after tool execution
            if "attempt_completion" in tool_msg.content:
                break

        # Remove note context message from final conversation
        final_conversation = [msg for msg in conversation_with_note if msg != note_context_msg]

        # Build final result
        result = {
            "status": "success",
            "message": final_conversation[-1].content if final_conversation else "Question generated",
            "conversation": final_conversation,
            "workflow_completed": workflow_completed,
        }

        # Include final response if completed
        if workflow_completed:
            try:
                # Extract final response from the last tool result
                final_response = final_conversation[-1].content if final_conversation else "Workflow completed"
                result["final_response"] = final_response
            except Exception as e:
                logger.warning(f"Failed to extract final response: {e}")

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

        # Read template content for system prompt
        template_content = ""
        try:
            with open(self.template_path, encoding="utf-8") as f:
                template_content = f.read()
        except Exception as e:
            logger.warning(f"Could not read template content: {e}")

        system_prompt = INTERVIEW_QUESTION_GENERATION_PROMPT.format(
            tools_str=tool_str, domain=self.domain, role=self.role, note_path=self.note_path, template_content=template_content
        )

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

    async def _execute_tool(self, tool_name: str, params: dict, thinking_content: str, conversation: list) -> MessageData:
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
            else:
                role = SenderRole.USER  # User will provide tool result

            message_data = MessageData(role=role, content=content, require_user=result.require_user, treat_as_tool=True)

            return message_data

        except Exception as e:
            error_msg = f"Failed to execute tool: {str(e)}"
            logger.error(error_msg)
            return MessageData(role=SenderRole.USER, content=f"Error: {error_msg}")
