from dana.api.services.intent_detection.intent_handlers.abstract_handler import AbstractHandler
from dana.api.services.intent_detection.intent_handlers.handler_prompts.knowledge_ops_prompts import (
    TOOL_SELECTION_PROMPT,
    TREE_NAVIGATION_PROMPT,
    FOLLOW_UP_QUESTION_PROMPT,
)
from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.resource.rag.knowledge_resource import KnowledgeResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc
from dana.api.core.schemas import DomainKnowledgeTree, IntentDetectionRequest, DomainNode, MessageData
from typing import Dict, Any, List, Optional
from dana.api.services.intent_detection.intent_handlers.handler_tools.knowledge_ops_tools import AskFollowUpQuestionTool
import logging

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

    AVAILABLE_TOOLS = [
        "navigate_tree",
        "ask_follow_up_question",
        "create_plan",
        "ask_approval",
        "check_existing",
        "generate_facts",
        "generate_plans",
        "generate_heuristics",
        "validate",
        "persist",
    ]

    def __init__(self, llm: LLMResource | None = None, tree_structure: DomainKnowledgeTree | None = None):
        self.llm = llm or LLMResource()
        self.tree_structure = tree_structure

    def _initialize_tools(self):
        self.tools = {}
        self.tools.update(AskFollowUpQuestionTool().as_dict())

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
            next_tool = await self._determine_next_tool(conversation, request)

            if next_tool == "complete":
                break

            # Validate tool exists
            valid_tools = self.AVAILABLE_TOOLS + ["complete"]
            if next_tool not in valid_tools:
                # Add error message to conversation and let LLM decide what to do next
                error_msg = f"ERROR: Tool '{next_tool}' does not exist. Available tools: {', '.join(self.AVAILABLE_TOOLS)}. Please choose a valid tool."
                conversation.append(MessageData(role="assistant", content=error_msg))
                logger.warning(f"Invalid tool '{next_tool}' suggested, added error to conversation")
                continue

            # Add tool call as assistant message
            conversation.append(MessageData(role="assistant", content=f"I'll use the {next_tool} tool."))

            # Execute tool and add result as user message
            tool_result = await self._execute_tool(next_tool, conversation, request)
            conversation.append(MessageData(role="user", content=f"[{next_tool}] {tool_result}"))

        # Mock final result
        return {
            "status": "success",
            "message": "Successfully generated and stored 10 knowledge artifacts",
            "conversation": conversation,
            "final_result": {"artifacts": 10, "types": ["facts", "plans", "heuristics"]},
        }

    async def _determine_next_tool(self, conversation: List[MessageData], request: IntentDetectionRequest) -> str:
        """
        LLM decides next tool based purely on conversation history.

        Returns tool name or "complete"
        """
        # Convert conversation to string
        conv_str = "\n".join([f"{msg.role}: {msg.content}" for msg in conversation])

        system_prompt = TOOL_SELECTION_PROMPT

        llm_request = BaseRequest(
            arguments={
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Conversation:\n{conv_str}\n\nWhat tool should I use next?"},
                ],
                "temperature": 0.1,
                "max_tokens": 50,
            }
        )

        response = await self.llm.query(llm_request)
        tool_name = Misc.get_response_content(response).strip().lower()

        return tool_name

    async def _execute_tool(self, tool_name: str, conversation: List[MessageData], request: IntentDetectionRequest) -> str:
        """
        Execute tool and return result as string.
        All results are human-readable for conversation.
        """
        if tool_name == "navigate_tree":
            return await self._navigate_tree(conversation, request)
        elif tool_name == "ask_follow_up_question":
            return await self._ask_follow_up_question(conversation, request)
        elif tool_name == "create_plan":
            return await self._create_plan(conversation, request)
        elif tool_name == "ask_approval":
            return await self._ask_approval(conversation, request)
        elif tool_name == "check_existing":
            return await self._check_existing(conversation, request)
        elif tool_name == "generate_facts":
            return await self._generate_facts(conversation, request)
        elif tool_name == "generate_plans":
            return await self._generate_plans(conversation, request)
        elif tool_name == "generate_heuristics":
            return await self._generate_heuristics(conversation, request)
        elif tool_name == "validate":
            return await self._validate(conversation, request)
        elif tool_name == "persist":
            return await self._persist(conversation, request)
        else:
            return f"Unknown tool: {tool_name}"

    async def _navigate_tree(self, conversation: List[MessageData], request: IntentDetectionRequest) -> str:
        """
        Navigate knowledge tree to target location by extracting topic from user request.

        Returns: "Tree Navigation: Located path 'Domain > Subdomain > Topic'. Node status."
        """
        # Extract the original user message (first user message in conversation)
        user_message = request.user_message
        for msg in conversation:
            if msg.role == "user" and not msg.content.startswith("["):
                user_message = msg.content
                break

        # Use LLM to extract hierarchical topic structure
        prompt = TREE_NAVIGATION_PROMPT.format(user_message=user_message)

        llm_request = BaseRequest(arguments={"messages": [{"role": "user", "content": prompt}], "temperature": 0.1, "max_tokens": 200})

        try:
            response = await self.llm.query(llm_request)
            result = Misc.text_to_dict(Misc.get_response_content(response))

            path = result.get("path", ["General", "Unknown", "Topic"])
            reasoning = result.get("reasoning", "")

            # TODO: In real implementation, would check/create nodes in actual tree structure
            # For now, simulate tree navigation
            path_str = " > ".join(path)

            return f"Tree Navigation: Located path '{path_str}'. Reasoning: {reasoning}. Node ready for knowledge addition."

        except Exception as e:
            logger.error(f"Failed to navigate tree: {e}")
            # Fallback path extraction
            return f"Tree Navigation: Located path 'General > Knowledge > {user_message[:50]}'. Fallback navigation used."

    async def _ask_follow_up_question(self, conversation: List[MessageData], request: IntentDetectionRequest) -> str:
        """
        Ask user for clarification when request is ambiguous.

        Returns: "Follow-up Question: [question text]"
        """
        # Extract the original user message
        user_message = request.user_message
        for msg in conversation:
            if msg.role == "user" and not msg.content.startswith("["):
                user_message = msg.content
                break

        # Use LLM to identify what clarification is needed
        prompt = FOLLOW_UP_QUESTION_PROMPT.format(user_message=user_message)

        llm_request = BaseRequest(arguments={"messages": [{"role": "user", "content": prompt}], "temperature": 0.1, "max_tokens": 100})

        try:
            response = await self.llm.query(llm_request)
            question = Misc.get_response_content(response).strip()

            return f"Follow-up Question: {question}"

        except Exception as e:
            logger.error(f"Failed to generate follow-up question: {e}")
            return f"Follow-up Question: Could you provide more specific details about '{user_message}'?"

    async def _create_plan(self, conversation: List[MessageData], request: IntentDetectionRequest) -> str:
        """
        Create generation plan based on conversation context.

        Mock return: Multi-line plan showing what will be generated with counts and examples.
        """
        return """Generation Plan:
📁 Current Ratio Knowledge
├── 📄 Facts (5): Definitions, formulas, interpretations  
│   └── Example: "Current ratio = Current Assets / Current Liabilities"
├── 📋 Plans (2): Calculation procedures, analysis workflows
│   └── Example: "Step-by-step ratio calculation process"
└── 💡 Heuristics (3): Industry benchmarks, warning signs
    └── Example: "Ratio < 1.0 indicates potential liquidity risk"

Estimated time: ~2 minutes
Total artifacts: 10"""

    async def _ask_approval(self, conversation: List[MessageData], request: IntentDetectionRequest) -> str:
        """
        Ask user for approval (this is our human-in-the-loop point).

        Mock return: "User Approval: APPROVED. Proceeding with plan as presented."
        """
        return "User Approval: APPROVED. Proceeding with plan as presented."

    async def _check_existing(self, conversation: List[MessageData], request: IntentDetectionRequest) -> str:
        """
        Check for existing knowledge to avoid duplicates.

        Mock return: "Existing Check: No duplicate knowledge found at target location. Safe to proceed."
        """
        return "Existing Check: No duplicate knowledge found at target location. Safe to proceed."

    async def _generate_facts(self, conversation: List[MessageData], request: IntentDetectionRequest) -> str:
        """
        Generate factual knowledge.

        Mock return: Summary of generated facts.
        """
        return """Generated Facts (5):
• Current ratio measures ability to pay short-term obligations
• Formula: Current Assets ÷ Current Liabilities  
• Ratio of 1.0 means assets equal liabilities
• Current assets include cash, receivables, inventory
• Current liabilities include payables, short-term debt"""

    async def _generate_plans(self, conversation: List[MessageData], request: IntentDetectionRequest) -> str:
        """
        Generate procedural knowledge.

        Mock return: Summary of generated procedures.
        """
        return """Generated Plans (2):
• "Calculate Current Ratio": 5-step process from balance sheet to interpretation
• "Analyze Ratio Trends": Multi-period analysis with benchmarking"""

    async def _generate_heuristics(self, conversation: List[MessageData], request: IntentDetectionRequest) -> str:
        """
        Generate best practices and heuristics.

        Mock return: Summary of generated heuristics.
        """
        return """Generated Heuristics (3):
• Ratio < 1.0 indicates liquidity risk (with industry exceptions)
• Ratio > 3.0 may indicate inefficient asset use (seasonal exceptions)
• Always compare to industry averages, not absolute values"""

    async def _validate(self, conversation: List[MessageData], request: IntentDetectionRequest) -> str:
        """
        Validate all generated knowledge.

        Mock return: "Validation: All 10 artifacts validated. Accuracy score: 95%. No gaps identified."
        """
        return "Validation: All 10 artifacts validated. Accuracy score: 95%. No gaps identified."

    async def _persist(self, conversation: List[MessageData], request: IntentDetectionRequest) -> str:
        """
        Persist all knowledge to vector DB.

        Mock return: "Persistence: Successfully stored 10 knowledge artifacts to vector DB for agent 123."
        """
        return f"Persistence: Successfully stored 10 knowledge artifacts to vector DB for agent {request.agent_id}."


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

            print(f"\n{'='*20} RESULTS {'='*20}")
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            print(f"Entities: {result['entities']}")
            print(f"Summary: {result['knowledge_summary']}")

            print(f"\n{'='*20} CONVERSATION FLOW {'='*20}")
            for i, msg in enumerate(result["conversation"], 1):
                role_display = msg.role.upper().ljust(9)
                content_preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
                print(f"{i:2}. {role_display}: {content_preview}")

            print(f"\n{'='*20} READY FOR NEXT INPUT {'='*20}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Continuing...")
