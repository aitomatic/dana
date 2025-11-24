"""
Interview Note Handler for capturing user expertise and updating interview notes.

A specialized handler focused solely on extracting insights from user messages
and updating the interview note with captured knowledge.
"""

from dana.studio.api.services.intent_detection.intent_handlers.abstract_handler import AbstractHandler
from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.lang.common.types import BaseRequest
from dana.lang.common.utils.misc import Misc
from dana.studio.api.core.schemas import IntentDetectionRequest, MessageData
from dana.studio.api.core.schemas import SenderRole
from typing import Any
import logging
import os
from pathlib import Path
from datetime import datetime

from dana.studio.api.services.knowledge_pack.interview_handler.tools import (
    UpdateNoteTool,
    AttemptCompletionTool,
)
from dana.studio.api.services.knowledge_pack.interview_handler.prompts import INTERVIEW_NOTE_CAPTURE_PROMPT

logger = logging.getLogger(__name__)


class InterviewNoteHandler(AbstractHandler):
    """
    LLM-driven note capture handler for interview sessions.

    Flow:
    1. Read current note state
    2. Extract insights from user message
    3. Update note with captured insights
    4. Update understanding level based on template coverage
    """

    def __init__(
        self,
        session_dir: str,
        template_path: str,
        llm: LLMResource | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
    ):
        self.session_dir = session_dir
        self.note_path = f"{session_dir}/interview_notes.md"
        self.template_path = template_path
        self.domain = domain
        self.role = role
        self.llm = llm or LLMResource()
        self.tools = {}

        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize note-based tools."""
        self.tools.update(UpdateNoteTool(self.note_path).as_dict())
        self.tools.update(AttemptCompletionTool().as_dict())

    async def _initialize_note_from_template(self, template_path: str, note_path: str):
        """Initialize interview note from template using LLM."""
        try:
            # Read template content
            with open(template_path, encoding="utf-8") as f:
                template_content = f.read()

            # Use LLM to generate intelligent note structure
            note_content = await self._generate_note_with_llm(template_content)

            # Create directory if needed
            Path(note_path).parent.mkdir(parents=True, exist_ok=True)

            # Write note
            with open(note_path, "w") as f:
                f.write(note_content)

            logger.info(f"Initialized interview note at {note_path}")
        except Exception as e:
            logger.error(f"Failed to initialize note from template: {e}")
            # Create minimal note
            minimal_note = f"""# Interview Notes - {self.domain}
**Date**: {datetime.now().strftime('%Y-%m-%d')}

## Topics to Cover
*To be determined from conversation*

## Expert Insights
*No insights captured yet*

## Current Understanding Level
- **Completeness**: 0% - Interview just started
- **Confidence**: Low
- **Next Steps**: Begin with opening questions

## Documents Found
*No documents searched yet*
"""
            Path(note_path).parent.mkdir(parents=True, exist_ok=True)
            with open(note_path, "w") as f:
                f.write(minimal_note)

    async def _generate_note_with_llm(self, template_content: str) -> str:
        """Generate interview note using LLM based on template content."""
        prompt = f"""You are an expert interview coordinator. Based on the provided interview template, create a structured interview note that will guide the knowledge capture session.

INTERVIEW TEMPLATE:
{template_content}

Create a markdown interview note with the following structure:

# Interview Notes - [Domain from template]
**Date**: {datetime.now().strftime('%Y-%m-%d')}

## Interview Goal
[Extract and summarize the goal from the template]

## Topics to Cover
[For each topic in the template, create a section with:]
### [Topic Name]
**Background**: [Topic background from template]
**Status**: Not started
**Key Questions**: 
1. [First opening question from template]
2. [Second opening question from template]
3. [Third opening question from template]
[Continue with numbered list format for all questions]

## Expert Insights
*No insights captured yet*

## Current Understanding Level
- **Completeness**: 0% - Interview just started
- **Confidence**: Low
- **Next Steps**: Begin with opening questions from the template

## Documents Found
*No documents searched yet*

## Relationship Exploration Prompts
[Include the relationship exploration prompts from template]

CRITICAL FORMATTING REQUIREMENTS:
1. Extract all topics and their details from the template
2. For **Key Questions** sections, ALWAYS use numbered list format: "1. Question text"
3. Each question must be on its own line starting with a number and period
4. Preserve the interview approach and style from the template
5. Create a comprehensive but organized note structure
6. Use the exact wording from the template where appropriate

Generate the complete markdown note:"""

        try:
            llm_request = BaseRequest(
                arguments={
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert interview coordinator who creates structured interview notes from templates.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": None,
                }
            )

            response = await self.llm.query(llm_request)
            note_content = Misc.get_response_content(response)

            # Clean up the response to ensure it's valid markdown
            if note_content.startswith("```markdown"):
                note_content = note_content[11:]
            if note_content.endswith("```"):
                note_content = note_content[:-3]

            return note_content.strip()

        except Exception as e:
            logger.error(f"Failed to generate note with LLM: {e}")
            # Fallback to simple note generation
            return self._generate_simple_note(template_content)

    def _generate_simple_note(self, template_content: str) -> str:
        """Fallback simple note generation without LLM."""
        return f"""# Interview Notes - {self.domain}
**Date**: {datetime.now().strftime('%Y-%m-%d')}

## Topics to Cover
*To be determined from conversation*

## Expert Insights
*No insights captured yet*

## Current Understanding Level
- **Completeness**: 0% - Interview just started
- **Confidence**: Low
- **Next Steps**: Begin with opening questions

## Documents Found
*No documents searched yet*
"""

    async def handle(
        self,
        request: IntentDetectionRequest,
        current_note_content: str,  # Always provided
    ) -> dict[str, Any]:
        """
        Main handler - captures user input and updates notes.

        Args:
            request: Intent detection request with conversation history
            current_note_content: Current interview note content

        Returns:
        {
            "status": "success",
            "conversation": [...],
            "note_updated": bool,
            "updated_note_content": str | None
        }
        """
        # Initialize note from template if not exists
        if not os.path.exists(self.note_path):
            await self._initialize_note_from_template(self.template_path, self.note_path)

        # Initialize conversation with user request
        conversation = request.chat_history

        if len(conversation) >= 10:  # FOR NOW, ONLY USE LAST 10 MESSAGES
            conversation = conversation[-10:]

        # Add current note content to conversation context for LLM
        # This allows the LLM to use note state without reading file
        note_context_msg = MessageData(
            role=SenderRole.USER,
            content=f"[Current Interview Note State]\n{current_note_content}",
            treat_as_tool=True,
        )
        # Insert note context at the beginning of conversation for context
        conversation_with_note = [note_context_msg] + conversation

        # Track if note was updated
        note_updated = False

        # Tool loop - max 15 iterations
        for _ in range(15):
            # Determine next tool from conversation (with note context)
            tool_msg = await self._determine_next_tool(conversation_with_note, current_note_content)
            conversation_with_note.append(tool_msg)

            try:
                tool_name, params, thinking_content = self._parse_xml_tool_call(tool_msg.content)
                tool_result_msg = await self._execute_tool(tool_name, params, thinking_content, conversation_with_note)
            except Exception as e:
                conversation_with_note.append(MessageData(role=SenderRole.USER, content=f"Error: {e}", treat_as_tool=True))
                continue

            # Check if complete
            if isinstance(tool_msg, MessageData) and tool_msg.content.strip().lower() == "complete":
                break

            # Track if note was updated
            if tool_name in ["update_note"]:
                note_updated = True

            # Check if this was a completion
            if tool_name in ["attempt_completion"]:
                # Exit loop when completion is signaled
                conversation_with_note.append(tool_result_msg)
                break

            # Add result to conversation
            conversation_with_note.append(tool_result_msg)

        # Remove note context message from final conversation
        final_conversation = [msg for msg in conversation_with_note if msg != note_context_msg]

        # Read updated note content if note was updated
        updated_note_content = None
        if note_updated and os.path.exists(self.note_path):
            try:
                with open(self.note_path, encoding="utf-8") as f:
                    updated_note_content = f.read()
            except Exception as e:
                logger.warning(f"Failed to read updated note: {e}")

        # Build final result
        result = {
            "status": "success",
            "conversation": final_conversation,
            "note_updated": note_updated,
            "updated_note_content": updated_note_content,
        }

        return result

    async def _determine_next_tool(self, conversation: list[MessageData], current_note_content: str) -> MessageData:
        """
        LLM decides next tool based on conversation history and current note content.

        Args:
            conversation: Conversation history with note context
            current_note_content: Current interview note content (always provided)

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

        system_prompt = INTERVIEW_NOTE_CAPTURE_PROMPT.format(
            tools_str=tool_str, domain=self.domain, role=self.role, note_path=self.note_path, template_content=template_content
        )

        llm_request = BaseRequest(
            arguments={
                "messages": [
                    {"role": "system", "content": system_prompt},
                ]
                + llm_conversation,
                "temperature": 0.1,
                "max_tokens": None,
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
