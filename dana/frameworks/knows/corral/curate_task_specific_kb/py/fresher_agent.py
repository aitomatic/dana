"""
Fresher Agent for Task-Specific Knowledge Generation

This agent generates targeted questions to comprehensively cover a specific domain,
role, and tasks. It adapts the pattern from curate_general_kb but focuses on
task-specific knowledge generation rather than general domain coverage.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import logging
from typing import Any

from dana.core.lang.sandbox_context import SandboxContext
from dana.libs.corelib.py_wrappers.py_reason import py_reason as reason_function
from .domains.default_domain import DefaultDomain

logger = logging.getLogger(__name__)


def reason(prompt: str, target_type: type | None = None) -> str:
    """Wrapper for Dana's reason function"""
    context = SandboxContext()
    context.set("system:__current_assignment_type", target_type)
    return reason_function(context, prompt)


class TaskSpecificFresherAgent:
    """
    Fresher agent that generates questions to comprehensively cover role, domain, and tasks.

    Unlike the general knowledge fresher, this agent focuses on generating questions
    that specifically address the capabilities needed for a defined role and tasks
    within a specific domain.
    """

    def __init__(
        self,
        domain: str,
        role: str,
        tasks: list[str],
        domain_cls: DefaultDomain,
        confidence_threshold: float = 85.0,
        max_iterations: int = 10,
    ):
        """
        Initialize the fresher agent for task-specific question generation.

        Args:
            domain: The domain name
            role: The role name
            tasks: List of tasks
            domain_cls: The domain class
            confidence_threshold: Minimum confidence threshold for completion
            max_iterations: Maximum iterations for refinement
        """
        self.domain = domain
        self.role = role
        self.tasks = tasks
        self.domain_cls = domain_cls
        self.confidence_threshold = confidence_threshold
        self.max_iterations = max_iterations
        self.domain_obj = domain_cls(domain=domain, role=role, tasks=tasks)

        logger.info(f"Initialized TaskSpecificFresherAgent for {self.role} in {self.domain}")

    def generate_tree_path_questions(self, tree_structure: dict[str, Any]) -> dict[str, list[str]]:
        """
        Generate "How to..." questions for each path from root to leaf in the tree structure.
        These questions will be used to generate plan, fact, and heuristic knowledge.

        Args:
            tree_structure: The hierarchical tree structure from domain coverage agent

        Returns:
            Dictionary with path-specific "How to..." questions
        """

        # Extract all paths from root to leaf
        def extract_paths(node, current_path=None):
            """Recursively extract all paths from root to leaf"""
            if current_path is None:
                current_path = []
            topic = node.get("topic", "")
            new_path = current_path + [topic]
            children = node.get("children", [])

            if not children:  # Leaf node
                return [new_path]

            all_paths = []
            for child in children:
                all_paths.extend(extract_paths(child, new_path))
            return all_paths

        # Get all paths
        root = tree_structure.get("root", {})
        if not root:
            logger.error("No root node found in tree structure")
            return {}

        all_paths = extract_paths(root)

        # Build paths description for the prompt
        paths_description = ""
        for i, path in enumerate(all_paths, 1):
            path_str = " → ".join(path)
            paths_description += f"{i}. {path_str}\n"

        task_descriptions = "\n".join([f"- {task}" for task in self.tasks])

        # Use domain-specific prompt if available, otherwise use generic prompt
        prompt = self.domain_obj.get_fresher_question_prompt(paths_description, task_descriptions)

        logger.debug(f"Generating 'How to...' questions for {len(all_paths)} tree paths")
        return reason(prompt, target_type=dict)

    def assess_question_coverage(self, questions: dict[str, list[str]]) -> dict:
        """
        Assess how well the current questions cover the role's needs

        Args:
            questions: Dictionary of questions by category

        Returns:
            Assessment with confidence scores and gaps
        """

        # Build current questions summary for assessment
        questions_summary = ""
        for category, question_list in questions.items():
            questions_summary += f"\n**{category.upper()}**:\n"
            for i, q in enumerate(question_list, 1):
                questions_summary += f"{i}. {q}\n"

        task_descriptions = "\n".join([f"- {task}" for task in self.tasks])

        prompt = f"""You are evaluating question coverage for a {self.role} role assessment.

**ROLE TO ASSESS**: {self.role}
**DOMAIN**: {self.domain}
**KEY TASKS THEY MUST PERFORM**:
{task_descriptions}

**CURRENT QUESTIONS**:
{questions_summary}

**EVALUATION CRITERIA**:
Rate each category 0-100 based on how well the questions would test the knowledge needed for this specific role and tasks:

1. **domain_fundamentals**: Do questions cover essential domain knowledge?
2. **role_expertise**: Do questions test role-specific specialized skills?  
3. **task_execution**: Do questions cover practical knowledge for the key tasks?
4. **tools_and_methods**: Do questions address tools/methods used in this role?
5. **decision_making**: Do questions test judgment needed for this role?
6. **problem_solving**: Do questions assess problem-solving in this domain?

**ASSESSMENT INSTRUCTIONS**:
- Overall confidence = average of all category scores
- Status: "Ready to proceed" if ≥85, else "More questions needed"
- For gaps: list categories scoring <85 with specific improvement suggestions

**OUTPUT FORMAT** (valid JSON):
{{
    "category_scores": {{
        "domain_fundamentals": 0-100,
        "role_expertise": 0-100,
        "task_execution": 0-100, 
        "tools_and_methods": 0-100,
        "decision_making": 0-100,
        "problem_solving": 0-100
    }},
    "overall_confidence": 0-100,
    "status": "Ready to proceed | More questions needed",
    "gaps": [
        {{"category": "category_name", "score": score, "improvement": "specific suggestion"}}
    ]
}}"""

        logger.debug("Assessing question coverage")
        return reason(prompt, target_type=dict)

    def improve_questions_for_gaps(self, questions: dict[str, list[str]], gaps: list[dict]) -> dict[str, list[str]]:
        """
        Generate additional questions to address identified gaps

        Args:
            questions: Current questions by category
            gaps: List of gaps from assessment

        Returns:
            Dictionary of additional questions for gap categories
        """

        if not gaps:
            return {}

        # Focus on categories that need improvement
        gap_categories = [gap["category"] for gap in gaps]
        gap_details = {gap["category"]: gap["improvement"] for gap in gaps}

        current_questions_for_gaps = {cat: questions.get(cat, []) for cat in gap_categories}

        task_descriptions = "\n".join([f"- {task}" for task in self.tasks])

        prompt = f"""You are improving questions for a {self.role} assessment in {self.domain}.

**ROLE**: {self.role}  
**DOMAIN**: {self.domain}
**KEY TASKS**:
{task_descriptions}

**CATEGORIES NEEDING IMPROVEMENT**: {gap_categories}

**CURRENT QUESTIONS IN THESE CATEGORIES**:
{current_questions_for_gaps}

**SPECIFIC IMPROVEMENTS NEEDED**:
{gap_details}

**OBJECTIVE**: Generate 1-2 additional targeted questions for each gap category that address the specific improvements mentioned.

**QUALITY REQUIREMENTS**:
- Questions should directly address the improvement suggestions
- Focus on knowledge essential for this specific role and tasks
- Make questions practical and answerable by competent practitioners
- Avoid duplicating existing questions

**OUTPUT FORMAT** (valid JSON):
{{
    "category_name_1": ["new question 1", "new question 2"],
    "category_name_2": ["new question 1"]
}}"""

        logger.debug(f"Generating improved questions for {len(gaps)} gap categories")
        return reason(prompt, target_type=dict)

    def generate_comprehensive_questions_from_tree(self, tree_structure: dict[str, Any]) -> dict:
        """
        Main method to generate comprehensive questions based on tree structure paths.

        Args:
            tree_structure: The hierarchical tree structure from domain coverage agent

        Returns:
            Dictionary with path-based questions and metrics
        """

        logger.info(f"Generating comprehensive questions from tree structure for {self.role} in {self.domain}")

        # Generate questions for each tree path
        path_questions = self.generate_tree_path_questions(tree_structure)

        # Organize questions by path and flatten for easy use
        all_questions = []
        questions_by_path = {}

        for path_key, path_data in path_questions.items():
            path = path_data.get("path", [])
            questions = path_data.get("questions", [])

            # Store by path
            questions_by_path[path_key] = {"path": path, "path_string": " → ".join(path), "questions": questions}

            # Add to all questions
            all_questions.extend(questions)

        # Count paths and topics
        root = tree_structure.get("root", {})

        def count_leaves(node):
            children = node.get("children", [])
            if not children:
                return 1
            return sum(count_leaves(child) for child in children)

        total_paths = count_leaves(root)

        result = {
            "domain": self.domain,
            "role": self.role,
            "tasks": self.tasks,
            "tree_structure": tree_structure,
            "questions_by_path": questions_by_path,
            "all_questions": all_questions,
            "generation_metrics": {
                "total_tree_paths": total_paths,
                "paths_with_questions": len(questions_by_path),
                "questions_per_path_avg": len(all_questions) / max(len(questions_by_path), 1),
                "total_questions": len(all_questions),
            },
            "metadata": {
                "generation_method": "tree_path_based",
                "question_types": "diverse_real_world_scenarios",
                "suitable_for": ["plan_generation", "fact_extraction", "heuristic_development"],
            },
        }

        logger.info(f"Generated {len(all_questions)} questions across {len(questions_by_path)} tree paths")
        logger.info(f"Average {result['generation_metrics']['questions_per_path_avg']:.1f} questions per path")

        return result

    def generate_comprehensive_questions(self) -> dict:
        """
        Backward compatibility method - generates questions using original category-based approach.

        Returns:
            Dictionary with final questions and assessment metrics
        """

        logger.warning(
            "Using legacy category-based question generation. Consider using generate_comprehensive_questions_from_tree() for tree-based generation."
        )

        # This would be the original implementation
        # For now, return a simple structure
        return {
            "domain": self.domain,
            "role": self.role,
            "tasks": self.tasks,
            "questions_by_category": {},
            "all_questions": [],
            "final_confidence": 0,
            "category_scores": {},
            "iterations_used": 0,
            "total_questions": 0,
            "note": "Use generate_comprehensive_questions_from_tree() for tree-based question generation",
        }


if __name__ == "__main__":
    from .domains.financial_stmt_analysis import FinancialStmtAnalysisDomain

    # Test the fresher agent
    agent = TaskSpecificFresherAgent(
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

    result = agent.generate_comprehensive_questions()

    print(f"\nGenerated {result['total_questions']} questions with {result['final_confidence']}% confidence")
    print(f"Categories: {list(result['questions_by_category'].keys())}")

    # Show sample questions from each category
    for category, questions in result["questions_by_category"].items():
        print(f"\n{category.upper()}:")
        for i, q in enumerate(questions[:2], 1):  # Show first 2 questions
            print(f"  {i}. {q}")
        if len(questions) > 2:
            print(f"  ... and {len(questions) - 2} more")
