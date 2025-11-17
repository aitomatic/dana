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

from dana.studio.api.services.knowledge_pack.interview_question_handler.tools import (
    AskQuestionTool,
    AttemptCompletionTool,
)
from dana.studio.api.services.knowledge_pack.interview_question_handler.prompts import INTERVIEW_QUESTION_GENERATION_PROMPT_V2
import re

logger = logging.getLogger(__name__)


class InterviewQuestionHandler(AbstractHandler):
    """
    LLM-driven question generation handler for interview sessions.

    Flow:
    1. Use note state (provided in system context)
    2. Generate next question based on conversation and note
    3. Handle completion or meta-questions
    """

    def __init__(
        self,
        kp_id: int,
        template_path: str,
        rag_docs: RAGResourceV2 | None = None,
        llm: LLMResource | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
    ):
        self.kp_id = kp_id
        self.template_path = template_path
        self.rag_docs = rag_docs
        self.domain = domain
        self.role = role
        self.llm = llm or LLMResource()
        self.tools = {}
        self.db = None  # Database session set by API route

        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize question generation tools."""
        self.tools.update(AskQuestionTool().as_dict())
        self.tools.update(AttemptCompletionTool().as_dict())

    async def handle(
        self,
        request: IntentDetectionRequest,
        current_note_content: str,  # Always provided
        document_answer: str | None = None,  # Precomputed answer from documents
    ) -> dict[str, Any]:
        """
        Main handler - generates next question based on conversation and note.

        Args:
            request: Intent detection request with conversation history
            current_note_content: Current interview note content (read-only)
            document_answer: Optional precomputed answer from documents for comparison

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

        if len(conversation) >= 4:  # FOR NOW, ONLY USE LAST 4 MESSAGES
            conversation = conversation[-4:]

        # Track if workflow was completed
        workflow_completed = False

        # Tool loop - max 15 iterations
        for _ in range(15):
            # Determine next tool from conversation (note content injected in _determine_next_tool)
            tool_msg = await self._determine_next_tool(conversation, current_note_content, document_answer=document_answer)
            conversation.append(tool_msg)

            print("=" * 100)
            print(tool_msg.content)

            try:
                tool_name, params, thinking_content = self._parse_xml_tool_call(tool_msg.content)
                tool_result_msg = await self._execute_tool(tool_name, params, thinking_content)
                print("-" * 100)
                print(tool_result_msg.content)
            except Exception as e:
                conversation.append(MessageData(role=SenderRole.USER, content=f"Error: {e}", treat_as_tool=True))
                continue

            # Check if complete
            if isinstance(tool_msg, MessageData) and tool_msg.content.strip().lower() == "complete":
                break

            # Check if this was a completion
            if tool_name in ["attempt_completion"]:
                workflow_completed = True

            # Add result to conversation
            conversation.append(tool_result_msg)

            # Check if user input is required
            if tool_result_msg.require_user:
                return {
                    "status": "user_input_required",
                    "message": tool_result_msg.content,
                    "conversation": conversation,
                    "workflow_completed": workflow_completed,
                }

            # Check if workflow completed after tool execution
            if "attempt_completion" in tool_msg.content:
                break

        # Build final result
        result = {
            "status": "success",
            "message": conversation[-1].content if conversation else "Question generated",
            "conversation": conversation,
            "workflow_completed": workflow_completed,
        }

        # Include final response if completed
        if workflow_completed:
            try:
                # Extract final response from the last tool result
                final_response = conversation[-1].content if conversation else "Workflow completed"
                result["final_response"] = final_response
            except Exception as e:
                logger.warning(f"Failed to extract final response: {e}")

        return result

    async def _determine_next_tool(
        self,
        conversation: list[MessageData],
        current_note_content: str,
        document_answer: str | None = None,
    ) -> MessageData:
        """
        LLM decides next tool based purely on conversation history.
        Note content is injected into LLM messages but not conversation history.

        Args:
            conversation: Conversation history
            current_note_content: Current interview note content
            document_answer: Optional precomputed answer from documents for comparison

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

        # Build base system prompt
        system_prompt = INTERVIEW_QUESTION_GENERATION_PROMPT_V2.format(tools_str=tool_str, domain=self.domain, role=self.role)

        # Build messages array starting with system prompt
        messages = [{"role": "system", "content": system_prompt}]

        # Add template content as separate user message if template_path is available
        if template_content:
            template_message = (
                f"Here is the current interview template, read and understand it : <template>\n{template_content}\n</template>"
            )
            messages.append({"role": "user", "content": template_message})

        # Add note content as separate user message
        note_message = f"Here is the current interview note state (read-only): <note>\n{current_note_content}\n</note>"
        messages.append({"role": "user", "content": note_message})

        # Add document answer if provided (for comparison)
        if document_answer:
            # Extract user's last answer from conversation
            user_answer_text = None
            previous_question = None

            # Find the last user message (their answer)
            for msg in reversed(conversation):
                if msg.role == "user" and not msg.treat_as_tool:
                    user_answer_text = msg.content
                    break

            # Find the previous question (last assistant message that requires user input)
            for msg in reversed(conversation):
                if msg.role in ("assistant", "agent") and hasattr(msg, "require_user") and msg.require_user:
                    # Try to extract question from the message content
                    question_match = re.search(r"<strong>(.*?)</strong>", msg.content, re.DOTALL)
                    if question_match:
                        previous_question = question_match.group(1).strip()
                    elif "<question>" in msg.content.lower():
                        question_match = re.search(r"<question>(.*?)</question>", msg.content, re.DOTALL)
                        if question_match:
                            previous_question = question_match.group(1).strip()
                    break

            # Build comparison message
            comparison_parts = []

            if previous_question:
                comparison_parts.append(f"The previous question was: {previous_question}\n")

            comparison_parts.append(
                f"Here is what the DOCUMENTS say about this question:\n<document_answer>\n{document_answer}\n</document_answer>\n"
            )

            if user_answer_text:
                comparison_parts.append(f"Here is what the USER said in their answer:\n<user_answer>\n{user_answer_text}\n</user_answer>\n")

            comparison_parts.append(
                "\nCRITICAL COMPARISON TASK:\n"
                "Compare what the DOCUMENTS say (above) with what the USER said (from conversation).\n"
                "- If documents assume certain equipment/processes exist but user says they don't → Ask about how process works without them\n"
                "- If documents describe verification steps but user's answer doesn't mention them → Ask about the difference\n"
                "- Focus on the SPECIFIC difference between document answer and user answer\n"
                "- DO NOT compare user's answer with the original question - that's not relevant\n"
                "- If there are significant differences, ask a followup question (category: followup) that addresses the difference between what documents say and what the user said."
            )

            document_answer_message = "\n".join(comparison_parts)
            messages.append({"role": "user", "content": document_answer_message})

        # Add conversation history
        messages.extend(llm_conversation)

        llm_request = BaseRequest(
            arguments={
                "messages": messages,
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
            else:
                role = SenderRole.USER  # User will provide tool result

            message_data = MessageData(role=role, content=content, require_user=result.require_user, treat_as_tool=True)

            return message_data

        except Exception as e:
            error_msg = f"Failed to execute tool: {str(e)}"
            logger.error(error_msg)
            return MessageData(role=SenderRole.USER, content=f"Error: {error_msg}")
