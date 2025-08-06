from dana.api.services.intent_detection.intent_handlers.abstract_handler import AbstractHandler
from dana.api.services.intent_detection.intent_handlers.handler_prompts.knowledge_ops_prompts import TOOL_SELECTION_PROMPT
from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.resource.rag.knowledge_resource import KnowledgeResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc
from dana.api.core.schemas import DomainKnowledgeTree, IntentDetectionRequest, DomainNode, MessageData
from typing import Dict, Any, List, Optional
from dana.api.services.intent_detection.intent_handlers.handler_tools.knowledge_ops_tools import AskFollowUpQuestionTool, NavigateTreeTool
import logging
import re
import json
from xml.etree import ElementTree as ET

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

    def __init__(self, llm: LLMResource | None = None, tree_structure: DomainKnowledgeTree | None = None):
        self.llm = llm or LLMResource()
        self.tree_structure = tree_structure
        self.tools = {}
        self._initialize_tools()

    def _initialize_tools(self):
        self.tools.update(AskFollowUpQuestionTool().as_dict())
        self.tools.update(NavigateTreeTool(llm=self.llm, tree_structure=self.tree_structure).as_dict())

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

            # The tool already returns a MessageData object
            return result

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

    handler = KnowledgeOpsHandler()
    chat_history = []
    init = True

    print("Testing Knowledge Ops Handler - Interactive Mode")
    print("=" * 60)
    print("Commands:")
    print("- Type any knowledge request to test")
    print("- Type 'quit' to exit")
    print("- Type 'reset' to clear conversation history")
    print("=" * 60)

    while True:
        try:
            if init:
                user_message = "Add knowledge about current ratio analysis for financial analysts"
                print(f"\nInitial test message: {user_message}")
                init = False
            else:
                user_message = input("\nUser: ").strip()

            if user_message.lower() == "quit":
                break
            elif user_message.lower() == "reset":
                chat_history = []
                print("Chat history cleared.")
                continue
            elif not user_message:
                continue

            # Create request
            request = IntentDetectionRequest(user_message=user_message, chat_history=chat_history, current_domain_tree=None, agent_id=1)

            print(f"\n{'='*20} PROCESSING {'='*20}")

            # Run handler
            result = asyncio.run(handler.handle(request))

            # Update chat history for next iteration
            chat_history = result["conversation"]

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Continuing...")
