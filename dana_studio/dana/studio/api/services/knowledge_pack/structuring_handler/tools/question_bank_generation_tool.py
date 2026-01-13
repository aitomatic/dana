from typing import Any
from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
    ToolResult,
)
from dana.studio.api.core.schemas_v2 import DomainKnowledgeTreeV2, DomainNodeV2
from dana.studio.api.services.knowledge_status_manager import KnowledgeStatusManager
from dana.lang.core.lang.sandbox_context import SandboxContext
from dana.lang.libs.corelib.py_wrappers.py_reason import py_reason as reason_function
from dana.studio.api.services.intent_detection.intent_handlers.handler_prompts.knowledge_ops_prompts import (
    GENERATE_QUESTION_PROMPT,
    ACCESS_COVERAGE_PROMPT,
)
from dana.studio.api.core.schemas_v2 import KnowledgeGenerationStatus
import logging
import asyncio
import json
from pathlib import Path
from pydantic import BaseModel
from dana.studio.api.routers.v2.ws.domain_knowledge_ws import kp_question_generation_ws_notifier, WSManager

logger = logging.getLogger(__name__)


def reason(prompt: str, target_type: type | None = None) -> str:
    """Wrapper for Dana's reason function"""
    context = SandboxContext()
    context.set("system:__current_assignment_type", target_type)
    return reason_function(context, prompt)


class KnowledgeUnit(BaseModel):
    content: str
    references: list[dict] = []


class Knowledge(BaseModel):
    question: str = ""
    facts: list[KnowledgeUnit] = []
    heuristics: list[KnowledgeUnit] = []
    procedures: list[KnowledgeUnit] = []


class KnowledgeNode(BaseModel):
    path_parts: list[str] = []
    knowledges: list[Knowledge] = []
    structured_data: dict[Any, Any] = {}
    total_questions: int = 0


class QuestionBankGenerationTool(BaseTool):
    def __init__(
        self,
        knowledge_id: int,
        knowledge_status_path: str | None = None,
        storage_path: str | None = None,
        tree_structure_path: str | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
        tasks: list[str] | None = None,
        ws_manager: WSManager = kp_question_generation_ws_notifier,
        max_concurrent: int = 5,
    ):
        self.knowledge_status_path = knowledge_status_path
        self.storage_path = storage_path
        self.tree_structure_path = tree_structure_path
        self.domain = domain
        self.role = role
        self.tasks = tasks or ["Analyze Information", "Provide Insights", "Answer Questions"]
        self.notifier = kp_question_generation_ws_notifier.get_notifier(str(knowledge_id))
        self.max_concurrent = max_concurrent

        # Load tree structure from path if provided
        self.tree_structure = None
        if tree_structure_path:
            self.tree_structure = self._load_tree_structure()

        # Initialize KnowledgeStatusManager
        self.status_manager = None
        if knowledge_status_path:
            self.status_manager = KnowledgeStatusManager(knowledge_status_path)

        tool_info = BaseToolInformation(
            name="question_bank_generation",
            description="Generate question banks and create folder hierarchy with prefilled knowledge.json files",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="user_message",
                        type="string",
                        description="A comprehensive message that acknowledges the user's request and explains what question bank generation will be performed",
                        example="I understand you want to generate comprehensive question banks for all topics in the tree structure. This will create detailed questions to guide knowledge generation.",
                    ),
                    BaseArgument(
                        name="context",
                        type="string",
                        description="Additional context from the plan",
                        example="Focus on practical applications and real-world scenarios",
                    ),
                ],
                required=[],
            ),
        )
        super().__init__(tool_info)

    def _load_tree_structure(self) -> DomainKnowledgeTreeV2:
        """Load tree structure from the provided path."""
        from dana.studio.api.services.intent_detection.intent_handlers.handler_utility import knowledge_ops_utils as ko_utils
        from pathlib import Path

        if not self.tree_structure_path:
            raise ValueError("tree_structure_path is required to load tree structure")

        _path = Path(self.tree_structure_path)
        if not _path.exists():
            # Create a new tree if it doesn't exist
            tree = DomainKnowledgeTreeV2(root=DomainNodeV2(topic=self.domain, children=[]))
            ko_utils.save_tree(tree, self.tree_structure_path)
        else:
            tree = DomainKnowledgeTreeV2.model_validate_json(_path.read_text())
        return tree

    def _find_leaf_node_in_tree(self, path: list[str]) -> DomainNodeV2 | None:
        """Find a leaf node in the tree by its path."""
        if not self.tree_structure or not path:
            return None

        # Start from root and navigate through the path
        current_node = self.tree_structure.root
        for topic in path[1:]:  # Skip root node
            found = False
            for child in current_node.children:
                if child.topic == topic:
                    current_node = child
                    found = True
                    break
            if not found:
                return None

        return current_node

    async def _execute(self, user_message: str = "", context: str = "", **kwargs) -> ToolResult:
        try:
            return await self._generate_question_banks_for_all_leaves(user_message, context)
        except Exception as e:
            logger.error(f"Failed to generate question banks: {e}")
            return ToolResult(
                name=self.name,
                result=self._build_structured_response(user_message, f"❌ Error generating question banks: {str(e)}"),
                require_user=False,
            )

    async def _extract_leaf_paths(self, node: DomainNodeV2, current_path: list[str] | None = None) -> list[list[str]]:
        """Recursively extract all paths from root to leaf nodes."""
        if current_path is None:
            current_path = []
        topic = node.topic
        new_path = current_path + [topic]
        children = node.children

        if not children:  # Leaf node
            return [new_path]

        all_paths = []
        for child in children:
            all_paths.extend(await self._extract_leaf_paths(child, new_path))
        return all_paths

    async def _notify(
        self, tool_name: str, content: str, status: str, progression: float | None = None, path_parts: list[str] | None = None
    ) -> None:
        """Send a notification message to the frontend."""
        if not self.notifier:
            return

        message = {
            "tool_name": tool_name,
            "content": content,
            "status": status,
            "progression": progression,
        }

        if path_parts is not None:
            message["path_parts"] = path_parts

        await self.notifier(message)

    async def _initialize_path_in_status_manager(self, path_parts: list[str]) -> None:
        """Initialize a path in the status manager if it doesn't exist."""
        if not self.status_manager:
            return

        path_str = self._path_parts_to_string(path_parts)

        # Only add if topic doesn't already exist
        if not self.status_manager.get_topic_entry(path_str):
            from datetime import datetime, UTC

            current_time = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            file_path = self._build_file_path_from_path_parts(path_parts)
            self.status_manager.add_or_update_topic(path_str, file_path, current_time, "pending")

    async def _generate_question_banks_for_all_leaves(self, user_message: str, context: str) -> ToolResult:
        """Generate question banks for all leaf nodes in the tree structure using concurrent processing."""
        if not self.tree_structure or not self.tree_structure.root:
            return ToolResult(
                name="generate_question_bank",
                result=self._build_structured_response(user_message, "❌ Error: No tree structure available for question bank generation"),
                require_user=False,
            )

        all_leaf_paths = await self._extract_leaf_paths(self.tree_structure.root)

        for path_parts in all_leaf_paths:
            await self._initialize_path_in_status_manager(path_parts)

        logger.info(f"Found {len(all_leaf_paths)} leaf nodes to process")

        # Stream initial progress
        await self._notify(
            "generate_question_bank",
            f"🌳 Starting concurrent question bank generation for {len(all_leaf_paths)} topics",
            "in_progress",
            0.0,
        )

        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # Process all leaf paths concurrently
        results = await asyncio.gather(
            *[self._process_single_leaf_path(semaphore, i, path, len(all_leaf_paths)) for i, path in enumerate(all_leaf_paths)],
            return_exceptions=True,
        )

        # Process results
        successful_generations = 0
        failed_generations = 0
        status_text = ""
        generation_results = []

        for i, result in enumerate(results):
            leaf_topic = all_leaf_paths[i][-1]

            if isinstance(result, Exception):
                logger.error(f"Failed to generate question bank for {all_leaf_paths[i]}: {result}")
                failed_generations += 1
                generation_results.append(f"❌ Failed '{leaf_topic}': {str(result)}")
            elif result.get("skipped"):
                generation_results.append(f"⏭️ Skipped '{leaf_topic}' - {result.get('reason', 'already complete')}")
            elif result.get("success"):
                successful_generations += 1
                status_text += f"- {leaf_topic}: {result.get('questions_count', 0)} questions generated\n"
            else:
                failed_generations += 1
                generation_results.append(f"❌ Failed '{leaf_topic}': Unknown error")

        await self._notify("generate_question_bank", f"✅ Question bank generation complete. Summary: \n{status_text}", "finish", 1.0)

        return ToolResult(
            name="generate_question_bank",
            result=self._build_structured_response(user_message, f"✅ Question bank generation complete. Summary: \n{status_text}"),
            require_user=False,
        )

    async def _process_single_leaf_path(self, semaphore: asyncio.Semaphore, index: int, path: list[str], total_paths: int) -> dict:
        """Process a single leaf path with semaphore-controlled concurrency."""
        async with semaphore:
            try:
                leaf_topic = path[-1]  # Last element in path is the leaf topic
                path_str = self._path_parts_to_string(path)

                logger.info(f"Processing leaf {index + 1}/{total_paths}: {leaf_topic}")

                # Check if already generated
                if self.status_manager:
                    if self.status_manager.is_success(path_str):
                        return {"skipped": True, "reason": "already complete"}

                # Stream progress update
                progress = (index / total_paths) if total_paths > 0 else 0.0
                await self._notify(
                    self.name,
                    f"📝 Processing {index + 1}/{total_paths}: {leaf_topic}",
                    KnowledgeGenerationStatus.GENERATING,
                    progress,
                    path_parts=path,
                )

                # Create storage directory if it doesn't exist
                if not self.storage_path:
                    raise ValueError("storage_path is required for question bank generation")
                file_path = self._build_file_path_from_path_parts(path)
                storage_dir = Path(self.storage_path)
                full_file_path = storage_dir / file_path
                full_file_path.parent.mkdir(parents=True, exist_ok=True)

                if not full_file_path.exists():
                    # Generate questions for this topic
                    knowledge_node = await self._generate_questions_for_topic_paths(path)

                    # Save to file
                    with open(full_file_path, "w", encoding="utf-8") as f:
                        json.dump(knowledge_node.model_dump(mode="json"), f, indent=4)

                    # Update status to questions_generated
                    if self.status_manager:
                        self.status_manager.set_status(path_str, KnowledgeGenerationStatus.QUESTION_GENERATED)

                    # Update leaf node status in tree and save tree
                    if self.tree_structure and self.tree_structure_path:
                        # Find the leaf node in the tree
                        leaf_node = self._find_leaf_node_in_tree(path)
                        if leaf_node:
                            leaf_node.status = KnowledgeGenerationStatus.QUESTION_GENERATED
                            # Save the tree
                            from dana.studio.api.services.intent_detection.intent_handlers.handler_utility import (
                                knowledge_ops_utils as ko_utils,
                            )

                            ko_utils.save_tree(self.tree_structure, self.tree_structure_path)

                    await self._notify(
                        self.name,
                        f"✅ Question bank generation complete for {leaf_topic}",
                        KnowledgeGenerationStatus.QUESTION_GENERATED,
                        progress,
                        path_parts=path,
                    )

                    return {"success": True, "questions_count": knowledge_node.total_questions, "leaf_topic": leaf_topic}
                else:
                    return {"skipped": True, "reason": "file already exists"}

            except Exception as e:
                logger.error(f"Failed to generate question bank for {path}: {e}")
                if self.status_manager:
                    self.status_manager.set_status(path_str, "failed")
                raise e

    async def _generate_questions_for_topic_paths(self, paths: list[str]) -> KnowledgeNode:
        """Generate questions for a topic path using iterative confidence-based refinement."""
        current_confidence = 0
        count = 0
        path = " → ".join(paths)
        tasks = "\n".join([f"- {task}" for task in self.tasks])
        suggestion = "Initial generation"
        questions = ""
        knowledges = []

        while (current_confidence < 85) and (count < 15):
            count += 1
            new_questions = await asyncio.to_thread(
                reason,
                GENERATE_QUESTION_PROMPT.format(
                    path=path,
                    tasks=tasks,
                    role=self.role,
                    domain=self.domain,
                    confidence=current_confidence,
                    suggestion=suggestion,
                    questions=questions,
                ),
            )
            knowledge = Knowledge(question=new_questions)
            knowledges.append(knowledge)
            questions = questions + f"\n{new_questions}"
            confidence_result = await asyncio.to_thread(
                reason,
                prompt=ACCESS_COVERAGE_PROMPT.format(
                    questions=questions, role=self.role, domain=self.domain, tasks=tasks, confidence=current_confidence
                ),
                target_type=dict,
            )
            current_confidence = confidence_result.get("confidence", 0)
            suggestion = confidence_result.get("suggestion", "Continue generation")
        knowledge_node = KnowledgeNode(
            path_parts=paths, knowledges=knowledges, structured_data={}, total_questions=self.get_number_of_questions(questions)
        )
        return knowledge_node

    def get_number_of_questions(self, questions: str) -> int:
        """Get the number of questions in the questions string."""
        return len(questions.split("*Question"))

    def _path_parts_to_string(self, path_parts: list[str]) -> str:
        """Convert path parts to string format (excluding root node)."""
        return " - ".join(path_parts[1:]) if len(path_parts) > 1 else " - ".join(path_parts)

    def _build_file_path_from_path_parts(self, path_parts: list[str]) -> str:
        """Build file path from a list of path parts (excluding root) by converting ' - ' to '/' and adding '/knowledge.json'."""
        # Convert to file path format with "/" separators
        file_path = "/".join([DomainNodeV2(topic=topic).fd_name for topic in path_parts])
        # Add "/knowledge.json" suffix
        return file_path + "/knowledge.json"

    def _build_structured_response(self, user_message: str, content: str) -> str:
        """Build a structured response with user message and generation content."""
        response_parts = []

        # Add user message first (acknowledgment and context)
        if user_message:
            response_parts.append(f"{user_message}")
            response_parts.append("")  # Empty line for spacing

        # Add the generation content
        response_parts.append(content)

        # Join all parts with proper spacing
        return "\n".join(response_parts)


if __name__ == "__main__":
    import json
    from pathlib import Path

    knowledge_path = "agents/agent_3_lama/domain_knowledge.json"
    knows_folder = Path(knowledge_path).parent / "knows"
    knows_folder.mkdir(parents=True, exist_ok=True)

    with open(knowledge_path) as f:
        tree_structure = json.load(f)

    tree_structure = DomainKnowledgeTreeV2.model_validate(tree_structure)

    tool = QuestionBankGenerationTool(
        knowledge_status_path=str(knows_folder / "knowledge_status.json"),
        domain="Finance",
        role="Financial Analyst",
        storage_path=str(knows_folder.resolve()),
        tree_structure=tree_structure,
    )
    print(
        asyncio.run(
            tool._execute(
                user_message="Generate question banks for all topics in the tree structure",
                context="Focus on practical applications and real-world scenarios",
            )
        )
    )
