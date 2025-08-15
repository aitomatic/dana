"""
Task-Specific Domain Coverage Agent

This agent creates comprehensive coverage of all aspects needed for a specific role
to perform specific tasks in a domain. Unlike general domain coverage, this focuses
on the practical requirements and knowledge areas needed for task execution.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import logging
from typing import Any

from dana.core.lang.sandbox_context import SandboxContext
from dana.libs.corelib.py_wrappers.py_reason import py_reason as reason_function
from .domains.default_domain import DefaultDomain
from datetime import UTC

logger = logging.getLogger(__name__)


def reason(prompt: str, target_type: type | None = None) -> str:
    """Wrapper for Dana's reason function"""
    context = SandboxContext()
    context.set("system:__current_assignment_type", target_type)
    return reason_function(context, prompt)


class TaskSpecificDomainCoverageAgent:
    """
    Agent that builds hierarchical task-focused domain coverage in a tree structure:
    domain → subdomain → topic

    For example, in financial statement analysis:
    Financial Statement Analysis → Trend Analysis → Revenue Growth Patterns
                                → Cash Flow Analysis → Operating Cash Flow Trends
                                → Ratio Analysis → Profitability Ratios

    This agent creates comprehensive coverage by:
    1. Identifying subdomains that emerge from the specific tasks
    2. Breaking down each subdomain into specific topics
    3. Using role and domain context to ensure relevance and completeness
    4. Building a hierarchical tree structure for organized knowledge coverage
    """

    def __init__(self, domain: str, role: str, tasks: list[str], domain_cls: DefaultDomain):
        """
        Initialize the domain coverage agent.

        Args:
            domain: The domain name
            role: The role name
            tasks: List of specific tasks the role must perform
            domain_cls: The domain class
        """
        self.domain = domain
        self.role = role
        self.tasks = tasks
        self.domain_cls = domain_cls
        self.domain_obj = domain_cls(domain=domain, role=role, tasks=tasks)

        logger.info(f"Initialized TaskSpecificDomainCoverageAgent for {self.role} in {self.domain}")

    def identify_task_subdomains(self) -> dict[str, Any]:
        """
        Identify the subdomains that emerge from analyzing the specific tasks.

        Returns:
            Dictionary with subdomains derived from task analysis
        """

        task_descriptions = "\n".join([f"- {task}" for task in self.tasks])

        prompt = f"""You are identifying subdomains for task-specific coverage in {self.domain}.

**OBJECTIVE**: Based on the specific tasks this {self.role} performs, identify the key subdomains that naturally emerge. These subdomains should represent major knowledge/skill areas needed for the tasks.

**DOMAIN**: {self.domain}
**ROLE**: {self.role} (provides context for depth and specialization)

**TASKS TO ANALYZE**:
{task_descriptions}

**SUBDOMAIN IDENTIFICATION FRAMEWORK**:
- Look at the tasks and identify the major knowledge/skill areas they require
- Group related activities and knowledge areas into coherent subdomains
- Each subdomain should represent a significant area of expertise within the domain
- Subdomains should be specific enough to be actionable but broad enough to be meaningful

**EXAMPLES OF GOOD SUBDOMAINS** (for context, not to copy):
- Financial Statement Analysis → "Trend Analysis", "Ratio Analysis", "Cash Flow Analysis"
- Software Development → "Code Architecture", "Testing Strategy", "Performance Optimization"
- Marketing → "Market Research", "Campaign Strategy", "Performance Analytics"

**INSTRUCTIONS**:
- Derive subdomains directly from what the tasks require
- Use role and domain context to make subdomains appropriately specialized
- Aim for 4-8 subdomains that comprehensively cover the task requirements
- Each subdomain should be clearly distinct from others

**OUTPUT FORMAT** (valid JSON):
{{
    "subdomains": {{
        "subdomain_1_name": {{
            "description": "Clear description of what this subdomain covers",
            "relevance_to_tasks": "How this subdomain relates to the specific tasks",
            "key_focus_areas": ["focus area 1", "focus area 2", "focus area 3"]
        }},
        "subdomain_2_name": {{
            "description": "Clear description of what this subdomain covers", 
            "relevance_to_tasks": "How this subdomain relates to the specific tasks",
            "key_focus_areas": ["focus area 1", "focus area 2", "focus area 3"]
        }}
    }}
}}"""

        logger.debug("Identifying task-derived subdomains")
        return reason(prompt, target_type=dict)

    def generate_subdomain_topics(self, subdomains: dict[str, Any]) -> dict[str, Any]:
        """
        Generate specific topics for each subdomain based on task requirements.

        Args:
            subdomains: Dictionary of identified subdomains

        Returns:
            Dictionary with topics organized by subdomain
        """

        if not isinstance(subdomains, dict) or "subdomains" not in subdomains:
            logger.error("Invalid subdomains structure provided")
            return {}

        task_descriptions = "\n".join([f"- {task}" for task in self.tasks])
        subdomain_info = ""

        for subdomain_name, subdomain_data in subdomains["subdomains"].items():
            subdomain_info += f"\n**{subdomain_name}**:\n"
            subdomain_info += f"  Description: {subdomain_data.get('description', '')}\n"
            subdomain_info += f"  Key Focus Areas: {', '.join(subdomain_data.get('key_focus_areas', []))}\n"

        prompt = f"""You are generating specific topics for each subdomain in {self.domain}.

**OBJECTIVE**: For each subdomain, generate 3-6 specific topics that a {self.role} needs to master to excel at the given tasks.

**DOMAIN**: {self.domain}
**ROLE**: {self.role}

**TASKS CONTEXT**:
{task_descriptions}

**SUBDOMAINS TO DEVELOP**:
{subdomain_info}

**TOPIC GENERATION FRAMEWORK**:
- Each topic should be specific and actionable
- Topics should directly support the role's ability to perform the tasks
- Topics should build on the subdomain's key focus areas
- Think about what someone would need to learn/master in each subdomain
- Topics should be at the right level of granularity (not too broad, not too narrow)

**EXAMPLES OF GOOD TOPICS** (for context):
- Subdomain "Trend Analysis" → Topics: "Revenue Growth Patterns", "Seasonal Variations", "Multi-Year Trend Identification"
- Subdomain "Cash Flow Analysis" → Topics: "Operating Cash Flow Trends", "Free Cash Flow Calculation", "Cash Conversion Cycles"

**INSTRUCTIONS**:
- Generate 3-6 topics per subdomain
- Make topics specific to this role and domain combination
- Ensure topics collectively cover the subdomain comprehensively
- Topics should be learnable/masterable knowledge areas

**OUTPUT FORMAT** (valid JSON):
{{
    "subdomain_1_name": {{
        "topics": [
            "specific topic 1",
            "specific topic 2", 
            "specific topic 3"
        ]
    }},
    "subdomain_2_name": {{
        "topics": [
            "specific topic 1",
            "specific topic 2",
            "specific topic 3"
        ]
    }}
}}"""

        logger.debug("Generating topics for each subdomain")
        return reason(prompt, target_type=dict)

    def validate_and_refine_coverage_tree(self, subdomains: dict[str, Any], topics_by_subdomain: dict[str, Any]) -> dict[str, Any]:
        """
        Validate the coverage tree and identify any gaps or refinements needed.

        Args:
            subdomains: Dictionary of identified subdomains
            topics_by_subdomain: Dictionary of topics organized by subdomain

        Returns:
            Dictionary with validation results and refinement suggestions
        """

        task_descriptions = "\n".join([f"- {task}" for task in self.tasks])

        # Build current tree structure for validation
        tree_structure = f"**CURRENT COVERAGE TREE**:\n{self.domain}\n"

        if isinstance(subdomains, dict) and "subdomains" in subdomains:
            for subdomain_name in subdomains["subdomains"].keys():
                tree_structure += f"├── {subdomain_name}\n"
                if isinstance(topics_by_subdomain, dict) and subdomain_name in topics_by_subdomain:
                    topics = topics_by_subdomain[subdomain_name].get("topics", [])
                    for topic in topics:
                        tree_structure += f"│   ├── {topic}\n"

        prompt = f"""You are validating the coverage tree for a {self.role} in {self.domain}.

**OBJECTIVE**: Evaluate whether the current domain → subdomain → topic tree provides comprehensive coverage for the specific tasks, and identify any gaps or improvements.

**ROLE**: {self.role}
**DOMAIN**: {self.domain}

**TASKS TO COVER**:
{task_descriptions}

{tree_structure}

**VALIDATION FRAMEWORK**:

1. **Coverage Completeness**: Are all aspects of the tasks adequately covered?
2. **Structure Balance**: Are subdomains and topics well-balanced and appropriately sized?
3. **Task Alignment**: Does each branch of the tree clearly support the specific tasks?
4. **Knowledge Gaps**: Are there important knowledge areas missing from the tree?
5. **Redundancy Check**: Are there overlaps or redundancies that should be addressed?
6. **Practical Usability**: Is the tree structure practical for knowledge organization?

**INSTRUCTIONS**:
- Evaluate the tree against the specific task requirements
- Identify specific gaps, overlaps, or structural issues
- Suggest concrete improvements while maintaining the tree structure
- Focus on making the tree more effective for this role performing these tasks

**OUTPUT FORMAT** (valid JSON):
{{
    "validation_summary": {{
        "coverage_completeness": "assessment of how well tasks are covered",
        "structure_balance": "assessment of tree balance and organization",
        "overall_quality": "HIGH | MEDIUM | LOW"
    }},
    "identified_gaps": [
        "specific gap 1 (missing knowledge area)",
        "specific gap 2 (uncovered task aspect)"
    ],
    "structural_improvements": [
        "improvement suggestion 1",
        "improvement suggestion 2"
    ],
    "refinement_recommendations": [
        "specific recommendation for better task alignment",
        "specific recommendation for better coverage"
    ]
}}"""

        logger.debug("Validating and refining coverage tree")
        return reason(prompt, target_type=dict)

    def build_comprehensive_task_coverage(self) -> dict[str, Any]:
        """
        Build comprehensive hierarchical coverage tree: domain → subdomain → topic.

        Returns:
            Complete hierarchical tree structure focused on tasks
        """

        logger.info(f"Building hierarchical task coverage tree for {self.role} in {self.domain}")

        # Step 1: Identify subdomains from tasks
        logger.debug("Step 1: Identifying task-derived subdomains")
        subdomains_result = self.identify_task_subdomains()

        # Step 2: Generate topics for each subdomain
        logger.debug("Step 2: Generating topics for each subdomain")
        topics_by_subdomain = self.generate_subdomain_topics(subdomains_result)

        # Step 3: Validate and refine the tree
        logger.debug("Step 3: Validating and refining coverage tree")
        validation_result = self.validate_and_refine_coverage_tree(subdomains_result, topics_by_subdomain)

        # Step 4: Build the final hierarchical tree structure in the required format
        def build_tree_node(topic_name: str, children_data: list = None, **metadata) -> dict:
            """Build a tree node with topic and children, plus metadata"""
            node = {"topic": topic_name, "children": []}
            # Add metadata fields
            for key, value in metadata.items():
                if value:  # Only add non-empty metadata
                    node[key] = value

            # Add children if provided
            if children_data:
                for child in children_data:
                    if isinstance(child, dict):
                        node["children"].append(child)
                    elif isinstance(child, str):
                        node["children"].append({"topic": child, "children": []})

            return node

        # Build children (subdomains and their topics)
        domain_children = []

        if isinstance(subdomains_result, dict) and "subdomains" in subdomains_result:
            for subdomain_name, subdomain_data in subdomains_result["subdomains"].items():
                # Get topics for this subdomain
                subdomain_topics = topics_by_subdomain.get(subdomain_name, {}).get("topics", [])

                # Build topic nodes
                topic_nodes = []
                for topic in subdomain_topics:
                    topic_nodes.append(build_tree_node(topic))

                # Build subdomain node with metadata
                subdomain_node = build_tree_node(
                    subdomain_name,
                    topic_nodes,
                    description=subdomain_data.get("description", ""),
                    relevance_to_tasks=subdomain_data.get("relevance_to_tasks", ""),
                    key_focus_areas=subdomain_data.get("key_focus_areas", []),
                )

                domain_children.append(subdomain_node)

        # Build root node
        domain_tree = {
            "root": build_tree_node(
                self.domain,
                domain_children,
                role_context=self.role,
                task_count=len(self.tasks),
                tasks=self.tasks,
                analysis_type="task_focused_hierarchical_coverage",
            )
        }

        # Step 5: Compile comprehensive coverage structure with additional metadata
        from datetime import datetime

        coverage_structure = {
            **domain_tree,  # Include the tree structure at root level
            "tree_analysis": {
                "subdomain_identification": subdomains_result,
                "topic_generation": topics_by_subdomain,
                "validation_results": validation_result,
            },
            "coverage_summary": {
                "total_tasks_analyzed": len(self.tasks),
                "total_subdomains": len(domain_children),
                "total_topics": sum(len(subdomain.get("children", [])) for subdomain in domain_children),
                "validation_quality": validation_result.get("validation_summary", {}).get("overall_quality", "UNKNOWN"),
                "structure_type": "hierarchical_tree",
            },
            "metadata": {
                "domain": self.domain,
                "role": self.role,
                "tasks": self.tasks,
                "coverage_version": "1.0",
                "domain_class": self.domain_obj.__class__.__name__,
                "analysis_type": "hierarchical_task_focused_tree",
                "tree_structure": "domain_subdomain_topic",
                "primary_focus": "tasks_with_role_domain_context",
            },
            "last_updated": datetime.now(UTC).isoformat(),
            "version": 1,
        }

        logger.info("Completed hierarchical task coverage tree")
        logger.info(
            f"- Tree structure: {self.domain} → {coverage_structure['coverage_summary']['total_subdomains']} subdomains → {coverage_structure['coverage_summary']['total_topics']} topics"
        )
        logger.info(f"- Validation quality: {coverage_structure['coverage_summary']['validation_quality']}")
        logger.info(f"- Based on {len(self.tasks)} specific tasks for {self.role}")

        return coverage_structure


if __name__ == "__main__":
    from .domains.financial_stmt_analysis import FinancialStmtAnalysisDomain

    # Test the domain coverage agent
    agent = TaskSpecificDomainCoverageAgent(
        domain="Financial Statement Analysis",
        role="Senior Financial Statement Analyst",
        tasks=[
            "Analyze Financial Statements",
            "Provide Financial Insights",
            "Answer Financial Questions",
            "Forecast Financial Performance",
        ],
        domain_cls=FinancialStmtAnalysisDomain,
    )

    # Build comprehensive coverage
    coverage = agent.build_comprehensive_task_coverage()

    print("\n🎯 Hierarchical Task Coverage Tree Complete!")
    print(f"📊 Role Context: {coverage['metadata']['role']}")
    print(f"🏢 Domain: {coverage['metadata']['domain']}")
    print(f"📋 Tasks analyzed: {len(coverage['metadata']['tasks'])}")
    print(
        f"🌳 Tree structure: {coverage['coverage_summary']['total_subdomains']} subdomains → {coverage['coverage_summary']['total_topics']} topics"
    )
    print(f"✅ Validation quality: {coverage['coverage_summary']['validation_quality']}")
    print(f"🕒 Last updated: {coverage['last_updated']}")
    print(f"📝 Version: {coverage['version']}")

    # Show the hierarchical tree structure in JSON format
    print("\n🌳 JSON TREE STRUCTURE (like domain_knowledge.json):")

    def print_tree_node(node, depth=0):
        """Recursively print tree structure"""
        indent = "  " * depth
        topic = node.get("topic", "Unknown")
        children = node.get("children", [])

        print(f"{indent}📂 {topic}")

        # Show metadata for subdomains (depth 1)
        if depth == 1:
            if "description" in node:
                print(f"{indent}   📝 {node['description'][:60]}...")

        # Print children
        for child in children:
            print_tree_node(child, depth + 1)

    root = coverage.get("root", {})
    if root:
        print_tree_node(root)

    # Show JSON structure sample
    print("\n📄 JSON FORMAT PREVIEW:")
    import json

    # Create a simplified version for preview
    root_sample = coverage.get("root", {})
    if root_sample and root_sample.get("children"):
        # Show first subdomain with its topics
        first_subdomain = root_sample["children"][0] if root_sample["children"] else {}

        sample_structure = {
            "root": {
                "topic": root_sample.get("topic", ""),
                "role_context": root_sample.get("role_context", ""),
                "task_count": root_sample.get("task_count", 0),
                "children": [
                    {
                        "topic": first_subdomain.get("topic", ""),
                        "description": first_subdomain.get("description", ""),
                        "children": first_subdomain.get("children", [])[:3],  # Show first 3 topics
                    }
                ]
                if first_subdomain
                else [],
            },
            "last_updated": coverage.get("last_updated"),
            "version": coverage.get("version"),
        }

        print(json.dumps(sample_structure, indent=2)[:500] + "...")

    # Show validation results
    validation = coverage.get("tree_analysis", {}).get("validation_results", {})
    if validation:
        print("\n🔍 Validation Summary:")
        validation_summary = validation.get("validation_summary", {})
        print(f"  Coverage: {validation_summary.get('coverage_completeness', 'N/A')[:60]}...")
        print(f"  Structure: {validation_summary.get('structure_balance', 'N/A')[:60]}...")

        gaps = validation.get("identified_gaps", [])
        if gaps:
            print(f"  🚨 Identified gaps: {len(gaps)} gap(s)")
            for gap in gaps[:2]:
                print(f"    - {gap[:70]}...")

    print("\n📊 Coverage Statistics:")
    print(f"  • Domain focus: Task-specific coverage for {coverage['metadata']['role']}")
    print(f"  • Subdomains derived from: {len(coverage['metadata']['tasks'])} specific tasks")
    print(f"  • Total knowledge areas: {coverage['coverage_summary']['total_topics']} topics")
    print(f"  • Structure type: {coverage['metadata']['tree_structure']}")
    print("  • JSON compatible: ✅ Same format as domain_knowledge.json")
