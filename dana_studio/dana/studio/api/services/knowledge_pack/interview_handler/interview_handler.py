"""
Interview Handler for orchestrating knowledge capture sessions.

A conversational handler for expert knowledge sharing with intelligent assessment and
parallel processing, using LLM-driven tool orchestration.
"""

from dana.studio.api.services.intent_detection.intent_handlers.abstract_handler import AbstractHandler
from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.lang.common.types import BaseRequest
from dana.lang.common.utils.misc import Misc
from dana.studio.api.core.schemas import IntentDetectionRequest, MessageData
from dana.studio.api.core.schemas import SenderRole
from dana.lang.common.sys_resource.rag.rag_resource_v2 import RAGResourceV2
from typing import Any, Literal, Awaitable, Callable
import logging
import re
import asyncio
import os
from pathlib import Path
from datetime import datetime

from dana.studio.api.services.knowledge_pack.interview_handler.tools import (
    ViewNoteTool,
    UpdateNoteTool,
    DocumentSearchTool,
    AskQuestionTool,
    AttemptCompletionTool,
)
from dana.studio.api.services.knowledge_pack.interview_handler.prompts import INTERVIEW_HANDLER_PROMPT
# from dana.studio.api.services.knowledge_pack.template_handler.utils import parse_template

logger = logging.getLogger(__name__)


class InterviewHandler(AbstractHandler):
    """
    LLM-driven interview orchestrator using persistent interview note.

    Flow:
    1. Initialize interview note from template
    2. LLM updates note with expert insights
    3. LLM searches documents for context
    4. LLM asks questions or completes based on note state
    """

    def __init__(
        self,
        session_dir: str,
        template_path: str,
        response_generator,
        rag_resource: RAGResourceV2,
        llm: LLMResource | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
        notifier: Callable[[str, str, Literal["init", "in_progress", "finish", "error"], float | None], Awaitable[None]] | None = None,
    ):
        self.session_dir = session_dir
        self.note_path = f"{session_dir}/interview_notes.md"
        self.template_path = template_path
        self.response_generator = response_generator
        self.rag_resource = rag_resource
        self.domain = domain
        self.role = role
        self.llm = llm or LLMResource()
        self.notifier = notifier
        self.tools = {}

        # Store template path for later initialization
        self.template_path = template_path

        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize note-based tools."""
        self.tools.update(ViewNoteTool(self.note_path).as_dict())
        self.tools.update(UpdateNoteTool(self.note_path).as_dict())
        self.tools.update(DocumentSearchTool(self.rag_resource).as_dict())
        self.tools.update(AskQuestionTool().as_dict())
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

    def _generate_initial_note(self, template_data: dict) -> str:
        """Generate structured interview note from template data."""
        sections = []

        # Header
        approach = template_data.get("approach", {})
        domain_name = self.domain
        sections.append(f"# Interview Notes - {domain_name}")
        sections.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d')}")
        sections.append("")

        # Interview approach summary
        if approach.get("goal"):
            sections.append("## Interview Goal")
            sections.append(f"{approach['goal']}")
            sections.append("")

        # Topics from template
        topics = template_data.get("topics", [])
        if topics:
            sections.append("## Topics to Cover")
            for topic in topics:
                sections.append(f"### {topic['name']}")
                if topic.get("background"):
                    sections.append(f"**Background**: {topic['background']}")
                sections.append("**Status**: Not started")
                if topic.get("questions"):
                    sections.append("**Key Questions**: {} prepared".format(len(topic["questions"])))
                sections.append("")
        else:
            sections.append("## Topics to Cover")
            sections.append("*To be determined from conversation*")
            sections.append("")

        # Expert insights (empty initially)
        sections.append("## Expert Insights")
        sections.append("*No insights captured yet*")
        sections.append("")

        # Understanding level
        sections.append("## Current Understanding Level")
        sections.append("- **Completeness**: 0% - Interview just started")
        sections.append("- **Confidence**: Low")
        sections.append("- **Next Steps**: Begin with opening questions")
        sections.append("")

        # Documents found (empty initially)
        sections.append("## Documents Found")
        sections.append("*No documents searched yet*")
        sections.append("")

        return "\n".join(sections)

    async def handle(self, request: IntentDetectionRequest) -> dict[str, Any]:
        """
        Main stateless handler - runs tool loop until completion.

        Returns:
        {
            "status": "success" | "user_input_required",
            "message": "...",
            "conversation": [...],
            "workflow_completed": bool,
            "final_response": str (if completed)
        }
        """
        # Initialize note from template if not exists
        if not os.path.exists(self.note_path):
            await self._initialize_note_from_template(self.template_path, self.note_path)

        # Initialize conversation with user request
        conversation = request.chat_history

        if len(conversation) >= 10:  # FOR NOW, ONLY USE LAST 10 MESSAGES
            conversation = conversation[-10:]

        # Track if workflow was completed
        workflow_completed = False

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
                tool_result_msg = await self._execute_tool(tool_name, params, thinking_content, conversation)
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
            "message": conversation[-1].content,
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

        system_prompt = INTERVIEW_HANDLER_PROMPT.format(
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


if __name__ == "__main__":
    import asyncio

    # Test with sample components

    class MockResponseGenerator:
        async def generate_response_with_gaps(self, rewritten_message, document_chunks, topic_result, sharing_assessment):
            return {
                "response": "Thank you for sharing your expertise about safety procedures.",
                "follow_up_question": "Can you tell me more about specific procedures?",
                "success": True,
            }

    # Mock RAG resource
    class MockRAGResource(RAGResourceV2):
        def __init__(self):
            super().__init__(sources=[], name="mock_rag")
            self._is_ready = True

        async def query(self, query, num_results=10):
            return f"Document content about: {query}"

    print("🎯 Interview Handler - Interactive Testing Environment")
    print("=" * 70)
    print("Commands:")
    print("- Type any expert sharing to test the workflow")
    print("- Type 'quit' or 'exit' to quit")
    print("- Type 'reset' to clear conversation history")
    print("- Type 'history' to view conversation")
    print("- Type 'tools' to list available tools")
    print("=" * 70)

    # Create temporary template for testing
    import tempfile

    test_template_content = """# Master Interview Template: Industrial Safety

## Interview Approach
- **Goal**: Capture expert's safety knowledge
- **Style**: Conversational, expert-driven
- **Duration**: 60-90 minutes
- **Topics Covered**: Safety procedures

---

## Topic Opening Questions

### Conveyor Safety
**Background**: Safety procedures for conveyor systems
**Opening Questions**:
1. What safety procedures do you follow?
2. How do you handle lockout/tagout?

---
"""

    temp_template = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    temp_template.write(test_template_content)
    temp_template.close()

    # Initialize handler
    handler = InterviewHandler(
        session_dir="/tmp/test_session",
        # template_path=temp_template.name,
        template_path="/Users/lam/Desktop/repos/opendxa/knowledge_packs/1/templates/default_template/README.md",
        response_generator=MockResponseGenerator(),
        rag_resource=MockRAGResource(),
        domain="Industrial Safety",
        role="Safety Expert",
    )
    chat_history = []

    while True:
        try:
            user_message = input(f"\n💬 User ({len(chat_history) // 2 + 1}): ").strip()
            chat_history.append(MessageData(role=SenderRole.USER, content=user_message))

            if user_message.lower() in ["quit", "exit"]:
                print("👋 Goodbye!")
                break
            elif user_message.lower() == "reset":
                chat_history = []
                print("🗑️  Chat history cleared.")
                continue
            elif user_message.lower() == "history":
                if not chat_history:
                    print("📝 No conversation history yet.")
                else:
                    print(f"\n📝 Conversation History ({len(chat_history)} messages):")
                    for i, msg in enumerate(chat_history, 1):
                        role_emoji = "👤" if msg.role == "user" else "🤖"
                        print(f"  {i:2}. {role_emoji} {msg.role.upper()}: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
                continue
            elif user_message.lower() == "tools":
                print(f"\n🛠️  Available Tools ({len(handler.tools)}):")
                for i, (name, tool) in enumerate(handler.tools.items(), 1):
                    print(
                        f"  {i:2}. {name}: {tool.tool_information.description[:80]}{'...' if len(tool.tool_information.description) > 80 else ''}"
                    )
                continue
            elif not user_message:
                continue

            # Create request
            request = IntentDetectionRequest(user_message=user_message, chat_history=chat_history, current_domain_tree=None, agent_id=1)

            print(f"\n{'⚡' * 3} PROCESSING REQUEST {'⚡' * 3}")
            print(f"Request: {user_message}")

            # Run handler
            result = asyncio.run(handler.handle(request))

            # Display results
            print(f"\n{'📊' * 3} WORKFLOW RESULTS {'📊' * 3}")
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            print(f"Workflow Completed: {result.get('workflow_completed', False)}")

            # Show conversation flow
            conversation = result["conversation"]
            print(f"\n{'💭' * 3} CONVERSATION FLOW ({len(conversation)} messages) {'💭' * 3}")

            for i, msg in enumerate(conversation, 1):
                role_emoji = "👤" if msg.role == "user" else "🤖"
                role_color = "\033[94m" if msg.role == "user" else "\033[92m"  # Blue for user, green for assistant
                reset_color = "\033[0m"

                print(f"\n{i:2}. {role_emoji} {role_color}{msg.role.upper()}{reset_color}:")

                # Handle tool calls vs regular messages
                if msg.role == "assistant" and ("<" in msg.content and ">" in msg.content):
                    # This looks like a tool call
                    if "<thinking>" in msg.content:
                        # Extract thinking for display
                        thinking_match = re.search(r"<thinking>(.*?)</thinking>", msg.content, re.DOTALL)
                        if thinking_match:
                            thinking = thinking_match.group(1).strip()
                            print(f"    💭 Thinking: {thinking}")

                    # Extract tool name and arguments (skip thinking tags)
                    tool_match = re.search(r"<(?!thinking)(\w+)", msg.content)
                    if tool_match:
                        tool_name = tool_match.group(1)
                        print(f"    🔧 Tool Call: {tool_name}")

                        # Extract and display tool arguments
                        try:
                            _, params, _ = handler._parse_xml_tool_call(msg.content)
                            if params:
                                print("    📝 Arguments:")
                                for key, value in params.items():
                                    if isinstance(value, list):
                                        print(f"      {key}: {value}")
                                    elif isinstance(value, str) and len(value) > 100:
                                        print(f"      {key}: {value[:100]}...")
                                    else:
                                        print(f"      {key}: {value}")
                        except Exception as e:
                            print(f"    ⚠️ Could not parse arguments: {e}")
                else:
                    # Regular message content
                    content_lines = msg.content.split("\n")
                    for line in content_lines:  # Show first 5 lines
                        if line.strip():
                            print(f"    {line}")

            # Update chat history for next iteration
            chat_history = conversation

            # Check if workflow is complete or needs user input
            if result["status"] == "user_input_required":
                print(f"\n{'⏸️' * 3} WORKFLOW PAUSED - USER INPUT REQUIRED {'⏸️' * 3}")
                print("The system is waiting for your response to continue.")
            elif result["status"] == "success":
                print(f"\n{'✅' * 3} WORKFLOW COMPLETED SUCCESSFULLY {'✅' * 3}")
                print("You can start a new interview session or type 'reset' to clear history.")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            print("Full traceback:")
            traceback.print_exc()
            print("\n💡 Continuing... (you can type 'reset' to clear state)")
