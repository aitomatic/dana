from dana.api.services.intent_detection.intent_handlers.abstract_handler import AbstractHandler
from dana.api.services.intent_detection.intent_handlers.handler_prompts.knowledge_ops_prompts import TOOL_SELECTION_PROMPT
from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.resource.rag.knowledge_resource import KnowledgeResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc
from dana.api.core.schemas import DomainKnowledgeTree, IntentDetectionRequest, DomainNode, MessageData
from typing import Dict, Any, List, Optional
from dana.api.services.intent_detection.intent_handlers.handler_tools.knowledge_ops_tools import (
    AskFollowUpQuestionTool, NavigateTreeTool, CreatePlanTool, AskApprovalTool,
    GenerateKnowledgeTool, ModifyTreeTool, ValidateTool, PersistTool, 
    CheckExistingTool, AttemptCompletionTool
)
from dana.api.services.intent_detection.intent_handlers.handler_utility import knowledge_ops_utils as ko_utils
import logging
import re
import json
from xml.etree import ElementTree as ET
from pathlib import Path

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

    def __init__(self, 
                 domain_knowledge_path: str, 
                 llm: LLMResource | None = None,  
                 domain : str = "General",
                 role : str = "Domain Expert"):
        self.domain_knowledge_path = domain_knowledge_path
        self.domain = domain
        self.role = role
        self.llm = llm or LLMResource()
        self.tree_structure = self._load_tree_structure(domain_knowledge_path)
        self.tools = {}
        self._initialize_tools()

    def _load_tree_structure(self, domain_knowledge_path : str | None = None):
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
            
            # Update the NavigateTreeTool with the new tree structure
            if "navigate_tree" in self.tools:
                self.tools["navigate_tree"].tree_structure = self.tree_structure
        except Exception as e:
            logger.error(f"Failed to reload tree structure: {e}")

    def _initialize_tools(self):
        # Core workflow tools
        self.tools.update(AskFollowUpQuestionTool().as_dict())
        self.tools.update(NavigateTreeTool(llm=self.llm, tree_structure=self.tree_structure).as_dict())
        self.tools.update(CreatePlanTool(llm=self.llm).as_dict())
        self.tools.update(AskApprovalTool().as_dict())
        
        # Generation tool (unified)
        self.tools.update(GenerateKnowledgeTool(llm=self.llm).as_dict())
        
        # Tree management
        self.tools.update(ModifyTreeTool(tree_structure=self.tree_structure, domain_knowledge_path=self.domain_knowledge_path).as_dict())
        
        # Quality and completion tools
        self.tools.update(ValidateTool(llm=self.llm).as_dict())
        self.tools.update(PersistTool().as_dict())
        self.tools.update(CheckExistingTool().as_dict())
        self.tools.update(AttemptCompletionTool().as_dict())

    async def handle(self, request: IntentDetectionRequest) -> Dict[str, Any]:
        """
        Main stateless handler - runs tool loop until completion.

        Mock return:
        {
            "status": "success",
            "message": "Generated 10 knowledge artifacts",
            "conversation": [...],  # Full conversation with all tool results
            "final_result": {...}
        }
        """
        # Initialize conversation with user request
        conversation = request.chat_history + [MessageData(role="user", content=request.user_message)]

        # Tool loop - max 15 iterations
        for iteration in range(15):
            # Determine next tool from conversation
            tool_msg = await self._determine_next_tool(conversation)

            # Check if complete
            if isinstance(tool_msg, MessageData) and tool_msg.content.strip().lower() == "complete":
                break

            # Add tool call to conversation
            conversation.append(tool_msg)

            # Execute tool and get result
            tool_result_msg = await self._execute_tool(tool_msg)

            if tool_result_msg.require_user:
                return {
                    "status": "user_input_required",
                    "message": "User input required",
                    "conversation": conversation,
                    "final_result": None,
                }

            # Add result to conversation
            conversation.append(tool_result_msg)
        # Mock final result
        return {
            "status": "success",
            "message": "Successfully generated and stored 10 knowledge artifacts",
            "conversation": conversation,
            "final_result": {"artifacts": 10, "types": ["facts", "plans", "heuristics"]},
        }

    async def _determine_next_tool(self, conversation: List[MessageData]) -> MessageData:
        """
        LLM decides next tool based purely on conversation history.

        Returns MessageData with tool call XML or "complete"
        """
        # Convert conversation to string
        llm_conversation = []
        for message in conversation:
            llm_conversation.append({"role": message.role, "content": message.content})

        tool_str = "\n\n".join([f"{tool}" for tool in self.tools.values()])

        system_prompt = TOOL_SELECTION_PROMPT.format(tools_str=tool_str)

        llm_request = BaseRequest(
            arguments={
                "messages": [
                    {"role": "system", "content": system_prompt},
                ]
                + llm_conversation,
                "temperature": 0.1,
                "max_tokens": 500,
            }
        )

        response = await self.llm.query(llm_request)
        tool_call = Misc.get_response_content(response).strip()

        return MessageData(role="assistant", content=tool_call)

    async def _execute_tool(self, tool_msg: MessageData) -> MessageData:
        """
        Execute the tool and return the result.
        """
        content = tool_msg.content

        try:
            # Extract tool name, parameters, and thinking from XML
            tool_name, params, thinking_content = self._parse_xml_tool_call(content)

            # Log thinking content for debugging
            if thinking_content:
                logger.debug(f"LLM thinking: {thinking_content}")

            # Check if tool exists
            if tool_name not in self.tools:
                error_msg = f"Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"
                logger.error(error_msg)
                return MessageData(role="user", content=f"Error: {error_msg}")

            # Execute the tool
            tool = self.tools[tool_name]
            result = tool.execute(**params)

            # Convert ToolResult to MessageData
            message_data = MessageData(
                role="user", 
                content=result.result, 
                require_user=result.require_user
            )
            
            # If this was a modify_tree operation, reload the tree structure
            if tool_name == "modify_tree" and "Tree Structure" in result.result:
                self._reload_tree_structure()
            
            return message_data

        except Exception as e:
            error_msg = f"Failed to execute tool: {str(e)}"
            logger.error(error_msg)
            return MessageData(role="user", content=f"Error: {error_msg}")

    def _parse_xml_tool_call(self, xml_content: str) -> tuple[str, dict, str]:
        """
        Parse XML tool call to extract tool name, parameters, and thinking content.

        Example input:
        <thinking>...</thinking>
        <ask_follow_up_question>
        <question>What type of ratios?</question>
        <options>
          <option>financial</option>
          <option>mathematical</option>
        </options>
        </ask_follow_up_question>

        Returns: ("ask_follow_up_question", {"question": "...", "options": [...]}, "thinking content")
        """
        # Clean up the content - remove any extra whitespace
        xml_content = xml_content.strip()

        # Extract thinking content if present
        thinking_match = re.search(r"<thinking>(.*?)</thinking>", xml_content, flags=re.DOTALL)
        thinking_content = thinking_match.group(1).strip() if thinking_match else ""

        # Remove thinking tags for tool parsing
        xml_without_thinking = re.sub(r"<thinking>.*?</thinking>\s*", "", xml_content, flags=re.DOTALL)

        # Extract tool name - look for the first tag that's not 'thinking'
        tool_match = re.search(r"<(\w+)(?:\s[^>]*)?>(?!.*<thinking>)", xml_without_thinking)
        if not tool_match:
            raise ValueError(f"Could not find tool name in XML: {xml_content}")

        tool_name = tool_match.group(1)

        # Extract just the tool XML block
        tool_pattern = rf"<{tool_name}.*?>(.*?)</{tool_name}>"
        tool_content_match = re.search(tool_pattern, xml_without_thinking, re.DOTALL)
        if not tool_content_match:
            raise ValueError(f"Could not extract tool content for {tool_name}")

        tool_xml = tool_content_match.group(0)

        # Parse the XML
        try:
            root = ET.fromstring(tool_xml)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML format: {e}")

        # Extract parameters recursively
        params = self._extract_params_from_element(root)

        return tool_name, params, thinking_content

    def _extract_params_from_element(self, element) -> dict:
        """
        Recursively extract parameters from XML element.
        Handles nested structures like <options><option>...</option></options>
        """
        params = {}

        for child in element:
            param_name = child.tag

            # Check if this element has children
            if len(child) > 0:
                # Handle nested elements
                if param_name == "options":
                    # Special case for options - extract as list
                    options = []
                    for option in child:
                        if option.text:
                            options.append(option.text.strip())
                    params[param_name] = options
                else:
                    # Recursively extract nested params
                    params[param_name] = self._extract_params_from_element(child)
            else:
                # Simple text value
                param_value = child.text
                if param_value:
                    param_value = param_value.strip()

                    # Handle JSON lists
                    if param_value.startswith("[") and param_value.endswith("]"):
                        try:
                            param_value = json.loads(param_value)
                        except Exception as _:
                            pass

                params[param_name] = param_value

        return params


if __name__ == "__main__":
    import asyncio
    from dana.api.core.schemas import MessageData

    handler = KnowledgeOpsHandler(domain_knowledge_path="/Users/lam/Desktop/repos/opendxa/agents/financial_stmt_analysis/test_new_knows/domain_knowledge.json")
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
            user_message = input(f"\n💬 User ({len(chat_history)//2 + 1}): ").strip()

            if user_message.lower() in ['quit', 'exit']:
                print("👋 Goodbye!")
                break
            elif user_message.lower() == 'reset':
                chat_history = []
                print("🗑️  Chat history cleared.")
                continue
            elif user_message.lower() == 'history':
                if not chat_history:
                    print("📝 No conversation history yet.")
                else:
                    print(f"\n📝 Conversation History ({len(chat_history)} messages):")
                    for i, msg in enumerate(chat_history, 1):
                        role_emoji = "👤" if msg.role == "user" else "🤖"
                        print(f"  {i:2}. {role_emoji} {msg.role.upper()}: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
                continue
            elif user_message.lower() == 'tools':
                print(f"\n🛠️  Available Tools ({len(handler.tools)}):")
                for i, (name, tool) in enumerate(handler.tools.items(), 1):
                    print(f"  {i:2}. {name}: {tool.tool_information.description[:80]}{'...' if len(tool.tool_information.description) > 80 else ''}")
                continue
            elif not user_message:
                continue

            # Create request
            request = IntentDetectionRequest(
                user_message=user_message, 
                chat_history=chat_history, 
                current_domain_tree=None, 
                agent_id=1
            )

            print(f"\n{'⚡'*3} PROCESSING REQUEST {'⚡'*3}")
            print(f"Request: {user_message}")

            # Run handler
            result = asyncio.run(handler.handle(request))

            # Display results
            print(f"\n{'📊'*3} WORKFLOW RESULTS {'📊'*3}")
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            
            if result.get('final_result'):
                final = result['final_result']
                print(f"Artifacts: {final.get('artifacts', 'N/A')}")
                print(f"Types: {final.get('types', 'N/A')}")

            # Show conversation flow
            conversation = result['conversation']
            print(f"\n{'💭'*3} CONVERSATION FLOW ({len(conversation)} messages) {'💭'*3}")
            
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
                        thinking_match = re.search(r'<thinking>(.*?)</thinking>', msg.content, re.DOTALL)
                        if thinking_match:
                            thinking = thinking_match.group(1).strip()
                            print(f"    💭 Thinking: {thinking[:100]}{'...' if len(thinking) > 100 else ''}")
                    
                    # Extract tool name
                    tool_match = re.search(r'<(\w+)', msg.content)
                    if tool_match:
                        tool_name = tool_match.group(1)
                        print(f"    🔧 Tool Call: {tool_name}")
                else:
                    # Regular message content
                    content_lines = msg.content.split('\n')
                    for line in content_lines:  # Show first 5 lines
                        if line.strip():
                            print(f"    {line}")

            # Update chat history for next iteration
            chat_history = conversation
            
            # Check if workflow is complete or needs user input
            if result['status'] == 'user_input_required':
                print(f"\n{'⏸️'*3} WORKFLOW PAUSED - USER INPUT REQUIRED {'⏸️'*3}")
                print("The system is waiting for your response to continue.")
            elif result['status'] == 'success':
                print(f"\n{'✅'*3} WORKFLOW COMPLETED SUCCESSFULLY {'✅'*3}")
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
