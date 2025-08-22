from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
    ToolResult,
)
from dana.api.core.schemas import DomainKnowledgeTree
import logging

logger = logging.getLogger(__name__)


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

    async def _execute(self, query: str = "", depth: str = "3") -> ToolResult:
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
        # Use parameters to avoid unused variable warnings
        _ = query, target_node, generation_status

        footer = ""

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
        # Use parameters to avoid unused variable warnings
        _ = query, target_node, generation_status

        return ""
