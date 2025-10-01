from typing import Any
from llama_index.core.schema import NodeWithScore
from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
    ToolResult,
)
from dana.api.core.schemas import DomainKnowledgeTree, DomainNode
from dana.api.services.knowledge_status_manager import KnowledgeStatusManager
from collections.abc import Callable
from dana.core.lang.sandbox_context import SandboxContext
from dana.libs.corelib.py_wrappers.py_reason import py_reason as reason_function
from dana.api.services.intent_detection.intent_handlers.handler_prompts.knowledge_ops_prompts import (
    GENERATE_QUESTION_PROMPT,
    ACCESS_COVERAGE_PROMPT,
    KNOWLEDGE_EXTRACTION_PROMPT,
    KNOWLEDGE_GENERATION_PROMPT,
)
import logging
import asyncio
import re
from dana.common.sys_resource.rag.rag_resource import RAGResource
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


class GenerateKnowledgeTool(BaseTool):
    def __init__(
        self,
        knowledge_status_path: str | None = None,
        storage_path: str | None = None,
        document_path: str | None = None,
        tree_structure: DomainKnowledgeTree | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
        tasks: list[str] | None = None,
        notifier: Callable[[str, str, str, float | None], None] | None = None,
        agent_id: str | None = None,
        question_batch_size: int = 5,
    ):
        self.knowledge_status_path = knowledge_status_path
        self.storage_path = storage_path
        self.document_path = document_path
        self.tree_structure = tree_structure
        self.domain = domain
        self.role = role
        self.tasks = tasks or ["Analyze Information", "Provide Insights", "Answer Questions"]
        self.question_batch_size = question_batch_size
        self.notifier = notifier

        # Initialize KnowledgeStatusManager
        self.status_manager = None
        if knowledge_status_path:
            self.status_manager = KnowledgeStatusManager(knowledge_status_path, agent_id)

        tool_info = BaseToolInformation(
            name="generate_knowledge",
            description="Generate knowledge for all leaf nodes in the tree structure. Checks knowledge status and only generates for topics with status != 'success'.",
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
        if document_path:
            self.rag_resource = RAGResource([document_path], debug=True, return_raw=True, reranking=True)
        else:
            self.rag_resource = None

    async def _execute(self, user_message: str = "", counts: str = "", context: str = "") -> ToolResult:
        try:
            return await self._generate_for_all_leaves(user_message, counts, context)
        except Exception as e:
            logger.error(f"Failed to generate knowledge: {e}")
            return ToolResult(
                name="generate_knowledge",
                result=self._build_structured_response(user_message, f"❌ Error generating knowledge: {str(e)}"),
                require_user=False,
            )

    async def _extract_leaf_paths(self, node: DomainNode, current_path: list[str] = None) -> list[list[str]]:
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

    async def _generate_for_all_leaves(self, user_message: str, counts: str, context: str) -> ToolResult:
        """Generate knowledge for all leaf nodes in the tree structure."""
        if not self.tree_structure or not self.tree_structure.root:
            return ToolResult(
                name="generate_knowledge",
                result=self._build_structured_response(user_message, "❌ Error: No tree structure available for all_leaves mode"),
                require_user=False,
            )

        all_leaf_paths = await self._extract_leaf_paths(self.tree_structure.root)
        logger.info(f"Found {len(all_leaf_paths)} leaf nodes to process")

        # Stream initial progress
        if self.notifier:
            await self.notifier("generate_knowledge", f"🌳 Starting bulk generation for {len(all_leaf_paths)} topics", "in_progress", 0.0)

        # Generate knowledge for each leaf
        successful_generations = 0
        failed_generations = 0
        status_text = ""
        generation_results = []

        for i, path in enumerate(all_leaf_paths):
            try:
                leaf_topic = path[-1]  # Last element in path is the leaf topic
                # Exclude root node in path string to match knowledge status format
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
                if self.notifier:
                    await self.notifier(
                        "generate_knowledge", f"📝 Processing {i + 1}/{len(all_leaf_paths)}: {leaf_topic}", "in_progress", progress
                    )

                # Initialize status manager for the current path if it hasn't been done yet
                await self._initialize_path_in_status_manager(path)

                # Create storage directory if it doesn't exist
                file_path = self._build_file_path_from_path_parts(path)
                storage_dir = Path(self.storage_path)
                full_file_path = storage_dir / file_path
                full_file_path.parent.mkdir(parents=True, exist_ok=True)

                if not full_file_path.exists():
                    questions = await self._generate_questions_for_topic_paths(path)
                    raw_knowledges = await self._generate_knowledge_for_topic_paths(path, questions)
                    knowledges = await self._transform_knowledge_units(raw_knowledges)
                    knowledge_node = KnowledgeNode(path_parts=path, knowledges=knowledges)
                    with open(full_file_path, "w", encoding="utf-8") as f:
                        json.dump(knowledge_node.model_dump(mode="json"), f, indent=4)
                    successful_generations += 1
                    status_text += f"- {leaf_topic}: {knowledge_node.get_overview()}\n"
                self.status_manager.set_status(path_str, "success")
            except Exception as e:
                logger.error(f"Failed to generate knowledge for {path}: {e}")
                self.status_manager.set_status(path_str, "failed")
                failed_generations += 1
                traceback.print_exc()
            if self.notifier:
                await self.notifier(
                    "generate_knowledge",
                    f"✅ Completed '{leaf_topic}' - {i + 1}/{len(all_leaf_paths)} done",
                    "in_progress",
                    (i + 1) / len(all_leaf_paths),
                )

        if self.notifier:
            await self.notifier(
                "generate_knowledge", f"✅ Knowledge generation complete. Knowledge overview: \n{status_text}", "finish", 1.0
            )

        return ToolResult(
            name="generate_knowledge",
            result=self._build_structured_response(user_message, f"✅ Knowledge generation complete. Knowledge overview: \n{status_text}"),
            require_user=False,
        )

    async def _generate_questions_for_topic_paths(self, paths: list[str]) -> str:
        current_confidence = 0
        count = 0
        path = " → ".join(paths)
        tasks = "\n".join([f"- {task}" for task in self.tasks])
        suggestion = "Intial generation"
        questions = ""
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
            questions = questions + f"\n{new_questions}"
            confidence_result = await asyncio.to_thread(
                reason,
                prompt=ACCESS_COVERAGE_PROMPT.format(
                    questions=questions, role=self.role, domain=self.domain, tasks=tasks, confidence=current_confidence
                ),
                target_type=dict,
            )
            current_confidence = confidence_result["confidence"]
            suggestion = confidence_result["suggestion"]
        return questions

    async def _generate_knowledge_for_topic_paths(self, paths: list[str], questions: str) -> list[RawFormatKnowledge]:
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

        regex = re.compile(r"^\*Question [0-9]*\*.+$", re.MULTILINE)
        question_list = re.findall(regex, questions)
        new_question_list = []
        start = 0
        for start in range(0, len(question_list), self.question_batch_size):
            end = start + self.question_batch_size
            new_question_list.append("\n".join(question_list[start:end]))
        question_list = new_question_list
        if self.rag_resource.filenames and any([fn != "system" for fn in self.rag_resource.filenames]):
            relevant_chunks = await asyncio.gather(*[self.rag_resource.query(question, num_results=30) for question in question_list])
        else:
            relevant_chunks = [[] for _ in question_list]
        async_tasks = []
        path_str = " → ".join(paths)
        for question, chunks in zip(question_list, relevant_chunks, strict=False):
            if question:
                async_tasks.append(generate_knowledge(question, chunks, path_str))
        knowledges = await asyncio.gather(*async_tasks)
        return knowledges

    async def _transform_knowledge_units(self, knowledge_units: list[RawFormatKnowledge]) -> list[Knowledge]:
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
        # For file paths, we need to include the root node
        # The path_parts excludes the root, so add it back

        # Convert to file path format with "/" separators
        file_path = "/".join(path_parts)
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

    tasks = tasks = [
        # Storage Systems & Technologies
        "Design and manage silo storage for bulk sugar",
        "Oversee warehouse storage for bagged sugar",
        "Implement bulk storage solutions depending on capacity needs",
        "Regulate temperature in sugar storage facilities",
        "Control humidity levels to prevent sugar caking",
        "Maintain proper ventilation systems for sugar storage areas",
        "Operate and maintain conveyors for sugar handling",
        "Operate and maintain elevators for sugar transfer",
        "Operate and maintain pneumatic systems for sugar transport",
        "Implement pest control programs in storage and handling areas",
        "Install foreign body detection systems for sugar quality assurance",
        "Develop and enforce cleaning protocols for storage and handling facilities",
        # Process Optimization & Efficiency
        "Conduct material flow mapping of sugar movement",
        "Identify bottlenecks in sugar storage and handling processes",
        "Integrate SCADA systems for process monitoring and control",
        "Deploy sensors and instrumentation for real-time monitoring",
        "Monitor energy consumption in sugar handling and storage",
        "Implement efficiency improvements in conveying and storage systems",
        "Reduce waste such as spillage, contamination, and product loss",
        "Promote continuous improvement initiatives in sugar handling",
        # Quality Assurance & Compliance
        "Apply standardized sampling methods for sugar quality testing",
        "Perform moisture content testing to prevent caking and spoilage",
        "Carry out granule size analysis to ensure consistency",
        "Ensure compliance with food safety standards",
        "Maintain adherence to British and EU sugar storage regulations",
        "Implement batch tracking systems for sugar traceability",
        "Maintain documentation practices for audits and quality checks",
        # Health, Safety & Environmental Management
        "Identify hazards such as dust explosion risks and slip hazards",
        "Develop and implement safe operating procedures",
        "Plan and conduct emergency response drills",
        "Implement dust control measures such as filters and scrubbers",
        "Manage waste disposal from sugar dust and rejected product",
        "Conduct staff training programs on sugar handling and safety",
    ]

    import asyncio

    tree_structure = DomainKnowledgeTree.model_validate(tree_structure)
    tool = GenerateKnowledgeTool(
        knowledge_status_path="agents/domain_knowledge/knows/knowledge_status.json",
        domain="Sugar Manufacturing",
        role="Process Engineer",
        storage_path="agents/domain_knowledge/knows",
        document_path="agents/domain_knowledge/doccs",
        tasks=tasks,
        tree_structure=tree_structure,
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

    # import pickle
    # with open("agents/domain_knowledge/knowledge.pkl", "rb") as f:
    #     knowledges = pickle.load(f)
    # asyncio.run(tool._transform_knowledge_units(knowledges))
