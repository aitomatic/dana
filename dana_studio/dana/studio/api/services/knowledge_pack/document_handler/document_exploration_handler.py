"""
Document Exploration Handler for Knowledge Pack Document Analysis

A conversational handler for exploring and analyzing documents within knowledge packs,
enabling users to discover insights, ask questions, and understand document content
through natural language interactions.
"""

from dana.studio.api.services.intent_detection.intent_handlers.abstract_handler import AbstractHandler
from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.lang.common.types import BaseRequest
from dana.lang.common.utils.misc import Misc
from dana.studio.api.core.schemas import IntentDetectionRequest, MessageData
from dana.studio.api.core.schemas import SenderRole
from typing import Any, Literal, Awaitable, Callable
from dana.studio.api.services.knowledge_pack.document_handler.tools import (
    AttemptCompletionTool,
    AskQuestionTool,
    ReadDocumentsTool,
)
from dana.studio.api.services.knowledge_pack.document_handler.prompts import DOCUMENT_EXPLORATION_PROMPT
from dana.lang.common.sys_resource.rag.rag_resource_v2 import RAGResourceV2
from dana.studio.api.repositories.domain_knowledge_repo import SQLDomainKnowledgeRepo
from dana.studio.api.repositories.document_repo import SQLDocumentRepo
from dana.studio.api.core.logger import log as logger


class DocumentExplorationHandler(AbstractHandler):
    """
    Stateless document exploration handler using conversation history as state.

    Flow:
    1. Each tool result is added as assistant message
    2. LLM reads full conversation to decide next action
    3. No complex state management needed
    4. Human approval happens via conversation
    """

    def __init__(
        self,
        kp_id: int,
        doc_paths: list[str] | None = None,
        template_path: str | None = None,
        llm: LLMResource | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
        notifier: Callable[[str, str, Literal["init", "in_progress", "finish", "error"], float | None], Awaitable[None]] | None = None,
    ):
        self.kp_id = kp_id
        self.doc_paths = doc_paths
        self.template_path = template_path
        self.domain = domain
        self.role = role
        self.llm = llm or LLMResource()
        self.notifier = notifier
        self.tools = {}
        self.rag_docs = None
        self.db = None  # Database session set by API route
        self._initialize_tools()

    async def _initialize_rag(self) -> None:
        """Initialize RAG resource for document content retrieval."""
        # Initialize RAG for additional document paths
        if self.doc_paths:
            self.rag_docs = RAGResourceV2(
                sources=self.doc_paths,
                name="document_exploration_rag",
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
        """Initialize all available tools for document exploration."""
        # Core workflow tools
        self.tools.update(AskQuestionTool().as_dict())
        self.tools.update(AttemptCompletionTool().as_dict())

        # Document exploration tool
        self.tools.update(ReadDocumentsTool(kp_id=self.kp_id, rag_docs=self.rag_docs).as_dict())

    async def handle(self, request: IntentDetectionRequest) -> dict[str, Any]:
        """
        Main stateless handler - runs tool loop until completion.

        Returns:
        {
            "status": "success" | "user_input_required",
            "message": "...",
            "conversation": [...],
        }
        """
        # Initialize RAG resources if not already done
        if self.rag_docs is None and self.doc_paths:
            await self._initialize_rag()
            # Re-initialize tools with RAG resources
            self._initialize_tools()

        # Initialize conversation with user request
        conversation = request.chat_history

        if len(conversation) >= 4:  # FOR NOW, ONLY USE LAST 4 MESSAGES
            conversation = conversation[-4:]

        # Tool loop - max 15 iterations
        for _ in range(15):
            # Determine next tool from conversation
            tool_msg = await self._determine_next_tool(conversation)
            logger.debug("=" * 100)
            logger.debug(tool_msg.content)
            logger.debug("=" * 100)
            conversation.append(tool_msg)
            init = False
            tool_name = None
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
                if self.notifier and init and tool_name:
                    await self.notifier(tool_name, f"Error: {e}", "error", None)
                continue

            logger.debug("-" * 100)
            logger.debug(tool_result_msg.content)
            logger.debug("-" * 100)

            # Check if complete
            if isinstance(tool_msg, MessageData) and tool_msg.content.strip().lower() == "complete":
                break

            # Add result to conversation
            conversation.append(tool_result_msg)

            # Check if user input is required
            if tool_result_msg.require_user:
                return {
                    "status": "user_input_required",
                    "message": tool_result_msg.content,
                    "conversation": conversation,
                }

            # Check if workflow completed after tool execution
            if "attempt_completion" in tool_msg.content:
                break

        # Build final result
        result = {
            "status": "success",
            "message": conversation[-1].content,
            "conversation": conversation,
        }

        return result

    @property
    def tool_str(self) -> str:
        return "\n\n".join([f"{tool}" for tool in self.tools.values()])

    async def _get_document_list(self) -> list:
        """Fetch all documents associated with this knowledge pack."""
        if not self.db:
            return []

        try:
            # Get associated document IDs
            doc_ids = await SQLDomainKnowledgeRepo.get_kp_associated_documents(kp_id=self.kp_id, db=self.db)

            if not doc_ids:
                return []

            # Fetch document details
            documents = await SQLDocumentRepo.get_document_by_ids(document_ids=doc_ids, db=self.db)

            return documents if documents else []
        except Exception as e:
            logger.error(f"Error fetching document list: {e}")
            return []

    def _build_document_context(self, documents: list) -> str:
        """
        Build document context string for prompt.
        If <=10 documents: Include IDs and names.
        If >10 documents: Include instruction to refuse list requests.
        """
        doc_count = len(documents)

        if doc_count == 0:
            return "**Available Documents**: No documents are currently associated with this knowledge pack."

        if doc_count <= 10:
            # Include document IDs and names
            doc_list = []
            for doc in documents:
                doc_list.append(f"- Document ID {doc.id}: {doc.original_filename}")

            doc_list_str = "\n".join(doc_list)
            return f"""**Available Documents** ({doc_count} document{'s' if doc_count > 1 else ''}):
{doc_list_str}

You can reference these documents by their IDs when users ask about specific documents."""
        else:
            # Too many documents - instruct to refuse list requests
            return f"""**Available Documents**: This knowledge pack contains {doc_count} documents.

**IMPORTANT**: If the user asks to "list all documents" or "show all documents", politely explain that there are too many documents ({doc_count}) to list individually. Instead, suggest they:
- Query for specific information using read_documents with a query
- Ask about a specific topic or document type
- Provide a document ID if they know which document they want to explore

Do NOT attempt to list all documents - use read_documents with a query to help them find what they need."""

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

        tool_str = self.tool_str

        # Fetch document list and build context
        documents = await self._get_document_list()
        document_context = self._build_document_context(documents)

        # Read custom system prompt if it exists
        custom_system_prompt = ""
        if self.template_path:
            try:
                from pathlib import Path

                template_folder = Path(self.template_path).parent
                system_prompt_file = template_folder / "system_prompt.prompt"
                if system_prompt_file.exists():
                    custom_system_prompt = system_prompt_file.read_text(encoding="utf-8")
                    logger.debug(f"Loaded custom system prompt from {system_prompt_file}")
            except Exception as e:
                logger.debug(f"Could not read system prompt file: {e}")

        # Build base system prompt with document context
        base_system_prompt = DOCUMENT_EXPLORATION_PROMPT.format(
            tools_str=tool_str, domain=self.domain, role=self.role, kp_id=self.kp_id, document_context=document_context
        )

        # Prepend custom system prompt if it exists
        if custom_system_prompt:
            system_prompt = f"<user_instructions>\n{custom_system_prompt}\n</user_instructions>\n\n{base_system_prompt}"
        else:
            system_prompt = base_system_prompt

        # Build messages array starting with system prompt
        messages = [{"role": "system", "content": system_prompt}]

        # Add template content as system message if template_path is available
        if self.template_path:
            try:
                with open(self.template_path, encoding="utf-8") as f:
                    template_content = f.read()
                template_message = (
                    f"Here is the current interview template, read and understand it : <template>\n{template_content}\n</template>"
                )
                messages.append({"role": "user", "content": template_message})
            except Exception as e:
                logger.debug(f"Could not read template file {self.template_path}: {e}")

        # Add conversation history
        messages.extend(llm_conversation)

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

            # Execute the tool with context
            tool = self.tools[tool_name]

            # Add context parameters (include db session only for tools that need it)
            context_params = {}
            if self.db and tool_name in ("read_documents",):
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


if __name__ == "__main__":
    import asyncio

    # Test with sample knowledge pack
    handler = DocumentExplorationHandler(
        kp_id=1,
        doc_paths=[
            "/Users/lam/Desktop/repos/opendxa/uploads/2024-SiemensHealthineers-AnnualFinStatements.pdf",
            "/Users/lam/Desktop/repos/opendxa/uploads/STD-ENG-015.pdf",
        ],
        domain="Food Manufacturing",
        role="Process Operator",
    )

    logger.debug("🎯 Document Exploration Handler - Interactive Testing Environment")
    logger.debug("=" * 70)
    logger.debug("Commands:")
    logger.debug("- Type any document exploration request to test the workflow")
    logger.debug("- Type 'quit' or 'exit' to quit")
    logger.debug("- Type 'reset' to clear conversation history")
    logger.debug("- Type 'history' to view conversation")
    logger.debug("- Type 'tools' to list available tools")
    logger.debug("=" * 70)

    chat_history = []

    logger.debug(handler.tool_str)

    while True:
        try:
            user_message = input(f"\n💬 User ({len(chat_history) // 2 + 1}): ").strip()

            if user_message.lower() in ["quit", "exit"]:
                logger.debug("👋 Goodbye!")
                break
            elif user_message.lower() == "reset":
                chat_history = []
                logger.debug("🗑️  Chat history cleared.")
                continue
            elif user_message.lower() == "history":
                if not chat_history:
                    logger.debug("📝 No conversation history yet.")
                else:
                    logger.debug(f"\n📝 Conversation History ({len(chat_history)} messages):")
                    for i, msg in enumerate(chat_history, 1):
                        role_emoji = "👤" if msg.role == "user" else "🤖"
                        logger.debug(
                            f"  {i:2}. {role_emoji} {msg.role.upper()}: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}"
                        )
                continue
            elif user_message.lower() == "tools":
                logger.debug(f"\n🛠️  Available Tools ({len(handler.tools)}):")
                for i, (name, tool) in enumerate(handler.tools.items(), 1):
                    logger.debug(
                        f"  {i:2}. {name}: {tool.tool_information.description[:80]}{'...' if len(tool.tool_information.description) > 80 else ''}"
                    )
                continue
            elif not user_message:
                continue

            chat_history.append(MessageData(role=SenderRole.USER, content=user_message))

            # Create request
            request = IntentDetectionRequest(user_message=user_message, chat_history=chat_history, current_domain_tree=None, agent_id=1)

            logger.debug(f"\n{'⚡' * 3} PROCESSING REQUEST {'⚡' * 3}")
            logger.debug(f"Request: {user_message}")

            # Run handler
            result = asyncio.run(handler.handle(request))

            # Display results
            logger.debug(f"\n{'📊' * 3} WORKFLOW RESULTS {'📊' * 3}")
            logger.debug(f"Status: {result['status']}")
            logger.debug(f"Message: {result['message']}")

            # Show conversation flow
            conversation = result["conversation"]
            logger.debug(f"\n{'💭' * 3} CONVERSATION FLOW ({len(conversation)} messages) {'💭' * 3}")

            for i, msg in enumerate(conversation, 1):
                role_emoji = "👤" if msg.role == "user" else "🤖"
                role_color = "\033[94m" if msg.role == "user" else "\033[92m"  # Blue for user, green for assistant
                reset_color = "\033[0m"

                logger.debug(f"\n{i:2}. {role_emoji} {role_color}{msg.role.upper()}{reset_color}:")

                # Handle tool calls vs regular messages
                if msg.role == "assistant" and ("<" in msg.content and ">" in msg.content):
                    # This looks like a tool call
                    if "<thinking>" in msg.content:
                        # Extract thinking for display
                        import re

                        thinking_match = re.search(r"<thinking>(.*?)</thinking>", msg.content, re.DOTALL)
                        if thinking_match:
                            thinking = thinking_match.group(1).strip()
                            logger.debug(f"    💭 Thinking: {thinking}")

                    # Extract tool name and arguments (skip thinking tags)
                    import re

                    tool_match = re.search(r"<(?!thinking)(\w+)", msg.content)
                    if tool_match:
                        tool_name = tool_match.group(1)
                        logger.debug(f"    🔧 Tool Call: {tool_name}")

                        # Extract and display tool arguments
                        try:
                            _, params, _ = handler._parse_xml_tool_call(msg.content)
                            if params:
                                logger.debug("    📝 Arguments:")
                                for key, value in params.items():
                                    if isinstance(value, list):
                                        logger.debug(f"      {key}: {value}")
                                    elif isinstance(value, str) and len(value) > 100:
                                        logger.debug(f"      {key}: {value[:100]}...")
                                    else:
                                        logger.debug(f"      {key}: {value}")
                        except Exception as e:
                            logger.debug(f"    ⚠️ Could not parse arguments: {e}")
                else:
                    # Regular message content
                    content_lines = msg.content.split("\n")
                    for line in content_lines[:5]:  # Show first 5 lines
                        if line.strip():
                            logger.debug(f"    {line}")

            # Update chat history for next iteration
            chat_history = conversation

            # Check if workflow is complete or needs user input
            if result["status"] == "user_input_required":
                logger.debug(f"\n{'⏸️' * 3} WORKFLOW PAUSED - USER INPUT REQUIRED {'⏸️' * 3}")
                logger.debug("The system is waiting for your response to continue.")
            elif result["status"] == "success":
                logger.debug(f"\n{'✅' * 3} WORKFLOW COMPLETED SUCCESSFULLY {'✅' * 3}")
                logger.debug("You can start a new document exploration request or type 'reset' to clear history.")

        except KeyboardInterrupt:
            logger.debug("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            logger.debug(f"\n❌ Error: {e}")
            import traceback

            logger.debug("Full traceback:")
            traceback.print_exc()
            logger.debug("\n💡 Continuing... (you can type 'reset' to clear state)")
