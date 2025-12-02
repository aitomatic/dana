from typing import Any
from llama_index.core.schema import NodeWithScore
from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
    ToolResult,
)
from dana.studio.api.core.schemas_v2 import DomainKnowledgeTreeV2, DomainNodeV2, KnowledgeGenerationStatus
from dana.studio.api.services.knowledge_status_manager import KnowledgeStatusManager
from dana.lang.core.lang.sandbox_context import SandboxContext
from dana.lang.libs.corelib.py_wrappers.py_reason import py_reason as reason_function
from dana.studio.api.services.intent_detection.intent_handlers.handler_prompts.knowledge_ops_prompts import (
    KNOWLEDGE_EXTRACTION_PROMPT,
    KNOWLEDGE_GENERATION_PROMPT,
)
from dana.studio.api.repositories.config import DEFAULT_TEMPLATE_FOLDER
import logging
import asyncio
import re
from dana.lang.common.sys_resource.rag.rag_resource_v2 import RAGResourceV2 as RAGResource
from pydantic import BaseModel
from pathlib import Path
import traceback
import json

logger = logging.getLogger(__name__)


def reason(prompt: str, target_type: type | None = None) -> str:
    """Wrapper for Dana's reason function"""
    context = SandboxContext()
    context.set("system:__current_assignment_type", target_type)
    return reason_function(context, prompt)


class RawFormatKnowledge(BaseModel):
    question: str
    chunks: list[NodeWithScore]
    knowledge: str
    from_doc: bool = False


class Reference(BaseModel):
    source: str
    page_number: int | None = None


class KnowledgeUnit(BaseModel):
    content: str
    references: list[Reference]


class Knowledge(BaseModel):
    question: str = ""
    facts: list[KnowledgeUnit] = []
    heuristics: list[KnowledgeUnit] = []
    procedures: list[KnowledgeUnit] = []


class KnowledgeNode(BaseModel):
    path_parts: list[str] = []
    knowledges: list[Knowledge] = []
    structured_data: dict[Any, Any] = {}

    def get_overview(self) -> str:
        fact_count = 0
        procedure_count = 0
        heuristic_count = 0
        for knowledge in self.knowledges:
            fact_count += len(knowledge.facts)
            procedure_count += len(knowledge.procedures)
            heuristic_count += len(knowledge.heuristics)
        output = f"{len(self.knowledges)} artifacts ({fact_count} facts, {heuristic_count} heuristics, {procedure_count} procedures)"
        return output


class KnowledgeGenerationTool(BaseTool):
    # Timeout constants (in seconds)
    DEFAULT_LLM_CALL_TIMEOUT = 30  # 30 secs for LLM calls
    DEFAULT_RAG_QUERY_TIMEOUT = 60  # 1 minute for RAG queries
    DEFAULT_BATCH_TIMEOUT = 600  # 10 minutes for batch operations
    DEFAULT_LEAF_PROCESSING_TIMEOUT = 600  # 10 minutes per leaf
    DEFAULT_RETRY_MAX_ATTEMPTS = 2  # Maximum retry attempts
    DEFAULT_RETRY_BACKOFF_BASE = 2  # Exponential backoff base (seconds)

    def __init__(
        self,
        knowledge_id: int,
        knowledge_status_path: str | None = None,
        storage_path: str | None = None,
        document_paths: list[str] | None = None,
        tree_structure_path: str | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
        tasks: list[str] | None = None,
        ws_manager=None,
        question_batch_size: int = 1,
        allow_outside_document: bool = False,
        template_generation_prompt: str | None = None,  # KP override prompt
        llm_call_timeout: int | None = None,  # Timeout for LLM calls
        rag_query_timeout: int | None = None,  # Timeout for RAG queries
        batch_timeout: int | None = None,  # Timeout for batch operations
        leaf_processing_timeout: int | None = None,  # Timeout per leaf processing
        max_retry_attempts: int | None = None,  # Max retry attempts
    ):
        self.knowledge_id = knowledge_id
        self.knowledge_status_path = knowledge_status_path
        self.storage_path = storage_path
        self.document_paths = document_paths or []
        self.tree_structure_path = tree_structure_path
        self.allow_outside_document = allow_outside_document
        self.template_generation_prompt = template_generation_prompt  # KP override
        # Load tree structure from path if provided
        self.tree_structure = None
        if tree_structure_path:
            self.tree_structure = self._load_tree_structure()
        self.domain = domain
        self.role = role
        self.tasks = tasks or ["Analyze Information", "Provide Insights", "Answer Questions"]
        self.question_batch_size = question_batch_size

        # Timeout configuration
        self.llm_call_timeout = llm_call_timeout or self.DEFAULT_LLM_CALL_TIMEOUT
        self.rag_query_timeout = rag_query_timeout or self.DEFAULT_RAG_QUERY_TIMEOUT
        self.batch_timeout = batch_timeout or self.DEFAULT_BATCH_TIMEOUT
        self.leaf_processing_timeout = leaf_processing_timeout or self.DEFAULT_LEAF_PROCESSING_TIMEOUT
        self.max_retry_attempts = max_retry_attempts or self.DEFAULT_RETRY_MAX_ATTEMPTS

        logger.info(
            f"Initialized KnowledgeGenerationTool with timeouts: "
            f"LLM={self.llm_call_timeout}s, RAG={self.rag_query_timeout}s, "
            f"Batch={self.batch_timeout}s, Leaf={self.leaf_processing_timeout}s, "
            f"MaxRetries={self.max_retry_attempts}"
        )

        # Initialize RAG resource if document paths are provided
        if self.document_paths:
            self.rag_resource = RAGResource(self.document_paths, debug=True, return_raw=True, reranking=True)
        else:
            self.rag_resource = None

        # Import WS manager inside constructor to avoid circular imports
        if ws_manager is None:
            from dana.studio.api.routers.v2.ws.domain_knowledge_ws import kp_question_generation_ws_notifier

            ws_manager = kp_question_generation_ws_notifier

        self.notifier = ws_manager.get_notifier(str(knowledge_id))

        # Get WebSocket manager for real-time status updates
        self.server_ws_manager = None

        # Initialize KnowledgeStatusManager
        self.status_manager = None
        if self.knowledge_status_path:
            self.status_manager = KnowledgeStatusManager(self.knowledge_status_path, str(self.knowledge_id))

        tool_info = BaseToolInformation(
            name="generate_knowledge",
            description="Generate knowledge from questions in existing knowledge.json files for all leaf nodes",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="user_message",
                        type="string",
                        description="A comprehensive message that acknowledges the user's request and explains what knowledge generation will be performed",
                        example="I understand you want to generate comprehensive knowledge for all topics in the tree structure. This will create detailed facts, procedures, and heuristics to enhance the agent's capabilities.",
                    ),
                    BaseArgument(
                        name="counts",
                        type="string",
                        description="Number of each type to generate",
                        example="5 facts, 2 procedures, 3 heuristics",
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

    async def _notify(
        self, tool_name: str, content: str, status: str, progression: float | None = None, path_parts: list[str] | None = None
    ) -> None:
        """Helper method to send WebSocket notifications with proper formatting."""
        if self.notifier:
            message = {
                "tool_name": tool_name,
                "content": content,
                "status": status,
                "progression": progression,
                "path_parts": path_parts,
            }
            await self.notifier(message)

    def _load_tree_structure(self) -> DomainKnowledgeTreeV2:
        """Load tree structure from the provided path."""
        from dana.studio.api.services.intent_detection.intent_handlers.handler_utility import knowledge_ops_utils as ko_utils
        from pathlib import Path

        if not self.tree_structure_path:
            raise ValueError("tree_structure_path is required to load tree structure")

        _path = Path(self.tree_structure_path)
        if not _path.exists():
            tree = DomainKnowledgeTreeV2(root=DomainNodeV2(topic=self.domain, children=[]))
            ko_utils.save_tree(tree, self.tree_structure_path)
        else:
            tree = DomainKnowledgeTreeV2.model_validate_json(_path.read_text())
        return tree

    def _find_leaf_node_in_tree(self, path: list[str]) -> DomainNodeV2 | None:
        """Find a leaf node in the tree by its path."""
        if not self.tree_structure or not path:
            return None

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

    async def _execute(self, user_message: str = "", counts: str = "", context: str = "", **kwargs) -> ToolResult:
        """
        Main execution flow for knowledge generation pipeline:
        1. Generate knowledge for all leaf nodes (saves to knowledge.json)
        2. Generate summaries for all completed topics (updates knowledge.json with summary field)
        3. Generate default capture template (reads all summaries and creates template)

        Each step is independent and resumable - reads from/writes to file system.
        """
        try:
            # Step 1: Generate knowledge for all leaves
            logger.info("🚀 Step 1: Generating knowledge for all leaf nodes...")
            await self._generate_knowledge_for_all_leaves(user_message, counts, context)

            # Step 2: Generate summaries for all successfully processed topics
            try:
                logger.info("📝 Step 2: Generating summaries for all topics...")
                await self._generate_summary_for_all_leaves()
                logger.info("✅ Summaries generated successfully")
            except Exception as e:
                logger.error(f"Failed to generate summaries: {e}")
                # Don't raise - summary generation is not critical

            # Step 3: Generate master interview template
            try:
                logger.info("🎯 Step 3: Generating default capture template...")
                await self._generate_master_interview_template()
                logger.info("✅ Default capture template generated successfully")
            except Exception as e:
                logger.error(f"Failed to generate default capture template: {e}")
                # Don't raise - template is not critical

            # Return success result
            return ToolResult(
                name="generate_knowledge",
                result=self._build_structured_response(user_message, "✅ Knowledge generation pipeline complete."),
                require_user=False,
            )

        except Exception as e:
            logger.error(f"Failed to generate knowledge: {e}")
            return ToolResult(
                name="generate_knowledge",
                result=self._build_structured_response(user_message, f"❌ Error generating knowledge: {str(e)}"),
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

    async def _generate_knowledge_for_all_leaves(self, user_message: str, counts: str, context: str) -> None:
        """
        Generate knowledge for all leaf nodes by reading questions from existing knowledge.json files.
        Saves generated knowledge to knowledge.json files in the storage directory.
        """
        if not self.tree_structure or not self.tree_structure.root:
            logger.error("No tree structure available for knowledge generation")
            return

        all_leaf_paths = await self._extract_leaf_paths(self.tree_structure.root)
        logger.info(f"Found {len(all_leaf_paths)} leaf nodes to process")

        # Stream initial progress
        await self._notify("generate_knowledge", f"🌳 Starting knowledge generation for {len(all_leaf_paths)} topics", "in_progress", 0.0)

        # Generate knowledge for each leaf
        successful_generations = 0
        failed_generations = 0
        status_text = ""
        generation_results = []

        for i, path in enumerate(all_leaf_paths):
            leaf_topic = path[-1]  # Last element in path is the leaf topic
            path_str = self._path_parts_to_string(path)
            try:
                logger.info(f"[Leaf {i + 1}/{len(all_leaf_paths)}] Processing '{leaf_topic}' (path: {path_str})")

                # Check if already generated
                if self.status_manager:
                    if self.status_manager.is_success(path_str):
                        logger.info(f"[Leaf {i + 1}/{len(all_leaf_paths)}] Skipping '{leaf_topic}' - already complete")
                        generation_results.append(f"⏭️ Skipped '{leaf_topic}' - already complete")
                        continue

                # Initialize status manager for the current path if it hasn't been done yet
                await self._initialize_path_in_status_manager(path)

                # Build file path and check if knowledge.json exists
                if not self.storage_path:
                    raise ValueError("storage_path is required for knowledge generation")
                file_path = self._build_file_path_from_path_parts(path)
                storage_dir = Path(self.storage_path)
                full_file_path = storage_dir / file_path

                if not full_file_path.exists():
                    logger.warning(
                        f"[Leaf {i + 1}/{len(all_leaf_paths)}] Skipping '{leaf_topic}' - no knowledge.json found at {full_file_path}"
                    )
                    generation_results.append(f"⚠️ Skipped '{leaf_topic}' - no knowledge.json found (run question bank generation first)")
                    continue

                # Read existing knowledge.json to extract questions
                logger.debug(f"[Leaf {i + 1}/{len(all_leaf_paths)}] Reading knowledge.json from {full_file_path}")
                knowledge_node = await self._read_questions_from_knowledge_json(full_file_path)
                if not knowledge_node or not knowledge_node.knowledges:
                    logger.warning(f"[Leaf {i + 1}/{len(all_leaf_paths)}] Skipping '{leaf_topic}' - no questions found in knowledge.json")
                    generation_results.append(f"⚠️ Skipped '{leaf_topic}' - no questions found in knowledge.json")
                    continue

                # Generate knowledge from questions with timeout protection
                logger.info(f"Generating knowledge for '{leaf_topic}' with {len(knowledge_node.knowledges)} knowledge entries")
                try:
                    raw_knowledges = await asyncio.wait_for(
                        self._generate_knowledge_from_questions(path, knowledge_node.knowledges),
                        timeout=self.leaf_processing_timeout,
                    )
                    logger.info(f"Successfully generated raw knowledge for '{leaf_topic}', transforming...")
                    completed_knowledges = await self._transform_knowledge_units(raw_knowledges)
                    logger.info(f"Successfully transformed knowledge for '{leaf_topic}': {len(completed_knowledges)} knowledge artifacts")
                except TimeoutError:
                    logger.error(f"Knowledge generation for '{leaf_topic}' timed out after {self.leaf_processing_timeout}s")
                    raise
                except Exception as e:
                    logger.error(f"Knowledge generation for '{leaf_topic}' failed: {e}")
                    raise

                # Update the knowledge.json with generated content
                logger.debug(
                    f"[Leaf {i + 1}/{len(all_leaf_paths)}] Updating knowledge.json with {len(completed_knowledges)} knowledge artifacts"
                )
                await self._update_knowledge_json(full_file_path, completed_knowledges)
                logger.info(f"[Leaf {i + 1}/{len(all_leaf_paths)}] ✅ Successfully completed '{leaf_topic}'")

                successful_generations += 1
                status_text += f"- {leaf_topic}: {len(completed_knowledges)} knowledge artifacts generated\n"

                # Update status manager
                if self.status_manager:
                    self.status_manager.set_status(path_str, "success")

                # Update leaf node status in tree and save tree
                if self.tree_structure and self.tree_structure_path:
                    leaf_node = self._find_leaf_node_in_tree(path)
                    if leaf_node:
                        leaf_node.status = KnowledgeGenerationStatus.COMPLETED
                        from dana.studio.api.services.intent_detection.intent_handlers.handler_utility import (
                            knowledge_ops_utils as ko_utils,
                        )

                        ko_utils.save_tree(self.tree_structure, self.tree_structure_path)

                        await self._notify(
                            "generate_question_bank",
                            f"✅ Completed '{leaf_node}' - {i + 1}/{len(all_leaf_paths)} done",
                            KnowledgeGenerationStatus.COMPLETED,
                            (i + 1) / len(all_leaf_paths),
                            path_parts=path,
                        )

            except TimeoutError:
                logger.error(
                    f"[Leaf {i + 1}/{len(all_leaf_paths)}] ⏱️ Timeout processing '{leaf_topic}' after {self.leaf_processing_timeout}s"
                )
                if self.status_manager:
                    self.status_manager.set_status(path_str, "failed")
                failed_generations += 1
                generation_results.append(f"❌ Failed '{leaf_topic}': Timeout after {self.leaf_processing_timeout}s")
            except Exception as e:
                logger.error(f"[Leaf {i + 1}/{len(all_leaf_paths)}] ❌ Failed to generate knowledge for '{leaf_topic}': {e}")
                logger.debug(f"[Leaf {i + 1}/{len(all_leaf_paths)}] Error details:", exc_info=True)
                if self.status_manager:
                    self.status_manager.set_status(path_str, "failed")
                failed_generations += 1
                generation_results.append(f"❌ Failed '{leaf_topic}': {str(e)}")
                traceback.print_exc()

        logger.info(
            f"Knowledge generation completed: {successful_generations} successful, {failed_generations} failed "
            f"out of {len(all_leaf_paths)} total leaves"
        )
        if generation_results:
            logger.debug("Generation results summary:")
            for result in generation_results[:10]:  # Log first 10 results
                logger.debug(f"  {result}")
            if len(generation_results) > 10:
                logger.debug(f"  ... and {len(generation_results) - 10} more results")

    async def _read_questions_from_knowledge_json(self, file_path: Path) -> KnowledgeNode | None:
        """Read existing knowledge.json and extract questions."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            return KnowledgeNode.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to read knowledge.json from {file_path}: {e}")
            return None

    async def _update_knowledge_json(self, file_path: Path, completed_knowledges: list[Knowledge]) -> None:
        """Update existing knowledge.json with generated content."""
        try:
            # Read existing file
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Update the knowledges with completed content
            data["knowledges"] = [knowledge.model_dump(mode="json") for knowledge in completed_knowledges]

            # Write back to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        except Exception as e:
            logger.error(f"Failed to update knowledge.json at {file_path}: {e}")
            raise

    def _parse_summary_sections(self, summary: str) -> dict:
        """Extract key concepts and important questions from summary markdown."""
        result = {
            "key_concepts": [],
            "important_questions": [],
            "referenced_documents": [],
        }

        try:
            # Split by sections
            lines = summary.split("\n")
            current_section = None

            for line in lines:
                line = line.strip()

                # Detect section headers
                if "# Key Concepts" in line or "## Key Concepts" in line:
                    current_section = "key_concepts"
                elif "# Most Important Questions" in line or "## Most Important Questions" in line:
                    current_section = "important_questions"
                elif "# Referenced Documents" in line or "## Referenced Documents" in line:
                    current_section = "referenced_documents"
                elif line.startswith("#"):
                    current_section = None
                # Extract bullet points
                elif line.startswith("-") and current_section:
                    item = line[1:].strip()
                    if item:
                        result[current_section].append(item)

        except Exception as e:
            logger.warning(f"Failed to parse summary sections: {e}")

        return result

    async def _generate_summary_for_all_leaves(self) -> None:
        """
        Generate summaries for all leaf nodes by discovering knowledge.json files in storage directory.
        Updates each knowledge.json with a summary field.
        """
        if not self.storage_path:
            logger.warning("Storage path not set, skipping summary generation")
            return

        storage_dir = Path(self.storage_path)
        if not storage_dir.exists():
            logger.warning(f"Storage directory does not exist: {storage_dir}")
            return

        # Discover all knowledge.json files
        knowledge_files = list(storage_dir.rglob("knowledge.json"))
        logger.info(f"Found {len(knowledge_files)} knowledge.json files to process for summaries")

        for i, file_path in enumerate(knowledge_files, 1):
            try:
                # Extract topic name from path
                topic_name = file_path.parent.name

                # Check if summary already exists
                with open(file_path, encoding="utf-8") as f:
                    knowledge_data = json.load(f)

                if knowledge_data.get("summary"):
                    logger.info(f"Skipping {topic_name} - summary already exists")
                    continue

                logger.info(f"[Summary {i}/{len(knowledge_files)}] Generating summary for '{topic_name}'")
                try:
                    await asyncio.wait_for(
                        self._generate_knowledge_summary(file_path, topic_name),
                        timeout=self.llm_call_timeout + 10,  # Add small buffer for file I/O
                    )
                    logger.info(f"[Summary {i}/{len(knowledge_files)}] ✅ Successfully generated summary for '{topic_name}'")
                except TimeoutError:
                    logger.error(f"[Summary {i}/{len(knowledge_files)}] ⏱️ Summary generation timed out for '{topic_name}'")
                except Exception as e:
                    logger.error(f"[Summary {i}/{len(knowledge_files)}] ❌ Failed to generate summary for '{topic_name}': {e}")

            except Exception as e:
                logger.error(f"Failed to generate summary for {file_path}: {e}")
                # Continue with other summaries

    async def _generate_knowledge_summary(self, file_path: Path, topic_name: str) -> None:
        """Generate a summary for the knowledge.json file and add it as a summary field."""
        try:
            # Read the updated knowledge.json
            with open(file_path, encoding="utf-8") as f:
                knowledge_data = json.load(f)

            # Create the prompt
            summary_prompt = f"""
Based on the following knowledge json:
```json
{json.dumps(knowledge_data, indent=2)}
```

Provide an overview paragraph with less than 500 words to brief me about this knowledge pack. Also include 5 most key concepts and referenced document names if any

RESPONSE FORMAT:
```markdown
# Summary
...

# Key Concepts
- concept_1
- concept_2
- ...

# Referenced Documents
- document_name_1
- document_name_2
- ...
```
"""

            # Generate summary using the reason function with timeout protection
            logger.debug(f"Generating summary for '{topic_name}' with timeout={self.llm_call_timeout}s")
            try:
                summary = await asyncio.wait_for(
                    asyncio.to_thread(reason, summary_prompt),
                    timeout=self.llm_call_timeout,
                )
                logger.debug(f"Successfully generated summary for '{topic_name}' (length: {len(summary)} chars)")
            except TimeoutError:
                logger.error(f"Summary generation for '{topic_name}' timed out after {self.llm_call_timeout}s")
                # Set a default summary indicating timeout
                summary = f"# Summary\n\nSummary generation timed out for topic: {topic_name}\n\n# Key Concepts\n- (Summary generation incomplete)\n\n# Most Important Questions\n- (Summary generation incomplete)\n\n# Referenced Documents\n- (Summary generation incomplete)"
            except Exception as e:
                logger.error(f"Summary generation for '{topic_name}' failed: {e}")
                # Set a default summary indicating error
                summary = f"# Summary\n\nSummary generation failed for topic: {topic_name}\n\nError: {str(e)}\n\n# Key Concepts\n- (Summary generation incomplete)\n\n# Most Important Questions\n- (Summary generation incomplete)\n\n# Referenced Documents\n- (Summary generation incomplete)"

            # Add summary to the knowledge_data
            knowledge_data["summary"] = summary

            # Write the updated knowledge.json back to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(knowledge_data, f, indent=4)

            logger.info(f"Generated and added summary for {topic_name} to {file_path}")

        except Exception as e:
            logger.error(f"Failed to generate summary for {file_path}: {e}")
            # Don't raise the exception as summary generation is not critical

    async def _generate_master_interview_template(self) -> None:
        """
        Generate default capture template by discovering and reading all knowledge.json files with summaries.
        Creates template/master_interview_template.md file.
        """
        try:
            if not self.storage_path:
                logger.warning("Storage path not set, skipping master interview template generation")
                return

            storage_dir = Path(self.storage_path)
            if not storage_dir.exists():
                logger.warning(f"Storage directory does not exist: {storage_dir}")
                return

            # Create template directory
            template_dir = storage_dir.parent / DEFAULT_TEMPLATE_FOLDER
            template_dir.mkdir(exist_ok=True)
            template_path = template_dir / "README.md"

            # Discover all knowledge.json files
            knowledge_files = list(storage_dir.rglob("knowledge.json"))
            logger.info(f"Discovering summaries from {len(knowledge_files)} knowledge.json files")

            # Read all summaries from knowledge.json files
            all_summaries_data = []
            for file_path in knowledge_files:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        knowledge_data = json.load(f)

                    summary_text = knowledge_data.get("summary", "")
                    if not summary_text:
                        continue

                    # Extract topic info from path
                    topic_name = file_path.parent.name
                    relative_path = file_path.relative_to(storage_dir)
                    path_parts = list(relative_path.parts[:-1])  # Exclude 'knowledge.json'
                    path_str = " → ".join(path_parts)

                    parsed = self._parse_summary_sections(summary_text)
                    all_summaries_data.append(
                        {
                            "topic": topic_name,
                            "path": path_str,
                            "summary": summary_text,
                            "key_concepts": parsed["key_concepts"],
                            "important_questions": parsed["important_questions"],
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to read summary from {file_path}: {e}")
                    continue

            if not all_summaries_data:
                logger.warning("No summaries found, skipping master interview template generation")
                return

            # Format summaries for prompt
            formatted_summaries = ""
            for i, data in enumerate(all_summaries_data, 1):
                formatted_summaries += f"\n### Topic {i}: {data['topic']}\n"
                formatted_summaries += f"**Path**: {data['path']}\n\n"
                formatted_summaries += f"{data['summary']}\n\n"
                formatted_summaries += "---\n"

            # Get template prompt using hierarchy: KP Override > Global Default > Hardcoded Fallback
            template_prompt = await self._get_template_generation_prompt(formatted_summaries)
            print("TEMPLATE PROMPT", template_prompt)

            # Generate template using the reason function with timeout protection
            logger.info(
                f"Generating master interview template for {len(all_summaries_data)} topics with timeout={self.llm_call_timeout}s..."
            )
            try:
                template_content = await asyncio.wait_for(
                    asyncio.to_thread(reason, template_prompt),
                    timeout=self.llm_call_timeout,
                )
                logger.info(f"Successfully generated master interview template (length: {len(template_content)} chars)")
            except TimeoutError:
                logger.error(f"Master interview template generation timed out after {self.llm_call_timeout}s")
                template_content = (
                    f"# Master Interview Template: {self.domain} - {self.role}\n\n"
                    f"⚠️ Template generation timed out. Please try again or generate templates individually.\n"
                )
            except Exception as e:
                logger.error(f"Master interview template generation failed: {e}")
                template_content = f"# Master Interview Template: {self.domain} - {self.role}\n\n⚠️ Template generation failed: {str(e)}\n"

            print("TEMPLATE CONTENT", template_content)

            # Save template to file
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(template_content)

            logger.info(f"✅ Master interview template saved to {template_path}")

        except Exception as e:
            logger.error(f"Failed to generate master interview template: {e}")
            raise

    async def _generate_knowledge_from_questions(self, paths: list[str], existing_knowledges: list[Knowledge]) -> list[RawFormatKnowledge]:
        """Generate knowledge from existing questions in knowledge.json."""

        def _format_chunks(chunks: list[NodeWithScore]) -> str:
            output = ""
            for i, chunk in enumerate(chunks):
                output += f"### Chunk {i}\n\n{chunk.get_content()}\n---\n"
            return output

        async def generate_knowledge_with_retry(
            question: str, chunks: list[NodeWithScore], path_str: str, batch_index: int
        ) -> RawFormatKnowledge:
            """Generate knowledge with retry logic and timeout protection."""
            logger.debug(f"[Batch {batch_index}] Starting knowledge generation for question: {question[:100]}...")

            from_doc = False  # Initialize to avoid unbound variable
            for attempt in range(self.max_retry_attempts + 1):
                try:
                    if chunks:
                        logger.debug(
                            f"[Batch {batch_index}] Attempt {attempt + 1}/{self.max_retry_attempts + 1}: Extracting knowledge from documents"
                        )
                        res = await asyncio.wait_for(
                            asyncio.to_thread(
                                reason,
                                KNOWLEDGE_EXTRACTION_PROMPT.format(path=path_str, question=question, chunks=_format_chunks(chunks)),
                            ),
                            timeout=self.llm_call_timeout,
                        )
                        from_doc = True
                        logger.debug(f"[Batch {batch_index}] Successfully extracted knowledge from documents (length: {len(res)} chars)")
                    elif self.allow_outside_document:
                        logger.debug(
                            f"[Batch {batch_index}] Attempt {attempt + 1}/{self.max_retry_attempts + 1}: Generating knowledge without documents"
                        )
                        res = await asyncio.wait_for(
                            asyncio.to_thread(
                                reason,
                                KNOWLEDGE_GENERATION_PROMPT.format(path=path_str, question=question, role=self.role, domain=self.domain),
                            ),
                            timeout=self.llm_call_timeout,
                        )
                        from_doc = False
                        logger.debug(f"[Batch {batch_index}] Successfully generated knowledge without documents (length: {len(res)} chars)")
                    else:
                        logger.debug(f"[Batch {batch_index}] No chunks and outside documents not allowed, returning empty knowledge")
                        res = ""
                        from_doc = False

                    return RawFormatKnowledge(question=question, chunks=chunks, knowledge=res, from_doc=from_doc)

                except TimeoutError:
                    logger.warning(
                        f"[Batch {batch_index}] Attempt {attempt + 1}/{self.max_retry_attempts + 1} timed out after {self.llm_call_timeout}s "
                        f"for question: {question[:100]}..."
                    )
                    if attempt < self.max_retry_attempts:
                        wait_time = self.DEFAULT_RETRY_BACKOFF_BASE**attempt
                        logger.info(f"[Batch {batch_index}] Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"[Batch {batch_index}] All {self.max_retry_attempts + 1} attempts timed out")
                        return RawFormatKnowledge(question=question, chunks=chunks, knowledge="", from_doc=from_doc)

                except Exception as e:
                    logger.error(
                        f"[Batch {batch_index}] Attempt {attempt + 1}/{self.max_retry_attempts + 1} failed with error: {e} "
                        f"for question: {question[:100]}..."
                    )
                    if attempt < self.max_retry_attempts:
                        wait_time = self.DEFAULT_RETRY_BACKOFF_BASE**attempt
                        logger.info(f"[Batch {batch_index}] Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"[Batch {batch_index}] All {self.max_retry_attempts + 1} attempts failed")
                        # Return empty knowledge instead of raising to ensure all code paths return
                        return RawFormatKnowledge(question=question, chunks=chunks, knowledge="", from_doc=from_doc)

            # Fallback return (should never reach here, but satisfies type checker)
            return RawFormatKnowledge(question=question, chunks=chunks, knowledge="", from_doc=from_doc)

        # Extract questions from existing knowledges
        all_questions = []
        for knowledge in existing_knowledges:
            if knowledge.question:
                all_questions.append(knowledge.question)

        logger.info(f"Extracted {len(all_questions)} questions from {len(existing_knowledges)} knowledge entries")

        # Process questions in batches
        question_batches = []
        for i in range(0, len(all_questions), self.question_batch_size):
            batch = all_questions[i : i + self.question_batch_size]
            question_batches.append("\n".join(batch))

        logger.info(f"Created {len(question_batches)} question batches (batch_size={self.question_batch_size})")

        # Query RAG for relevant chunks if available
        if self.rag_resource and self.rag_resource.filenames and any([fn != "system" for fn in self.rag_resource.filenames]):
            logger.info(f"Querying RAG for {len(question_batches)} batches with timeout={self.rag_query_timeout}s each")
            try:

                async def query_rag_with_timeout(batch_index: int, question_batch: str):
                    """Query RAG with timeout protection."""
                    logger.debug(f"[RAG Batch {batch_index}] Querying RAG for batch: {question_batch[:100]}...")
                    if not self.rag_resource:
                        logger.warning(f"[RAG Batch {batch_index}] RAG resource is None, returning empty chunks")
                        return []
                    try:
                        result = await asyncio.wait_for(
                            self.rag_resource.query(question_batch, num_results=30),
                            timeout=self.rag_query_timeout,
                        )
                        logger.debug(
                            f"[RAG Batch {batch_index}] RAG query successful, returned {len(result) if isinstance(result, list) else 'non-list'} results"
                        )
                        return result
                    except TimeoutError:
                        logger.error(f"[RAG Batch {batch_index}] RAG query timed out after {self.rag_query_timeout}s")
                        return []
                    except Exception as e:
                        logger.error(f"[RAG Batch {batch_index}] RAG query failed: {e}")
                        return []

                relevant_chunks = await asyncio.wait_for(
                    asyncio.gather(
                        *[query_rag_with_timeout(i, batch) for i, batch in enumerate(question_batches)],
                        return_exceptions=True,
                    ),
                    timeout=self.batch_timeout,
                )

                # Handle exceptions from gather
                valid_chunks = []
                for i, result in enumerate(relevant_chunks):
                    if isinstance(result, Exception):
                        logger.error(f"[RAG Batch {i}] Exception during RAG query: {result}")
                        valid_chunks.append([])
                    elif isinstance(result, TimeoutError):
                        logger.error(f"[RAG Batch {i}] Timeout during RAG query")
                        valid_chunks.append([])
                    else:
                        valid_chunks.append(result)

                relevant_chunks = valid_chunks
                logger.info(
                    f"Successfully queried RAG for all batches, got chunks for {sum(1 for c in relevant_chunks if c)}/{len(relevant_chunks)} batches"
                )

            except TimeoutError:
                logger.error(f"RAG batch query operation timed out after {self.batch_timeout}s")
                relevant_chunks = [[] for _ in question_batches]
            except Exception as e:
                logger.error(f"RAG query operation failed: {e}")
                relevant_chunks = [[] for _ in question_batches]
        else:
            logger.info("RAG resource not available, skipping RAG queries")
            relevant_chunks = [[] for _ in question_batches]

        print("SUCCESSFULLY QUERY RAG")

        # Generate knowledge for each batch
        async_tasks = []
        path_str = " → ".join(paths)
        for batch_index, (question_batch, chunks) in enumerate(zip(question_batches, relevant_chunks, strict=False)):
            if question_batch:
                # Ensure chunks is a list of NodeWithScore
                if not isinstance(chunks, list):
                    chunks = []
                logger.debug(f"[Batch {batch_index}] Creating knowledge generation task with {len(chunks)} chunks")
                async_tasks.append(generate_knowledge_with_retry(question_batch, chunks, path_str, batch_index))

        logger.info(f"Starting knowledge generation for {len(async_tasks)} batches with timeout={self.batch_timeout}s")
        try:
            knowledges = await asyncio.wait_for(
                asyncio.gather(*async_tasks, return_exceptions=True),
                timeout=self.batch_timeout,
            )

            # Filter out exceptions and log them
            valid_knowledges = []
            for i, result in enumerate(knowledges):
                if isinstance(result, Exception):
                    logger.error(f"[Batch {i}] Knowledge generation failed with exception: {result}")
                    traceback.print_exc()
                    # Optionally create empty knowledge entry
                    valid_knowledges.append(
                        RawFormatKnowledge(
                            question=question_batches[i] if i < len(question_batches) else "", chunks=[], knowledge="", from_doc=False
                        )
                    )
                elif isinstance(result, TimeoutError):
                    logger.error(f"[Batch {i}] Knowledge generation timed out")
                    valid_knowledges.append(
                        RawFormatKnowledge(
                            question=question_batches[i] if i < len(question_batches) else "", chunks=[], knowledge="", from_doc=False
                        )
                    )
                else:
                    valid_knowledges.append(result)

            logger.info(f"Knowledge generation completed: {len(valid_knowledges)}/{len(async_tasks)} batches successful")
            return valid_knowledges

        except TimeoutError:
            logger.error(f"Batch knowledge generation timed out after {self.batch_timeout}s")
            # Return empty knowledge entries for all batches
            return [RawFormatKnowledge(question=batch, chunks=[], knowledge="", from_doc=False) for batch in question_batches]

    async def _transform_knowledge_units(self, knowledge_units: list[RawFormatKnowledge]) -> list[Knowledge]:
        """Transform raw knowledge into structured format."""
        knowledge_section_regex = re.compile(r"^[ ]*##[ \w\/]+$", re.MULTILINE)
        chunk_ref_regex = re.compile(r"^- (\[Chunk \d+(?:,\s*Chunk \d+)*\])", re.MULTILINE)
        results = []

        for unit in knowledge_units:
            knowledge_content = unit.knowledge
            chunks = unit.chunks
            output_knowledge = Knowledge(question=unit.question)
            matches = re.findall(knowledge_section_regex, knowledge_content)
            sections = re.split(knowledge_section_regex, knowledge_content)
            if len(sections) > 1:
                sections = sections[1:]

            for section, section_content in zip(matches, sections, strict=False):
                if unit.from_doc is True and "[Chunk" in section_content:
                    # IF FROM DOC, WE NEED TO GET THE CHUNK REFERENCES
                    ref_chunk_idxs = []
                    parts = re.split(chunk_ref_regex, section_content)
                    for part in parts:
                        if "[Chunk" in part:
                            matches = re.findall(r"\[Chunk (\d+)(?:,\s*Chunk (\d+))*\]", part)
                            ref_chunk_idxs = []
                            for match in matches:
                                ref_chunk_idxs.extend([int(value) for value in match if value.isdigit()])
                        else:
                            if ref_chunk_idxs:
                                knowledge_unit = KnowledgeUnit(
                                    content=part.strip(),
                                    references=[
                                        Reference(
                                            source=chunks[idx].node.metadata["source"],
                                            page_number=chunks[idx].node.metadata.get("page_label", 0),
                                        )
                                        for idx in ref_chunk_idxs
                                    ],
                                )
                                if "fact" in section.lower():
                                    output_knowledge.facts.append(knowledge_unit)
                                elif "heuristic" in section.lower():
                                    output_knowledge.heuristics.append(knowledge_unit)
                                elif "procedure" in section.lower():
                                    output_knowledge.procedures.append(knowledge_unit)
                elif unit.from_doc is False:
                    # IF NOT FROM DOC, WE CAN GROUP FACTS, HEURISTICS BUT NEED TO SPLIT PROCEDURES
                    knowledge_unit = KnowledgeUnit(content=section_content, references=[])
                    if "fact" in section.lower():
                        output_knowledge.facts.append(knowledge_unit)
                    elif "heuristic" in section.lower():
                        output_knowledge.heuristics.append(knowledge_unit)
                    elif "procedure" in section.lower():
                        llm_procedure_regex = re.compile(r"^- Overview \d+:", re.MULTILINE)
                        all_procedures = re.split(llm_procedure_regex, section_content)
                        for procedure in all_procedures:
                            stripped_procedure = procedure.strip()
                            if stripped_procedure:
                                procedure_unit = KnowledgeUnit(content=stripped_procedure, references=[])
                                output_knowledge.procedures.append(procedure_unit)
                        output_knowledge.procedures.append(knowledge_unit)
            results.append(output_knowledge)
        return results

    def _path_parts_to_string(self, path_parts: list[str]) -> str:
        """Convert path parts to string format (excluding root node)."""
        return " - ".join(path_parts[1:]) if len(path_parts) > 1 else " - ".join(path_parts)

    def _build_file_path_from_path_parts(self, path_parts: list[str]) -> str:
        """Build file path from a list of path parts (excluding root) by converting ' - ' to '/' and adding '/knowledge.json'."""
        # Convert to file path format with "/" separators
        file_path = "/".join([DomainNodeV2(topic=topic).fd_name for topic in path_parts])
        # Add "/knowledge.json" suffix
        return file_path + "/knowledge.json"

    async def _get_template_generation_prompt(self, formatted_summaries: str) -> str:
        """
        Get template generation prompt using hierarchy:
        1. Knowledge Pack Override (self.template_generation_prompt)
        2. Global Default (from ApplicationSettings)
        3. Hardcoded Fallback
        """
        # Priority 1: Knowledge Pack Override
        if self.template_generation_prompt:
            return self._format_prompt(self.template_generation_prompt, formatted_summaries)

        # Priority 2: Global Default (from database)
        try:
            from dana.studio.api.repositories import get_application_settings_repo
            from dana.studio.api.core.database import get_db

            for db in get_db():
                settings_repo = get_application_settings_repo()
                global_prompt = await settings_repo.get_setting("template_generation", "prompt", db)
                if global_prompt:
                    return self._format_prompt(global_prompt, formatted_summaries)
                break
        except Exception as e:
            logger.warning(f"Failed to load global template prompt: {e}")

        # Priority 3: Hardcoded Fallback (existing default)
        return self._format_prompt(self._get_default_template_prompt(), formatted_summaries)

    def _format_prompt(self, prompt_template: str, formatted_summaries: str) -> str:
        """Format prompt with placeholders."""
        return prompt_template.format(
            formatted_summaries=formatted_summaries,
            domain=self.domain,
            role=self.role,
        )

    def _get_default_template_prompt(self) -> str:
        """Get hardcoded fallback prompt."""
        return """Based on the following knowledge summaries from multiple topics:

{formatted_summaries}

Generate a conversational interview template for a {role} expert in {domain}.

Requirements:
1. Create 3-5 natural, open-ended opening questions per topic
2. Add relationship listening prompts (what connections to listen for between topics)
3. Include a follow-up question framework
4. Keep it conversational and expert-driven
5. No rigid detailed questions - let expert guide the conversation
6. Focus questions strictly on the domain and topics provided - avoid generic or off-topic questions
7. Ensure all questions are directly relevant to the specific knowledge summaries provided

Template Structure:
# Master Interview Template: {domain} - {role}

## Topic Opening Questions

For each topic, provide:
### [Topic Name]
**Background**: [1-2 sentence context from summary]

**Opening Questions**:
1. [Natural, open-ended question]
2. [Natural, open-ended question]
3. [Natural, open-ended question]

---

## Relationship Exploration Prompts
- When expert mentions [Topic A], explore connection to [Topic B]
- If they discuss [specific concept], ask how it applies elsewhere
- Listen for natural transitions between topics

## Follow-up Framework
- Can you tell me more about that?
- What's an example of when that happened?
- How do you typically handle that situation?
- What else should I know about this?"""

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

    with open("agents/domain_knowledge/domain_knowledge.json") as f:
        tree_structure = json.load(f)

    tree_structure = DomainKnowledgeTreeV2.model_validate(tree_structure)
    tool = KnowledgeGenerationTool(
        knowledge_id=1,
        knowledge_status_path="agents/domain_knowledge/knows/knowledge_status.json",
        domain="Sugar Manufacturing",
        role="Process Engineer",
        storage_path="agents/domain_knowledge/knows",
        document_paths=["agents/domain_knowledge/doccs"],
        tree_structure_path="agents/domain_knowledge/domain_knowledge.json",
    )
    print(
        asyncio.run(
            tool._execute(
                user_message="Generate knowledge for all topics in the tree structure",
                counts="Not specified",
                context="Focus on practical applications and real-world scenarios",
            )
        )
    )
