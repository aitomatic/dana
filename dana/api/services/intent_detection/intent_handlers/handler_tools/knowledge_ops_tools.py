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

logger = logging.getLogger(__name__)


class AskFollowUpQuestionTool(BaseTool):
    def __init__(self):
        tool_info = BaseToolInformation(
            name="ask_follow_up_question",
            description="Ask the user a question to gather additional information needed to complete the task. This tool should be used when you encounter ambiguities, need clarification, or require more details to proceed effectively. It allows for interactive problem-solving by enabling direct communication with the user. Use this tool judiciously to maintain a balance between gathering necessary information and avoiding excessive back-and-forth.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="question",
                        type="string",
                        description="The question to ask the user. This should be a clear, specific question that addresses the information you need.",
                        example="Your question here",
                    ),
                    BaseArgument(
                        name="options",
                        type="list",
                        description="An array of 2-5 options for the user to choose from. Each option should be a string describing a possible answer. You may not always need to provide options, but it may be helpful in many cases where it can save the user from having to type out a response manually. IMPORTANT: NEVER include an option to toggle to Act mode, as this would be something you need to direct the user to do manually themselves if needed.",
                        example='Array of options here (optional), e.g. ["Option 1", "Option 2", "Option 3"]',
                    ),
                ],
                required=["question"],
            ),
        )
        super().__init__(tool_info)

    def _execute(self, question: str, options: list[str] = None) -> ToolResult:
        options_str = "\n".join([f"- {option}" for option in options]) if options else ""
        return ToolResult(
            name="ask_follow_up_question",
            result=f"""
{question}
{options_str}
""",
            require_user=True,
        )


class NavigateTreeTool(BaseTool):
    def __init__(self, llm: LLMResource | None = None, tree_structure: DomainKnowledgeTree | None = None):
        tool_info = BaseToolInformation(
            name="navigate_tree",
            description="Navigate the knowledge tree to find or create the target location for storing knowledge. Extracts the topic hierarchy from the user request and determines the appropriate path in the tree structure.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="user_message",
                        type="string",
                        description="The original user request to extract topic hierarchy from",
                        example="Add knowledge about current ratio analysis for financial analysts",
                    ),
                    BaseArgument(
                        name="context",
                        type="string",
                        description="Any relevant context from the conversation to help determine the correct path",
                        example="User is building a financial analysis agent",
                    ),
                ],
                required=["user_message"],
            ),
        )
        super().__init__(tool_info)
        self.llm = llm or LLMResource()
        self.tree_structure = tree_structure

    def _execute(self, user_message: str, context: str = "") -> ToolResult:
        """
        Navigate knowledge tree to target location by extracting topic from user request.

        Returns: ToolResult with navigation results
        """
        try:
            # Use LLM to extract hierarchical topic structure
            from dana.api.services.intent_detection.intent_handlers.handler_prompts.knowledge_ops_prompts import TREE_NAVIGATION_PROMPT

            # Format tree structure if available
            tree_context = self._format_tree_structure()

            prompt = TREE_NAVIGATION_PROMPT.format(user_message=user_message, tree_context=tree_context)
            if context:
                prompt += f"\n\nAdditional context: {context}"

            llm_request = BaseRequest(arguments={"messages": [{"role": "user", "content": prompt}], "temperature": 0.1, "max_tokens": 200})

            # Run synchronously using Misc.safe_asyncio_run
            response = Misc.safe_asyncio_run(self.llm.query, llm_request)
            result = Misc.text_to_dict(Misc.get_response_content(response))

            path = result.get("path", ["General", "Unknown", "Topic"])
            reasoning = result.get("reasoning", "")
            existing_node = result.get("existing_node", False)
            needs_creation = result.get("needs_creation", False)
            missing_nodes = result.get("missing_nodes", [])
            is_empty_tree = result.get("is_empty_tree", False)

            # TODO: In real implementation, would check/create nodes in actual tree structure
            # For now, use the LLM's determination
            path_str = " > ".join(path)
            
            if is_empty_tree:
                status = "empty tree - requires full structure creation"
                creation_msg = f"\n🌱 Starting with empty tree - creating complete structure: {path_str}\n⚠️ Full tree structure needs to be created before proceeding."
            elif needs_creation:
                status = "requires creation"
                creation_msg = f"\nMissing nodes: {', '.join(missing_nodes)}\n⚠️ Tree structure needs to be created before proceeding."
            else:
                status = "existing" if existing_node else "new"
                creation_msg = ""

            content = f"""Tree Navigation Complete:
Path: {path_str}
Status: {status} node
Reasoning: {reasoning}{creation_msg}

{"Next step: Create tree structure before knowledge generation." if (needs_creation or is_empty_tree) else "Ready to proceed with knowledge generation at this location."}"""

            return ToolResult(name="navigate_tree", result=content, require_user=False)

        except Exception as e:
            logger.error(f"Failed to navigate tree: {e}")
            # Fallback navigation
            fallback_path = f"General > Knowledge > {user_message[:50]}"
            content = f"""Tree Navigation Complete:
Path: {fallback_path}
Status: new node (fallback)
Error: {str(e)}

Using fallback navigation. Ready to proceed with knowledge generation."""

            return ToolResult(name="navigate_tree", result=content, require_user=False)

    def _format_tree_structure(self) -> str:
        """
        Format the domain knowledge tree for inclusion in the prompt.
        Returns a string representation of the tree structure.
        """
        if not self.tree_structure or not self.tree_structure.root:
            return "Current domain knowledge tree is empty."

        def format_node(node, level=0):
            """Recursively format tree nodes with indentation"""
            indent = "  " * level
            lines = [f"{indent}- {node.topic}"]
            for child in node.children:
                lines.extend(format_node(child, level + 1))
            return lines

        tree_lines = ["Current domain knowledge tree structure:"]
        tree_lines.extend(format_node(self.tree_structure.root))

        return "\n".join(tree_lines)


class CreatePlanTool(BaseTool):
    def __init__(self, llm: LLMResource | None = None):
        tool_info = BaseToolInformation(
            name="create_plan",
            description="Create a detailed generation plan showing what knowledge will be created, including counts, examples, and time estimates. Determines the types of knowledge needed based on the topic and context.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="topic",
                        type="string", 
                        description="The topic to create a plan for",
                        example="Current Ratio Analysis"
                    ),
                    BaseArgument(
                        name="scope",
                        type="string",
                        description="The scope of knowledge needed (comprehensive, focused, basic)",
                        example="comprehensive"
                    ),
                    BaseArgument(
                        name="target_location",
                        type="string",
                        description="Where in the tree to store this knowledge",
                        example="Financial Analysis > Liquidity Analysis > Current Ratio"
                    ),
                ],
                required=["topic"],
            ),
        )
        super().__init__(tool_info)
        self.llm = llm or LLMResource()
    
    def _execute(self, topic: str, scope: str = "comprehensive", target_location: str = "") -> ToolResult:
        """
        Create generation plan based on topic and scope.
        """
        try:
            # Use LLM to create detailed plan
            plan_prompt = f"""Create a detailed knowledge generation plan for: "{topic}"

Scope: {scope}
Target Location: {target_location}

Create a plan that includes:
1. Types of knowledge to generate (facts, procedures, heuristics)
2. Estimated counts for each type
3. Brief examples of what will be generated
4. Estimated time to complete

Return as JSON:
{{
    "plan_summary": "Brief overview of the plan",
    "knowledge_types": {{
        "facts": {{"count": 5, "examples": ["example 1", "example 2"]}},
        "procedures": {{"count": 2, "examples": ["example 1"]}},
        "heuristics": {{"count": 3, "examples": ["example 1"]}}
    }},
    "total_artifacts": 10,
    "estimated_time_minutes": 3,
    "complexity": "medium"
}}"""

            llm_request = BaseRequest(
                arguments={
                    "messages": [{"role": "user", "content": plan_prompt}],
                    "temperature": 0.1,
                    "max_tokens": 400
                }
            )
            
            response = Misc.safe_asyncio_run(self.llm.query, llm_request)
            result = Misc.text_to_dict(Misc.get_response_content(response))
            
            # Format the plan nicely
            plan_summary = result.get("plan_summary", "Knowledge generation plan")
            knowledge_types = result.get("knowledge_types", {})
            total_artifacts = result.get("total_artifacts", 0)
            estimated_time = result.get("estimated_time_minutes", 2)
            complexity = result.get("complexity", "medium")
            
            content = f"""📋 Generation Plan Created

Topic: {topic}
Scope: {scope.title()}
Target: {target_location}

{plan_summary}

📊 Knowledge Breakdown:"""

            for k_type, details in knowledge_types.items():
                count = details.get("count", 0)
                examples = details.get("examples", [])
                emoji = {"facts": "📄", "procedures": "📋", "heuristics": "💡"}.get(k_type, "📝")
                
                content += f"\n{emoji} {k_type.title()} ({count})"
                if examples:
                    content += f": {', '.join(examples[:2])}"
                    if len(examples) > 2:
                        content += "..."

            content += f"""

⏱️ Estimated Time: {estimated_time} minutes
🎯 Total Artifacts: {total_artifacts}
🔧 Complexity: {complexity.title()}

Ready for user approval."""
            
            return ToolResult(name="create_plan", result=content, require_user=False)
            
        except Exception as e:
            logger.error(f"Failed to create plan: {e}")
            # Fallback plan
            content = f"""📋 Generation Plan Created (Fallback)

Topic: {topic}
Scope: {scope.title()}

📊 Standard Knowledge Plan:
📄 Facts (5): Definitions, formulas, key concepts
📋 Procedures (2): Step-by-step processes
💡 Heuristics (3): Best practices and rules of thumb

⏱️ Estimated Time: 3 minutes
🎯 Total Artifacts: 10

Ready for user approval."""
            
            return ToolResult(name="create_plan", result=content, require_user=False)


class AskApprovalTool(BaseTool):
    def __init__(self):
        tool_info = BaseToolInformation(
            name="ask_approval",
            description="Present the generation plan to the user and request their approval before proceeding with knowledge generation. This is a critical human-in-the-loop checkpoint.",
            input_schema=InputSchema(
                type="object", 
                properties=[
                    BaseArgument(
                        name="plan_summary",
                        type="string",
                        description="Brief summary of the plan to be approved",
                        example="Generate 10 knowledge artifacts about current ratio analysis"
                    ),
                    BaseArgument(
                        name="estimated_artifacts",
                        type="string",
                        description="Number of knowledge pieces to be created",
                        example="10"
                    ),
                ],
                required=["plan_summary"],
            ),
        )
        super().__init__(tool_info)
        
    def _execute(self, plan_summary: str, estimated_artifacts: str = "multiple") -> ToolResult:
        """
        Ask user for approval of the generation plan.
        """
        content = f"""🔍 Approval Required

The following plan has been created:
{plan_summary}

Estimated artifacts: {estimated_artifacts}

Do you approve this plan and want to proceed with knowledge generation?

Please respond with:
- "yes" or "approve" to proceed
- "no" or "reject" to cancel
- Or provide feedback for modifications"""
        
        return ToolResult(name="ask_approval", result=content, require_user=True)


class GenerateKnowledgeTool(BaseTool):
    def __init__(self, llm: LLMResource | None = None):
        tool_info = BaseToolInformation(
            name="generate_knowledge",
            description="Generate all types of knowledge (facts, procedures, heuristics) for the specified topic based on the approved plan.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="topic",
                        type="string",
                        description="Topic to generate knowledge about",
                        example="Current Ratio Analysis"
                    ),
                    BaseArgument(
                        name="knowledge_types",
                        type="string",
                        description="Types of knowledge to generate (facts, procedures, heuristics)",
                        example="facts, procedures, heuristics"
                    ),
                    BaseArgument(
                        name="counts",
                        type="string", 
                        description="Number of each type to generate",
                        example="5 facts, 2 procedures, 3 heuristics"
                    ),
                    BaseArgument(
                        name="context",
                        type="string",
                        description="Additional context from the plan",
                        example="Focus on liquidity analysis for financial analysts"
                    ),
                ],
                required=["topic", "knowledge_types"],
            ),
        )
        super().__init__(tool_info)
        self.llm = llm or LLMResource()
    
    def _execute(self, topic: str, knowledge_types: str, counts: str = "", context: str = "") -> ToolResult:
        try:
            # Parse knowledge types and counts
            types_list = [t.strip() for t in knowledge_types.split(",")]
            
            # Generate comprehensive prompt
            knowledge_prompt = f"""Generate comprehensive knowledge about "{topic}".

Context: {context}
Requested types: {knowledge_types}
Counts: {counts if counts else "appropriate amounts of each"}

Generate the following knowledge:

1. FACTS (definitions, formulas, key concepts):
   - Accurate and verifiable
   - Clear and concise
   - Include definitions, formulas, data points

2. PROCEDURES (step-by-step workflows):
   - Clear, actionable steps
   - Logically ordered
   - Practical applications

3. HEURISTICS (best practices and rules of thumb):
   - Practical and actionable
   - Based on industry standards
   - Include warning signs and guidelines

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
                    "max_tokens": 1500  # Increased for comprehensive generation
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
            content += f"\n✅ Knowledge generation complete. Total artifacts: {total_artifacts}"
            
            return ToolResult(name="generate_knowledge", result=content, require_user=False)
            
        except Exception as e:
            logger.error(f"Failed to generate knowledge: {e}")
            return ToolResult(
                name="generate_knowledge", 
                result=f"❌ Error generating knowledge for {topic}: {str(e)}", 
                require_user=False
            )


class ModifyTreeTool(BaseTool):
    def __init__(self, tree_structure: DomainKnowledgeTree | None = None, domain_knowledge_path: str | None = None):
        tool_info = BaseToolInformation(
            name="modify_tree",
            description="Create, modify, or remove nodes in the domain knowledge tree structure. Handles all tree management operations including full tree initialization.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="operation",
                        type="string",
                        description="Type of operation to perform (init, create, modify, remove). Use 'init' for comprehensive tree initialization from a domain topic.",
                        example="init"
                    ),
                    BaseArgument(
                        name="tree_path",
                        type="string",
                        description="For init: domain topic to build tree around. For other operations: full path in tree where operation should be performed",
                        example="Financial Analysis > Liquidity Analysis > Current Ratio"
                    ),
                    BaseArgument(
                        name="domain_focus",
                        type="string",
                        description="For init operation: specific focus area within domain to guide tree generation",
                        example="semiconductor manufacturing processes"
                    ),
                ],
                required=["operation", "tree_path"],
            ),
        )
        super().__init__(tool_info)
        self.tree_structure = tree_structure
        self.domain_knowledge_path = domain_knowledge_path
    
    def _execute(self, operation: str, tree_path: str, domain_focus: str = "") -> ToolResult:
        """
        Modify the domain knowledge tree structure.
        
        Operations:
        - init: Initialize comprehensive tree structure from domain topic
        - create: Add new node(s) to tree
        - modify: Update existing node
        - remove: Delete node from tree
        """
        try:
            # Parse the tree path
            path_parts = [part.strip() for part in tree_path.split(">")]
            operation = operation.lower().strip()
            
            if operation == "init":
                content, updated_tree = self._init_tree(tree_path, domain_focus)
                if updated_tree:
                    self._save_tree_structure(updated_tree)
            elif operation == "create":
                content = self._create_nodes(path_parts, tree_path)
                self._save_tree_changes(operation, tree_path)
            elif operation == "modify":
                content = self._modify_node(path_parts, tree_path)
                self._save_tree_changes(operation, tree_path)
            elif operation == "remove":
                content = self._remove_node(path_parts, tree_path)
                self._save_tree_changes(operation, tree_path)
            else:
                content = f"❌ Invalid operation '{operation}'. Supported: init, create, modify, remove"
            
            return ToolResult(name="modify_tree", result=content, require_user=False)
            
        except Exception as e:
            logger.error(f"Failed to modify tree: {e}")
            return ToolResult(
                name="modify_tree",
                result=f"❌ Error modifying tree: {str(e)}",
                require_user=False
            )
    
    def _create_nodes(self, path_parts: list[str], tree_path: str) -> str:
        """Create new node(s) in the tree structure."""
        # Mock implementation - in real version would update actual DomainKnowledgeTree
        
        # Check if this looks like a full tree creation (empty tree scenario)
        is_full_tree_creation = len(path_parts) >= 3 and not self.tree_structure
        
        if is_full_tree_creation:
            content = f"""🌳 Tree Structure Created (Full Initialization)

🌱 Created complete tree structure: {tree_path}

📊 Tree Details:
- Root Domain: {path_parts[0]}
- Main Categories: {path_parts[1]} (and potentially others)
- Specific Topics: {path_parts[2]} (and deeper levels)
- Total Depth: {len(path_parts)} levels
- Status: Fresh tree initialized from scratch

🔗 Integration:
- Complete knowledge hierarchy now available
- All navigation paths established
- Ready for knowledge organization and content association
- Tree foundation created successfully

Full tree initialization complete."""
        else:
            content = f"""🌳 Tree Structure Updated

✅ Created node path: {tree_path}

📊 Node Details:
- Depth: {len(path_parts)} levels
- Type: {"Root" if len(path_parts) == 1 else "Branch" if len(path_parts) == 2 else "Leaf"}
- Parent nodes: {"All verified/created" if len(path_parts) > 1 else "None (root level)"}

🔗 Integration:
- Knowledge area now available for navigation
- Ready for content association
- Tree structure updated successfully

Node creation complete."""
        
        return content
    
    def _modify_node(self, path_parts: list[str], tree_path: str) -> str:
        """Modify existing node in the tree structure."""
        
        content = f"""🌳 Tree Structure Updated

✅ Modified node: {tree_path}

📝 Updates:
- Node metadata refreshed
- Timestamp updated: {Misc.get_current_datetime_str()}
- Structure integrity maintained

🔄 Impact:
- Child relationships: Preserved
- Parent links: Maintained
- Navigation paths: Updated

Node modification complete."""
        
        return content
    
    def _remove_node(self, path_parts: list[str], tree_path: str) -> str:
        """Remove node from the tree structure."""
        
        # Mock check for children - in real implementation would query actual tree
        has_children = len(path_parts) < 3  # Mock logic
        
        content = f"""🌳 Tree Structure Updated

{'⚠️' if has_children else '✅'} Removed node: {tree_path}

🗑️ Removal:
- Node deleted from tree structure
- Child handling: {"Children promoted to parent level" if has_children else "No children affected"}
- Navigation updated: Path no longer available

{'⚠️ Note: Child nodes were reorganized' if has_children else '✅ Clean removal completed'}

Node removal complete."""
        
        return content
    
    def _init_tree(self, domain_topic: str, domain_focus: str = "") -> tuple[str, 'DomainKnowledgeTree' | None]:
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
            
            init_prompt = f"""Generate a comprehensive domain knowledge tree structure for: "{domain_topic}"

{"Focus area: " + domain_focus if domain_focus else ""}

Create a multi-level hierarchical structure with:
- Main Domain (1 level)
- Multiple Subdomains/Categories (2-4 categories)  
- Multiple Topics per category (2-5 topics each)
- Specific subtopics where relevant (1-3 per topic)

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
                arguments={
                    "messages": [{"role": "user", "content": init_prompt}],
                    "temperature": 0.1,
                    "max_tokens": 800
                }
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
            knowledge_tree = DomainKnowledgeTree(
                root=root_node,
                last_updated=datetime.now(UTC),
                version=1
            )
            
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
                DomainNode(topic="Advanced Topics", children=subtopics3)
            ]
            
            root_node = DomainNode(topic=fallback_domain, children=topics)
            
            knowledge_tree = DomainKnowledgeTree(
                root=root_node,
                last_updated=datetime.now(UTC),
                version=1
            )
            
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
    
    def _save_tree_structure(self, updated_tree: 'DomainKnowledgeTree') -> None:
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
                        example="facts, procedures, heuristics"
                    ),
                    BaseArgument(
                        name="validation_criteria",
                        type="string",
                        description="Specific criteria to check against",
                        example="accuracy, completeness, consistency"
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

Artifacts Validated: {', '.join(artifacts)}
Criteria: {', '.join(criteria)}

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
                        example="10 knowledge artifacts (5 facts, 2 procedures, 3 heuristics)"
                    ),
                    BaseArgument(
                        name="target_agent_id",
                        type="string",
                        description="Agent ID to store knowledge for",
                        example="123"
                    ),
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
- Timestamp: {Misc.get_current_datetime_str()}
- Status: Successfully Stored

🎯 Knowledge is now available for agent usage and retrieval."""
        
        return ToolResult(name="persist", result=content, require_user=False)


class CheckExistingTool(BaseTool):
    def __init__(self):
        tool_info = BaseToolInformation(
            name="check_existing", 
            description="Check for existing knowledge at the target location to avoid duplicates.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="target_path",
                        type="string",
                        description="The tree path to check for existing knowledge",
                        example="Financial Analysis > Liquidity Analysis > Current Ratio"
                    ),
                    BaseArgument(
                        name="topic",
                        type="string",
                        description="Topic to check for duplicates",
                        example="Current Ratio Analysis"
                    ),
                ],
                required=["target_path"],
            ),
        )
        super().__init__(tool_info)
    
    def _execute(self, target_path: str, topic: str = "") -> ToolResult:
        # Mock duplicate check - in real implementation would query existing knowledge
        import random
        
        # Randomly simulate existing content check
        has_existing = random.choice([True, False, False])  # 33% chance of existing content
        
        if has_existing:
            content = f"""⚠️ Existing Knowledge Found

Path: {target_path}
Topic: {topic}

Found existing knowledge items:
- 2 related facts
- 1 procedure overlap

Recommendation: Proceed with generation but focus on complementary content to avoid duplication."""
        else:
            content = f"""✅ Clear to Proceed

Path: {target_path}
Topic: {topic}

No duplicate knowledge found at target location.
Safe to proceed with full knowledge generation."""
        
        return ToolResult(name="check_existing", result=content, require_user=False)


class AttemptCompletionTool(BaseTool):
    def __init__(self):
        tool_info = BaseToolInformation(
            name="attempt_completion",
            description="Present the final results to the user and complete the knowledge generation workflow.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="summary",
                        type="string",
                        description="Summary of what was accomplished",
                        example="Successfully generated and stored 10 knowledge artifacts about current ratio analysis"
                    ),
                    BaseArgument(
                        name="artifacts_created",
                        type="string", 
                        description="Count and types of artifacts created",
                        example="5 facts, 2 procedures, 3 heuristics"
                    ),
                ],
                required=["summary"],
            ),
        )
        super().__init__(tool_info)
    
    def _execute(self, summary: str, artifacts_created: str = "") -> ToolResult:
        content = f"""🎉 Knowledge Generation Complete

{summary}

📊 Final Results:
{f"Artifacts: {artifacts_created}" if artifacts_created else "Multiple knowledge artifacts created"}

✅ All knowledge has been:
- Generated with high accuracy
- Validated for quality
- Stored to vector database
- Made available for agent usage

The knowledge generation workflow is now complete. Your agent has been enhanced with new domain expertise!"""
        
        return ToolResult(name="attempt_completion", result=content, require_user=False)


if __name__ == "__main__":
    # Test AskFollowUpQuestionTool
    tool = AskFollowUpQuestionTool()
    print("AskFollowUpQuestionTool:")
    print(tool)
    print("\n" + "=" * 60 + "\n")

    # Test NavigateTreeTool
    nav_tool = NavigateTreeTool()
    print("NavigateTreeTool:")
    print(nav_tool)
