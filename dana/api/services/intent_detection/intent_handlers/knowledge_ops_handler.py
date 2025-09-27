from dana.api.services.intent_detection.intent_handlers.abstract_handler import AbstractHandler
from dana.api.services.intent_detection.intent_handlers.handler_prompts.knowledge_ops_prompts import TOOL_SELECTION_PROMPT
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc
from dana.api.core.schemas import DomainKnowledgeTree, IntentDetectionRequest, DomainNode, MessageData
from typing import Any, Literal, Awaitable, Callable
from dana.api.services.intent_detection.intent_handlers.handler_tools.knowledge_ops_tools import (
    AskQuestionTool,
    ExploreKnowledgeTool,
    ModifyTreeTool,
    AttemptCompletionTool,
    ProposeKnowledgeStructureTool,
    RefineKnowledgeStructureTool,
    PreviewKnowledgeTopicTool,
    GenerateKnowledgeFromDocTool,
)
from dana.api.services.intent_detection.intent_handlers.handler_utility import knowledge_ops_utils as ko_utils
import logging
import re
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class KnowledgeOpsHandler(AbstractHandler):
    """
    Stateless knowledge generation handler using conversation history as state.

    Flow:
    1. Each tool result is added as assistant message
    2. LLM reads full conversation to decide next action
    3. No complex state management needed
    4. Human approval happens via conversation
    """

    def __init__(
        self,
        domain_knowledge_path: str,
        llm: LLMResource | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
        tasks: list[str] | None = None,
        knowledge_status_path: str | None = None,
        notifier: Callable[[str, str, Literal["init", "in_progress", "finish", "error"], float | None], Awaitable[None]] | None = None,
    ):
        from pathlib import Path

        base_path = Path(domain_knowledge_path).parent

        self.domain_knowledge_path = domain_knowledge_path
        # Default knowledge_status_path to same directory as domain_knowledge if not provided
        self.knowledge_status_path = knowledge_status_path or os.path.join(str(base_path), "knowledge_status.json")
        # Derive storage path from domain_knowledge_path parent directory
        self.storage_path = os.path.join(str(base_path), "knows")
        self.document_path = os.path.join(str(base_path), "docs")
        self.domain = domain
        self.role = role
        self.tasks = tasks or ["Analyze Information", "Provide Insights", "Answer Questions"]
        self.llm = llm or LLMResource()
        self.tree_structure = self._load_tree_structure(domain_knowledge_path)
        self.tools = {}
        self.notifier = notifier
        self._initialize_tools()

    def _load_tree_structure(self, domain_knowledge_path: str | None = None):
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

        # Generation tool (unified) with persistence
        self.tools.update(
            GenerateKnowledgeFromDocTool(
                knowledge_status_path=self.knowledge_status_path,
                storage_path=self.storage_path,
                tree_structure=self.tree_structure,
                domain=self.domain,
                role=self.role,
                tasks=self.tasks,
                notifier=self.notifier,
                document_path=self.document_path,
            ).as_dict()
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

    async def handle(self, request: IntentDetectionRequest) -> dict[str, Any]:
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
        conversation = request.chat_history  # TODO : IMPROVE MANAGING CONVERSATION HISTORY

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
                conversation.append(MessageData(role="user", content=f"Error: {e}"))
                if self.notifier and init:
                    await self.notifier(tool_name, f"Error: {e}", "error", None)
                continue

            # Check if complete
            if isinstance(tool_msg, MessageData) and tool_msg.content.strip().lower() == "complete":
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

        return MessageData(role="assistant", content=tool_call, treat_as_tool=True)

    async def _execute_tool(self, tool_name: str, params: dict, thinking_content: str) -> MessageData:
        """
        Execute the tool and return the result.
        """
        try:
            # Log thinking content for debugging
            if thinking_content:
                logger.debug(f"LLM thinking: {thinking_content}")

            # Guard against using modify_tree without exploration
            # if tool_name == "modify_tree" and conversation:
            #     # Check if explore_knowledge was used in this conversation
            #     # Look through the conversation history for exploration
            #     exploration_found = False
            #     for msg in conversation:
            #         if msg.role == "assistant" and "explore_knowledge" in msg.content:
            #             exploration_found = True
            #             break

            #     if not exploration_found:
            #         return MessageData(
            #             role="user",
            #             content="⚠️ Error: You must use explore_knowledge before modify_tree to understand the current tree structure. Please explore the tree first to see what nodes exist and their exact paths.",
            #         )

            # Check if tool exists
            if tool_name not in self.tools:
                error_msg = f"Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"
                logger.error(error_msg)
                return MessageData(role="user", content=f"Error calling tool `{tool_name}`: {error_msg}")

            # Execute the tool
            tool = self.tools[tool_name]
            result = await tool.execute(**params)

            # Convert ToolResult to MessageData
            content = result.result
            if tool_name in ("attempt_completion", "ask_question"):
                content = f"{content}"
            message_data = MessageData(role="user", content=content, require_user=result.require_user, treat_as_tool=True)

            # If this was a modify_tree operation, reload the tree structure
            if tool_name == "modify_tree":
                self._reload_tree_structure()

            return message_data

        except Exception as e:
            error_msg = f"Failed to execute tool: {str(e)}"
            logger.error(error_msg)
            return MessageData(role="user", content=f"Error: {error_msg}")


if __name__ == "__main__":
    import asyncio
    from dana.api.core.schemas import MessageData

    # Test with financial statement analysis agent path
    handler = KnowledgeOpsHandler(
        domain_knowledge_path="/Users/lam/Desktop/repos/opendxa/agents/financial_stmt_analysis/test_new_knows/domain_knowledge.json",
        domain="Financial Statement Analysis",
        role="Senior Financial Analyst",
        tasks=[
            "Analyze Financial Statements",
            "Provide Financial Insights",
            "Answer Financial Questions",
            "Forecast Financial Performance",
        ],
    )
    chat_history = []

    print("🔧 Knowledge Ops Handler - Interactive Testing Environment")
    print("=" * 70)
    print("Commands:")
    print("- Type any knowledge request to test the workflow")
    print("- Type 'quit' or 'exit' to quit")
    print("- Type 'reset' to clear conversation history")
    print("- Type 'history' to view conversation")
    print("- Type 'tools' to list available tools")
    print("=" * 70)

    while True:
        try:
            user_message = input(f"\n💬 User ({len(chat_history) // 2 + 1}): ").strip()

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

            if result.get("final_result"):
                final = result["final_result"]
                print(f"Artifacts: {final.get('artifacts', 'N/A')}")
                print(f"Types: {final.get('types', 'N/A')}")

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
                        import re

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
                print("You can start a new knowledge request or type 'reset' to clear history.")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            print("Full traceback:")
            traceback.print_exc()
            print("\n💡 Continuing... (you can type 'reset' to clear state)")
