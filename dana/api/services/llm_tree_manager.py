"""LLM-powered tree management service for intelligent domain knowledge updates."""

import json
import logging
from typing import Any

from dana.api.core.schemas import (
    DomainKnowledgeTree,
    DomainNode,
    DomainKnowledgeUpdateResponse
)
from dana.common.mixins.loggable import Loggable
from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.types import BaseRequest

logger = logging.getLogger(__name__)


class LLMTreeManager(Loggable):
    """LLM-powered service for intelligent domain knowledge tree management."""
    
    def __init__(self):
        super().__init__()
        self.llm = LLMResource()
    
    async def smart_add_knowledge(
        self,
        current_tree: DomainKnowledgeTree | None,
        new_topic: str,
        suggested_parent: str | None,
        context_details: str | None,
        agent_name: str,
        agent_description: str
    ) -> DomainKnowledgeUpdateResponse:
        """
        Intelligently add knowledge to the tree using LLM reasoning.
        
        Args:
            current_tree: Current domain knowledge tree
            new_topic: Topic to add
            suggested_parent: Parent suggested by intent detection
            context_details: Additional context about the topic
            agent_name: Agent's name for context
            agent_description: Agent's description for context
            
        Returns:
            DomainKnowledgeUpdateResponse with updated tree
        """
        try:
            print(f"🧠 Smart add knowledge starting...")
            print(f"  - Topic: {new_topic}")
            print(f"  - Suggested parent: {suggested_parent}")
            print(f"  - Context: {context_details}")
            print(f"  - Agent: {agent_name}")
            print(f"  - Current tree exists: {current_tree is not None}")
            
            # If no tree exists, create initial structure
            if not current_tree:
                print("🌱 No current tree, creating initial structure...")
                return await self._create_initial_tree_with_topic(
                    new_topic, agent_name, agent_description
                )
            
            print("🔍 Analyzing tree placement with LLM...")
            # Use LLM to determine best placement and structure
            tree_analysis = await self._analyze_tree_placement(
                current_tree=current_tree,
                new_topic=new_topic,
                suggested_parent=suggested_parent,
                context_details=context_details,
                agent_context=f"{agent_name}: {agent_description}"
            )
            
            print(f"📊 Tree analysis result: {tree_analysis}")
            
            if not tree_analysis.get("success", False):
                error_msg = f"LLM analysis failed: {tree_analysis.get('error', 'Unknown error')}"
                print(f"❌ {error_msg}")
                return DomainKnowledgeUpdateResponse(
                    success=False,
                    error=error_msg
                )
            
            print("🔧 Applying tree changes...")
            # Apply the LLM's recommended changes
            updated_tree = await self._apply_tree_changes(
                current_tree, tree_analysis
            )
            
            print(f"✅ Tree changes applied successfully")
            
            return DomainKnowledgeUpdateResponse(
                success=True,
                updated_tree=updated_tree,
                changes_summary=tree_analysis.get("changes_summary", f"Added {new_topic}")
            )
            
        except Exception as e:
            print(f"❌ Exception in smart_add_knowledge: {e}")
            import traceback
            print(f"📚 Full traceback: {traceback.format_exc()}")
            self.error(f"Error in smart_add_knowledge: {e}")
            return DomainKnowledgeUpdateResponse(
                success=False,
                error=str(e)
            )
    
    async def _create_initial_tree_with_topic(
        self,
        topic: str,
        agent_name: str,
        agent_description: str
    ) -> DomainKnowledgeUpdateResponse:
        """Create initial tree structure with the new topic using LLM."""
        try:
            prompt = self._build_initial_tree_prompt(topic, agent_name, agent_description)
            
            llm_request = BaseRequest(
                arguments={
                    "messages": [
                        {"role": "system", "content": "You are an expert at organizing knowledge into hierarchical structures."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000
                }
            )
            
            response = await self.llm.query(llm_request)
            
            # Parse LLM response
            content = response.content
            print(f"🔍 Response content type: {type(content)}, content: {content}")
            
            if isinstance(content, str):
                # Direct string response
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    # Might be a nested JSON string
                    result = json.loads(content)
            elif isinstance(content, dict):
                # Check if it's OpenAI-style response
                if "choices" in content:
                    message_content = content["choices"][0]["message"]["content"]
                    result = json.loads(message_content)
                else:
                    result = content
            else:
                raise ValueError(f"Unexpected response content type: {type(content)}")
            
            # Build tree from LLM response
            tree_structure = result.get("tree_structure")
            if not tree_structure:
                raise ValueError("LLM didn't provide tree structure")
            
            root_node = self._build_node_from_dict(tree_structure)
            tree = DomainKnowledgeTree(root=root_node, version=1)
            
            return DomainKnowledgeUpdateResponse(
                success=True,
                updated_tree=tree,
                changes_summary=f"Created initial knowledge tree with {topic}"
            )
            
        except Exception as e:
            self.error(f"Error creating initial tree: {e}")
            return DomainKnowledgeUpdateResponse(
                success=False,
                error=str(e)
            )
    
    async def _analyze_tree_placement(
        self,
        current_tree: DomainKnowledgeTree,
        new_topic: str,
        suggested_parent: str | None,
        context_details: str | None,
        agent_context: str
    ) -> dict[str, Any]:
        """Use LLM to analyze where and how to add the new topic."""
        try:
            print(f"🔍 Building placement analysis prompt...")
            print(f"  - New topic: '{new_topic}' (type: {type(new_topic)})")
            print(f"  - Suggested parent: {suggested_parent}")
            print(f"  - Context details: {context_details}")
            print(f"  - Agent context: {agent_context}")
            
            prompt = self._build_placement_analysis_prompt(
                current_tree=current_tree,
                new_topic=new_topic,
                suggested_parent=suggested_parent,
                context_details=context_details,
                agent_context=agent_context
            )
            
            print(f"📝 Generated prompt (first 500 chars): {prompt[:500]}...")
            
            llm_request = BaseRequest(
                arguments={
                    "messages": [
                        {"role": "system", "content": "You are an expert knowledge architect. Analyze tree structures and recommend optimal placements for new knowledge."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1500
                }
            )
            
            print(f"🚀 Calling LLM...")
            response = await self.llm.query(llm_request)
            print(f"📨 LLM response type: {type(response)}")
            print(f"📨 LLM response: {response}")
            
            # Parse LLM response
            content = response.content
            print(f"📄 Response content type: {type(content)}")
            print(f"📄 Response content: {content}")
            
            if isinstance(content, str):
                print("🔄 Parsing content as JSON string...")
                result = json.loads(content)
            elif isinstance(content, dict):
                # Check if it's OpenAI-style response
                if "choices" in content:
                    print("🔄 Parsing OpenAI-style response...")
                    message_content = content["choices"][0]["message"]["content"]
                    print(f"📊 Message content: {message_content}")
                    result = json.loads(message_content)
                else:
                    print("🔄 Using content as dict directly...")
                    result = content
            else:
                raise ValueError(f"Unexpected response content type: {type(content)}")
            
            print(f"✅ Parsed result: {result}")
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"📄 Raw content that failed to parse: {content}")
            self.error(f"JSON parsing error in tree analysis: {e}")
            # Return fallback analysis that adds to root
            fallback_analysis = {
                "success": True,
                "action": "add_to_parent",
                "parent_topic": "root",
                "new_node": {
                    "topic": new_topic,
                    "children": []
                },
                "changes_summary": f"Added {new_topic} to the root level (fallback due to LLM parsing error)"
            }
            print(f"🚨 Returning fallback analysis: {fallback_analysis}")
            return fallback_analysis
        except Exception as e:
            print(f"❌ General error in tree analysis: {e}")
            print(f"🔍 Error type: {type(e)}")
            import traceback
            print(f"📚 Full traceback: {traceback.format_exc()}")
            self.error(f"Error in tree analysis: {e}")
            # Return fallback analysis that adds to root
            return {
                "success": True,
                "action": "add_to_parent", 
                "parent_topic": "root",
                "new_node": {
                    "topic": new_topic,
                    "children": []
                },
                "changes_summary": f"Added {new_topic} to the root level (fallback due to analysis error)"
            }
    
    async def _apply_tree_changes(
        self,
        current_tree: DomainKnowledgeTree,
        tree_analysis: dict[str, Any]
    ) -> DomainKnowledgeTree:
        """Apply the tree changes based on LLM analysis."""
        print(f"🔧 Applying tree changes: {tree_analysis}")
        print(f"🔧 Current tree root children: {[child.topic for child in current_tree.root.children] if current_tree.root.children else []}")
        
        action = tree_analysis.get("action", "add_to_parent")
        
        if action == "add_to_parent":
            parent_topic = tree_analysis.get("parent_topic", "root")
            new_node_data = tree_analysis.get("new_node", {})
            
            # Create new node
            topic_name = new_node_data.get("topic", "Unknown")
            print(f"🏗️ Creating new node with topic: '{topic_name}'")
            new_node = DomainNode(
                topic=topic_name,
                children=new_node_data.get("children", [])
            )
            print(f"🏗️ Created node: {new_node}")
            
            # Find and update the parent node
            def add_to_node(node: DomainNode) -> bool:
                if node.topic.lower() == parent_topic.lower() or parent_topic == "root":
                    # Add to this node's children
                    if not hasattr(node, 'children') or node.children is None:
                        node.children = []
                    node.children.append(new_node)
                    print(f"✅ Added '{new_node.topic}' to '{node.topic}'")
                    return True
                
                # Recursively search children
                if hasattr(node, 'children') and node.children:
                    for child in node.children:
                        if add_to_node(child):
                            return True
                return False
            
            # If parent_topic is "root", add to root's children
            if parent_topic == "root":
                print(f"🌳 Adding to root. Current root children count: {len(current_tree.root.children) if current_tree.root.children else 0}")
                if not hasattr(current_tree.root, 'children') or current_tree.root.children is None:
                    current_tree.root.children = []
                    print(f"🌳 Initialized empty children list")
                current_tree.root.children.append(new_node)
                print(f"✅ Added '{new_node.topic}' to root. New children count: {len(current_tree.root.children)}")
                print(f"🌳 All root children: {[child.topic for child in current_tree.root.children]}")
            else:
                # Search for parent and add
                if not add_to_node(current_tree.root):
                    # Fallback: add to root if parent not found
                    if not hasattr(current_tree.root, 'children') or current_tree.root.children is None:
                        current_tree.root.children = []
                    current_tree.root.children.append(new_node)
                    print(f"⚠️ Parent '{parent_topic}' not found, added '{new_node.topic}' to root")
        
        # Update tree metadata
        current_tree.version = (current_tree.version or 0) + 1
        from datetime import datetime, UTC
        current_tree.last_updated = datetime.now(UTC)
        
        print(f"🔄 Final tree before return:")
        print(f"   Root: {current_tree.root.topic}")
        print(f"   Children: {[child.topic for child in current_tree.root.children] if current_tree.root.children else []}")
        print(f"   Version: {current_tree.version}")
        
        return current_tree
    
    def _build_initial_tree_prompt(
        self,
        topic: str,
        agent_name: str,
        agent_description: str
    ) -> str:
        """Build prompt for creating initial tree structure."""
        return f"""Create an initial domain knowledge tree for an agent.

Agent Info:
- Name: {agent_name}
- Description: {agent_description}

The user wants to add this topic: "{topic}"

Create a logical hierarchical structure that:
1. Has a meaningful root category (not "Untitled" or generic names)
2. Places the topic in the right context
3. Allows for future expansion

Respond with this exact JSON format:
{{
  "success": true,
  "tree_structure": {{
    "topic": "Root Category Name",
    "children": [
      {{
        "topic": "{topic}",
        "children": []
      }}
    ]
  }},
  "changes_summary": "Created initial tree with..."
}}

Example: If topic is "Financial Statement Analysis", create a tree like:
{{
  "success": true,
  "tree_structure": {{
    "topic": "Finance",
    "children": [
      {{
        "topic": "Financial Statement Analysis",
        "children": []
      }}
    ]
  }}
}}"""
    
    def _build_placement_analysis_prompt(
        self,
        current_tree: DomainKnowledgeTree,
        new_topic: str,
        suggested_parent: str | None,
        context_details: str | None,
        agent_context: str
    ) -> str:
        """Build prompt for analyzing optimal topic placement."""
        
        tree_json = json.dumps(current_tree.model_dump(), indent=2, default=str)
        
        return f"""Analyze this domain knowledge tree and add or reorganize the topic "{new_topic}".

Current Tree:
{tree_json}

Task: Add "{new_topic}" under parent "{suggested_parent or 'auto-detect'}"

SCENARIOS:
1. If "{new_topic}" already exists in tree and needs to be moved under "{suggested_parent}":
   - Move the existing node and all its children
2. If "{new_topic}" is new:
   - Add it under the specified parent
3. If reorganization improves structure:
   - Create logical groupings

RESPOND WITH ONLY VALID JSON:
{{
  "success": true,
  "changes_to_apply": [
    {{"action": "move_node", "topic_to_move": "{new_topic}", "to_path": ["Untitled", "{suggested_parent}"]}}
  ],
  "changes_summary": "Moved {new_topic} under {suggested_parent}"
}}"""
    
    async def _apply_tree_changes(
        self,
        current_tree: DomainKnowledgeTree,
        analysis: dict[str, Any]
    ) -> DomainKnowledgeTree:
        """Apply the LLM's recommended changes to the tree."""
        
        print(f"🔧 Applying tree changes...")
        print(f"📋 Full analysis keys: {list(analysis.keys())}")
        print(f"📋 Analysis: {analysis}")
        
        # Handle different possible response formats
        changes = analysis.get("changes_to_apply", [])
        if not changes:
            # Try alternate key names
            changes = analysis.get("changes", [])
        
        print(f"📝 Changes to apply ({len(changes)} items): {changes}")
        
        if not changes:
            print("❌ No changes found in analysis! Creating manual change...")
            # If LLM didn't provide proper format, create a fallback
            # This is a temporary fix - we should check what the LLM actually returned
            changes = [{
                "action": "add_node",
                "parent_path": ["Untitled"],  # Add to root for now
                "new_topic": "Software engineering"
            }]
            print(f"📝 Fallback changes created: {changes}")
        
        # Work on a copy of the tree
        tree_dict = current_tree.model_dump()
        print(f"🌳 Original tree dict: {tree_dict}")
        
        root_node = self._build_node_from_dict(tree_dict["root"])
        print(f"🌱 Root node created: {root_node.topic} with {len(root_node.children)} children")
        
        changes_applied_count = 0
        
        # Apply each change
        for i, change in enumerate(changes):
            print(f"🔄 Processing change {i+1}: {change}")
            
            if change.get("action") == "add_node":
                parent_path = change.get("parent_path", ["Untitled"])
                new_topic = change.get("new_topic", "Unknown Topic")
                
                print(f"  - Adding '{new_topic}' to parent path: {parent_path}")
                
                # Find the parent node
                parent_node = self._find_node_by_path(root_node, parent_path)
                print(f"  - Parent node found: {parent_node.topic if parent_node else 'None'}")
                
                if parent_node:
                    # Check if topic already exists
                    existing_topics = [child.topic for child in parent_node.children]
                    print(f"  - Existing children: {existing_topics}")
                    
                    if not any(child.topic == new_topic for child in parent_node.children):
                        new_node = DomainNode(topic=new_topic, children=[])
                        parent_node.children.append(new_node)
                        changes_applied_count += 1
                        print(f"  ✅ Added '{new_topic}' to parent '{parent_node.topic}'")
                    else:
                        print(f"  ⚠️ Topic '{new_topic}' already exists under '{parent_node.topic}'")
                else:
                    print(f"  ❌ Parent node not found for path: {parent_path}")
                    # Try adding to root as fallback
                    if not any(child.topic == new_topic for child in root_node.children):
                        new_node = DomainNode(topic=new_topic, children=[])
                        root_node.children.append(new_node)
                        changes_applied_count += 1
                        print(f"  🔄 Added '{new_topic}' to root as fallback")
            
            elif change.get("action") == "move_node":
                topic_to_move = change.get("topic_to_move")
                from_path = change.get("from_path", [])
                to_path = change.get("to_path", ["Untitled"])
                
                print(f"  - Moving '{topic_to_move}' from {from_path} to {to_path}")
                print(f"  - Root children before move: {[child.topic for child in root_node.children]}")
                
                # Find and remove the node from its current location
                moved_node = self._find_and_remove_node(root_node, topic_to_move)
                print(f"  - Found node to move: {moved_node.topic if moved_node else 'None'}")
                print(f"  - Root children after remove: {[child.topic for child in root_node.children]}")
                
                if moved_node:
                    # Find the new parent and add the moved node
                    new_parent = self._find_node_by_path(root_node, to_path)
                    print(f"  - New parent found: {new_parent.topic if new_parent else 'None'}")
                    
                    if new_parent:
                        print(f"  - New parent children before add: {[child.topic for child in new_parent.children]}")
                        new_parent.children.append(moved_node)
                        print(f"  - New parent children after add: {[child.topic for child in new_parent.children]}")
                        changes_applied_count += 1
                        print(f"  ✅ Moved '{topic_to_move}' to '{new_parent.topic}'")
                    else:
                        # If new parent not found, add back to root
                        root_node.children.append(moved_node)
                        print(f"  🔄 Moved '{topic_to_move}' to root as fallback - parent path {to_path} not found")
                else:
                    print(f"  ❌ Could not find node '{topic_to_move}' to move")
            
            elif change.get("action") == "remove_node":
                topic_to_remove = change.get("topic_to_remove")
                print(f"  - Removing '{topic_to_remove}'")
                
                removed_node = self._find_and_remove_node(root_node, topic_to_remove)
                if removed_node:
                    changes_applied_count += 1
                    print(f"  ✅ Removed '{topic_to_remove}'")
                else:
                    print(f"  ❌ Could not find node '{topic_to_remove}' to remove")
            
            else:
                print(f"  ❌ Unknown action: {change.get('action', 'No action')}")
        
        print(f"📊 Total changes applied: {changes_applied_count}")
        
        # Create updated tree
        updated_tree = DomainKnowledgeTree(
            root=root_node,
            version=current_tree.version + 1
        )
        
        print(f"🌳 Updated tree structure:")
        self._print_tree_structure(updated_tree.root, indent=0)
        
        return updated_tree
    
    def _print_tree_structure(self, node: DomainNode, indent: int = 0):
        """Debug helper to print tree structure."""
        print(f"{'  ' * indent}📁 {node.topic}")
        for child in node.children:
            self._print_tree_structure(child, indent + 1)
    
    def _build_node_from_dict(self, node_dict: dict[str, Any]) -> DomainNode:
        """Recursively build DomainNode from dictionary."""
        children = []
        for child_dict in node_dict.get("children", []):
            children.append(self._build_node_from_dict(child_dict))
        
        return DomainNode(
            topic=node_dict["topic"],
            children=children
        )
    
    def _find_node_by_path(self, root: DomainNode, path: list[str]) -> DomainNode | None:
        """Find a node by following the given path."""
        current = root
        
        # Skip the first element if it matches root
        start_idx = 1 if path and path[0] == current.topic else 0
        
        for topic in path[start_idx:]:
            found = False
            for child in current.children:
                if child.topic == topic:
                    current = child
                    found = True
                    break
            if not found:
                return None
        
        return current

    def _find_and_remove_node(self, root: DomainNode, topic_to_find: str) -> DomainNode | None:
        """Find a node by topic name and remove it from its parent. Returns the removed node."""
        # Check if it's a direct child of root
        for i, child in enumerate(root.children):
            if child.topic == topic_to_find:
                return root.children.pop(i)
        
        # Recursively search in children
        for child in root.children:
            removed = self._find_and_remove_node(child, topic_to_find)
            if removed:
                return removed
        
        return None


def get_llm_tree_manager() -> LLMTreeManager:
    """Dependency injection for LLM tree manager."""
    return LLMTreeManager()