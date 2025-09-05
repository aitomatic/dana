"""
Senior Agent for Task-Specific Knowledge Generation

This module provides a senior agent that generates comprehensive knowledge by using
domain-specific prompts to categorize questions and generate related planning,
factual, and heuristic knowledge. It follows the same pattern as curate_general_kb
but is specialized for task-specific domains.

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


class TaskSpecificSeniorAgent:
    """
    Senior agent with specialized knowledge for generating comprehensive task-specific knowledge.

    This agent follows the same pattern as the general knowledge senior agent but is
    specialized for task-specific knowledge generation using domain-specific prompts.
    """

    def __init__(self, domain: str, role: str, tasks: list[str], domain_cls: DefaultDomain):
        """
        Initialize the senior agent for a specific domain.

        Args:
            domain: The domain name (e.g., "Financial Statement Analysis")
            role: The role name (e.g., "Senior Financial Analyst")
            tasks: The specific tasks (e.g., ["Analyze Financial Performance"])
            domain_cls: The domain class containing prompt methods (e.g., FinancialStmtAnalysisDomain)
        """
        self.domain = domain
        self.role = role
        self.tasks = tasks
        self.domain_obj = domain_cls(domain=domain, role=role, tasks=tasks)

        logger.info(f"Initialized TaskSpecificSeniorAgent for {self.role} in {self.domain}")

    def answer_task_specific_question(self, question: str) -> str:
        """
        Answer a task-specific question with expert knowledge.

        Args:
            question: The question to answer

        Returns:
            Comprehensive answer to the question
        """

        # Use the domain-specific fact prompt to generate comprehensive knowledge
        fact_prompt = self.domain_obj.get_fact_prompt(question)

        try:
            answer = reason(fact_prompt, target_type=str)
            logger.debug(f"Generated answer for question: {question}")
            return answer
        except Exception as e:
            logger.error(f"Error generating answer for question '{question}': {str(e)}")
            return f"Error generating answer: {str(e)}"

    def generate_knowledge(self, question: str) -> dict[str, Any]:
        """
        Generate comprehensive knowledge for a given question.

        This method orchestrates the full knowledge generation workflow:
        1. Categorizes the question complexity
        2. Generates an execution plan
        3. Extracts factual requirements
        4. Provides expert heuristics

        Args:
            question: The question to generate knowledge for

        Returns:
            Dictionary containing:
            - category: The determined complexity level
            - plan: The generated execution plan
            - facts: The factual knowledge requirements
            - heuristics: The expert insights and rules of thumb

        Raises:
            Exception: If knowledge generation fails
        """
        logger.info(f"Generating knowledge for question: {question}")

        try:
            # Step 1: Categorize the question
            logger.debug("Step 1: Categorizing question complexity")
            categorize_prompt = self.domain_obj.get_categorize_prompt(question)
            categorization_response = self._reason(categorize_prompt, str)
            logger.info(f"Question categorized as: {categorization_response}")

            # Step 2: Generate execution plan
            logger.debug("Step 2: Generating execution plan")
            plan_prompt = self.domain_obj.get_plan_prompt(question, categorization_response)
            plan = self._reason(plan_prompt, str)

            # Step 3: Extract factual requirements
            logger.debug("Step 3: Extracting factual requirements")
            fact_prompt = self.domain_obj.get_fact_prompt(question)
            facts = self._reason(fact_prompt, str)

            # Step 4: Generate expert heuristics
            logger.debug("Step 4: Generating expert heuristics")
            heuristic_prompt = self.domain_obj.get_heuristic_prompt(question)
            heuristics = self._reason(heuristic_prompt, str)

            # Compile results
            knowledge = {
                "question": question,
                "domain": self.domain,
                "role": self.role,
                "task": self.tasks,
                "category": categorization_response,
                "plan": plan.strip(),
                "facts": facts.strip(),
                "heuristics": heuristics.strip(),
                "metadata": {"pipeline_version": "1.0", "domain_class": self.domain_obj.__class__.__name__},
            }

            logger.info(f"Successfully generated knowledge for question: {question}")
            return knowledge

        except Exception as e:
            logger.error(f"Failed to generate knowledge for question '{question}': {str(e)}")
            # Return a fallback structure to maintain API consistency
            return {
                "question": question,
                "domain": self.domain,
                "role": self.role,
                "task": self.tasks,
                "category": "UNKNOWN",
                "plan": f"Error generating plan: {str(e)}",
                "facts": f"Error extracting facts: {str(e)}",
                "heuristics": f"Error generating heuristics: {str(e)}",
                "metadata": {"pipeline_version": "1.0", "domain_class": self.domain_obj.__class__.__name__, "error": str(e)},
            }


# Backward compatibility alias for existing code
KnowledgePipeline = TaskSpecificSeniorAgent


if __name__ == "__main__":
    from .domains.financial_stmt_analysis import FinancialStmtAnalysisDomain

    # Test the senior agent
    agent = TaskSpecificSeniorAgent(
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

    # Test question answering
    test_question = "What are the key financial ratios for analyzing company profitability?"
    answer = agent.answer_task_specific_question(test_question)
    print(f"Answer: {answer}")

    # Test comprehensive knowledge generation
    knowledge = agent.generate_knowledge(test_question)
    print("\nKnowledge generated:")
    print(f"- Category: {knowledge['category']}")
    print(f"- Plan: {knowledge['plan'][:100]}...")
    print(f"- Facts: {knowledge['facts'][:100]}...")
    print(f"- Heuristics: {knowledge['heuristics'][:100]}...")
