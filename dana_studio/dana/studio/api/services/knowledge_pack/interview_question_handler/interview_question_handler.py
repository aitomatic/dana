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

from dana.studio.api.services.knowledge_pack.interview_question_handler.tools import (
    AskQuestionTool,
    AttemptCompletionTool,
)
from dana.studio.api.services.knowledge_pack.interview_question_handler.prompts import INTERVIEW_QUESTION_GENERATION_PROMPT_V2
from dana.studio.api.services.context_auto_compact import ContextAutoCompactor, inject_compacted_context_to_content
import re

from dana.studio.api.core.logger import log as logger


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
        max_followups: int = 2,
        followup_count: int = 0,
        user_preference: str = "",
    ):
        self.kp_id = kp_id
        self.template_path = template_path
        self.rag_docs = rag_docs
        self.domain = domain
        self.role = role
        self.llm = llm or LLMResource()
        self.tools = {}
        self.db = None  # Database session set by API route

        # Follow-up limiter settings
        self.max_followups = max_followups
        self.followup_count = followup_count
        self.user_preference_guidance = user_preference

        # Context auto-compaction for long conversations
        self.context_compactor = ContextAutoCompactor(llm=self.llm)

        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize question generation tools."""
        self.tools.update(AskQuestionTool().as_dict())
        self.tools.update(AttemptCompletionTool().as_dict())

    def _build_settings_context(self) -> str:
        """
        Build settings context to inject into LLM prompt.

        Includes follow-up limit status and expert guidance.

        Returns:
            Formatted settings context string
        """
        parts = []

        # Follow-up limit status with decision guidance
        remaining = self.max_followups - self.followup_count
        if remaining <= 0:
            parts.append(
                f"⚠️ FOLLOW-UP LIMIT REACHED ({self.followup_count}/{self.max_followups}). "
                "You MUST transition to the next interview question now.\n"
                "Reflect on the conversation: Did you gather sufficient insight from the user's answers? "
                "If yes, summarize the key takeaways. If important gaps remain due to the limit, briefly note them."
            )
        elif remaining == 1:
            parts.append(
                f"⚠️ LAST FOLLOW-UP AVAILABLE ({self.followup_count}/{self.max_followups}).\n"
                "Decide: Have you gathered enough insight to move on, or is there a critical gap worth clarifying?\n"
                "- If sufficient: Transition to the next interview question (no follow-up needed).\n"
                "- If critical gap exists: Ask ONE targeted follow-up about the most important ambiguity."
            )
        else:
            parts.append(
                f"Follow-up status: {self.followup_count}/{self.max_followups} used.\n"
                "Decide based on the user's answer: Is more clarification needed, or do you have enough insight to proceed?"
            )

        # Append expert guidance if provided
        if self.user_preference_guidance:
            parts.append(f"\n--- User Preference Guidance ---\n{self.user_preference_guidance}")

        settings_context = "\n".join(parts)
        return f"<system-reminder>\n{settings_context}\n</system-reminder>"

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

        # Apply intelligent context compaction instead of hard truncation
        compaction_result = await self.context_compactor.compact_if_needed(
            conversation=conversation,
            model=getattr(self.llm, "model", None),
        )
        conversation = compaction_result.compacted_conversation

        if compaction_result.summary_created:
            logger.info(
                f"Interview conversation compacted: {compaction_result.messages_compacted} messages summarized, "
                f"{compaction_result.messages_preserved} preserved"
            )

        # Track if workflow was completed
        workflow_completed = False

        # Tool loop - max 15 iterations
        for _ in range(15):
            # Determine next tool from conversation (note content injected in _determine_next_tool)
            tool_msg = await self._determine_next_tool(conversation, current_note_content, document_answer=document_answer)
            conversation.append(tool_msg)

            logger.debug("=" * 100)
            logger.debug(tool_msg.content)

            try:
                tool_name, params, thinking_content = self._parse_xml_tool_call(tool_msg.content)
                tool_result_msg = await self._execute_tool(tool_name, params, thinking_content)
                logger.debug("-" * 100)
                logger.debug(tool_result_msg.content)
            except Exception as e:
                conversation.append(MessageData(role=SenderRole.USER, content=f"Error: {e}", treat_as_tool=True))
                continue

            logger.debug("-" * 100)
            logger.debug(tool_result_msg.content)
            logger.debug("-" * 100)

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

    def _build_interview_guidance(self, document_answer: str, conversation: list[MessageData]) -> str:
        """
        Build interview guidance prompt with document answer and handling instructions.

        Args:
            document_answer: Precomputed answer from documents
            conversation: Conversation history

        Returns:
            Formatted guidance prompt string
        """
        # Extract the original question from conversation
        previous_question = None
        for msg in reversed(conversation):
            if msg.role in ("assistant", "agent") and hasattr(msg, "require_user") and msg.require_user:
                question_match = re.search(r"<strong>(.*?)</strong>", msg.content, re.DOTALL)
                if question_match:
                    previous_question = question_match.group(1).strip()
                elif "<question>" in msg.content.lower():
                    question_match = re.search(r"<question>(.*?)</question>", msg.content, re.DOTALL)
                    if question_match:
                        previous_question = question_match.group(1).strip()
                break

        question_text = previous_question or "the current interview question"

        return f"""<interview_guidance>
You are facilitating an interview. Review the conversation above for the expert's previous answers.

<original_question>{question_text}</original_question>
<document_answer>{document_answer}</document_answer>

A <system-reminder> with follow-up limits will appear next, followed by the expert's latest message.

Based on the expert's response, use the appropriate tool:

1. If they ANSWER the question:
   → Combine their answer with previous answers from conversation
   → Compare combined answer with document_answer, identify gaps/differences
   → Use ask_question with category: followup to clarify differences

2. If they ASK for the answer or clarification:
   → Provide relevant info from document_answer
   → Use ask_question with category: normal to respond

3. If they want to SKIP or move on:
   → Use ask_question with category: interview_note to proceed to next question

4. If they REQUEST something else:
   → Handle their request appropriately using category: normal
</interview_guidance>"""

    async def _determine_next_tool(
        self,
        conversation: list[MessageData],
        current_note_content: str,
        document_answer: str | None = None,
    ) -> MessageData:
        """
        LLM decides next tool based purely on conversation history.
        Note content is injected into LLM messages but not conversation history.

        Message order (user's last message at END so LLM responds to it):
        1. System prompt
        2. Note content
        3. Conversation history (EXCLUDING last user message)
        4. <interview_guidance> (if document_answer exists)
        5. <system-reminder> (follow-up limits + expert guidance)
        6. User's LAST message (at the END)

        Args:
            conversation: Conversation history
            current_note_content: Current interview note content
            document_answer: Optional precomputed answer from documents for comparison

        Returns MessageData with tool call XML or "complete"
        """
        # Separate last user message from conversation history
        last_user_message = None
        conversation_without_last = list(conversation)

        # Find and extract the last user message (non-tool)
        for i in range(len(conversation_without_last) - 1, -1, -1):
            if conversation_without_last[i].role == "user" and not conversation_without_last[i].treat_as_tool:
                last_user_message = conversation_without_last.pop(i)
                break

        # Convert conversation (without last user message) to LLM format
        llm_conversation = []
        for i, message in enumerate(conversation_without_last):
            role = "assistant" if message.role == "agent" else message.role

            # Inject compacted context from first message's metadata (if summary was created)
            if i == 0:
                content = inject_compacted_context_to_content(message)
            else:
                content = message.content

            llm_conversation.append({"role": role, "content": content})

        tool_str = "\n\n".join([f"{tool}" for tool in self.tools.values()])

        # Build base system prompt
        system_prompt = INTERVIEW_QUESTION_GENERATION_PROMPT_V2.format(tools_str=tool_str, domain=self.domain, role=self.role)

        # Build messages array starting with system prompt
        messages = [{"role": "system", "content": system_prompt}]

        # 1. Add note content as separate user message
        note_message = f"Here is the current interview note state (read-only): <note>\n{current_note_content}\n</note>"
        messages.append({"role": "user", "content": note_message})

        # 2. Add conversation history (WITHOUT last user message)
        messages.extend(llm_conversation)

        # 3. Add interview guidance (if document_answer exists)
        if document_answer:
            guidance = self._build_interview_guidance(document_answer, conversation)
            messages.append({"role": "user", "content": guidance})

        # 4. Add settings context as <system-reminder>
        settings_context = self._build_settings_context()
        if settings_context:
            messages.append({"role": "user", "content": settings_context})

        # 5. Add user's LAST message at the END (LLM responds to this)
        if last_user_message:
            messages.append({"role": "user", "content": last_user_message.content})

        llm_request = BaseRequest(
            arguments={
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": None,
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
