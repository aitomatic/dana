"""LLM-powered tree management service for intelligent domain knowledge updates."""

import json
import logging
from typing import Any

from dana.api.core.schemas import DomainKnowledgeTree, DomainNode, DomainKnowledgeUpdateResponse
from dana.common.mixins.loggable import Loggable
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.common.types import BaseRequest

logger = logging.getLogger(__name__)


class LLMTreeManager(Loggable):
    """LLM-powered service for intelligent domain knowledge tree management."""

    def __init__(self):
        super().__init__()
        self.llm = LLMResource()

    async def add_topic_to_knowledge(
        self,
        current_tree: DomainKnowledgeTree | None,
        paths: list[str],
        suggested_parent: str | None,
        context_details: str | None,
        agent_name: str,
        agent_description: str,
        chat_history: list = None,
    ) -> DomainKnowledgeUpdateResponse:
        try:
            print("🧠 Smart add knowledge starting...")
            print(f"  - Paths: {paths}")
            print(f"  - Current tree exists: {current_tree is not None}")

            # Check if the final topic already exists anywhere in the tree
            if current_tree and paths:
                final_topic = paths[-1]
                existing_node = self._find_topic_in_tree_simple(current_tree.root, final_topic)
                if existing_node:
                    print(f"⚠️ Topic '{final_topic}' already exists in the tree. Skipping duplicate creation.")
                    return DomainKnowledgeUpdateResponse(
                        success=True,
                        updated_tree=current_tree,
                        changes_summary=f"Topic '{final_topic}' already exists in tree - no changes needed",
                    )

            # changed will be used to determine if the tree has changed
            current_node = current_tree
            changed = False
            for node_name in paths:
                if hasattr(current_node, node_name):
                    current_node = getattr(current_node, node_name)
                elif hasattr(current_node, "topic") and current_node.topic == node_name:
                    continue
                elif hasattr(current_node, "children"):
                    # check if the node exists in the children or this is a new path to add
                    is_new_path = True
                    for child in current_node.children:
                        if child.topic == node_name:
                            current_node = child
                            is_new_path = False
                            break
                    if is_new_path:
                        current_node.children.append(DomainNode(topic=node_name, children=[]))
                        current_node = current_node.children[-1]
                        changed = True
                else:
                    current_node.children.append(DomainNode(topic=node_name, children=[]))
                    current_node = current_node.children[-1]
                    changed = True
            if changed:
                current_tree.version += 1
            return DomainKnowledgeUpdateResponse(success=True, updated_tree=current_tree, changes_summary=f"Added {paths} to the tree")
        except Exception as e:
            print(f"❌ Exception in add_topic_to_knowledge: {e}")
            self.error(f"Error in add_topic_to_knowledge: {e}. Falling back to smart_add_knowledge.")
            return await self.smart_add_knowledge(
                current_tree=current_tree,
                new_topic=paths[-1],
                suggested_parent=suggested_parent,
                context_details=context_details,
                agent_name=agent_name,
                agent_description=agent_description,
                chat_history=chat_history,
            )

    async def smart_add_knowledge(
        self,
        current_tree: DomainKnowledgeTree | None,
        new_topic: str,
        suggested_parent: str | None,
        context_details: str | None,
        agent_name: str,
        agent_description: str,
        chat_history: list = None,
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
            chat_history: Recent chat messages for additional context

        Returns:
            DomainKnowledgeUpdateResponse with updated tree
        """
        try:
            print("🧠 Smart add knowledge starting...")
            print(f"  - Topic: {new_topic}")
            print(f"  - Suggested parent: {suggested_parent}")
            print(f"  - Context: {context_details}")
            print(f"  - Agent: {agent_name}")
            print(f"  - Current tree exists: {current_tree is not None}")

            # If no tree exists, create initial structure
            if not current_tree:
                print("🌱 No current tree, creating initial structure...")
                return await self._create_initial_tree_with_topic(new_topic, agent_name, agent_description)

            print("🔍 Analyzing tree placement with LLM...")
            # Use LLM to determine best placement and structure
            tree_analysis = await self._analyze_tree_placement(
                current_tree=current_tree,
                new_topic=new_topic,
                suggested_parent=suggested_parent,
                context_details=context_details,
                agent_context=f"{agent_name}: {agent_description}",
                chat_history=chat_history or [],
            )

            print(f"📊 Tree analysis result: {tree_analysis}")

            if not tree_analysis.get("success", False):
                error_msg = f"LLM analysis failed: {tree_analysis.get('error', 'Unknown error')}"
                print(f"❌ {error_msg}")
                return DomainKnowledgeUpdateResponse(success=False, error=error_msg)

            print("🔧 Applying tree changes...")
            # Apply the LLM's recommended changes
            updated_tree = await self._apply_tree_changes(current_tree, tree_analysis, new_topic)

            print("✅ Tree changes applied successfully")

            return DomainKnowledgeUpdateResponse(
                success=True, updated_tree=updated_tree, changes_summary=tree_analysis.get("changes_summary", f"Added {new_topic}")
            )

        except Exception as e:
            print(f"❌ Exception in smart_add_knowledge: {e}")
            import traceback

            print(f"📚 Full traceback: {traceback.format_exc()}")
            self.error(f"Error in smart_add_knowledge: {e}")
            return DomainKnowledgeUpdateResponse(success=False, error=str(e))

    async def _create_initial_tree_with_topic(self, topic: str, agent_name: str, agent_description: str) -> DomainKnowledgeUpdateResponse:
        """Create initial tree structure with the new topic using LLM."""
        try:
            prompt = self._build_initial_tree_prompt(topic, agent_name, agent_description)

            llm_request = BaseRequest(
                arguments={
                    "messages": [
                        {"role": "system", "content": "You are an expert at organizing knowledge into hierarchical structures."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000,
                }
            )

            response = await self.llm.query(llm_request)

            # Parse LLM response
            content = response.content
            print(f"🔍 Response content type: {type(content)}, content: {content}")

            if isinstance(content, str):
                # Direct string response
                # Handle markdown code blocks if present
                content_to_parse = content.strip()
                if content_to_parse.startswith("```json") and content_to_parse.endswith("```"):
                    content_to_parse = content_to_parse[7:-3].strip()
                elif content_to_parse.startswith("```") and content_to_parse.endswith("```"):
                    content_to_parse = content_to_parse[3:-3].strip()
                result = json.loads(content_to_parse)
            elif isinstance(content, dict):
                # Check if it's OpenAI-style response
                if "choices" in content:
                    message_content = content["choices"][0]["message"]["content"]
                    # Handle markdown code blocks if present
                    content_to_parse = message_content.strip()
                    if content_to_parse.startswith("```json") and content_to_parse.endswith("```"):
                        content_to_parse = content_to_parse[7:-3].strip()
                    elif content_to_parse.startswith("```") and content_to_parse.endswith("```"):
                        content_to_parse = content_to_parse[3:-3].strip()
                    result = json.loads(content_to_parse)
                else:
                    result = content
            else:
                raise ValueError(f"Unexpected response content type: {type(content)}")

            # Build tree from LLM response - handle different formats
            tree_structure = result.get("tree_structure")

            # If no tree_structure, check if response is in changes_to_apply format
            if not tree_structure:
                changes = result.get("changes_to_apply", [])
                if changes and len(changes) > 0:
                    change = changes[0]
                    if change.get("action") == "add_node_with_children":
                        # Convert to tree_structure format
                        new_topic = change.get("new_topic", topic)
                        child_topics = change.get("child_topics", [])

                        # Create children nodes
                        children = []
                        for child_topic in child_topics:
                            children.append({"topic": child_topic, "children": []})

                        # Create root with main topic as child
                        tree_structure = {"topic": "Domain Knowledge", "children": [{"topic": new_topic, "children": children}]}
                    else:
                        # Simple add_node format
                        new_topic = change.get("new_topic", topic)
                        tree_structure = {"topic": "Domain Knowledge", "children": [{"topic": new_topic, "children": []}]}
                else:
                    raise ValueError("LLM didn't provide tree structure or valid changes")

            root_node = self._build_node_from_dict(tree_structure)
            tree = DomainKnowledgeTree(root=root_node, version=1)

            return DomainKnowledgeUpdateResponse(
                success=True, updated_tree=tree, changes_summary=f"Created initial knowledge tree with {topic}"
            )

        except Exception as e:
            self.error(f"Error creating initial tree: {e}")
            return DomainKnowledgeUpdateResponse(success=False, error=str(e))

    async def _analyze_tree_placement(
        self,
        current_tree: DomainKnowledgeTree,
        new_topic: str,
        suggested_parent: str | None,
        context_details: str | None,
        agent_context: str,
        chat_history: list = None,
    ) -> dict[str, Any]:
        """Use LLM to analyze where and how to add the new topic."""
        try:
            print("🔍 Building placement analysis prompt...")
            print(f"  - New topic: '{new_topic}' (type: {type(new_topic)})")
            print(f"  - Suggested parent: {suggested_parent}")
            print(f"  - Context details: {context_details}")
            print(f"  - Agent context: {agent_context}")

            prompt = self._build_placement_analysis_prompt(
                current_tree=current_tree,
                new_topic=new_topic,
                suggested_parent=suggested_parent,
                context_details=context_details,
                agent_context=agent_context,
                chat_history=chat_history or [],
            )

            print(f"📝 Generated prompt (first 500 chars): {prompt[:500]}...")

            llm_request = BaseRequest(
                arguments={
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert knowledge architect. Analyze tree structures and recommend optimal placements for new knowledge.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1500,
                }
            )

            print("🚀 Calling LLM...")
            response = await self.llm.query(llm_request)
            print(f"📨 LLM response type: {type(response)}")
            print(f"📨 LLM response: {response}")

            # Parse LLM response
            content = response.content
            print(f"📄 Response content type: {type(content)}")
            print(f"📄 Response content: {content}")

            if isinstance(content, str):
                print("🔄 Parsing content as JSON string...")
                # Handle markdown code blocks if present
                content_to_parse = content.strip()
                if content_to_parse.startswith("```json") and content_to_parse.endswith("```"):
                    content_to_parse = content_to_parse[7:-3].strip()
                elif content_to_parse.startswith("```") and content_to_parse.endswith("```"):
                    content_to_parse = content_to_parse[3:-3].strip()
                result = json.loads(content_to_parse)
            elif isinstance(content, dict):
                # Check if it's OpenAI-style response
                if "choices" in content:
                    print("🔄 Parsing OpenAI-style response...")
                    message_content = content["choices"][0]["message"]["content"]
                    print(f"📊 Message content: {message_content}")
                    # Handle markdown code blocks if present
                    content_to_parse = message_content.strip()
                    if content_to_parse.startswith("```json") and content_to_parse.endswith("```"):
                        content_to_parse = content_to_parse[7:-3].strip()
                    elif content_to_parse.startswith("```") and content_to_parse.endswith("```"):
                        content_to_parse = content_to_parse[3:-3].strip()
                    result = json.loads(content_to_parse)
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
                "new_node": {"topic": new_topic, "children": []},
                "changes_summary": f"Added {new_topic} to the root level (fallback due to LLM parsing error)",
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
                "new_node": {"topic": new_topic, "children": []},
                "changes_summary": f"Added {new_topic} to the root level (fallback due to analysis error)",
            }

    def _build_initial_tree_prompt(self, topic: str, agent_name: str, agent_description: str) -> str:
        """Build prompt for creating initial tree structure."""
        return f"""Create an initial domain knowledge tree for an agent.

Agent Info:
- Name: {agent_name}
- Description: {agent_description}

The user wants to add this topic: "{topic}"

Create a logical hierarchical structure that:
1. Has a meaningful root category (not "Untitled" or generic names)
2. Places the topic in the right context
3. Includes 5-7 relevant child topics under the main topic to demonstrate expertise
4. For each child topic, include 2-4 grandchild topics (going 2-3 levels deep)
5. Allows for future expansion

IMPORTANT: Generate comprehensive child and grandchild topics that show deep understanding of the domain and provide immediate value to users.

Respond with this exact JSON format:
{{
  "success": true,
  "tree_structure": {{
    "topic": "Root Category Name",
    "children": [
      {{
        "topic": "{topic}",
        "children": [
          {{
            "topic": "Child Topic 1",
            "children": [
              {{"topic": "Grandchild 1.1", "children": []}},
              {{"topic": "Grandchild 1.2", "children": []}},
              {{"topic": "Grandchild 1.3", "children": []}}
            ]
          }},
          {{
            "topic": "Child Topic 2",
            "children": [
              {{"topic": "Grandchild 2.1", "children": []}},
              {{"topic": "Grandchild 2.2", "children": []}},
              {{"topic": "Grandchild 2.3", "children": []}}
            ]
          }},
          {{
            "topic": "Child Topic 3",
            "children": [
              {{"topic": "Grandchild 3.1", "children": []}},
              {{"topic": "Grandchild 3.2", "children": []}}
            ]
          }},
          {{
            "topic": "Child Topic 4",
            "children": [
              {{"topic": "Grandchild 4.1", "children": []}},
              {{"topic": "Grandchild 4.2", "children": []}}
            ]
          }},
          {{
            "topic": "Child Topic 5",
            "children": [
              {{"topic": "Grandchild 5.1", "children": []}},
              {{"topic": "Grandchild 5.2", "children": []}}
            ]
          }}
        ]
      }}
    ]
  }},
  "changes_summary": "Created initial tree with {topic} and comprehensive 2-3 level hierarchy"
}}

Example: If topic is "Personal Finance Advisory", create:
{{
  "success": true,
  "tree_structure": {{
    "topic": "Finance",
    "children": [
      {{
        "topic": "Personal Finance Advisory",
        "children": [
          {{"topic": "Retirement Planning", "children": []}},
          {{"topic": "Investment Strategies", "children": []}},
          {{"topic": "Budget Management", "children": []}},
          {{"topic": "Tax Planning", "children": []}},
          {{"topic": "Insurance Planning", "children": []}},
          {{"topic": "Estate Planning", "children": []}}
        ]
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
        agent_context: str,
        chat_history: list = None,
    ) -> str:
        """Build prompt for analyzing optimal topic placement."""

        tree_json = json.dumps(current_tree.model_dump(), indent=2, default=str)

        # Build chat history context
        chat_context = ""
        if chat_history and len(chat_history) > 0:
            chat_context = "\n\nRecent Chat History (for context):\n"
            for msg in chat_history[-5:]:  # Last 5 messages
                role = getattr(msg, "role", "unknown")
                content = getattr(msg, "content", str(msg))
                chat_context += f"{role}: {content}\n"

        return f"""Analyze this domain knowledge tree and add or reorganize the topic "{new_topic}".

Agent Context: {agent_context}

Current Tree:
{tree_json}

Task: Add "{new_topic}" under parent "{suggested_parent or "auto-detect"}"
Additional Context: {context_details or "None"}{chat_context}

CRITICAL REQUIREMENT: When adding "{new_topic}", you MUST automatically generate:
1. The main topic "{new_topic}"
2. 5-7 relevant child topics (subtopics) under "{new_topic}" that demonstrate deep domain understanding
3. For each child topic, generate 2-4 grandchild topics (going 2-3 levels deep minimum)

This automatic hierarchy generation ensures users get comprehensive domain coverage when they mention any topic.

Example: If new_topic is "Cryptocurrency", generate:
- Cryptocurrency (main topic)
  - Bitcoin and Altcoins
    - Bitcoin Trading Strategies
    - Altcoin Investment Analysis
    - DeFi Protocols
  - Blockchain Technology
    - Smart Contracts
    - Consensus Mechanisms
    - Cryptocurrency Mining
  - Market Analysis
    - Technical Analysis
    - Market Sentiment
    - Price Prediction Models
  - Risk Management
    - Portfolio Diversification
    - Security Best Practices
    - Regulatory Compliance
  - Trading Platforms
    - Exchange Selection
    - Trading Tools
    - Order Types

This comprehensive structure gives users immediate access to related knowledge areas.

Example child topics for different domains:
- If adding "Retirement Planning": child topics could be "401k Management", "IRA Strategies", "Social Security Optimization", "Healthcare Planning", "Estate Planning", "Tax-Efficient Withdrawals", "Investment Allocation"
- If adding "Machine Learning": child topics could be "Supervised Learning", "Neural Networks", "Feature Engineering", "Model Evaluation", "Deep Learning", "Natural Language Processing", "Computer Vision"
- If adding "Digital Marketing": child topics could be "SEO Optimization", "Social Media Strategy", "Content Marketing", "Email Campaigns", "PPC Advertising", "Analytics Tracking", "Conversion Optimization"

SCENARIOS:
1. If "{new_topic}" already exists anywhere in the tree:
   - DO NOT create a duplicate - the system will handle this automatically
   - If it needs to be moved, use the move_node action
2. If "{new_topic}" is new:
   - Add it under the specified parent
3. If reorganization improves structure:
   - Create logical groupings

CRITICAL: Before suggesting any new topic, carefully check if "{new_topic}" already exists anywhere in the current tree structure. If it exists, do not create duplicates.

RESPOND WITH ONLY VALID JSON including multi-level child topics:
{{
  "success": true,
  "changes_to_apply": [
    {{
      "action": "add_node_with_hierarchical_children",
      "parent_path": ["Untitled", "{suggested_parent or "Untitled"}"],
      "new_topic": "{new_topic}",
      "hierarchical_structure": {{
        "topic": "{new_topic}",
        "children": [
          {{
            "topic": "Child Topic 1", 
            "children": [
              {{"topic": "Grandchild 1.1", "children": []}},
              {{"topic": "Grandchild 1.2", "children": []}},
              {{"topic": "Grandchild 1.3", "children": []}}
            ]
          }},
          {{
            "topic": "Child Topic 2",
            "children": [
              {{"topic": "Grandchild 2.1", "children": []}},
              {{"topic": "Grandchild 2.2", "children": []}},
              {{"topic": "Grandchild 2.3", "children": []}}
            ]
          }},
          {{
            "topic": "Child Topic 3",
            "children": [
              {{"topic": "Grandchild 3.1", "children": []}},
              {{"topic": "Grandchild 3.2", "children": []}}
            ]
          }},
          {{
            "topic": "Child Topic 4",
            "children": [
              {{"topic": "Grandchild 4.1", "children": []}},
              {{"topic": "Grandchild 4.2", "children": []}}
            ]
          }},
          {{
            "topic": "Child Topic 5",
            "children": [
              {{"topic": "Grandchild 5.1", "children": []}},
              {{"topic": "Grandchild 5.2", "children": []}}
            ]
          }}
        ]
      }}
    }}
  ],
  "changes_summary": "Added {new_topic} with comprehensive 2-3 level hierarchy including child and grandchild topics"
}}

If moving existing topics, use:
{{
  "success": true,
  "changes_to_apply": [
    {{"action": "move_node", "topic_to_move": "{new_topic}", "to_path": ["Untitled", "{suggested_parent}"]}}
  ],
  "changes_summary": "Moved {new_topic} under {suggested_parent}"
}}"""

    async def _apply_tree_changes(self, current_tree: DomainKnowledgeTree, analysis: dict[str, Any], new_topic: str) -> DomainKnowledgeTree:
        """Apply the LLM's recommended changes to the tree."""

        print("🔧 Applying tree changes...")
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
            # If LLM didn't provide proper format, create a fallback using the actual topic
            changes = [
                {
                    "action": "add_node",
                    "parent_path": ["Untitled"],  # Add to root for now
                    "new_topic": new_topic,  # Use the actual new_topic instead of hardcoded value
                }
            ]
            print(f"📝 Fallback changes created: {changes}")

        # Work on a copy of the tree
        tree_dict = current_tree.model_dump()
        print(f"🌳 Original tree dict: {tree_dict}")

        root_node = self._build_node_from_dict(tree_dict["root"])
        print(f"🌱 Root node created: {root_node.topic} with {len(root_node.children)} children")

        changes_applied_count = 0

        # Apply each change
        for i, change in enumerate(changes):
            print(f"🔄 Processing change {i + 1}: {change}")

            if change.get("action") == "add_node":
                parent_path = change.get("parent_path", ["Untitled"])
                new_topic = change.get("new_topic", "Unknown Topic")

                print(f"  - Adding '{new_topic}' to parent path: {parent_path}")

                # Find the parent node
                parent_node = self._find_node_by_path(root_node, parent_path)
                print(f"  - Parent node found: {parent_node.topic if parent_node else 'None'}")

                if parent_node:
                    # Check if topic already exists anywhere in the tree (comprehensive check)
                    existing_node = self._find_topic_in_tree_simple(root_node, new_topic)
                    if existing_node:
                        print(f"  ⚠️ Topic '{new_topic}' already exists in the tree. Skipping duplicate creation.")
                    else:
                        # Check if topic exists under this specific parent
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
                    existing_node = self._find_topic_in_tree_simple(root_node, new_topic)
                    if existing_node:
                        print(f"  ⚠️ Topic '{new_topic}' already exists in the tree. Skipping duplicate creation.")
                    elif not any(child.topic == new_topic for child in root_node.children):
                        new_node = DomainNode(topic=new_topic, children=[])
                        root_node.children.append(new_node)
                        changes_applied_count += 1
                        print(f"  🔄 Added '{new_topic}' to root as fallback")

            elif change.get("action") == "add_node_with_children":
                parent_path = change.get("parent_path", ["Untitled"])
                new_topic = change.get("new_topic", "Unknown Topic")
                child_topics = change.get("child_topics", [])

                print(f"  - Adding '{new_topic}' with {len(child_topics)} children to parent path: {parent_path}")
                print(f"  - Child topics: {child_topics}")

                # Find the parent node
                parent_node = self._find_node_by_path(root_node, parent_path)
                print(f"  - Parent node found: {parent_node.topic if parent_node else 'None'}")

                if parent_node:
                    # Check if topic already exists anywhere in the tree (comprehensive check)
                    existing_node = self._find_topic_in_tree_simple(root_node, new_topic)
                    if existing_node:
                        print(f"  ⚠️ Topic '{new_topic}' already exists in the tree. Skipping duplicate creation.")
                    else:
                        # Check if topic exists under this specific parent
                        existing_topics = [child.topic for child in parent_node.children]
                        print(f"  - Existing children: {existing_topics}")

                        if not any(child.topic == new_topic for child in parent_node.children):
                            # Create child nodes
                            child_nodes = []
                            for child_topic in child_topics:
                                child_nodes.append(DomainNode(topic=child_topic, children=[]))

                            # Create the main node with children
                            new_node = DomainNode(topic=new_topic, children=child_nodes)
                            parent_node.children.append(new_node)
                            changes_applied_count += 1
                            print(f"  ✅ Added '{new_topic}' with {len(child_topics)} children to parent '{parent_node.topic}'")
                        else:
                            print(f"  ⚠️ Topic '{new_topic}' already exists under '{parent_node.topic}'")
                else:
                    print(f"  ❌ Parent node not found for path: {parent_path}")
                    # Try adding to root as fallback
                    existing_node = self._find_topic_in_tree_simple(root_node, new_topic)
                    if existing_node:
                        print(f"  ⚠️ Topic '{new_topic}' already exists in the tree. Skipping duplicate creation.")
                    elif not any(child.topic == new_topic for child in root_node.children):
                        # Create child nodes
                        child_nodes = []
                        for child_topic in child_topics:
                            child_nodes.append(DomainNode(topic=child_topic, children=[]))

                        # Create the main node with children
                        new_node = DomainNode(topic=new_topic, children=child_nodes)
                        root_node.children.append(new_node)
                        changes_applied_count += 1
                        print(f"  🔄 Added '{new_topic}' with {len(child_topics)} children to root as fallback")

            elif change.get("action") == "add_node_with_hierarchical_children":
                parent_path = change.get("parent_path", ["Untitled"])
                new_topic = change.get("new_topic", "Unknown Topic")
                hierarchical_structure = change.get("hierarchical_structure", {})

                print(f"  - Adding '{new_topic}' with hierarchical structure to parent path: {parent_path}")
                print(f"  - Hierarchical structure: {hierarchical_structure}")

                # Find the parent node
                parent_node = self._find_node_by_path(root_node, parent_path)
                print(f"  - Parent node found: {parent_node.topic if parent_node else 'None'}")

                if parent_node:
                    # Check if topic already exists anywhere in the tree (comprehensive check)
                    existing_node = self._find_topic_in_tree_simple(root_node, new_topic)
                    if existing_node:
                        print(f"  ⚠️ Topic '{new_topic}' already exists in the tree. Skipping duplicate creation.")
                    else:
                        # Check if topic exists under this specific parent
                        existing_topics = [child.topic for child in parent_node.children]
                        print(f"  - Existing children: {existing_topics}")

                        if not any(child.topic == new_topic for child in parent_node.children):
                            # Build hierarchical structure recursively
                            new_node = self._build_node_from_dict(hierarchical_structure)
                            parent_node.children.append(new_node)
                            changes_applied_count += 1
                            print(f"  ✅ Added '{new_topic}' with hierarchical structure to parent '{parent_node.topic}'")
                        else:
                            print(f"  ⚠️ Topic '{new_topic}' already exists under '{parent_node.topic}'")
                else:
                    print(f"  ❌ Parent node not found for path: {parent_path}")
                    # Try adding to root as fallback
                    existing_node = self._find_topic_in_tree_simple(root_node, new_topic)
                    if existing_node:
                        print(f"  ⚠️ Topic '{new_topic}' already exists in the tree. Skipping duplicate creation.")
                    elif not any(child.topic == new_topic for child in root_node.children):
                        # Build hierarchical structure recursively
                        new_node = self._build_node_from_dict(hierarchical_structure)
                        root_node.children.append(new_node)
                        changes_applied_count += 1
                        print(f"  🔄 Added '{new_topic}' with hierarchical structure to root as fallback")

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
                preserve_children = change.get("preserve_children", False)  # Default to removing children with parent
                print(f"  - Removing '{topic_to_remove}' (preserve_children: {preserve_children})")

                if preserve_children:
                    removed_node, promoted_children = self._find_and_remove_node_preserve_children(root_node, topic_to_remove)
                    if removed_node:
                        changes_applied_count += 1
                        if promoted_children:
                            print(f"  ✅ Removed '{topic_to_remove}' and promoted {len(promoted_children)} children")
                        else:
                            print(f"  ✅ Removed '{topic_to_remove}' (no children to promote)")
                    else:
                        print(f"  ❌ Could not find node '{topic_to_remove}' to remove")
                else:
                    # Use original method that removes children too
                    removed_node = self._find_and_remove_node(root_node, topic_to_remove)
                    if removed_node:
                        changes_applied_count += 1
                        print(f"  ✅ Removed '{topic_to_remove}' including all children")
                    else:
                        print(f"  ❌ Could not find node '{topic_to_remove}' to remove")

            else:
                print(f"  ❌ Unknown action: {change.get('action', 'No action')}")

        print(f"📊 Total changes applied: {changes_applied_count}")

        # Create updated tree
        updated_tree = DomainKnowledgeTree(root=root_node, version=current_tree.version + 1)

        print("🌳 Updated tree structure:")
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

        # Preserve existing UUID if present, otherwise let default factory generate one
        if "id" in node_dict:
            return DomainNode(id=node_dict["id"], topic=node_dict["topic"], children=children)
        else:
            return DomainNode(topic=node_dict["topic"], children=children)

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

    def _find_and_remove_node_preserve_children(self, root: DomainNode, topic_to_find: str) -> tuple[DomainNode | None, list[DomainNode]]:
        """
        Find a node by topic name and remove it from its parent, but preserve its children.
        Returns the removed node and its children that should be promoted to the parent level.
        """
        # Check if it's a direct child of root
        for i, child in enumerate(root.children):
            if child.topic == topic_to_find:
                removed_node = root.children.pop(i)
                children_to_promote = removed_node.children if removed_node.children else []
                # Add the children back to the parent (root) at the same position
                for j, promoted_child in enumerate(children_to_promote):
                    root.children.insert(i + j, promoted_child)
                print(f"🔄 Promoted {len(children_to_promote)} children of '{topic_to_find}' to parent level")
                return removed_node, children_to_promote

        # Recursively search in children
        for child in root.children:
            removed, promoted = self._find_and_remove_node_preserve_children(child, topic_to_find)
            if removed:
                return removed, promoted

        return None, []

    def _find_topic_in_tree(self, root: DomainNode, topic_name: str) -> tuple[DomainNode | None, list[str]]:
        """
        Find a topic anywhere in the tree and return the node and its path.

        Args:
            root: Root node of the tree
            topic_name: Topic name to search for (case-insensitive)

        Returns:
            Tuple of (node, path) where node is the found node or None, and path is the list of topic names from root
        """

        def search_recursive(node: DomainNode, current_path: list[str]) -> tuple[DomainNode | None, list[str]]:
            if not node:
                return None, []

            # Check if current node matches (case-insensitive)
            if node.topic.lower() == topic_name.lower():
                return node, current_path + [node.topic]

            # Search in children
            for child in getattr(node, "children", []) or []:
                found_node, found_path = search_recursive(child, current_path + [node.topic])
                if found_node:
                    return found_node, found_path

            return None, []

        return search_recursive(root, [])

    def _find_topic_in_tree_simple(self, root: DomainNode, topic_name: str) -> DomainNode | None:
        """
        Find a topic anywhere in the tree and return the node.

        Args:
            root: Root node of the tree
            topic_name: Topic name to search for (case-insensitive)

        Returns:
            The found node or None
        """
        node, _ = self._find_topic_in_tree(root, topic_name)
        return node

    async def remove_topic_from_knowledge(
        self,
        current_tree: DomainKnowledgeTree | None,
        topics_to_remove: list[str],
        agent_name: str,
        agent_description: str,
    ) -> DomainKnowledgeUpdateResponse:
        """Remove topics from the knowledge tree."""
        try:
            print("🗑️ Smart remove knowledge starting...")
            print(f"  - Topics to remove: {topics_to_remove}")
            print(f"  - Current tree exists: {current_tree is not None}")

            if not current_tree:
                return DomainKnowledgeUpdateResponse(success=False, error="No knowledge tree exists to remove topics from")

            if not topics_to_remove:
                return DomainKnowledgeUpdateResponse(success=False, error="No topics specified for removal")

            # Create changes for each topic to remove
            changes_to_apply = []
            topics_found = []
            topics_not_found = []

            for topic in topics_to_remove:
                # Check if topic exists in the tree
                existing_node = self._find_topic_in_tree_simple(current_tree.root, topic)
                if existing_node:
                    # Check if node has children - default to removing children with parent
                    # This prevents orphaned "not generated" children
                    has_children = existing_node.children and len(existing_node.children) > 0
                    changes_to_apply.append(
                        {
                            "action": "remove_node",
                            "topic_to_remove": topic,
                            "preserve_children": False,  # Remove children with parent to avoid orphaned nodes
                        }
                    )
                    topics_found.append(topic)
                    if has_children:
                        print(f"  ⚠️ Removing '{topic}' along with {len(existing_node.children)} children to avoid orphaned nodes")
                else:
                    topics_not_found.append(topic)

            if not topics_found:
                return DomainKnowledgeUpdateResponse(
                    success=False, error=f"None of the specified topics found in tree: {', '.join(topics_not_found)}"
                )

            # Apply the removal changes using existing infrastructure
            analysis = {
                "success": True,
                "changes_to_apply": changes_to_apply,
                "changes_summary": f"Removed {', '.join(topics_found)} from knowledge tree",
            }

            updated_tree = await self._apply_tree_changes(
                current_tree,
                analysis,
                topics_found[0],  # Use first topic as reference
            )

            changes_summary = f"Removed {', '.join(topics_found)}"
            if topics_not_found:
                changes_summary += f" (Could not find: {', '.join(topics_not_found)})"

            return DomainKnowledgeUpdateResponse(success=True, updated_tree=updated_tree, changes_summary=changes_summary)

        except Exception as e:
            print(f"❌ Exception in remove_topic_from_knowledge: {e}")
            return DomainKnowledgeUpdateResponse(success=False, error=f"Error removing topics: {str(e)}")


def get_llm_tree_manager() -> LLMTreeManager:
    """Dependency injection for LLM tree manager."""
    return LLMTreeManager()
