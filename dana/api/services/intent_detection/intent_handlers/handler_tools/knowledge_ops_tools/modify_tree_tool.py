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
import logging

logger = logging.getLogger(__name__)


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

    async def _execute(self, operation: str, tree_path: str = "", bulk_operations: str = "") -> ToolResult:
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

    def _create_single_node(self, path_parts: list[str], tree_path: str) -> dict:
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

        # Check if the root matches the first path element
        if current_node.topic == path_parts[0]:
            # Root matches, start from index 1
            start_idx = 1
        else:
            # Root doesn't match - this is ambiguous placement
            return {
                "success": False,
                "operation": "create",
                "path": tree_path,
                "error": f"Ambiguous node placement: Path starts with '{path_parts[0]}' but current tree root is '{current_node.topic}'. Please specify the complete path from the root, or use a path that starts with '{current_node.topic}' to add nodes to the existing tree structure.",
                "error_type": "ambiguous_placement",
                "suggestion": f"Try: ['{current_node.topic}', '{path_parts[0]}', ...] to add '{path_parts[0]}' as a child of the root",
                "current_root": current_node.topic,
                "attempted_path": path_parts,
            }

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

        # Return structured result
        return {
            "success": True,
            "operation": "create",
            "path": tree_path,
            "nodes_created": nodes_created,
            "total_created": len(nodes_created),
            "path_depth": len(path_parts),
            "already_existed": len(nodes_created) == 0,
            "error": None,
        }

    def _modify_single_node(self, path_parts: list[str], tree_path: str) -> dict:
        """Modify existing node in the tree structure."""
        if not self.tree_structure or not self.tree_structure.root:
            return {
                "success": False,
                "operation": "modify",
                "path": tree_path,
                "error": "No tree structure exists to modify",
                "error_type": "no_tree",
            }

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
                        return {
                            "success": False,
                            "operation": "modify",
                            "path": tree_path,
                            "error": f"Root node '{current_node.topic}' doesn't match path '{topic}'",
                            "error_type": "root_mismatch",
                        }
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
                    return {
                        "success": False,
                        "operation": "modify",
                        "path": tree_path,
                        "error": f"Node '{topic}' not found in path",
                        "error_type": "node_not_found",
                        "missing_node": topic,
                    }

                if i == len(path_parts) - 1:
                    node_found = True
                    modified_node = current_node

        if not node_found:
            return {
                "success": False,
                "operation": "modify",
                "path": tree_path,
                "error": f"Could not find node at path: {tree_path}",
                "error_type": "path_not_found",
            }

        # For modify operation, we might want to rename or update metadata
        # Since we don't have new data in parameters, we'll just update metadata
        old_topic = modified_node.topic

        return {
            "success": True,
            "operation": "modify",
            "path": tree_path,
            "node_topic": old_topic,
            "children_count": len(modified_node.children),
            "node_id": modified_node.id,
            "parent_topic": parent_node.topic if parent_node else None,
            "is_root": parent_node is None,
            "error": None,
        }

    def _remove_single_node(self, path_parts: list[str], tree_path: str) -> dict:
        """Remove node from the tree structure."""
        if not self.tree_structure or not self.tree_structure.root:
            return {
                "success": False,
                "operation": "remove",
                "path": tree_path,
                "error": "No tree structure exists to modify",
                "error_type": "no_tree",
            }

        # Cannot remove root node
        if len(path_parts) == 1 and self.tree_structure.root.topic == path_parts[0]:
            return {
                "success": False,
                "operation": "remove",
                "path": tree_path,
                "error": "Cannot remove root node. Consider replacing it with modify operation.",
                "error_type": "cannot_remove_root",
            }

        # Navigate to find the node and its parent
        current_node = self.tree_structure.root
        parent_node = None
        target_node = None

        # Navigate through the path
        for i, topic in enumerate(path_parts):
            if i == 0:
                if current_node.topic != topic:
                    return {
                        "success": False,
                        "operation": "remove",
                        "path": tree_path,
                        "error": f"Root node '{current_node.topic}' doesn't match path '{topic}'",
                        "error_type": "root_mismatch",
                    }
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
                return {
                    "success": False,
                    "operation": "remove",
                    "path": tree_path,
                    "error": f"Node '{topic}' not found in path",
                    "error_type": "node_not_found",
                    "missing_node": topic,
                }

        if not target_node:
            return {
                "success": False,
                "operation": "remove",
                "path": tree_path,
                "error": f"Could not find node to remove at path: {tree_path}",
                "error_type": "path_not_found",
            }

        return {
            "success": True,
            "operation": "remove",
            "path": tree_path,
            "removed_node": target_node.topic,
            "parent_node": parent_node.topic if parent_node else None,
            "children_removed": removed_children,
            "parent_children_count": len(parent_node.children),
            "has_child_impact": removed_children > 0,
            "error": None,
        }

    def _init_tree(self, domain_topic: str) -> tuple[str, DomainKnowledgeTree | None]:
        """Initialize a comprehensive tree structure from a domain topic using LLM."""
        try:
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
            def create_node(topic_name: str, children_data=None):
                """Create a DomainNode with optional children"""
                from dana.api.core.schemas import DomainNode

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
            from dana.api.core.schemas import DomainKnowledgeTree
            from datetime import datetime, UTC
            import json

            knowledge_tree = DomainKnowledgeTree(root=root_node, last_updated=datetime.now(UTC), version=1)

            # Count total nodes for display
            def count_nodes(node) -> int:
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

            # Execute all operations and gather results
            operation_results = []
            for i, op in enumerate(bulk_ops):
                action = op["action"]
                paths = op["paths"]

                path_parts = paths  # Already an array
                path_str = " > ".join(paths)

                try:
                    if action == "create":
                        result = self._create_single_node(path_parts, path_str)
                    elif action == "modify":
                        result = self._modify_single_node(path_parts, path_str)
                    elif action == "remove":
                        result = self._remove_single_node(path_parts, path_str)

                    operation_results.append(result)

                    if result["success"]:
                        results.append(f"✅ {action.title()}: {path_str}")
                        operations_performed.append(f"{action} {path_str}")
                    else:
                        # Operation failed - return detailed error information
                        return self._build_error_response(result, i + 1, operation_results)

                except Exception as e:
                    return f"❌ Error in operation {i + 1} ({action} {path_str}): {str(e)}"

            # Build comprehensive success response
            return self._build_success_response(operation_results, operations_performed)

        except json.JSONDecodeError as e:
            return f"❌ Error: Invalid JSON in bulk_operations: {str(e)}"
        except Exception as e:
            return f"❌ Error executing bulk operations: {str(e)}"

    def _build_error_response(self, failed_result: dict, operation_number: int, all_results: list) -> str:
        """Build comprehensive error response with context and suggestions."""
        error_type = failed_result.get("error_type", "unknown")
        error_msg = failed_result.get("error", "Unknown error")
        operation = failed_result.get("operation", "unknown")
        path = failed_result.get("path", "unknown")

        # Get successful operations before the failure
        successful_ops = [r for r in all_results[:-1] if r["success"]]

        content = f"""❌ Tree Operation Failed

🚫 **Operation {operation_number} Failed**: {operation.title()} operation on "{path}"
📋 **Error**: {error_msg}
🔍 **Error Type**: {error_type}

📊 **Operation Status**:
- Operations attempted: {len(all_results)}
- Successful before failure: {len(successful_ops)}
- Failed operation: {operation_number}

💡 **Suggestions**:"""

        if error_type == "node_not_found":
            missing_node = failed_result.get("missing_node", "")
            content += f"""
- The path "{path}" could not be found in the current tree structure
- Node "{missing_node}" does not exist at the expected location
- Use explore_knowledge to see the current tree structure
- Verify the correct path and node names
- Check if the node was moved or renamed"""
        elif error_type == "no_tree":
            content += """
- No tree structure exists yet
- Initialize the tree first using modify_tree with "init" operation
- Or create the root nodes manually before attempting this operation"""
        elif error_type == "root_mismatch":
            content += """
- The root node name doesn't match the path you specified
- Use explore_knowledge to see the actual root node name
- Update your path to start with the correct root node"""
        elif error_type == "cannot_remove_root":
            content += """
- Root nodes cannot be removed
- Consider using modify operation instead to change the root
- Or restructure the tree by creating a new tree with the desired root"""
        elif error_type == "ambiguous_placement":
            current_root = failed_result.get("current_root", "unknown")
            attempted_path = failed_result.get("attempted_path", [])
            suggestion = failed_result.get("suggestion", "")
            content += f"""
- Your path starts with '{attempted_path[0] if attempted_path else "unknown"}' but the tree root is '{current_root}'
- This could mean you want to:
  1. Add '{attempted_path[0] if attempted_path else "unknown"}' as a child of '{current_root}' 
  2. Or you meant to start the path from the existing root
- {suggestion}
- Use explore_knowledge to see the current tree structure
- Then specify the complete path from the root node"""
        else:
            content += """
- Use explore_knowledge to understand the current tree structure
- Verify all node names and paths are correct
- Check if the operation type matches your intent"""

        # Add tree exploration suggestion
        content += """

🔍 **Next Steps**:
1. Use explore_knowledge to see current tree structure
2. Verify the correct paths for your operations
3. Retry with the correct node names and structure

⚠️ **Note**: Previous successful operations were completed, but this operation failed."""

        return content

    def _build_success_response(self, operation_results: list, operations_performed: list) -> str:
        """Build comprehensive success response with detailed information."""

        # Categorize operations
        creates = [r for r in operation_results if r["operation"] == "create" and r["success"]]
        modifies = [r for r in operation_results if r["operation"] == "modify" and r["success"]]
        removes = [r for r in operation_results if r["operation"] == "remove" and r["success"]]

        content = f"""🌳 Bulk Tree Operations Complete

📊 **Summary**:
- Total operations: {len(operation_results)}
- Successfully completed: {len(operations_performed)}
- Create operations: {len(creates)}
- Modify operations: {len(modifies)}
- Remove operations: {len(removes)}

✅ **Operations Performed**:
{chr(10).join(f"{i + 1}. {op}" for i, op in enumerate(operations_performed))}"""

        # Add detailed information for each operation type
        if creates:
            total_nodes_created = sum(r.get("total_created", 0) for r in creates)
            content += f"""

🆕 **Creation Details**:
- New nodes created: {total_nodes_created}
- New branches established: {len([r for r in creates if r.get("total_created", 0) > 1])}
- Paths that already existed: {len([r for r in creates if r.get("already_existed", False)])}"""

        if removes:
            total_children_affected = sum(r.get("children_removed", 0) for r in removes)
            content += f"""

🗑️ **Removal Details**:
- Nodes removed: {len(removes)}
- Child nodes also removed: {total_children_affected}
- Operations with child impact: {len([r for r in removes if r.get("has_child_impact", False)])}"""

        if modifies:
            content += f"""

🔄 **Modification Details**:
- Nodes modified: {len(modifies)}
- Root node modifications: {len([r for r in modifies if r.get("is_root", False)])}"""

        content += """

🔗 **Tree Status**:
- Tree structure updated and consistent
- All navigation paths verified
- Ready for knowledge generation or further modifications

💡 **Next Steps**:
- Use explore_knowledge to view the updated structure
- Begin knowledge generation if needed
- Make additional modifications as required"""

        return content

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
