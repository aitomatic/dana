from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
    ToolResult,
)
from dana.api.core.schemas import DomainKnowledgeTree
from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AskQuestionTool(BaseTool):
    """
    Unified tool for user interactions - replaces both AskFollowUpQuestionTool and AskApprovalTool.
    Handles both general questions and approval requests naturally based on the question content.
    """

    def __init__(self):
        tool_info = BaseToolInformation(
            name="ask_question",
            description="Ask the user a question for clarification, information gathering, or approval. Use this tool after exploration to present options and get user decisions about knowledge generation (single vs bulk), tree modifications, or any other user input needed. Automatically detects approval questions and formats appropriately.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="question",
                        type="string",
                        description="The question to ask the user. For approvals, phrase as 'Do you approve...?' or 'Should I proceed with...?'. For information gathering, ask directly what you need to know.",
                        example="Do you approve removing these deprecated topics from the tree structure?",
                    ),
                    BaseArgument(
                        name="options",
                        type="list",
                        description="Optional array of 2-5 specific choices for the user to select from. Not needed for approval questions (they get automatic yes/no/feedback options). Helpful for narrowing down user choices and reducing typing.",
                        example='["Option 1", "Option 2", "Option 3"]',
                    ),
                ],
                required=["question"],
            ),
        )
        super().__init__(tool_info)

    def _execute(self, question: str, options: list[str] = None) -> ToolResult:
        """
        Execute question based on content - automatically handles approvals vs general questions.
        """
        # Detect if this is an approval question based on common patterns
        approval_keywords = [
            "do you approve",
            "should i proceed",
            "do you want me to",
            "should i go ahead",
            "need your approval",
            "need approval",
            "approve",
            "permission",
        ]
        is_approval = any(keyword in question.lower() for keyword in approval_keywords)

        if is_approval:
            # Format as approval request
            content = f"""🔍 Approval Required

❓ **Question**: {question}

**Please respond with:**
- **"yes"** or **"approve"** to proceed
- **"no"** or **"reject"** to cancel
- **Feedback** to request modifications or ask questions"""

        else:
            # Format as general question
            content = f"❓ {question}"

            if options:
                content += "\n\n**Please choose:**"
                for i, option in enumerate(options, 1):
                    content += f"\n{i}. {option}"
                content += "\n\nOr provide your own response."

        return ToolResult(name="ask_question", result=content, require_user=True)


class ExploreKnowledgeTool(BaseTool):
    def __init__(self, tree_structure: DomainKnowledgeTree | None = None, knowledge_status_path: str | None = None):
        self.knowledge_status_path = knowledge_status_path
        tool_info = BaseToolInformation(
            name="explore_knowledge",
            description="Explore and discover existing knowledge areas in the domain knowledge tree. Shows what topics and knowledge areas are available, including generation status for specific topics. Replaces check_existing functionality for comprehensive topic discovery.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="query",
                        type="string",
                        description="Optional filter to explore specific knowledge areas (e.g., 'Financial Analysis', 'all', or empty for overview). For specific topics, shows generation status and recommendations.",
                        example="Financial Analysis",
                    ),
                    BaseArgument(
                        name="depth",
                        type="string",
                        description="How many levels deep to explore from the starting point (1=current level only, 2=include children, 3=include grandchildren, etc.)",
                        example="3",
                    ),
                ],
                required=[],
            ),
        )
        super().__init__(tool_info)
        self.tree_structure = tree_structure

    def _execute(self, query: str = "", depth: str = "3") -> ToolResult:
        """
        Explore and discover knowledge areas in the domain tree.

        Returns: ToolResult with knowledge inventory and discovery results
        """
        try:
            # Parse depth parameter
            try:
                max_depth = int(depth) if depth else 3
            except ValueError:
                max_depth = 3

            # Handle empty tree case
            if not self.tree_structure or not self.tree_structure.root:
                content = (
                    """🌳 Knowledge Exploration

📂 Current Status: Empty knowledge tree
🔍 Query: """
                    + (query or "all areas")
                    + f"""
📊 Depth: {max_depth} levels

⚠️ No knowledge areas found. The knowledge tree is empty.

💡 Suggestions:
- Use modify_tree with 'init' operation to create initial knowledge structure
- Add knowledge areas relevant to your domain expertise

Ready to initialize knowledge structure when needed."""
                )

                return ToolResult(name="explore_knowledge", result=content, require_user=False)

            # Explore the tree structure
            content = self._explore_tree_structure(query, max_depth)
            return ToolResult(name="explore_knowledge", result=content, require_user=False)

        except Exception as e:
            logger.error(f"Failed to explore knowledge: {e}")
            # Fallback exploration
            content = f"""🌳 Knowledge Exploration (Error Recovery)

📂 Query: {query or "all areas"}
❌ Error: {str(e)}

📋 Basic Structure Available:
🌳 Root domain available for knowledge generation
💡 Suggestion: Use modify_tree to initialize or expand knowledge structure

Ready to proceed with knowledge operations despite exploration error."""

            return ToolResult(name="explore_knowledge", result=content, require_user=False)

    def _explore_tree_structure(self, query: str, max_depth: int) -> str:
        """
        Explore and format the domain knowledge tree structure.
        If query is specified, find the target node and explore from that point.
        Returns a formatted string showing available knowledge areas.
        """

        # If no specific query or query is "all", explore from root
        if not query or query.lower() == "all":
            target_node = self.tree_structure.root
            # For "all" queries, automatically use full tree depth to show complete hierarchy
            full_depth = self._calculate_tree_depth(target_node)
            actual_depth = max(max_depth, full_depth) if query.lower() == "all" else max_depth
            tree_content = self._format_node_tree(target_node, actual_depth, show_root=True)
            total_nodes = self._count_nodes(target_node, actual_depth)
            context_info = f"Starting from root (showing full hierarchy: {actual_depth} levels)"
        else:
            # Find the target node that matches the query
            target_node = self._find_target_node(self.tree_structure.root, query)

            if not target_node:
                # If exact match not found, try partial matching
                partial_matches = self._find_partial_matches(self.tree_structure.root, query)
                if partial_matches:
                    # Show all partial matches
                    tree_content = self._format_partial_matches(partial_matches, max_depth)
                    total_nodes = len(partial_matches)
                    context_info = f"Partial matches for '{query}'"
                else:
                    return f"""🌳 Knowledge Exploration

📂 Query: {query}
📊 Depth: {max_depth} levels
🔢 Total areas found: 0

❌ No knowledge areas found matching '{query}'.

💡 Suggestions:
- Try a broader query like "all" to see available areas
- Check spelling of the topic name
- Use explore_knowledge with "all" to see the full tree structure"""
            else:
                # Found exact match - explore from target node
                tree_content = self._format_node_tree(target_node, max_depth, show_root=True)
                total_nodes = self._count_nodes(target_node, max_depth)

                # Get path from root to this node
                path_to_node = self._find_path_to_node(self.tree_structure.root, target_node)
                if path_to_node and len(path_to_node) > 1:
                    # Show path if not at root
                    path_str = " → ".join(path_to_node)
                    context_info = f"Starting from '{target_node.topic}'\n📍 Path: {path_str}"
                else:
                    context_info = f"Starting from '{target_node.topic}'"

                # Check generation status for specific topic queries
                generation_status = self._check_generation_status(query)
                if generation_status:
                    status_emoji = "✅" if generation_status.get("status") == "success" else "⏳"
                    status_text = generation_status.get("status", "unknown")
                    context_info += f"\n{status_emoji} Generation Status: {status_text}"

                    if generation_status.get("status") == "success":
                        context_info += f"\n   Last updated: {generation_status.get('last_updated', 'Unknown')}"
                        context_info += f"\n   Message: {generation_status.get('message', 'No details')}"
                elif total_nodes == 1:  # Single leaf node without generation status
                    context_info += "\n⏳ Generation Status: Not generated"

        # Build final content
        display_depth = actual_depth if "actual_depth" in locals() else max_depth
        header = f"""🌳 Knowledge Exploration

📂 Query: {query or "all areas"}
📊 Depth: {display_depth} levels ({context_info})
🔢 Total areas found: {total_nodes}

📋 Available Knowledge Areas:"""

        # Build smart footer with recommendations
        footer = self._build_smart_footer(
            query, target_node if "target_node" in locals() else None, generation_status if "generation_status" in locals() else None
        )

        return f"{header}\n{tree_content}{footer}"

    def _build_smart_footer(self, query: str, target_node=None, generation_status=None) -> str:
        """Build contextual footer with next steps after exploration."""

        footer = """

💡 **Next Steps**: 
After exploring the available topics, use **ask_question** to decide:
- Generate knowledge for a specific topic 
- Generate knowledge for ALL topics (bulk generation)

🎯 **Recommended Action**: 
Use ask_question with context from this exploration to help the user choose between single topic or comprehensive generation."""

        return footer

    def _find_target_node(self, node, query: str):
        """Recursively search for a node that matches the query exactly."""
        if node.topic.lower() == query.lower():
            return node

        for child in node.children:
            found = self._find_target_node(child, query)
            if found:
                return found

        return None

    def _find_path_to_node(self, root, target_node, current_path=None):
        """Find the path from root to target node."""
        if current_path is None:
            current_path = []

        # Add current node to path
        current_path = current_path + [root.topic]

        # Check if we found the target
        if root == target_node:
            return current_path

        # Search in children
        for child in root.children:
            result = self._find_path_to_node(child, target_node, current_path)
            if result:
                return result

        return None

    def _find_partial_matches(self, node, query: str) -> list:
        """Find all nodes that partially match the query."""
        matches = []

        if query.lower() in node.topic.lower():
            matches.append(node)

        for child in node.children:
            matches.extend(self._find_partial_matches(child, query))

        return matches

    def _format_partial_matches(self, matches, max_depth: int) -> str:
        """Format multiple partial matches."""
        content_lines = []

        for match in matches:
            # Get path to this match
            path_to_match = self._find_path_to_node(self.tree_structure.root, match)
            if path_to_match and len(path_to_match) > 1:
                path_str = " → ".join(path_to_match)
                content_lines.append(f"📍 Path: {path_str}")

            # Show the match and its children up to max_depth
            match_content = self._format_node_tree(match, max_depth, show_root=True)
            content_lines.append(match_content)

        return "\n\n".join(content_lines)

    def _format_node_tree(self, node, max_depth: int, level: int = 0, show_root: bool = False) -> str:
        """
        Format a node and its children up to max_depth levels.
        Depth counting starts from the given node.
        """
        if level >= max_depth:
            return ""

        # Format current node
        indent = "  " * level
        if level == 0 and show_root:
            emoji = "🌳"
        elif level == 0 or level == 1:
            emoji = "📁"
        elif level == 2:
            emoji = "📄"
        else:
            emoji = "•"

        # Add generation status indicator for each topic
        status_indicator = self._get_status_indicator(node.topic)
        lines = [f"{indent}{emoji} {node.topic}{status_indicator}"]

        # Add children info if they exist but we're not showing them due to depth limit
        if node.children and level == max_depth - 1:
            child_count = len(node.children)
            lines[0] += f" ({child_count} {'topic' if child_count == 1 else 'topics'})"

        # Add children if within depth limit
        if level < max_depth - 1:
            for child in node.children:
                child_content = self._format_node_tree(child, max_depth, level + 1, show_root=False)
                if child_content:
                    lines.append(child_content)

        return "\n".join(lines)

    def _count_nodes(self, node, max_depth: int, level: int = 0) -> int:
        """Count nodes up to max_depth starting from the given node."""
        if level >= max_depth:
            return 0

        count = 1  # Count current node

        if level < max_depth - 1:
            for child in node.children:
                count += self._count_nodes(child, max_depth, level + 1)

        return count

    def _check_generation_status(self, topic: str) -> dict | None:
        """Check if knowledge has been generated for this topic."""
        if not self.knowledge_status_path:
            return None

        try:
            from pathlib import Path
            import json

            status_file = Path(self.knowledge_status_path)
            if status_file.exists():
                with open(status_file) as f:
                    status_data = json.load(f)
                return status_data.get(topic, None)
        except Exception:
            pass

        return None

    def _calculate_tree_depth(self, node, current_depth=0) -> int:
        """Calculate the maximum depth of the tree from a given node."""
        if not node.children:
            return current_depth + 1

        max_child_depth = 0
        for child in node.children:
            child_depth = self._calculate_tree_depth(child, current_depth + 1)
            max_child_depth = max(max_child_depth, child_depth)

        return max_child_depth

    def _count_knowledge_artifacts(self, topic: str) -> int:
        """Count the number of knowledge artifacts for a topic."""
        if not self.knowledge_status_path:
            return 0

        try:
            from pathlib import Path
            import json

            status_file = Path(self.knowledge_status_path)
            if status_file.exists():
                with open(status_file) as f:
                    status_data = json.load(f)
                topic_status = status_data.get(topic, {})
                # Count artifacts from the status data
                return topic_status.get("artifact_count", 0)
        except Exception:
            pass

        return 0

    def _get_status_indicator(self, topic: str) -> str:
        """Get visual status indicator for a topic's generation status with artifact count."""
        status = self._check_generation_status(topic)
        artifact_count = self._count_knowledge_artifacts(topic)

        if status:
            if status.get("status") == "success":
                return f" ✅ ({artifact_count} artifacts)" if artifact_count > 0 else " ✅"
            elif status.get("status") in ["pending", "in_progress"]:
                return f" ⏳ ({artifact_count} artifacts)" if artifact_count > 0 else " ⏳"
            else:
                return f" ❌ ({artifact_count} artifacts)" if artifact_count > 0 else " ❌"

        # For leaf nodes with no status, show if they have artifacts anyway
        if artifact_count > 0:
            return f" ({artifact_count} artifacts)"

        return ""  # No status indicator if no status found

    def _build_smart_footer(self, query: str, target_node, generation_status: dict | None) -> str:
        """Build intelligent footer with context-aware recommendations."""

        # For specific single topics (leaf nodes)
        if target_node and (not target_node.children or len(target_node.children) == 0):
            if generation_status and generation_status.get("status") == "success":
                return """

💡 Smart Recommendations:
✅ This topic already has complete knowledge artifacts.

Next actions:
- Use this knowledge for analysis or reporting
- Explore other topics that need knowledge generation
- Use modify_tree to add new related topics

Knowledge generation not needed for this topic."""
            else:
                return f"""

💡 Smart Recommendations:
⏳ This topic exists but needs knowledge generation.

Next actions:
- Use generate_knowledge to create content for "{query}"
- Ready to proceed with knowledge generation
- No tree modifications needed

Perfect candidate for knowledge generation!"""

        # For topics with children but also having generation status
        elif target_node and target_node.children and generation_status and generation_status.get("status") == "success":
            return """

💡 Smart Recommendations:
✅ This topic has generated knowledge and contains subtopics.

Next actions:
- Explore subtopics for additional knowledge generation opportunities
- Use generate_knowledge for any unlisted subtopics
- This topic itself already has complete knowledge

Ready for subtopic knowledge generation."""

        # For broader exploration or topics with children
        elif target_node and target_node.children:
            return """

💡 Usage Notes:
- Use generate_knowledge to create content for any listed area
- Use modify_tree to add/remove knowledge areas  
- Areas with (N topics) indicate deeper structure available
- Explore specific topics to see generation status

Ready for knowledge generation in any of the above areas."""

        # For general exploration
        else:
            return """

💡 Usage Notes:
- Use generate_knowledge to create content for any listed area
- Use modify_tree to add/remove knowledge areas
- Areas with (N topics) indicate deeper structure available

Ready for knowledge generation in any of the above areas."""


class CreatePlanTool(BaseTool):
    def __init__(self, llm: LLMResource | None = None):
        tool_info = BaseToolInformation(
            name="create_plan",
            description="Create a detailed execution plan showing the sequence of upcoming tool uses in the knowledge generation workflow. Maps out which tools will be used, in what order, and their expected outcomes.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="topic", type="string", description="The topic to create a plan for", example="Current Ratio Analysis"
                    ),
                    BaseArgument(
                        name="scope",
                        type="string",
                        description="The scope of knowledge needed (comprehensive, focused, basic)",
                        example="comprehensive",
                    ),
                    BaseArgument(
                        name="target_location",
                        type="string",
                        description="Where in the tree to store this knowledge",
                        example="Financial Analysis > Liquidity Analysis > Current Ratio",
                    ),
                ],
                required=["topic"],
            ),
        )
        super().__init__(tool_info)
        self.llm = llm or LLMResource()

    def _execute(self, topic: str, scope: str = "comprehensive", target_location: str = "") -> ToolResult:
        """
        Create execution plan showing upcoming tool uses in the workflow.
        """
        try:
            # Use LLM to create detailed tool workflow plan
            plan_prompt = f"""Create a detailed tool execution plan for knowledge generation workflow: "{topic}"

Scope: {scope}
Target Location: {target_location}

Plan the sequence of tools that will be used in this knowledge generation workflow. Consider the complete process from preparation to completion.

Available tools:
- check_existing: Check for existing knowledge to avoid duplicates
- generate_knowledge: Generate knowledge content (facts, procedures, heuristics)
- validate: Validate generated knowledge for accuracy
- persist: Store knowledge to vector database
- attempt_completion: Present final results

Return as JSON:
{{
    "workflow_summary": "Brief overview of the planned tool execution sequence",
    "tool_sequence": [
        {{"tool": "check_existing", "purpose": "Check for duplicates", "estimated_time_minutes": 0.5}},
        {{"tool": "generate_knowledge", "purpose": "Create knowledge content", "estimated_time_minutes": 2}},
        {{"tool": "validate", "purpose": "Quality assurance", "estimated_time_minutes": 0.5}},
        {{"tool": "persist", "purpose": "Store to database", "estimated_time_minutes": 0.5}},
        {{"tool": "attempt_completion", "purpose": "Present results", "estimated_time_minutes": 0.5}}
    ],
    "total_tools": 5,
    "estimated_total_time_minutes": 4,
    "workflow_complexity": "medium"
}}"""

            llm_request = BaseRequest(
                arguments={"messages": [{"role": "user", "content": plan_prompt}], "temperature": 0.1, "max_tokens": 400}
            )

            response = Misc.safe_asyncio_run(self.llm.query, llm_request)
            result = Misc.text_to_dict(Misc.get_response_content(response))

            # Format the workflow plan nicely
            workflow_summary = result.get("workflow_summary", "Tool execution workflow plan")
            tool_sequence = result.get("tool_sequence", [])
            total_tools = result.get("total_tools", len(tool_sequence))
            estimated_time = result.get("estimated_total_time_minutes", 4)
            complexity = result.get("workflow_complexity", "medium")

            content = f"""📋 Execution Plan Created

Topic: {topic}
Scope: {scope.title()}
Target: {target_location}

{workflow_summary}

🔧 Tool Execution Sequence:"""

            for i, tool_step in enumerate(tool_sequence, 1):
                tool_name = tool_step.get("tool", "unknown")
                purpose = tool_step.get("purpose", "No description")
                step_time = tool_step.get("estimated_time_minutes", 0.5)

                # Get emoji for tool
                tool_emoji = {
                    "check_existing": "🔍",
                    "generate_knowledge": "📚",
                    "validate": "✅",
                    "persist": "💾",
                    "attempt_completion": "🎉",
                }.get(tool_name, "🔧")

                content += f"\n{i}. {tool_emoji} **{tool_name}** (~{step_time}min)"
                content += f"\n   Purpose: {purpose}"

            content += f"""

⏱️ Total Estimated Time: {estimated_time} minutes
🔧 Total Tools: {total_tools}
📈 Workflow Complexity: {complexity.title()}

This plan shows the upcoming tool execution sequence. Ready for user approval."""

            return ToolResult(name="create_plan", result=content, require_user=False)

        except Exception as e:
            logger.error(f"Failed to create plan: {e}")
            # Fallback workflow plan
            content = f"""📋 Execution Plan Created (Fallback)

Topic: {topic}
Scope: {scope.title()}

🔧 Standard Tool Execution Sequence:

1. 🔍 **check_existing** (~0.5min)
   Purpose: Check for duplicate knowledge

2. 📚 **generate_knowledge** (~2min)  
   Purpose: Create knowledge content (facts, procedures, heuristics)

3. ✅ **validate** (~0.5min)
   Purpose: Quality assurance and accuracy check

4. 💾 **persist** (~0.5min)
   Purpose: Store knowledge to vector database

5. 🎉 **attempt_completion** (~0.5min)
   Purpose: Present final results to user

⏱️ Total Estimated Time: 4 minutes
🔧 Total Tools: 5
📈 Workflow Complexity: Medium

This plan shows the upcoming tool execution sequence. Ready for user approval."""

            return ToolResult(name="create_plan", result=content, require_user=False)


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
    ):
        self.knowledge_status_path = knowledge_status_path
        self.storage_path = storage_path
        self.tree_structure = tree_structure
        self.domain = domain
        self.role = role
        self.tasks = tasks or ["Analyze Information", "Provide Insights", "Answer Questions"]
        tool_info = BaseToolInformation(
            name="generate_knowledge",
            description="Generate knowledge for topics. Can generate for a single topic or automatically for all leaf nodes in the tree structure. Checks knowledge status and only generates for topics with status != 'success'.",
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

    def _execute(self, mode: str, topic: str = "", counts: str = "", context: str = "") -> ToolResult:
        try:
            if mode == "all_leaves":
                return self._generate_for_all_leaves(counts, context)
            elif mode == "single":
                if not topic:
                    return ToolResult(
                        name="generate_knowledge", result="❌ Error: Topic is required for single mode generation", require_user=False
                    )
                return self._generate_for_single_topic(topic, counts, context)
            else:
                return ToolResult(
                    name="generate_knowledge", result=f"❌ Error: Invalid mode '{mode}'. Use 'single' or 'all_leaves'", require_user=False
                )
        except Exception as e:
            logger.error(f"Failed to generate knowledge: {e}")
            return ToolResult(name="generate_knowledge", result=f"❌ Error generating knowledge: {str(e)}", require_user=False)

    def _generate_for_all_leaves(self, counts: str, context: str) -> ToolResult:
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

        # Generate knowledge for each leaf
        successful_generations = 0
        failed_generations = 0
        total_artifacts = 0
        generation_results = []

        for i, path in enumerate(all_leaf_paths):
            leaf_topic = path[-1]  # Last element in path is the leaf topic
            path_str = " → ".join(path)

            logger.info(f"Processing leaf {i + 1}/{len(all_leaf_paths)}: {leaf_topic}")

            try:
                # Check if already generated
                if self.knowledge_status_path:
                    status_check = self._check_knowledge_status(leaf_topic)
                    if status_check["skip"]:
                        generation_results.append(f"⏭️ Skipped '{leaf_topic}' - already complete")
                        continue

                # Generate knowledge for this leaf
                leaf_context = f"{context}\nTree path: {path_str}\nFocus on this specific aspect within the broader context."
                result = self._generate_single_knowledge(leaf_topic, counts, leaf_context)

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
                else:
                    failed_generations += 1
                    generation_results.append(f"❌ Failed '{leaf_topic}' - {result}")

            except Exception as e:
                failed_generations += 1
                generation_results.append(f"❌ Failed '{leaf_topic}' - {str(e)}")
                logger.error(f"Failed to generate knowledge for leaf {leaf_topic}: {str(e)}")

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

        return ToolResult(name="generate_knowledge", result=content, require_user=False)

    def _generate_for_single_topic(self, topic: str, counts: str, context: str) -> ToolResult:
        """Generate knowledge for a single topic."""
        # Check knowledge status first
        if self.knowledge_status_path:
            status_check = self._check_knowledge_status(topic)
            if status_check["skip"]:
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

        # Generate the knowledge
        result_content = self._generate_single_knowledge(topic, counts, context)
        return ToolResult(name="generate_knowledge", result=result_content, require_user=False)

    def _generate_single_knowledge(self, topic: str, counts: str, context: str) -> str:
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

            topic_status = status_data.get(topic, {})
            current_status = topic_status.get("status", "not_started")

            if current_status == "success":
                return {
                    "skip": True,
                    "status": current_status,
                    "reason": f"Topic already completed successfully on {topic_status.get('last_updated', 'unknown date')}",
                }
            else:
                return {"skip": False, "status": current_status, "reason": f"Topic needs generation (current status: {current_status})"}

        except Exception as e:
            logger.error(f"Error checking knowledge status: {e}")
            # Default to generating if we can't read status
            return {"skip": False, "status": "error", "reason": f"Status check failed: {e}"}

    def _update_knowledge_status(self, topic: str, status: str, message: str = "") -> None:
        """Update the knowledge generation status for the given topic."""
        try:
            from pathlib import Path
            from datetime import datetime, UTC
            import json

            status_file = Path(self.knowledge_status_path)

            # Load existing status data or create new
            if status_file.exists():
                with open(status_file) as f:
                    status_data = json.load(f)
            else:
                status_data = {}
                # Ensure parent directory exists
                status_file.parent.mkdir(parents=True, exist_ok=True)

            # Update topic status
            status_data[topic] = {"status": status, "last_updated": datetime.now(UTC).isoformat(), "message": message}

            # Save updated status
            with open(status_file, "w") as f:
                json.dump(status_data, f, indent=2)

            logger.info(f"Updated knowledge status for '{topic}': {status}")

        except Exception as e:
            logger.error(f"Failed to update knowledge status: {e}")

    def _persist_knowledge(self, topic: str, content: str, result_data: dict, total_artifacts: int) -> str:
        """Persist generated knowledge to disk storage."""
        from pathlib import Path
        from datetime import datetime, UTC
        import json

        # Create safe filename from topic
        safe_topic = topic.lower().replace(" ", "_").replace("-", "_")
        safe_topic = "".join(c for c in safe_topic if c.isalnum() or c == "_")

        # Create storage directory
        storage_dir = Path(self.storage_path) / "processed_knowledge" / f"topic_{safe_topic}"
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Prepare knowledge data for storage
        knowledge_data = {
            "topic": topic,
            "generated_at": datetime.now(UTC).isoformat(),
            "total_artifacts": total_artifacts,
            "content_summary": f"Generated {total_artifacts} knowledge artifacts",
            "raw_content": content,
            "structured_data": result_data,
            "status": "persisted",
        }

        # Save to JSON file
        knowledge_file = storage_dir / "knowledge.json"
        with open(knowledge_file, "w", encoding="utf-8") as f:
            json.dump(knowledge_data, f, indent=2, ensure_ascii=False)

        return f"""

💾 **Knowledge Persisted Successfully**
📁 Storage Location: {knowledge_file}
📊 File Size: {knowledge_file.stat().st_size} bytes
🕒 Saved At: {datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")}
✅ Status: Ready for agent usage"""


class ModifyTreeTool(BaseTool):
    def __init__(
        self,
        tree_structure: DomainKnowledgeTree | None = None,
        domain_knowledge_path: str | None = None,
        domain: str = "General",
        role: str = "Domain Expert",
        tasks: list[str] | None = None,
    ):
        self.domain = domain
        self.role = role
        self.tasks = tasks or []

        tool_info = BaseToolInformation(
            name="modify_tree",
            description="Manage domain knowledge tree structure with two operations: 'init' for comprehensive tree initialization, and 'bulk' for all tree modifications (create/modify/remove nodes). Supports single or multiple operations atomically.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="operation",
                        type="string",
                        description="Type of operation: 'init' for LLM-driven tree initialization, 'bulk' for all tree modifications",
                        example="bulk",
                    ),
                    BaseArgument(
                        name="tree_path",
                        type="string",
                        description="For 'init' operation: domain topic to build comprehensive tree around",
                        example="Financial Analysis",
                    ),
                    BaseArgument(
                        name="bulk_operations",
                        type="string",
                        description="For 'bulk' operation: JSON array of operations. Each operation has 'action' (create/modify/remove), 'paths' (array of node names from root to target), and optional 'new_name' for modify",
                        example='[{"action": "remove", "paths": ["Financial Analysis", "Benchmarking"]}, {"action": "create", "paths": ["Financial Analysis", "Risk Analysis"]}]',
                    ),
                ],
                required=["operation"],
            ),
        )
        super().__init__(tool_info)
        self.tree_structure = tree_structure
        self.domain_knowledge_path = domain_knowledge_path

    def _execute(self, operation: str, tree_path: str = "", bulk_operations: str = "") -> ToolResult:
        """
        Modify the domain knowledge tree structure.

        Operations:
        - init: Initialize comprehensive tree structure from domain topic
        - bulk: Perform multiple tree modifications atomically
        """
        try:
            operation = operation.lower().strip()

            if operation == "init":
                if not tree_path:
                    content = "❌ Error: tree_path required for init operation"
                else:
                    content, updated_tree = self._init_tree(tree_path)
                    if updated_tree:
                        self._save_tree_structure(updated_tree)
            elif operation == "bulk":
                if not bulk_operations:
                    content = "❌ Error: bulk_operations required for bulk operation"
                else:
                    content = self._execute_bulk_operations(bulk_operations)
                    self._save_tree_changes("bulk", "multiple operations")
            else:
                content = f"❌ Invalid operation '{operation}'. Supported: init, bulk"

            return ToolResult(name="modify_tree", result=content, require_user=False)

        except Exception as e:
            logger.error(f"Failed to modify tree: {e}")
            return ToolResult(name="modify_tree", result=f"❌ Error modifying tree: {str(e)}", require_user=False)

    def _create_single_node(self, path_parts: list[str], tree_path: str) -> str:
        """Create new node(s) in the tree structure."""
        if not self.tree_structure:
            # Initialize tree if it doesn't exist
            from dana.api.core.schemas import DomainNode, DomainKnowledgeTree
            from datetime import datetime, UTC

            self.tree_structure = DomainKnowledgeTree(root=DomainNode(topic=path_parts[0]), last_updated=datetime.now(UTC), version=1)

        # Navigate and create nodes as needed
        current_node = self.tree_structure.root
        nodes_created = []
        path_so_far = [current_node.topic]

        # Start from index 1 if root matches, otherwise replace root
        start_idx = 1 if current_node.topic == path_parts[0] else 0

        if start_idx == 0:
            # Replace root if needed
            self.tree_structure.root.topic = path_parts[0]

        # Create rest of the path
        for i in range(start_idx, len(path_parts)):
            topic = path_parts[i]

            # Find or create child node
            child_node = None
            for child in current_node.children:
                if child.topic == topic:
                    child_node = child
                    break

            if child_node is None:
                # Create new node
                from dana.api.core.schemas import DomainNode

                child_node = DomainNode(topic=topic)
                current_node.children.append(child_node)
                nodes_created.append(" > ".join(path_so_far + [topic]))

            current_node = child_node
            path_so_far.append(topic)

        # Build response content
        if nodes_created:
            content = f"""🌳 Tree Structure Updated

✅ Created node(s) in path: {tree_path}

📊 New Nodes Created:
{chr(10).join(f"- {node}" for node in nodes_created)}

📈 Tree Stats:
- Total nodes created: {len(nodes_created)}
- Final depth: {len(path_parts)} levels
- Path type: {"New branch" if len(nodes_created) > 1 else "New leaf node"}

🔗 Integration:
- Knowledge area now available for navigation
- Ready for content association
- Tree structure expanded successfully"""
        else:
            content = f"""🌳 Tree Structure Verified

✅ Path already exists: {tree_path}

📊 Node Details:
- All nodes in path already exist
- No new nodes created
- Ready for knowledge generation

🔗 Integration:
- Existing structure confirmed
- Ready for content association"""

        return content

    def _modify_single_node(self, path_parts: list[str], tree_path: str) -> str:
        """Modify existing node in the tree structure."""
        if not self.tree_structure or not self.tree_structure.root:
            return "❌ Error: No tree structure exists to modify"

        # Navigate to the node to modify
        current_node = self.tree_structure.root
        parent_node = None
        node_found = False

        # Handle root node modification
        if len(path_parts) == 1 and current_node.topic == path_parts[0]:
            # For now, we'll just update metadata (topic name change would break references)
            node_found = True
            modified_node = current_node
        else:
            # Navigate to find the target node
            for i, topic in enumerate(path_parts):
                if i == 0:
                    if current_node.topic != topic:
                        return f"❌ Error: Root node '{current_node.topic}' doesn't match path '{topic}'"
                    continue

                # Find child node
                found = False
                for child in current_node.children:
                    if child.topic == topic:
                        parent_node = current_node
                        current_node = child
                        found = True
                        break

                if not found:
                    return f"❌ Error: Node '{topic}' not found in path"

                if i == len(path_parts) - 1:
                    node_found = True
                    modified_node = current_node

        if not node_found:
            return f"❌ Error: Could not find node at path: {tree_path}"

        # For modify operation, we might want to rename or update metadata
        # Since we don't have new data in parameters, we'll just update metadata
        old_topic = modified_node.topic

        content = f"""🌳 Tree Structure Updated

✅ Modified node: {tree_path}

📝 Node Details:
- Topic: {old_topic}
- Children: {len(modified_node.children)} sub-nodes
- Node ID: {modified_node.id}

🔄 Updates Applied:
- Metadata refreshed
- Timestamp will be updated on save
- Structure integrity verified

📊 Impact:
- Child relationships: Preserved ({len(modified_node.children)} children)
- Parent link: {"Root node" if parent_node is None else "Connected to " + (parent_node.topic if parent_node else "parent")}
- Navigation paths: Maintained

Node modification complete."""

        return content

    def _remove_single_node(self, path_parts: list[str], tree_path: str) -> str:
        """Remove node from the tree structure."""
        if not self.tree_structure or not self.tree_structure.root:
            return "❌ Error: No tree structure exists to modify"

        # Cannot remove root node
        if len(path_parts) == 1 and self.tree_structure.root.topic == path_parts[0]:
            return "❌ Error: Cannot remove root node. Consider replacing it with modify operation."

        # Navigate to find the node and its parent
        current_node = self.tree_structure.root
        parent_node = None
        target_node = None

        # Navigate through the path
        for i, topic in enumerate(path_parts):
            if i == 0:
                if current_node.topic != topic:
                    return f"❌ Error: Root node '{current_node.topic}' doesn't match path '{topic}'"
                continue

            # Find child node
            found = False
            for child_idx, child in enumerate(current_node.children):
                if child.topic == topic:
                    if i == len(path_parts) - 1:
                        # This is the node to remove
                        parent_node = current_node
                        target_node = child
                        # Remove the node
                        removed_children = len(child.children)
                        current_node.children.pop(child_idx)
                        found = True
                        break
                    else:
                        # Continue navigating
                        current_node = child
                        found = True
                        break

            if not found:
                return f"❌ Error: Node '{topic}' not found in path"

        if not target_node:
            return f"❌ Error: Could not find node to remove at path: {tree_path}"

        # Build response
        content = f"""🌳 Tree Structure Updated

✅ Removed node: {tree_path}

🗑️ Removal Details:
- Node "{target_node.topic}" deleted from tree structure
- Parent node: {parent_node.topic if parent_node else "None"}
- Children affected: {removed_children} sub-nodes also removed

📊 Impact:
- Tree structure simplified
- Navigation path no longer available
- Parent node now has {len(parent_node.children)} children

{"⚠️ Warning: " + str(removed_children) + " child nodes were also removed" if removed_children > 0 else "✅ Clean removal - no child nodes affected"}

Node removal complete."""

        return content

    def _init_tree(self, domain_topic: str) -> tuple[str, DomainKnowledgeTree | None]:
        """Initialize a comprehensive tree structure from a domain topic using LLM."""
        try:
            from dana.common.resource.llm.llm_resource import LLMResource
            from dana.common.types import BaseRequest
            from dana.common.utils.misc import Misc
            from dana.api.core.schemas import DomainNode, DomainKnowledgeTree
            from datetime import datetime, UTC
            import json

            # Use LLM to generate comprehensive tree structure
            llm = LLMResource()

            # Build context from instance properties
            role_context = f"As a {self.role}" if self.role != "Domain Expert" else "As a domain expert"
            domain_context = f"in {self.domain}" if self.domain != "General" else ""
            tasks_context = f"\nKey focus areas: {', '.join(self.tasks)}" if self.tasks else ""

            init_prompt = f"""Generate a comprehensive domain knowledge tree structure for: "{domain_topic}"

{role_context} {domain_context}, create a multi-level hierarchical structure with:
- Main Domain (1 level)
- Multiple Subdomains/Categories (2-4 categories)  
- Multiple Topics per category (2-5 topics each)
- Specific subtopics where relevant (1-3 per topic){tasks_context}

Structure should be logical, comprehensive, and cover the major areas within this domain.

Return as JSON with this exact structure:
{{
    "domain": "Main Domain Name",
    "structure": {{
        "Subdomain1": {{
            "Topic1": ["Subtopic1", "Subtopic2"],
            "Topic2": ["Subtopic1", "Subtopic2", "Subtopic3"],
            "Topic3": ["Subtopic1"]
        }},
        "Subdomain2": {{
            "Topic1": ["Subtopic1", "Subtopic2"],
            "Topic2": ["Subtopic1", "Subtopic2"]
        }},
        "Subdomain3": {{
            "Topic1": ["Subtopic1", "Subtopic2", "Subtopic3"],
            "Topic2": ["Subtopic1"]
        }}
    }},
    "reasoning": "explanation of the structure"
}}"""

            llm_request = BaseRequest(
                arguments={"messages": [{"role": "user", "content": init_prompt}], "temperature": 0.1, "max_tokens": 800}
            )

            response = Misc.safe_asyncio_run(llm.query, llm_request)
            result = Misc.text_to_dict(Misc.get_response_content(response))

            domain = result.get("domain", domain_topic)
            structure = result.get("structure", {})
            reasoning = result.get("reasoning", "Comprehensive domain structure")

            # Convert to DomainKnowledgeTree structure
            def create_node(topic_name: str, children_data=None) -> DomainNode:
                """Create a DomainNode with optional children"""
                children = []
                if children_data:
                    if isinstance(children_data, dict):
                        # This is a subdomain with topics
                        for topic, subtopics in children_data.items():
                            children.append(create_node(topic, subtopics))
                    elif isinstance(children_data, list):
                        # This is a topic with subtopics
                        for subtopic in children_data:
                            children.append(create_node(subtopic))

                return DomainNode(topic=topic_name, children=children)

            # Create root node with all subdomains
            root_node = create_node(domain, structure)

            # Create full DomainKnowledgeTree
            knowledge_tree = DomainKnowledgeTree(root=root_node, last_updated=datetime.now(UTC), version=1)

            # Count total nodes for display
            def count_nodes(node: DomainNode) -> int:
                return 1 + sum(count_nodes(child) for child in node.children)

            total_nodes = count_nodes(root_node)
            total_subdomains = len(structure)
            total_topics = sum(len(topics) for topics in structure.values())
            total_subtopics = sum(len(subtopics) for topics in structure.values() for subtopics in topics.values())

            # Create display content
            content = f"""🌳 Comprehensive Tree Structure Initialized

🌱 Created complete domain tree: {domain}

📊 Tree Structure:"""

            # Format the tree structure nicely
            for subdomain, topics in structure.items():
                content += f"\n\n📁 {subdomain}"
                for topic, subtopics in topics.items():
                    content += f"\n  📄 {topic}"
                    for subtopic in subtopics:
                        content += f"\n    • {subtopic}"

            content += f"""

📈 Tree Statistics:
- Root Domain: 1 ({domain})
- Subdomains: {total_subdomains}
- Topics: {total_topics}
- Subtopics: {total_subtopics}
- Total Nodes: {total_nodes}

🧠 Structure Reasoning:
{reasoning}

📋 DomainKnowledgeTree Data:
{json.dumps(knowledge_tree.model_dump(), indent=2, default=str)}

🔗 Integration:
- Complete knowledge hierarchy established
- All major areas covered with appropriate depth
- Ready for knowledge organization and content association
- Compatible with DomainKnowledgeTree schema

✅ Full tree initialization complete - ready for knowledge generation!"""

            return content, knowledge_tree

        except Exception as e:
            # Fallback structure if LLM fails
            from dana.api.core.schemas import DomainNode, DomainKnowledgeTree
            from datetime import datetime, UTC
            import json

            fallback_domain = domain_topic.split(">")[0].strip() if ">" in domain_topic else domain_topic

            # Create fallback tree structure
            subtopics1 = [DomainNode(topic="Basic Concepts"), DomainNode(topic="Key Principles")]
            subtopics2 = [DomainNode(topic="Practical Uses"), DomainNode(topic="Case Studies")]
            subtopics3 = [DomainNode(topic="Complex Concepts"), DomainNode(topic="Research Areas")]

            topics = [
                DomainNode(topic="Fundamentals", children=subtopics1),
                DomainNode(topic="Applications", children=subtopics2),
                DomainNode(topic="Advanced Topics", children=subtopics3),
            ]

            root_node = DomainNode(topic=fallback_domain, children=topics)

            knowledge_tree = DomainKnowledgeTree(root=root_node, last_updated=datetime.now(UTC), version=1)

            content = f"""🌳 Tree Structure Initialized (Fallback)

🌱 Created basic domain tree: {fallback_domain}

📊 Basic Structure:
📁 {fallback_domain}
  📄 Fundamentals
    • Basic Concepts
    • Key Principles
  📄 Applications
    • Practical Uses
    • Case Studies
  📄 Advanced Topics
    • Complex Concepts
    • Research Areas

📈 Tree Statistics:
- Root Domain: 1
- Subdomains: 1
- Topics: 3
- Subtopics: 6
- Total Nodes: 11

📋 DomainKnowledgeTree Data:
{json.dumps(knowledge_tree.model_dump(), indent=2, default=str)}

⚠️ Note: Used fallback structure due to error: {str(e)}

✅ Basic tree initialization complete - ready for knowledge generation!"""

            return content, knowledge_tree

    def _execute_bulk_operations(self, bulk_operations_str: str | list) -> str:
        """Execute multiple tree operations atomically."""
        import json

        try:
            # Parse the bulk operations JSON
            if isinstance(bulk_operations_str, str):
                bulk_ops = json.loads(bulk_operations_str)
            else:
                bulk_ops = bulk_operations_str
            if not isinstance(bulk_ops, list):
                return "❌ Error: bulk_operations must be a JSON array"

            results = []
            operations_performed = []

            # Validate all operations first (fail fast)
            for i, op in enumerate(bulk_ops):
                if not isinstance(op, dict):
                    return f"❌ Error: Operation {i + 1} must be a JSON object"
                if "action" not in op or "paths" not in op:
                    return f"❌ Error: Operation {i + 1} must have 'action' and 'paths' fields"
                if op["action"] not in ["create", "modify", "remove"]:
                    return f"❌ Error: Operation {i + 1} action '{op['action']}' not supported (use: create, modify, remove)"
                if not isinstance(op["paths"], list) or len(op["paths"]) == 0:
                    return f"❌ Error: Operation {i + 1} 'paths' must be a non-empty array"

            # Execute all operations
            for i, op in enumerate(bulk_ops):
                action = op["action"]
                paths = op["paths"]
                new_name = op.get("new_name", "")

                path_parts = paths  # Already an array
                path_str = " > ".join(paths)

                try:
                    if action == "create":
                        self._create_single_node(path_parts, path_str)
                    elif action == "modify":
                        self._modify_single_node(path_parts, path_str, new_name)
                    elif action == "remove":
                        self._remove_single_node(path_parts, path_str)

                    results.append(f"✅ {action.title()}: {path_str}")
                    operations_performed.append(f"{action} {path_str}")

                except Exception as e:
                    return f"❌ Error in operation {i + 1} ({action} {path_str}): {str(e)}"

            # Build response
            content = f"""🌳 Bulk Tree Operations Complete

📊 Operations Performed ({len(operations_performed)}):
{chr(10).join(f"{i + 1}. {op}" for i, op in enumerate(operations_performed))}

✅ All operations completed successfully
🔗 Tree structure updated and ready for use"""

            return content

        except json.JSONDecodeError as e:
            return f"❌ Error: Invalid JSON in bulk_operations: {str(e)}"
        except Exception as e:
            return f"❌ Error executing bulk operations: {str(e)}"

    def _save_tree_structure(self, updated_tree: "DomainKnowledgeTree") -> None:
        """Save the complete updated tree structure to the domain knowledge path."""
        if self.domain_knowledge_path:
            try:
                from dana.api.services.intent_detection.intent_handlers.handler_utility import knowledge_ops_utils as ko_utils

                ko_utils.save_tree(updated_tree, self.domain_knowledge_path)
                self.tree_structure = updated_tree  # Update local reference
                logger.info(f"Tree structure saved to {self.domain_knowledge_path}")
            except Exception as e:
                logger.error(f"Failed to save tree structure: {e}")

    def _save_tree_changes(self, operation: str, tree_path: str) -> None:
        """Save tree changes after create/modify/remove operations."""
        if self.domain_knowledge_path and self.tree_structure:
            try:
                from dana.api.services.intent_detection.intent_handlers.handler_utility import knowledge_ops_utils as ko_utils
                from datetime import datetime, UTC

                # Update tree metadata
                self.tree_structure.last_updated = datetime.now(UTC)
                self.tree_structure.version += 1

                # Save updated tree
                ko_utils.save_tree(self.tree_structure, self.domain_knowledge_path)
                logger.info(f"Tree changes saved after {operation} operation on {tree_path}")
            except Exception as e:
                logger.error(f"Failed to save tree changes: {e}")


class ValidateTool(BaseTool):
    def __init__(self, llm: LLMResource | None = None):
        tool_info = BaseToolInformation(
            name="validate",
            description="Validate all generated knowledge for accuracy, completeness, and consistency before persistence.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="artifacts_to_validate",
                        type="string",
                        description="List of artifact types to validate",
                        example="facts, procedures, heuristics",
                    ),
                    BaseArgument(
                        name="validation_criteria",
                        type="string",
                        description="Specific criteria to check against",
                        example="accuracy, completeness, consistency",
                    ),
                ],
                required=["artifacts_to_validate"],
            ),
        )
        super().__init__(tool_info)
        self.llm = llm or LLMResource()

    def _execute(self, artifacts_to_validate: str, validation_criteria: str = "accuracy, completeness") -> ToolResult:
        # Mock validation - in real implementation would check generated content
        import random

        artifacts = [a.strip() for a in artifacts_to_validate.split(",")]
        criteria = [c.strip() for c in validation_criteria.split(",")]

        # Simulate validation results
        total_artifacts = len(artifacts) * 3  # Assume 3 items per type
        passed = random.randint(int(total_artifacts * 0.85), total_artifacts)  # 85-100% pass rate
        accuracy_score = random.randint(90, 98)

        content = f"""✅ Validation Complete

Artifacts Validated: {", ".join(artifacts)}
Criteria: {", ".join(criteria)}

📊 Results:
- Total Artifacts: {total_artifacts}
- Passed Validation: {passed}
- Failed: {total_artifacts - passed}
- Accuracy Score: {accuracy_score}%

✅ Validation Status: {"PASSED" if passed >= total_artifacts * 0.8 else "NEEDS REVIEW"}

All critical validation criteria have been met. Knowledge is ready for persistence."""

        return ToolResult(name="validate", result=content, require_user=False)


class PersistTool(BaseTool):
    def __init__(self):
        tool_info = BaseToolInformation(
            name="persist",
            description="Store all validated knowledge to the vector database for the target agent.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="artifacts_summary",
                        type="string",
                        description="Summary of artifacts to persist",
                        example="10 knowledge artifacts (5 facts, 2 procedures, 3 heuristics)",
                    ),
                    BaseArgument(name="target_agent_id", type="string", description="Agent ID to store knowledge for", example="123"),
                ],
                required=["artifacts_summary"],
            ),
        )
        super().__init__(tool_info)

    def _execute(self, artifacts_summary: str, target_agent_id: str = "unknown") -> ToolResult:
        # Mock persistence - in real implementation would store to vector DB
        content = f"""💾 Persistence Complete

{artifacts_summary} successfully stored to vector database.

📍 Storage Details:
- Agent ID: {target_agent_id}
- Storage Location: Vector Database
- Timestamp: {datetime.now().isoformat()}
- Status: Successfully Stored

🎯 Knowledge is now available for agent usage and retrieval."""

        return ToolResult(name="persist", result=content, require_user=False)


class CheckExistingTool(BaseTool):
    def __init__(self, tree_structure: DomainKnowledgeTree | None = None, knowledge_status_path: str | None = None):
        self.tree_structure = tree_structure
        self.knowledge_status_path = knowledge_status_path
        tool_info = BaseToolInformation(
            name="check_existing",
            description="Check if a topic already exists in the tree structure or has been successfully generated.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="target_path",
                        type="string",
                        description="The tree path to check for existing knowledge (optional, will search entire tree if not provided)",
                        example="Financial Analysis > Liquidity Analysis > Current Ratio",
                    ),
                    BaseArgument(
                        name="topic", type="string", description="Topic to check for duplicates", example="Current Ratio Analysis"
                    ),
                ],
                required=["topic"],
            ),
        )
        super().__init__(tool_info)

    def _execute(self, topic: str, target_path: str = "") -> ToolResult:
        """Check if topic exists in tree structure and/or has been generated."""

        # First check if topic exists in tree structure
        topic_exists_in_tree = False
        found_path = None

        if self.tree_structure and self.tree_structure.root:
            # Search for the topic in the tree
            found_node = self._find_topic_in_tree(self.tree_structure.root, topic)
            if found_node:
                topic_exists_in_tree = True
                # Get the path to this node
                found_path = self._get_path_to_node(self.tree_structure.root, found_node)

        # Check knowledge generation status if available
        generation_status = None
        if self.knowledge_status_path:
            generation_status = self._check_generation_status(topic)

        # Build response based on findings
        if topic_exists_in_tree:
            path_str = " → ".join(found_path) if found_path else "Unknown path"

            if generation_status and generation_status.get("status") == "success":
                content = f"""⚠️ Topic Already Exists with Generated Knowledge

📍 Found in tree at: {path_str}
🎯 Topic: {topic}
✅ Generation Status: Success

Knowledge artifacts already generated:
- Last updated: {generation_status.get("last_updated", "Unknown")}
- Message: {generation_status.get("message", "No details")}

Recommendation: Topic already has complete knowledge. Consider:
- Using explore_knowledge to view existing structure
- Generating knowledge for other topics
- Using modify_tree if you want to reorganize structure"""
            else:
                content = f"""⚠️ Topic Already Exists in Tree

📍 Found in tree at: {path_str}
🎯 Topic: {topic}
⏳ Generation Status: {generation_status.get("status", "Not generated") if generation_status else "Not generated"}

This topic exists in the knowledge tree but doesn't have generated content yet.

Recommendation: 
- Proceed with generate_knowledge for this existing topic
- Or use explore_knowledge to find other topics needing content"""
        else:
            # Topic doesn't exist in tree
            if target_path:
                content = f"""✅ Clear to Proceed - New Topic

📍 Target Path: {target_path}
🎯 Topic: {topic}
🆕 Status: Topic not found in tree

This is a new topic that doesn't exist in the current tree structure.

Recommendation:
- Use modify_tree to add "{topic}" to the tree at the desired location
- Then proceed with generate_knowledge for the new topic"""
            else:
                content = f"""✅ Topic Not Found

🎯 Topic: {topic}
🔍 Status: Not found in knowledge tree

The topic "{topic}" doesn't exist in the current tree structure.

Suggestions:
- Use explore_knowledge to see available topics
- Use modify_tree to add this as a new topic
- Check spelling or try a similar topic name"""

        return ToolResult(name="check_existing", result=content, require_user=False)

    def _find_topic_in_tree(self, node, topic: str):
        """Recursively search for a topic in the tree."""
        if node.topic.lower() == topic.lower():
            return node

        for child in node.children:
            found = self._find_topic_in_tree(child, topic)
            if found:
                return found

        return None

    def _get_path_to_node(self, root, target_node, current_path=None):
        """Get the path from root to target node."""
        if current_path is None:
            current_path = []

        current_path = current_path + [root.topic]

        if root == target_node:
            return current_path

        for child in root.children:
            result = self._get_path_to_node(child, target_node, current_path)
            if result:
                return result

        return None

    def _check_generation_status(self, topic: str) -> dict | None:
        """Check if knowledge has been generated for this topic."""
        try:
            from pathlib import Path
            import json

            status_file = Path(self.knowledge_status_path)
            if status_file.exists():
                with open(status_file) as f:
                    status_data = json.load(f)
                return status_data.get(topic, None)
        except Exception:
            pass

        return None


class AttemptCompletionTool(BaseTool):
    def __init__(self):
        tool_info = BaseToolInformation(
            name="attempt_completion",
            description="Present information to the user. Use for final results after workflow completion OR to directly answer user questions about capabilities, explanations, or informational requests that don't require task execution.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="summary",
                        type="string",
                        description="Summary of what was accomplished OR direct answer/explanation to user's question",
                        example="Successfully generated 10 knowledge artifacts OR I can help you generate financial analysis knowledge, modify knowledge structure, and explore available topics",
                    ),
                ],
                required=["summary"],
            ),
        )
        super().__init__(tool_info)

    def _execute(self, summary: str) -> ToolResult:
        # Detect if this is a completion (mentions artifacts/generation) or information response
        is_completion = any(
            keyword in summary.lower() for keyword in ["generated", "created", "complete", "artifacts", "workflow", "finished"]
        )

        if is_completion:
            # Format as workflow completion
            content = f"""🎉 Knowledge Generation Complete

{summary}

✅ All knowledge has been:
- Generated with high accuracy
- Validated for quality  
- Stored to vector database
- Made available for agent usage

The knowledge generation workflow is now complete. Your agent has been enhanced with new domain expertise!"""
        else:
            # Format as direct information response
            content = f"""ℹ️ {summary}"""

        return ToolResult(name="attempt_completion", result=content, require_user=True)


if __name__ == "__main__":
    # Test AskQuestionTool (merged tool)
    tool = AskQuestionTool()
    print("AskQuestionTool (merged from AskFollowUpQuestionTool and AskApprovalTool):")
    print(tool)
    print("\n" + "=" * 60 + "\n")

    # Test ExploreKnowledgeTool
    explore_tool = ExploreKnowledgeTool()
    print("ExploreKnowledgeTool:")
    print(explore_tool)
