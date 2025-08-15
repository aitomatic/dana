from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
    ToolResult,
)
from dana.api.core.schemas import DomainKnowledgeTree
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc
from typing import Callable
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
    ):
        self.knowledge_status_path = knowledge_status_path
        self.storage_path = storage_path
        self.tree_structure = tree_structure
        self.domain = domain
        self.role = role
        self.tasks = tasks or ["Analyze Information", "Provide Insights", "Answer Questions"]
        self.notifier = notifier
        tool_info = BaseToolInformation(
            name="generate_knowledge",
            description="Generate knowledge for topics. Can generate for a single topic or automatically for all leaf nodes in the tree structure. Checks knowledge status and only generates for topics with status != 'success'. IMPORTANT NOTE: Running this tool takes a long time. Therefore, this tool CANNOT be used until you have received the command or approval from the user to generate knowledge EXPLICITLY.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="mode",
                        type="string",
                        description="Generation mode: 'single' for one topic or 'all_leaves' for all leaf nodes",
                        example="single",
                    ),
                    BaseArgument(
                        name="topic",
                        type="string",
                        description="Topic to generate knowledge about (required for single mode)",
                        example="Current Ratio Analysis",
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
                        example="Focus on liquidity analysis for financial analysts",
                    ),
                ],
                required=["mode"],
            ),
        )
        super().__init__(tool_info)
        self.llm = llm or LLMResource()

    async def _execute(self, mode: str, topic: str = "", counts: str = "", context: str = "") -> ToolResult:
        try:
            if mode == "all_leaves":
                return await self._generate_for_all_leaves(counts, context)
            elif mode == "single":
                if not topic:
                    return ToolResult(
                        name="generate_knowledge", result="❌ Error: Topic is required for single mode generation", require_user=False
                    )
                return await self._generate_for_single_topic(topic, counts, context)
            else:
                return ToolResult(
                    name="generate_knowledge", result=f"❌ Error: Invalid mode '{mode}'. Use 'single' or 'all_leaves'", require_user=False
                )
        except Exception as e:
            logger.error(f"Failed to generate knowledge: {e}")
            return ToolResult(name="generate_knowledge", result=f"❌ Error generating knowledge: {str(e)}", require_user=False)

    async def _generate_for_all_leaves(self, counts: str, context: str) -> ToolResult:
        """Generate knowledge for all leaf nodes in the tree structure."""
        if not self.tree_structure or not self.tree_structure.root:
            return ToolResult(
                name="generate_knowledge", result="❌ Error: No tree structure available for all_leaves mode", require_user=False
            )

        # Extract all leaf paths from the tree
        def extract_leaf_paths(node, current_path=None):
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
                all_paths.extend(extract_leaf_paths(child, new_path))
            return all_paths

        all_leaf_paths = extract_leaf_paths(self.tree_structure.root)
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
            path_str = " → ".join(path)

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
                if self.knowledge_status_path:
                    status_check = self._check_knowledge_status(leaf_topic)
                    if status_check["skip"]:
                        generation_results.append(f"⏭️ Skipped '{leaf_topic}' - already complete")
                        # Stream skip notification
                        if self.notifier:
                            await self.notifier(
                                "generate_knowledge", f"⏭️ Skipped '{leaf_topic}' - already complete", "in_progress", progress
                            )
                        continue

                # Generate knowledge for this leaf
                leaf_context = f"{context}\nTree path: {path_str}\nFocus on this specific aspect within the broader context."
                result = await self._generate_single_knowledge(leaf_topic, counts, leaf_context)

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

        return ToolResult(name="generate_knowledge", result=content, require_user=False)

    async def _generate_for_single_topic(self, topic: str, counts: str, context: str) -> ToolResult:
        """Generate knowledge for a single topic."""
        # Stream start notification
        if self.notifier:
            await self.notifier("generate_knowledge", f"📝 Starting knowledge generation for: {topic}", "in_progress", 0.0)

        # Check knowledge status first
        if self.knowledge_status_path:
            status_check = self._check_knowledge_status(topic)
            if status_check["skip"]:
                # Stream skip notification
                if self.notifier:
                    await self.notifier("generate_knowledge", f"⏭️ Skipped '{topic}' - already complete", "finish", 1.0)
                return ToolResult(
                    name="generate_knowledge",
                    result=f"""📚 Knowledge Generation Skipped

Topic: {topic}
Status: {status_check["status"]}
Reason: {status_check["reason"]}

✅ This topic already has successful knowledge generation.
No action needed - knowledge is up to date.""",
                    require_user=False,
                )

        # Stream progress update - starting generation
        if self.notifier:
            await self.notifier("generate_knowledge", f"🧠 Generating knowledge artifacts for: {topic}", "in_progress", 0.5)

        # Generate the knowledge
        result_content = await self._generate_single_knowledge(topic, counts, context)

        # Stream completion
        if self.notifier:
            await self.notifier("generate_knowledge", f"✅ Completed knowledge generation for: {topic}", "finish", 1.0)

        return ToolResult(name="generate_knowledge", result=result_content, require_user=False)

    async def _generate_single_knowledge(self, topic: str, counts: str, context: str) -> str:
        """Core method to generate knowledge for a single topic."""
        try:
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

**Additional Context**: {context}
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
                    "max_tokens": 1500,  # Increased for comprehensive generation
                }
            )

            response = Misc.safe_asyncio_run(self.llm.query, llm_request)
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
                    persistence_info = self._persist_knowledge(topic, content, result, total_artifacts)
                except Exception as e:
                    logger.error(f"Failed to persist knowledge to disk: {e}")
                    persistence_info = f"\n⚠️ Warning: Knowledge generated but not saved to disk: {str(e)}"

            content += f"\n✅ Knowledge generation complete. Total artifacts: {total_artifacts}"
            if persistence_info:
                content += persistence_info

            # Update knowledge status to success
            if self.knowledge_status_path:
                self._update_knowledge_status(topic, "success", f"Generated {total_artifacts} artifacts")

            return content

        except Exception as e:
            logger.error(f"Failed to generate knowledge for topic {topic}: {e}")
            # Update status to failed on error
            if self.knowledge_status_path:
                self._update_knowledge_status(topic, "failed", str(e))
            return f"❌ Error generating knowledge for {topic}: {str(e)}"

    def _check_knowledge_status(self, topic: str) -> dict:
        """Check if knowledge generation is needed for the given topic."""
        try:
            from pathlib import Path
            import json

            status_file = Path(self.knowledge_status_path)
            if not status_file.exists():
                # No status file means no topics have been processed yet
                return {"skip": False, "status": "not_started", "reason": "No status file found"}

            with open(status_file) as f:
                status_data = json.load(f)

            # Handle new structured format with topics array
            topics = status_data.get("topics", [])

            # Find topic by path or topic name
            topic_entry = None
            for t in topics:
                # Check if path contains the topic or if topic name matches
                if topic in t.get("path", "") or t.get("path", "").split(" - ")[-1] == topic:
                    topic_entry = t
                    break

            if not topic_entry:
                # Topic not found in status, needs to be added
                return {"skip": False, "status": "not_started", "reason": "Topic not found in status file"}

            current_status = topic_entry.get("status", "pending")

            if current_status == "success":
                last_generated = topic_entry.get("last_generated")
                return {
                    "skip": True,
                    "status": current_status,
                    "reason": f"Topic already completed successfully on {last_generated or 'unknown date'}",
                }
            else:
                return {"skip": False, "status": current_status, "reason": f"Topic needs generation (current status: {current_status})"}

        except Exception as e:
            logger.error(f"Error checking knowledge status: {e}")
            # Default to generating if we can't read status
            return {"skip": False, "status": "error", "reason": f"Status check failed: {e}"}

    def _update_knowledge_status(self, topic: str, status: str, message: str = "") -> None:
        """Update the knowledge generation status for the given topic using the structured format."""
        try:
            from pathlib import Path
            from datetime import datetime, UTC
            import json
            import uuid

            status_file = Path(self.knowledge_status_path)

            # Load existing status data or create new structure
            if status_file.exists():
                with open(status_file) as f:
                    status_data = json.load(f)
            else:
                status_data = {"topics": [], "agent_id": "1"}
                # Ensure parent directory exists
                status_file.parent.mkdir(parents=True, exist_ok=True)

            # Ensure topics array exists
            if "topics" not in status_data:
                status_data["topics"] = []

            # Find existing topic entry
            topic_entry = None
            for t in status_data["topics"]:
                # Check if path contains the topic or if topic name matches
                if topic in t.get("path", "") or t.get("path", "").split(" - ")[-1] == topic:
                    topic_entry = t
                    break

            current_time = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

            if topic_entry:
                # Update existing entry
                topic_entry["status"] = status
                topic_entry["last_topic_update"] = current_time
                if status == "success":
                    topic_entry["last_generated"] = current_time
                    topic_entry["error"] = None
                elif status == "failed":
                    topic_entry["error"] = message
                    topic_entry["last_generated"] = None
            else:
                # Create new topic entry
                # Build full path from tree structure (with " - " separators like the example)
                full_path = self._build_full_path_for_topic(topic)

                # Build file path independently (with "/" separators and /knowledge.json)
                actual_file_path = self._build_file_path_for_topic(topic)

                new_entry = {
                    "id": str(uuid.uuid4()),
                    "path": full_path,
                    "file": actual_file_path,
                    "status": status,
                    "last_generated": current_time if status == "success" else None,
                    "last_topic_update": current_time,
                    "error": message if status == "failed" else None,
                }
                status_data["topics"].append(new_entry)

            # Save updated status
            with open(status_file, "w") as f:
                json.dump(status_data, f, indent=2)

            logger.info(f"Updated knowledge status for '{topic}': {status}")

        except Exception as e:
            logger.error(f"Failed to update knowledge status: {e}")

    def _build_full_path_for_topic(self, topic: str) -> str:
        """Build full path from root to topic using tree structure with ' - ' separators."""
        if not self.tree_structure or not self.tree_structure.root:
            # Fallback: use domain if no tree structure
            return f"{self.domain} - {topic}"

        # Find the path to the topic in the tree
        def find_path_to_topic(node, target_topic, current_path=None):
            if current_path is None:
                current_path = []

            current_path = current_path + [node.topic]

            # Check if this is the target topic
            if node.topic == target_topic:
                return current_path

            # Search in children
            for child in node.children:
                path = find_path_to_topic(child, target_topic, current_path)
                if path:
                    return path

            return None

        path = find_path_to_topic(self.tree_structure.root, topic)
        if path:
            return " - ".join(path)
        else:
            # Fallback if topic not found in tree
            return f"{self.tree_structure.root.topic} - {topic}"

    def _build_file_path_for_topic(self, topic: str) -> str:
        """Build file path from root to topic using tree structure with '/' separators."""
        if not self.tree_structure or not self.tree_structure.root:
            # Fallback: use domain if no tree structure
            return f"{self.domain}/{topic}/knowledge.json"

        # Find the path to the topic in the tree
        def find_path_to_topic(node, target_topic, current_path=None):
            if current_path is None:
                current_path = []

            current_path = current_path + [node.topic]

            # Check if this is the target topic
            if node.topic == target_topic:
                return current_path

            # Search in children
            for child in node.children:
                path = find_path_to_topic(child, target_topic, current_path)
                if path:
                    return path

            return None

        path = find_path_to_topic(self.tree_structure.root, topic)
        if path:
            # Convert to file path format with / separators
            return "/".join(path) + "/knowledge.json"
        else:
            # Fallback if topic not found in tree
            return f"{self.tree_structure.root.topic}/{topic}/knowledge.json"

    def _get_knowledge_file_path(self, topic: str) -> str:
        """Wrapper for backward compatibility - use _build_file_path_for_topic directly."""
        return self._build_file_path_for_topic(topic)

    def _persist_knowledge(self, topic: str, content: str, result_data: dict, total_artifacts: int) -> str:
        """Persist generated knowledge to disk storage."""
        from pathlib import Path
        from datetime import datetime, UTC
        import json

        # Get the file path structure
        file_path = self._build_file_path_for_topic(topic)

        # Create full path from storage directory
        storage_dir = Path(self.storage_path)
        full_file_path = storage_dir / file_path

        # Create the directory structure
        full_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare knowledge data for storage
        knowledge_data = {
            "topic": topic,
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
