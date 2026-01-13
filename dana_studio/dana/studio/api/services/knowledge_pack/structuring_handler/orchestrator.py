from dana.studio.api.services.intent_detection.intent_handlers.abstract_handler import AbstractHandler
from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.knowledge_ops_tools import (
    AskQuestionTool,
    ExploreKnowledgeTool,
    ModifyTreeTool,
    ProposeKnowledgeStructureTool,
    RefineKnowledgeStructureTool,
    PreviewKnowledgeTopicTool,
)
from dana.studio.api.services.knowledge_pack.structuring_handler.tools.attempt_completion_tool import AttemptCompletionTool
from dana.studio.api.services.knowledge_pack.config import MAX_CONCURRENT
from dana.studio.api.core.schemas_v2 import HandlerConversation, HandlerMessage, SenderRole
from dana.studio.api.core.schemas import DomainKnowledgeTree, DomainNode
from dana.studio.api.services.intent_detection.intent_handlers.handler_utility import knowledge_ops_utils as ko_utils
from pathlib import Path
from dana.lang.common.utils.misc import Misc
import logging
from dana.studio.api.services.knowledge_pack.structuring_handler.prompts import TOOL_SELECTION_PROMPT
from dana.lang.common.types import BaseRequest
from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
import os
from typing import Any
from dana.studio.api.routers.v2.ws.domain_knowledge_ws import (
    DomainKnowledgeWSManager,
    kp_question_generation_ws_notifier,
    kp_structuring_ws_notifier,
)
from dana.studio.api.repositories.config import KNOW_FOLDER_NAME

logger = logging.getLogger(__name__)


class KPStructuringOrchestrator(AbstractHandler):
    def __init__(
        self,
        domain_knowledge_path: str,
        knowledge_status_path: str | None = None,
        llm: LLMResource | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
        tasks: list[str] | None = None,
        knowledge_id: int | None = None,
        ws_manager: DomainKnowledgeWSManager = kp_structuring_ws_notifier,
        **kwargs,
    ):
        base_path = Path(domain_knowledge_path).parent
        self.domain_knowledge_path = domain_knowledge_path
        self.knowledge_status_path = knowledge_status_path or os.path.join(str(base_path), "knowledge_status.json")
        self.llm = llm or LLMResource()
        self.domain = domain
        self.role = role
        self.tasks = tasks or ["Analyze Information", "Provide Insights", "Answer Questions"]
        self.storage_path = os.path.join(str(base_path), KNOW_FOLDER_NAME)
        self.document_path = os.path.join(str(base_path), "docs")
        self.knowledge_id = knowledge_id
        self.notifier = ws_manager.get_notifier(str(knowledge_id)) if knowledge_id else None
        self.tree_structure = self._load_tree_structure(domain_knowledge_path)
        self.tools = {}
        self._initialize_tools()

    async def _notify(self, tool_name: str, content: str, status: str, progression: float | None = None) -> None:
        """Send a notification message to the frontend."""
        if not self.notifier:
            return

        message = {
            "tool_name": tool_name,
            "content": content,
            "status": status,
            "progression": progression,
        }

        await self.notifier(message)

    def _load_tree_structure(self, domain_knowledge_path):
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
        except Exception as e:
            logger.error(f"Failed to reload tree structure: {e}")

    def _initialize_tools(self):
        # Core workflow tools
        self.tools.update(AskQuestionTool().as_dict())  # Unified tool for questions and approvals
        self.tools.update(
            ExploreKnowledgeTool(tree_structure=self.tree_structure, knowledge_status_path=self.knowledge_status_path).as_dict()
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
            ).as_dict()
        )

        # Question bank generation tool
        from dana.studio.api.services.knowledge_pack.structuring_handler.tools.question_bank_generation_tool import (
            QuestionBankGenerationTool,
        )

        self.tools.update(
            QuestionBankGenerationTool(
                knowledge_id=self.knowledge_id or 0,
                knowledge_status_path=self.knowledge_status_path,
                storage_path=self.storage_path,
                tree_structure_path=self.domain_knowledge_path,
                domain=self.domain,
                role=self.role,
                tasks=self.tasks,
                max_concurrent=MAX_CONCURRENT,
                ws_manager=kp_question_generation_ws_notifier,
            ).as_dict()
        )

        # Quality and completion tools
        self.tools.update(AttemptCompletionTool().as_dict())

    async def handle(self, request: HandlerConversation) -> dict[str, Any]:
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
        conversation = request.messages  # TODO : IMPROVE MANAGING CONVERSATION HISTORY

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
                await self._notify(tool_name, thinking_content, "init", None)
                init = True
                tool_result_msg = await self._execute_tool(tool_name, params, thinking_content)
                await self._notify(tool_name, tool_result_msg.content, "finish", 1.0)
                init = False
            except Exception as e:
                conversation.append(HandlerMessage(sender=SenderRole.USER, content=f"Error: {e}", treat_as_tool=True))
                if init:
                    await self._notify(tool_name, f"Error: {e}", "error", None)
                continue

            # Check if complete
            if isinstance(tool_msg, HandlerMessage) and tool_msg.content.strip().lower() == "complete":
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

    async def _determine_next_tool(self, conversation: list[HandlerMessage]) -> HandlerMessage:
        """
        LLM decides next tool based purely on conversation history.

        Returns HandlerMessage with tool call XML or "complete"
        """
        # Convert conversation to string
        llm_conversation = []
        for message in conversation:
            if message.sender == "agent":
                message.sender = "assistant"
            llm_conversation.append({"role": message.sender, "content": message.content})

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

        return HandlerMessage(role="assistant", content=tool_call, treat_as_tool=True)

    async def _execute_tool(self, tool_name: str, params: dict, thinking_content: str) -> HandlerMessage:
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
                return HandlerMessage(role="user", content=f"Error calling tool `{tool_name}`: {error_msg}")

            # Execute the tool
            tool = self.tools[tool_name]
            result = await tool.execute(**params)

            # Convert ToolResult to HandlerMessage
            content = result.result
            if tool_name in ("attempt_completion", "ask_question"):
                content = f"{content}"

            if result.require_user:
                role = SenderRole.ASSISTANT  # Assistant will ask for user input
            else:
                role = SenderRole.USER  # User will provide tool result
            message_data = HandlerMessage(role=role, content=content, require_user=result.require_user, treat_as_tool=True)

            # If this was a modify_tree operation, reload the tree structure
            if tool_name == "modify_tree":
                self._reload_tree_structure()

            return message_data

        except Exception as e:
            error_msg = f"Failed to execute tool: {str(e)}"
            logger.error(error_msg)
            return HandlerMessage(sender=SenderRole.USER, content=f"Error: {error_msg}")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    orchestrator = KPStructuringOrchestrator(domain_knowledge_path="knowledge_packs/1/domain_knowledge.json")

    xml_content = """
<thinking>
Intent: User approved the proposed knowledge structure for "Thick Juice Storage" in beet sugar manufacturing and wants it added to the domain knowledge.
Context: A comprehensive, detailed structure covering all key aspects of thick juice storage has been proposed and reviewed by the user, who confirmed it meets their needs.
Decision: Proceed to modify the knowledge tree by adding the approved structure under the appropriate domain.
Approval: Approval for structure addition has been granted by the user.
User Message: You confirmed the structure is suitable, so I'll now add it to the domain knowledge tree as outlined.
</thinking>

<modify_tree>
  <user_message>You approved the comprehensive "Thick Juice Storage" knowledge structure for beet sugar manufacturing. I'll now add this structure to the domain knowledge tree, ensuring all key subtopics and sections are included as proposed.</user_message>
  <operation>bulk</operation>
  <bulk_operations>[
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Storage Process Management"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Storage Process Management", "Receiving and Transferring Thick Juice from Evaporation"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Storage Process Management", "Tank Filling Procedures and Sequencing"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Storage Process Management", "Agitation and Circulation Management"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Storage Process Management", "Inventory Tracking and Recordkeeping"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Storage Process Management", "Thick Juice Withdrawal and Supply to Crystallization"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Storage Process Management", "Cleaning and Preparation of Storage Tanks"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Quality Control and Monitoring"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Quality Control and Monitoring", "Sampling Protocols for Thick Juice"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Quality Control and Monitoring", "Brix and Purity Measurement Techniques"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Quality Control and Monitoring", "Microbial Contamination Detection and Prevention"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Quality Control and Monitoring", "Temperature and pH Monitoring Procedures"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Quality Control and Monitoring", "Shelf Life Assessment and Degradation Indicators"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Quality Control and Monitoring", "Documentation and Reporting of Quality Data"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Equipment Operation and Maintenance"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Equipment Operation and Maintenance", "Storage Tank Design and Functionality"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Equipment Operation and Maintenance", "Pump and Valve Operation Procedures"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Equipment Operation and Maintenance", "Agitator and Mixer Maintenance"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Equipment Operation and Maintenance", "Instrumentation Calibration and Troubleshooting"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Equipment Operation and Maintenance", "CIP (Clean-in-Place) System Operation"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Equipment Operation and Maintenance", "Preventive Maintenance Scheduling"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Safety Protocols and Compliance"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Safety Protocols and Compliance", "Personal Protective Equipment (PPE) Requirements"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Safety Protocols and Compliance", "Chemical Handling and Spill Response"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Safety Protocols and Compliance", "Confined Space Entry Procedures"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Safety Protocols and Compliance", "Emergency Shutdown and Alarm Systems"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Safety Protocols and Compliance", "Regulatory Compliance (Food Safety, Environmental)"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Safety Protocols and Compliance", "Training and Certification Requirements"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Troubleshooting and Problem Resolution"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Troubleshooting and Problem Resolution", "Addressing Storage Tank Leaks and Structural Issues"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Troubleshooting and Problem Resolution", "Managing Unexpected Quality Deviations"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Troubleshooting and Problem Resolution", "Resolving Equipment Malfunctions (Pumps, Valves, Agitators)"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Troubleshooting and Problem Resolution", "Handling Microbial or Chemical Contamination Events"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Troubleshooting and Problem Resolution", "Responding to Process Interruptions or Power Failures"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Troubleshooting and Problem Resolution", "Root Cause Analysis and Corrective Actions"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Integration with Beet Sugar Manufacturing Workflow"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Integration with Beet Sugar Manufacturing Workflow", "Coordination with Evaporation and Crystallization Teams"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Integration with Beet Sugar Manufacturing Workflow", "Scheduling Storage to Match Production Demands"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Integration with Beet Sugar Manufacturing Workflow", "Data Integration with Plant Information Systems"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Integration with Beet Sugar Manufacturing Workflow", "Communication Protocols for Process Changes"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Integration with Beet Sugar Manufacturing Workflow", "Impact of Storage on Downstream Sugar Quality"]},
    {"action": "create", "paths": ["Beet Sugar Manufacturing", "Thick Juice Storage", "Integration with Beet Sugar Manufacturing Workflow", "Continuous Improvement and Process Optimization"]}
  ]</modify_tree>
"""

    print(orchestrator._parse_xml_tool_call(xml_content=xml_content))
