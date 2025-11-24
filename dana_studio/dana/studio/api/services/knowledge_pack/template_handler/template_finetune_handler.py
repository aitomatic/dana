"""
Template Fine-tuning Handler for Interview Template Refinement

A conversational handler for refining interview templates through natural language
interactions, allowing users to modify questions, reorder topics, and generate
new content based on LLM suggestions.
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
    RefineTopicQuestionsTool,
    GenerateAdditionalQuestionsTool,
    ReplaceInFileTool,
    AttemptCompletionTool,
    AskQuestionTool,
    ReadDocumentsTool,
)
from dana.studio.api.services.knowledge_pack.template_handler.prompts import TEMPLATE_FINETUNE_PROMPT
from dana.lang.common.sys_resource.rag.rag_resource_v2 import RAGResourceV2
from dana.studio.api.repositories.config import KNOW_FOLDER_NAME
import logging
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


class TemplateFinetuneHandler(AbstractHandler):
    """
    Stateless template fine-tuning handler using conversation history as state.

    Flow:
    1. Each tool result is added as assistant message
    2. LLM reads full conversation to decide next action
    3. No complex state management needed
    4. Human approval happens via conversation
    """

    def __init__(
        self,
        template_path: str,
        knowledge_pack_path: str,
        kp_id: int,
        doc_paths: list[str] | None = None,
        llm: LLMResource | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
        notifier: Callable[[str, str, Literal["init", "in_progress", "finish", "error"], float | None], Awaitable[None]] | None = None,
    ):
        self.template_path = template_path
        self.knowledge_pack_path = knowledge_pack_path
        self.kp_id = kp_id
        self.doc_paths = doc_paths
        self.domain = domain
        self.role = role
        self.llm = llm or LLMResource()
        self.notifier = notifier
        self.tools = {}
        self.rag_knows = None
        self.rag_docs = None
        self.db = None  # Database session set by API route
        self._initialize_tools()

    async def _initialize_rag(self) -> None:
        """Initialize two separate RAG resources: one for knows folder, one for doc_paths."""

        # Initialize RAG for knows folder
        knows_dir = Path(self.knowledge_pack_path) / KNOW_FOLDER_NAME
        if knows_dir.exists():
            self.rag_knows = RAGResourceV2(
                sources=[str(knows_dir)],
                name="template_rag_knows",
                chunk_size=1024,
                chunk_overlap=256,
                num_results=10,
                reranking=True,
                debug=False,
            )
            await self.rag_knows.initialize()
        else:
            self.rag_knows = None

        # Initialize RAG for additional document paths
        if self.doc_paths:
            self.rag_docs = RAGResourceV2(
                sources=self.doc_paths,
                name="template_rag_docs",
                chunk_size=1024,
                chunk_overlap=256,
                num_results=10,
                reranking=True,
                debug=False,
            )
            await self.rag_docs.initialize()
        else:
            self.rag_docs = None

    def _initialize_tools(self):
        """Initialize all available tools for template fine-tuning."""
        # Core workflow tools (reused from knowledge_ops)
        self.tools.update(AskQuestionTool().as_dict())
        self.tools.update(AttemptCompletionTool().as_dict())

        # Template-specific tools
        self.tools.update(ViewTemplateTool(template_path=str(self.template_path)).as_dict())
        self.tools.update(
            RefineTopicQuestionsTool(template_path=str(self.template_path), domain=self.domain, role=self.role, llm=self.llm).as_dict()
        )
        self.tools.update(
            GenerateAdditionalQuestionsTool(
                template_path=str(self.template_path),
                knowledge_pack_path=str(self.knowledge_pack_path),
                domain=self.domain,
                role=self.role,
                llm=self.llm,
                rag_knows=self.rag_knows,
                rag_docs=self.rag_docs,
            ).as_dict()
        )
        self.tools.update(ReplaceInFileTool(template_path=str(self.template_path)).as_dict())
        self.tools.update(ReadDocumentsTool(kp_id=self.kp_id, rag_docs=self.rag_docs).as_dict())

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
        # Initialize RAG resources if not already done
        if self.rag_knows is None and self.rag_docs is None:
            await self._initialize_rag()
            # Re-initialize tools with RAG resources
            self._initialize_tools()

        # Initialize conversation with user request
        conversation = request.chat_history

        if len(conversation) >= 10:  # FOR NOW, ONLY USE LAST 10 MESSAGES
            conversation = [conversation[0]] + conversation[-10:]

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
            if tool_name in [
                "refine_topic_questions",
                "generate_additional_questions",
                "update_interview_approach",
                "replace_in_template",
            ]:
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

        system_prompt = TEMPLATE_FINETUNE_PROMPT.format(
            tools_str=tool_str, domain=self.domain, role=self.role, template_path=self.template_path
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

            # Execute the tool with context
            tool = self.tools[tool_name]

            # Add context parameters (include db session only for tools that need it)
            context_params = {}
            if self.db and tool_name in ("read_documents", "generate_additional_questions"):
                context_params["db"] = self.db
            params.update(context_params)

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


if __name__ == "__main__":
    import asyncio

    # Test with sample template
    handler = TemplateFinetuneHandler(
        template_path="/Users/lam/Desktop/repos/opendxa/knowledge_packs/1/templates/template_2/README.md",
        knowledge_pack_path="/Users/lam/Desktop/repos/opendxa/knowledge_packs/1",
        kp_id=1,
        doc_paths=[
            "/Users/lam/Desktop/repos/opendxa/uploads/2024-SiemensHealthineers-AnnualFinStatements.pdf",
            "/Users/lam/Desktop/repos/opendxa/uploads/STD-ENG-015.pdf",
        ],
        domain="Food Manufacturing",
        role="Process Operator",
    )
    chat_history = []

    tool_call = """
<thinking>
Intent: Clear all questions from the "Managing Normal Operating Conditions Across Beet Sugar Process Steps" topic.
Context: The previous search pattern did not match the template, likely due to formatting differences (e.g., line breaks, spacing, or markdown structure). The section exists, but the exact match failed.
Decision: View only the specific topic section to capture its precise formatting and ensure the search pattern matches exactly for successful replacement.
Approval: None needed; this is a diagnostic step to ensure accuracy.
User Message: The previous attempt didn't match the template's formatting. I'll display just the "Managing Normal Operating Conditions Across Beet Sugar Process Steps" section to capture its exact structure before proceeding.
</thinking>

<view_template>
<section>topic:Managing Normally Operating Conditions Across Beet Sugar Process Steps</section>
</view_template>
"""

    tool_name, params, thinking_content = handler._parse_xml_tool_call(tool_call)
    print("=" * 100)
    print(tool_name)
    print(params)
    print(thinking_content)
    print("=" * 100)

    result = asyncio.run(handler._execute_tool(tool_name, params, thinking_content))
    print("=" * 100)
    print(result.content)
    print("=" * 100)

    # print("🎯 Template Fine-tuning Handler - Interactive Testing Environment")
    # print("=" * 70)
    # print("Commands:")
    # print("- Type any template refinement request to test the workflow")
    # print("- Type 'quit' or 'exit' to quit")
    # print("- Type 'reset' to clear conversation history")
    # print("- Type 'history' to view conversation")
    # print("- Type 'tools' to list available tools")
    # print("=" * 70)

    # while True:
    #     try:
    #         user_message = input(f"\n💬 User ({len(chat_history) // 2 + 1}): ").strip()
    #         chat_history.append(MessageData(role=SenderRole.USER, content=user_message))

    #         if user_message.lower() in ["quit", "exit"]:
    #             print("👋 Goodbye!")
    #             break
    #         elif user_message.lower() == "reset":
    #             chat_history = []
    #             print("🗑️  Chat history cleared.")
    #             continue
    #         elif user_message.lower() == "history":
    #             if not chat_history:
    #                 print("📝 No conversation history yet.")
    #             else:
    #                 print(f"\n📝 Conversation History ({len(chat_history)} messages):")
    #                 for i, msg in enumerate(chat_history, 1):
    #                     role_emoji = "👤" if msg.role == "user" else "🤖"
    #                     print(f"  {i:2}. {role_emoji} {msg.role.upper()}: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
    #             continue
    #         elif user_message.lower() == "tools":
    #             print(f"\n🛠️  Available Tools ({len(handler.tools)}):")
    #             for i, (name, tool) in enumerate(handler.tools.items(), 1):
    #                 print(
    #                     f"  {i:2}. {name}: {tool.tool_information.description[:80]}{'...' if len(tool.tool_information.description) > 80 else ''}"
    #                 )
    #             continue
    #         elif not user_message:
    #             continue

    #         # Create request
    #         request = IntentDetectionRequest(user_message=user_message, chat_history=chat_history, current_domain_tree=None, agent_id=1)

    #         print(f"\n{'⚡' * 3} PROCESSING REQUEST {'⚡' * 3}")
    #         print(f"Request: {user_message}")

    #         # Run handler
    #         result = asyncio.run(handler.handle(request))

    #         # Display results
    #         print(f"\n{'📊' * 3} WORKFLOW RESULTS {'📊' * 3}")
    #         print(f"Status: {result['status']}")
    #         print(f"Message: {result['message']}")
    #         print(f"Template Modified: {result.get('template_modified', False)}")

    #         # Show conversation flow
    #         conversation = result["conversation"]
    #         print(f"\n{'💭' * 3} CONVERSATION FLOW ({len(conversation)} messages) {'💭' * 3}")

    #         for i, msg in enumerate(conversation, 1):
    #             role_emoji = "👤" if msg.role == "user" else "🤖"
    #             role_color = "\033[94m" if msg.role == "user" else "\033[92m"  # Blue for user, green for assistant
    #             reset_color = "\033[0m"

    #             print(f"\n{i:2}. {role_emoji} {role_color}{msg.role.upper()}{reset_color}:")

    #             # Handle tool calls vs regular messages
    #             if msg.role == "assistant" and ("<" in msg.content and ">" in msg.content):
    #                 # This looks like a tool call
    #                 if "<thinking>" in msg.content:
    #                     # Extract thinking for display
    #                     thinking_match = re.search(r"<thinking>(.*?)</thinking>", msg.content, re.DOTALL)
    #                     if thinking_match:
    #                         thinking = thinking_match.group(1).strip()
    #                         print(f"    💭 Thinking: {thinking}")

    #                 # Extract tool name and arguments (skip thinking tags)
    #                 tool_match = re.search(r"<(?!thinking)(\w+)", msg.content)
    #                 if tool_match:
    #                     tool_name = tool_match.group(1)
    #                     print(f"    🔧 Tool Call: {tool_name}")

    #                     # Extract and display tool arguments
    #                     try:
    #                         _, params, _ = handler._parse_xml_tool_call(msg.content)
    #                         if params:
    #                             print("    📝 Arguments:")
    #                             for key, value in params.items():
    #                                 if isinstance(value, list):
    #                                     print(f"      {key}: {value}")
    #                                 elif isinstance(value, str) and len(value) > 100:
    #                                     print(f"      {key}: {value[:100]}...")
    #                                 else:
    #                                     print(f"      {key}: {value}")
    #                     except Exception as e:
    #                         print(f"    ⚠️ Could not parse arguments: {e}")
    #             else:
    #                 # Regular message content
    #                 content_lines = msg.content.split("\n")
    #                 for line in content_lines:  # Show first 5 lines
    #                     if line.strip():
    #                         print(f"    {line}")

    #         # Update chat history for next iteration
    #         chat_history = conversation

    #         # Check if workflow is complete or needs user input
    #         if result["status"] == "user_input_required":
    #             print(f"\n{'⏸️' * 3} WORKFLOW PAUSED - USER INPUT REQUIRED {'⏸️' * 3}")
    #             print("The system is waiting for your response to continue.")
    #         elif result["status"] == "success":
    #             print(f"\n{'✅' * 3} WORKFLOW COMPLETED SUCCESSFULLY {'✅' * 3}")
    #             print("You can start a new template refinement request or type 'reset' to clear history.")

    #     except KeyboardInterrupt:
    #         print("\n\n👋 Interrupted. Goodbye!")
    #         break
    #     except Exception as e:
    #         print(f"\n❌ Error: {e}")
    #         import traceback

    #         print("Full traceback:")
    #         traceback.print_exc()
    #         print("\n💡 Continuing... (you can type 'reset' to clear state)")
