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
        question_batch_size: int = 5,
    ):
        self.knowledge_id = knowledge_id
        self.knowledge_status_path = knowledge_status_path
        self.storage_path = storage_path
        self.document_paths = document_paths or []
        self.tree_structure_path = tree_structure_path
        # Load tree structure from path if provided
        self.tree_structure = None
        if tree_structure_path:
            self.tree_structure = self._load_tree_structure()
        self.domain = domain
        self.role = role
        self.tasks = tasks or ["Analyze Information", "Provide Insights", "Answer Questions"]
        self.question_batch_size = question_batch_size

        # Initialize RAG resource if document paths are provided
        if self.document_paths:
            self.rag_resource = RAGResource(self.document_paths, debug=True, return_raw=True, reranking=True)
        else:
            self.rag_resource = None

        # Import WS manager inside constructor to avoid circular imports
        if ws_manager is None:
            from dana.studio.api.routers.v2.ws.domain_knowledge_ws import kp_generation_ws_notifier

            ws_manager = kp_generation_ws_notifier

        self.notifier = ws_manager.get_notifier(str(knowledge_id))

        # Get WebSocket manager for real-time status updates
        try:
            from dana.studio.api.server.server import ws_manager as server_ws_manager

            self.server_ws_manager = server_ws_manager
        except ImportError:
            logger.warning("WebSocket manager not available for real-time updates")
            self.server_ws_manager = None

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
            try:
                leaf_topic = path[-1]  # Last element in path is the leaf topic
                path_str = self._path_parts_to_string(path)

                # Calculate progress percentage
                progress = (i / len(all_leaf_paths)) if len(all_leaf_paths) > 0 else 0.0

                logger.info(f"Processing leaf {i + 1}/{len(all_leaf_paths)}: {leaf_topic}")

                # Check if already generated
                if self.status_manager:
                    if self.status_manager.is_success(path_str):
                        generation_results.append(f"⏭️ Skipped '{leaf_topic}' - already complete")
                        continue

                # Stream progress update
                await self._notify(
                    "generate_knowledge", f"📝 Processing {i + 1}/{len(all_leaf_paths)}: {leaf_topic}", "in_progress", progress
                )

                # Initialize status manager for the current path if it hasn't been done yet
                await self._initialize_path_in_status_manager(path)

                # Build file path and check if knowledge.json exists
                if not self.storage_path:
                    raise ValueError("storage_path is required for knowledge generation")
                file_path = self._build_file_path_from_path_parts(path)
                storage_dir = Path(self.storage_path)
                full_file_path = storage_dir / file_path

                if not full_file_path.exists():
                    generation_results.append(f"⚠️ Skipped '{leaf_topic}' - no knowledge.json found (run question bank generation first)")
                    continue

                # Read existing knowledge.json to extract questions
                knowledge_node = await self._read_questions_from_knowledge_json(full_file_path)
                if not knowledge_node or not knowledge_node.knowledges:
                    generation_results.append(f"⚠️ Skipped '{leaf_topic}' - no questions found in knowledge.json")
                    continue

                # Generate knowledge from questions
                raw_knowledges = await self._generate_knowledge_from_questions(path, knowledge_node.knowledges)
                completed_knowledges = await self._transform_knowledge_units(raw_knowledges)

                # Update the knowledge.json with generated content
                await self._update_knowledge_json(full_file_path, completed_knowledges)

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

                # Broadcast WebSocket notification for success
                if self.server_ws_manager:
                    try:
                        topic_entry = self.status_manager.get_topic_entry(path_str) if self.status_manager else None
                        if topic_entry:
                            await self.server_ws_manager.broadcast(
                                {
                                    "type": "knowledge_status_update",
                                    "topic_id": topic_entry.get("id"),
                                    "path": topic_entry.get("path"),
                                    "status": "success",
                                    "last_generated": topic_entry.get("last_generated"),
                                }
                            )
                            logger.info(f"Broadcasted success status for: {path_str}")
                    except Exception as e:
                        logger.warning(f"Failed to broadcast success status for {path_str}: {e}")

            except Exception as e:
                logger.error(f"Failed to generate knowledge for {path}: {e}")
                if self.status_manager:
                    self.status_manager.set_status(path_str, "failed")

                # Broadcast WebSocket notification for failure
                if self.server_ws_manager:
                    try:
                        topic_entry = self.status_manager.get_topic_entry(path_str) if self.status_manager else None
                        if topic_entry:
                            await self.server_ws_manager.broadcast(
                                {
                                    "type": "knowledge_status_update",
                                    "topic_id": topic_entry.get("id"),
                                    "path": topic_entry.get("path"),
                                    "status": "failed",
                                }
                            )
                            logger.info(f"Broadcasted failed status for: {path_str}")
                    except Exception as e:
                        logger.warning(f"Failed to broadcast failed status for {path_str}: {e}")

                failed_generations += 1
                generation_results.append(f"❌ Failed '{leaf_topic}': {str(e)}")
                traceback.print_exc()

            await self._notify(
                "generate_knowledge",
                f"✅ Completed '{leaf_topic}' - {i + 1}/{len(all_leaf_paths)} done",
                "in_progress",
                (i + 1) / len(all_leaf_paths),
            )

        await self._notify("generate_knowledge", f"✅ Knowledge generation complete. Summary: \n{status_text}", "finish", 1.0)

        logger.info(f"Knowledge generation completed: {successful_generations} successful, {failed_generations} failed")

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

                logger.info(f"Generating summary {i}/{len(knowledge_files)}: {topic_name}")
                await self._generate_knowledge_summary(file_path, topic_name)

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

Provide an overview paragraph with less than 500 words to brief me about this knowledge pack. Also include 5 most important questions that can be used for further knowledge acquisition to augment the current knowledge, 3 most key concepts and referenced document names if any

RESPONSE FORMAT:
```markdown
# Summary
...

# Key Concepts
- concept_1
- concept_2
- ...

# Most Important Questions
- question_1
- question_2
- ...

# Referenced Documents
- document_name_1
- document_name_2
- ...
```
"""

            # Generate summary using the reason function
            summary = await asyncio.to_thread(reason, summary_prompt)

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

            # Create prompt for template generation
            template_prompt = f"""
Based on the following knowledge summaries from multiple topics:

{formatted_summaries}

Generate a conversational interview template for a {self.role} expert in {self.domain}.

Requirements:
1. Create 3-5 natural, open-ended opening questions per topic
2. Add relationship listening prompts (what connections to listen for between topics)
3. Include a follow-up question framework
4. Keep it conversational and expert-driven
5. No rigid detailed questions - let expert guide the conversation

Template Structure:
# Master Interview Template: {self.domain} - {self.role}

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
- What else should I know about this?
"""

            # Generate template using the reason function
            logger.info(f"Generating master interview template for {len(all_summaries_data)} topics...")
            template_content = await asyncio.to_thread(reason, template_prompt)

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

        async def generate_knowledge(question: str, chunks: list[NodeWithScore], path_str: str) -> RawFormatKnowledge:
            if chunks:
                res = await asyncio.to_thread(
                    reason, KNOWLEDGE_EXTRACTION_PROMPT.format(path=path_str, question=question, chunks=_format_chunks(chunks))
                )
                from_doc = True
            else:
                res = await asyncio.to_thread(
                    reason, KNOWLEDGE_GENERATION_PROMPT.format(path=path_str, question=question, role=self.role, domain=self.domain)
                )
                from_doc = False
            return RawFormatKnowledge(question=question, chunks=chunks, knowledge=res, from_doc=from_doc)

        # Extract questions from existing knowledges
        all_questions = []
        for knowledge in existing_knowledges:
            if knowledge.question:
                all_questions.append(knowledge.question)

        # Process questions in batches
        question_batches = []
        for i in range(0, len(all_questions), self.question_batch_size):
            batch = all_questions[i : i + self.question_batch_size]
            question_batches.append("\n".join(batch))

        # Query RAG for relevant chunks if available
        if self.rag_resource and self.rag_resource.filenames and any([fn != "system" for fn in self.rag_resource.filenames]):
            relevant_chunks = await asyncio.gather(
                *[self.rag_resource.query(question_batch, num_results=30) for question_batch in question_batches]
            )
        else:
            relevant_chunks = [[] for _ in question_batches]

        # Generate knowledge for each batch
        async_tasks = []
        path_str = " → ".join(paths)
        for question_batch, chunks in zip(question_batches, relevant_chunks, strict=False):
            if question_batch:
                # Ensure chunks is a list of NodeWithScore
                if not isinstance(chunks, list):
                    chunks = []
                async_tasks.append(generate_knowledge(question_batch, chunks, path_str))

        knowledges = await asyncio.gather(*async_tasks)
        return knowledges

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
