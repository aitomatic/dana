from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
    ToolResult,
)
from dana.api.core.schemas import DomainKnowledgeTree, DomainNode
from dana.api.services.knowledge_status_manager import KnowledgeStatusManager
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc
from collections.abc import Callable
import logging

logger = logging.getLogger(__name__)


class GenerateKnowledgeTool(BaseTool):
    def __init__(
        self,
        llm: LLMResource | None = None,
        knowledge_status_path: str | None = None,
        storage_path: str | None = None,
        tree_structure: DomainKnowledgeTree | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
        tasks: list[str] | None = None,
        notifier: Callable[[str, str, str, float | None], None] | None = None,
        agent_id: str | None = None,
    ):
        self.knowledge_status_path = knowledge_status_path
        self.storage_path = storage_path
        self.tree_structure = tree_structure
        self.domain = domain
        self.role = role
        self.tasks = tasks or ["Analyze Information", "Provide Insights", "Answer Questions"]
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
        self.llm = llm or LLMResource()

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
        total_artifacts = 0
        generation_results = []

        for i, path in enumerate(all_leaf_paths):
            leaf_topic = path[-1]  # Last element in path is the leaf topic
            # Exclude root node in path string to match knowledge status format
            path_str = self._path_parts_to_string(path)

            # Calculate progress percentage
            progress = (i / len(all_leaf_paths)) if len(all_leaf_paths) > 0 else 0.0

            logger.info(f"Processing leaf {i + 1}/{len(all_leaf_paths)}: {leaf_topic}")

            # Stream progress update
            if self.notifier:
                await self.notifier(
                    "generate_knowledge", f"📝 Processing {i + 1}/{len(all_leaf_paths)}: {leaf_topic}", "in_progress", progress
                )

            try:
                # Check if already generated
                if self.status_manager:
                    path_str = self._path_parts_to_string(path)
                    if self.status_manager.is_success(path_str):
                        generation_results.append(f"⏭️ Skipped '{leaf_topic}' - already complete")
                        # Stream skip notification
                        if self.notifier:
                            await self.notifier(
                                "generate_knowledge", f"⏭️ Skipped '{leaf_topic}' - already complete", "in_progress", progress
                            )
                        continue

                # Initialize status manager for the current path if it hasn't been done yet
                await self._initialize_path_in_status_manager(path)

                # Generate knowledge for this leaf
                leaf_context = f"{context}\nTree path: {path_str}\nFocus on this specific aspect within the broader context."
                result = await self._generate_single_knowledge(path, counts, leaf_context)

                if "Error" not in result:
                    successful_generations += 1
                    # Extract artifact count from result
                    artifacts_match = result.split("Total artifacts: ")
                    if len(artifacts_match) > 1:
                        try:
                            total_artifacts += int(artifacts_match[1].split()[0])
                        except ValueError:
                            pass
                    generation_results.append(f"✅ Generated '{leaf_topic}' - {path_str}")

                    # Stream success notification
                    if self.notifier:
                        await self.notifier(
                            "generate_knowledge",
                            f"✅ Completed '{leaf_topic}' - {successful_generations}/{len(all_leaf_paths)} done",
                            "in_progress",
                            (i + 1) / len(all_leaf_paths),
                        )
                else:
                    failed_generations += 1
                    generation_results.append(f"❌ Failed '{leaf_topic}' - {result}")

                    # Stream failure notification
                    if self.notifier:
                        await self.notifier(
                            "generate_knowledge",
                            f"❌ Failed '{leaf_topic}' - {failed_generations} failures so far",
                            "in_progress",
                            (i + 1) / len(all_leaf_paths),
                        )

            except Exception as e:
                failed_generations += 1
                generation_results.append(f"❌ Failed '{leaf_topic}' - {str(e)}")
                logger.error(f"Failed to generate knowledge for leaf {leaf_topic}: {str(e)}")

                # Stream error notification
                if self.notifier:
                    await self.notifier(
                        "generate_knowledge", f"❌ Error processing '{leaf_topic}': {str(e)}", "error", (i + 1) / len(all_leaf_paths)
                    )

        # Format comprehensive summary
        content = f"""🌳 Bulk Knowledge Generation Complete

📊 **Generation Summary:**
- Total leaf nodes: {len(all_leaf_paths)}
- Successfully generated: {successful_generations}
- Failed generations: {failed_generations}
- Total artifacts created: {total_artifacts}

📋 **Generation Results:**
"""
        for result in generation_results:
            content += f"{result}\n"

        if failed_generations == 0:
            content += "\n🎉 All leaf nodes have been successfully processed!"
        else:
            content += f"\n⚠️ {failed_generations} leaf nodes failed - check logs for details"

        # Stream completion notification
        if self.notifier:
            await self.notifier(
                "generate_knowledge",
                f"🎉 Bulk generation complete! {successful_generations} successful, {failed_generations} failed",
                "finish",
                1.0,
            )

        return ToolResult(name="generate_knowledge", result=self._build_structured_response(user_message, content), require_user=False)

    async def _generate_single_knowledge(self, path_parts: list[str], counts: str, context: str) -> str:
        """Core method to generate knowledge for a single path."""
        try:
            # Extract the actual topic name for generation (last part of path)
            topic = path_parts[-1] if path_parts else "unknown"

            # Always generate all types: facts, procedures, heuristics
            types_list = ["facts", "procedures", "heuristics"]

            # Build task descriptions for context
            tasks_str = "\n".join([f"- {task}" for task in self.tasks])

            # Generate domain/role/task-aware prompt
            knowledge_prompt = f"""You are a {self.role} working in the {self.domain} domain. Generate comprehensive knowledge about "{topic}" that is specifically tailored for someone in your role.

**Your Role**: {self.role}
**Domain**: {self.domain}  
**Key Tasks You Must Support**:
{tasks_str}

**Additional Constraints for this generation**: {context}
**Target Counts**: {counts if counts else "appropriate amounts of each"}

Generate knowledge that is immediately applicable and relevant for a {self.role} performing the above tasks. Focus on practical, actionable knowledge that supports real-world scenarios in {self.domain}.

Generate the following knowledge:

1. FACTS (definitions, formulas, key concepts):
   - Essential facts that a {self.role} MUST know about {topic}
   - Include formulas, ratios, thresholds specific to {self.domain}
   - Focus on facts directly applicable to: {", ".join(self.tasks)}

2. PROCEDURES (step-by-step workflows):
   - Detailed procedures that a {self.role} would follow for {topic}
   - Step-by-step workflows specific to {self.domain} context
   - Include decision points, inputs/outputs, and tools used
   - Address common scenarios in: {", ".join(self.tasks)}

3. HEURISTICS (best practices and rules of thumb):
   - Expert insights and judgment calls for {topic}
   - Red flags and warning signs specific to {self.domain}
   - Rules of thumb that experienced {self.role}s use
   - Decision-making guidelines for: {", ".join(self.tasks)}

Return as JSON:
{{
    "facts": [
        {{"fact": "content", "type": "definition|formula|data"}},
        ...
    ],
    "procedures": [
        {{
            "name": "Procedure name",
            "steps": ["Step 1", "Step 2", ...],
            "purpose": "Why this is needed"
        }},
        ...
    ],
    "heuristics": [
        {{
            "rule": "The heuristic",
            "explanation": "Why it works",
            "example": "Example application"
        }},
        ...
    ]
}}"""

            llm_request = BaseRequest(
                arguments={
                    "messages": [{"role": "user", "content": knowledge_prompt}],
                    "temperature": 0.1,
                    "max_tokens": 8000,  # Increased for comprehensive generation
                }
            )

            response = await self.llm.query(llm_request)
            result = Misc.text_to_dict(Misc.get_response_content(response))

            # Format the comprehensive output
            content = f"""📚 Generated Knowledge for: {topic}

"""

            # Process facts if requested
            if "facts" in types_list and "facts" in result:
                facts = result.get("facts", [])
                content += f"📄 **Facts ({len(facts)})**\n"
                for i, fact_item in enumerate(facts, 1):
                    fact = fact_item.get("fact", "")
                    fact_type = fact_item.get("type", "general")
                    content += f"{i}. [{fact_type.title()}] {fact}\n"
                content += "\n"

            # Process procedures if requested
            if "procedures" in types_list and "procedures" in result:
                procedures = result.get("procedures", [])
                content += f"📋 **Procedures ({len(procedures)})**\n"
                for i, proc in enumerate(procedures, 1):
                    name = proc.get("name", f"Procedure {i}")
                    steps = proc.get("steps", [])
                    purpose = proc.get("purpose", "")

                    content += f"\n{i}. {name}"
                    if purpose:
                        content += f"\n   Purpose: {purpose}"
                    content += "\n   Steps:"

                    for j, step in enumerate(steps, 1):
                        content += f"\n     {j}. {step}"
                    content += "\n"

            # Process heuristics if requested
            if "heuristics" in types_list and "heuristics" in result:
                heuristics = result.get("heuristics", [])
                content += f"\n💡 **Heuristics ({len(heuristics)})**\n"
                for i, heuristic in enumerate(heuristics, 1):
                    rule = heuristic.get("rule", "")
                    explanation = heuristic.get("explanation", "")
                    example = heuristic.get("example", "")

                    content += f"\n{i}. {rule}"
                    if explanation:
                        content += f"\n   Why: {explanation}"
                    if example:
                        content += f"\n   Example: {example}"
                    content += "\n"

            # Summary
            total_artifacts = len(result.get("facts", [])) + len(result.get("procedures", [])) + len(result.get("heuristics", []))

            # Persist knowledge to disk if storage path is provided
            persistence_info = ""
            if self.storage_path:
                try:
                    persistence_info = self._persist_knowledge(path_parts, content, result, total_artifacts)
                except Exception as e:
                    logger.error(f"Failed to persist knowledge to disk: {e}")
                    persistence_info = f"\n⚠️ Warning: Knowledge generated but not saved to disk: {str(e)}"

            content += f"\n✅ Knowledge generation complete. Total artifacts: {total_artifacts}"
            if persistence_info:
                content += persistence_info

            # Update knowledge status to success
            if self.status_manager:
                path_str = self._path_parts_to_string(path_parts)
                self.status_manager.set_status(path_str, "success")

            return content

        except Exception as e:
            path_str = self._path_parts_to_string(path_parts)
            logger.error(f"Failed to generate knowledge for path {path_str}: {e}")
            # Update status to failed on error
            if self.status_manager:
                path_str = self._path_parts_to_string(path_parts)
                self.status_manager.set_status(path_str, "failed", str(e))
            return f"❌ Error generating knowledge for {path_str}: {str(e)}"

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

    def _persist_knowledge(self, path_parts: list[str], content: str, result_data: dict, total_artifacts: int) -> str:
        """Persist generated knowledge to disk storage."""
        from pathlib import Path
        from datetime import datetime, UTC
        import json

        # Get the file path structure
        file_path = self._build_file_path_from_path_parts(path_parts)

        # Create full path from storage directory
        storage_dir = Path(self.storage_path)
        full_file_path = storage_dir / file_path

        # Create the directory structure
        full_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare knowledge data for storage
        knowledge_data = {
            "topic": path_parts[-1] if path_parts else "unknown",
            "generated_at": datetime.now(UTC).isoformat(),
            "total_artifacts": total_artifacts,
            "content_summary": f"Generated {total_artifacts} knowledge artifacts",
            "structured_data": result_data,
            "status": "persisted",
        }

        # Save to JSON file using the new path structure
        with open(full_file_path, "w", encoding="utf-8") as f:
            json.dump(knowledge_data, f, indent=2, ensure_ascii=False)

        return f"""

💾 **Knowledge Persisted Successfully**
📁 Storage Location: {full_file_path}
📊 File Size: {full_file_path.stat().st_size} bytes
🕒 Saved At: {datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")}
✅ Status: Ready for agent usage"""

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
