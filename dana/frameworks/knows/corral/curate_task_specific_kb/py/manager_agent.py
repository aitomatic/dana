"""
Manager Agent - Orchestrates the complete task-specific knowledge curation workflow

This manager follows the same interface pattern as curate_general_kb but is specialized for
task-specific knowledge generation focused on a particular role, domain, and tasks.

Flow:
1. Use domain coverage agent to generate hierarchical tree structure
2. Use fresher agent to generate targeted questions for each tree path
3. Use senior agent to generate comprehensive knowledge for each question
4. Return structured knowledge with metadata

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio
import logging
from typing import Any

from .domain_coverage_agent import TaskSpecificDomainCoverageAgent
from .fresher_agent import TaskSpecificFresherAgent
from .senior_agent import TaskSpecificSeniorAgent
from .domains.default_domain import DefaultDomain

logger = logging.getLogger(__name__)


class TaskSpecificManagerAgent:
    """
    Manager agent that orchestrates task-specific knowledge curation.

    This manager preserves the same interface as curate_general_kb but coordinates between
    three specialized agents to create comprehensive task-specific knowledge.
    """

    def __init__(self, topic: str, role: str, tasks: list[str] = None, domain_cls: DefaultDomain = None):
        """
        Initialize the manager agent - maintaining interface compatibility with curate_general_kb.

        Args:
            topic: The topic/domain name (for interface compatibility)
            role: The role name
            tasks: List of tasks (optional, will use domain defaults if not provided)
            domain_cls: The domain class (optional, will use DefaultDomain if not provided)
        """
        # Store original parameters
        self.topic = topic  # For interface compatibility
        self.role = role

        # Set defaults if not provided
        if tasks is None:
            tasks = ["Analyze Information", "Provide Insights", "Answer Questions"]
        if domain_cls is None:
            from .domains.default_domain import DefaultDomain

            domain_cls = DefaultDomain

        self.tasks = tasks
        self.domain_cls = domain_cls

        # Initialize all sub-agents using topic as domain for compatibility
        self.domain_agent = TaskSpecificDomainCoverageAgent(domain=topic, role=role, tasks=tasks, domain_cls=domain_cls)

        self.fresher_agent = TaskSpecificFresherAgent(domain=topic, role=role, tasks=tasks, domain_cls=domain_cls)

        self.senior_agent = TaskSpecificSeniorAgent(domain=topic, role=role, tasks=tasks, domain_cls=domain_cls)

        logger.info(f"Initialized TaskSpecificManagerAgent for {role} in {topic}")

    def create_domain_structure(self):
        """
        Create hierarchical domain coverage structure - maintains curate_general_kb interface.

        Returns:
            Domain coverage structure in JSON format similar to domain_knowledge.json
        """
        logger.info(f"Creating domain structure for {self.topic}")
        domain_structure = self.domain_agent.build_comprehensive_task_coverage()
        logger.info(f"Created domain structure with {domain_structure.get('coverage_summary', {}).get('total_subdomains', 0)} subdomains")
        return domain_structure

    def generate_knowledge_for_area(self, area_description: str, tree_path: list[str]):
        """
        Generate knowledge for a specific area/path - maintains curate_general_kb interface pattern.

        Args:
            area_description: Description of the knowledge area
            tree_path: The path from root to leaf in the tree structure

        Returns:
            Dictionary with questions and answers for the area
        """
        logger.info(f"Generating knowledge for area: {area_description}")

        # Create a mini tree structure for this specific path
        mini_tree = {"root": {"topic": tree_path[0] if tree_path else area_description, "children": []}}

        # Build the path structure
        current_node = mini_tree["root"]
        for i, topic in enumerate(tree_path[1:], 1):
            if i == len(tree_path) - 1:  # Last item (leaf)
                current_node["children"].append({"topic": topic, "children": []})
            else:  # Intermediate nodes
                child = {"topic": topic, "children": []}
                current_node["children"].append(child)
                current_node = child

        # Generate questions for this specific path
        questions_result = self.fresher_agent.generate_tree_path_questions(mini_tree)

        # Process questions with async pattern like curate_general_kb
        answers = {}
        semaphore = asyncio.Semaphore(4)

        async def answer_question(path_key, question):
            async with semaphore:
                print(f"Generating answer for question: {question}")
                loop = asyncio.get_event_loop()
                # Use the comprehensive knowledge generation method
                answer = await loop.run_in_executor(None, self.senior_agent.generate_knowledge, question)
                print(f"Answer generated: {question[:50]}...")
                return path_key, answer

        async def answer_all():
            tasks = []
            for path_key, path_data in questions_result.items():
                questions = path_data.get("questions", [])
                for question in questions:
                    tasks.append(answer_question(path_key, question))
            results = await asyncio.gather(*tasks)
            grouped = {}
            for path_key, answer in results:
                if path_key not in grouped:
                    grouped[path_key] = []
                grouped[path_key].append(answer)
            return grouped

        # Run the async answer_all in the current (possibly sync) context
        try:
            answers = asyncio.run(answer_all())
        except RuntimeError:
            answers = asyncio.get_event_loop().run_until_complete(answer_all())

        # Structure the result to match curate_general_kb format
        result = {
            "area_description": area_description,
            "tree_path": tree_path,
            "questions_by_path": questions_result,
            "answers_by_path": answers,
            "total_questions": sum(len(path_data.get("questions", [])) for path_data in questions_result.values()),
            "total_answers": sum(len(answers_list) for answers_list in answers.values()),
        }

        logger.info(f"Generated {result['total_questions']} questions and {result['total_answers']} answers for area: {area_description}")
        return result

    def generate_all_domain_knowledges(self, domain_structure: dict = None):
        """
        Generate knowledge for all areas in the domain structure - maintains curate_general_kb interface.

        Args:
            domain_structure: Pre-built domain structure, or None to create new one

        Returns:
            Complete domain structure with generated knowledge
        """
        logger.info(f"Generating all domain knowledge for {self.topic}")

        # Create domain structure if not provided
        if domain_structure is None:
            domain_structure = self.create_domain_structure()

        # Extract tree structure and process each path
        if "hierarchical_tree" in domain_structure:
            hierarchical_tree = domain_structure.get("hierarchical_tree", {})
            root = hierarchical_tree.get("root", {})
        else:
            root = domain_structure.get("root", {})

        if not root:
            logger.warning("No hierarchical tree found in domain structure")
            return domain_structure

        # Extract all paths from the tree structure
        def extract_all_paths(node, current_path=None):
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
                all_paths.extend(extract_all_paths(child, new_path))
            return all_paths

        all_paths = extract_all_paths(root)
        logger.info(f"Found {len(all_paths)} knowledge paths to process")

        # Process each path as an "area" using the curate_general_kb pattern
        knowledge_results = {}
        for i, path in enumerate(all_paths):
            area_name = " → ".join(path)
            logger.info(f"Processing path {i + 1}/{len(all_paths)}: {area_name}")

            try:
                knowledge = self.generate_knowledge_for_area(area_name, path)
                knowledge_results[f"path_{i + 1}_{path[-1].lower().replace(' ', '_')}"] = knowledge
            except Exception as e:
                logger.error(f"Failed to generate knowledge for path {area_name}: {str(e)}")
                knowledge_results[f"path_{i + 1}_{path[-1].lower().replace(' ', '_')}"] = {
                    "error": str(e),
                    "area_description": area_name,
                    "tree_path": path,
                }

        # Add the knowledge results to the domain structure
        domain_structure["generated_knowledge"] = knowledge_results
        domain_structure["knowledge_summary"] = {
            "total_paths_processed": len(all_paths),
            "successful_generations": len([k for k in knowledge_results.values() if "error" not in k]),
            "failed_generations": len([k for k in knowledge_results.values() if "error" in k]),
            "total_questions": sum(k.get("total_questions", 0) for k in knowledge_results.values() if "error" not in k),
            "total_answers": sum(k.get("total_answers", 0) for k in knowledge_results.values() if "error" not in k),
        }

        logger.info(f"Completed all domain knowledge generation: {domain_structure['knowledge_summary']}")
        return domain_structure

    def generate_knowledge_for_specific_questions(self, questions: list[str]) -> dict[str, Any]:
        """
        Generate knowledge for a specific list of questions.

        Args:
            questions: List of questions to generate knowledge for

        Returns:
            Dictionary containing knowledge for each question
        """

        logger.info(f"Generating knowledge for {len(questions)} specific questions")

        knowledge_by_question = {}

        for question in questions:
            logger.debug(f"Generating knowledge for: {question}")
            knowledge = self.senior_agent.generate_knowledge(question)
            knowledge_by_question[question] = knowledge

        result = {
            "domain": self.domain,
            "role": self.role,
            "tasks": self.tasks,
            "questions": questions,
            "knowledge_by_question": knowledge_by_question,
            "metadata": {
                "domain_class": self.domain_cls.__name__,
                "total_questions": len(questions),
                "knowledge_entries": len(knowledge_by_question),
                "pipeline_version": "1.0",
            },
        }

        logger.info(f"Completed knowledge generation for {len(questions)} specific questions")
        return result

    def generate_comprehensive_task_knowledge_with_coverage(self) -> dict[str, Any]:
        """
        Generate the most comprehensive task-specific knowledge including domain coverage analysis.

        This method:
        1. Builds comprehensive domain coverage for the role and tasks
        2. Generates targeted questions based on coverage analysis
        3. Generates knowledge for each question
        4. Returns integrated results

        Returns:
            Dictionary containing complete coverage analysis and generated knowledge
        """

        logger.info("Starting comprehensive task knowledge generation with coverage analysis")

        # Step 1: Build domain coverage
        logger.debug("Step 1: Building comprehensive task coverage")
        coverage_structure = self.domain_coverage_agent.build_comprehensive_task_coverage()

        # Step 2: Generate questions based on coverage tree
        logger.debug("Step 2: Generating comprehensive questions from tree structure")
        question_result = self.fresher_agent.generate_comprehensive_questions_from_tree(coverage_structure)

        all_questions = question_result.get("all_questions", [])
        questions_by_path = question_result.get("questions_by_path", {})

        logger.info(f"Generated {len(all_questions)} questions across {len(questions_by_path)} tree paths")

        # Step 3: Generate knowledge for each question
        logger.debug("Step 3: Generating knowledge for each question")
        knowledge_by_question = {}
        knowledge_by_path = {}

        for path_key, path_data in questions_by_path.items():
            path_string = path_data.get("path_string", "")
            questions = path_data.get("questions", [])

            logger.debug(f"Processing {len(questions)} questions for path: {path_string}")
            path_knowledge = []

            for question in questions:
                logger.debug(f"Generating knowledge for: {question}")
                knowledge = self.senior_agent.generate_knowledge(question)
                knowledge_by_question[question] = knowledge
                path_knowledge.append(knowledge)

            knowledge_by_path[path_key] = {
                "path": path_data.get("path", []),
                "path_string": path_string,
                "questions": questions,
                "knowledge": path_knowledge,
            }

        # Step 4: Compile comprehensive integrated result
        result = {
            "domain": self.domain,
            "role": self.role,
            "tasks": self.tasks,
            "domain_coverage": coverage_structure,
            "question_generation": {
                "questions_by_path": questions_by_path,
                "all_questions": all_questions,
                "generation_method": question_result.get("metadata", {}).get("generation_method", "tree_path_based"),
                "generation_metrics": question_result.get("generation_metrics", {}),
                "total_questions": question_result.get("generation_metrics", {}).get("total_questions", 0),
            },
            "knowledge_generation": {"knowledge_by_question": knowledge_by_question, "knowledge_by_path": knowledge_by_path},
            "integration_summary": {
                "total_subdomains": coverage_structure.get("coverage_summary", {}).get("total_subdomains", 0),
                "total_topics": coverage_structure.get("coverage_summary", {}).get("total_topics", 0),
                "total_tree_paths": question_result.get("generation_metrics", {}).get("total_tree_paths", 0),
                "total_questions_generated": len(all_questions),
                "total_knowledge_entries": len(knowledge_by_question),
                "question_paths": len(questions_by_path),
                "coverage_completeness": "comprehensive" if len(all_questions) > 10 else "basic",
                "tree_based_generation": True,
            },
            "metadata": {
                "domain_class": self.domain_cls.__name__,
                "pipeline_version": "1.0",
                "analysis_type": "comprehensive_task_specific_with_coverage",
                "includes_domain_coverage": True,
                "includes_question_generation": True,
                "includes_knowledge_generation": True,
            },
        }

        logger.info("Completed comprehensive task knowledge generation with coverage")
        logger.info(f"- Domain coverage: {result['integration_summary']['total_competency_categories']} competency categories")
        logger.info(
            f"- Questions: {result['integration_summary']['total_questions_generated']} across {result['integration_summary']['question_categories']} categories"
        )
        logger.info(f"- Knowledge: {result['integration_summary']['total_knowledge_entries']} knowledge entries")

        return result


if __name__ == "__main__":
    from .domains.financial_stmt_analysis import FinancialStmtAnalysisDomain

    # Test the manager agent
    manager = TaskSpecificManagerAgent(
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

    # Test using the same interface as curate_general_kb
    topic = "Financial Statement Analysis"
    role = "Senior Financial Statement Analyst"
    tasks = ["Analyze Financial Statements", "Provide Financial Insights", "Answer Financial Questions", "Forecast Financial Performance"]

    # Initialize manager with curate_general_kb compatible interface
    manager = TaskSpecificManagerAgent(topic, role, tasks, FinancialStmtAnalysisDomain)

    print("🧪 Testing curate_general_kb compatible interface...")

    # Step 1: Create domain structure (like curate_general_kb)
    print("📊 Creating domain structure...")
    domain_structure = manager.create_domain_structure()

    # Optional: Save domain structure
    # json.dump(domain_structure, open("task_specific_domain_structure.json", "w"), indent=2)

    # Step 2: Generate all domain knowledge (like curate_general_kb)
    print("🧠 Generating all domain knowledge...")
    result = manager.generate_all_domain_knowledges(domain_structure)

    # Optional: Save complete result
    # json.dump(result, open("task_specific_knowledge_output.json", "w"), indent=2)

    print("\n🎯 Task-Specific Knowledge Generation Complete!")
    print(f"📊 Domain: {topic}")
    print(f"👤 Role: {role}")
    print(f"📋 Tasks: {len(tasks)} tasks")

    # Show summary statistics
    knowledge_summary = result.get("knowledge_summary", {})
    print("\n📈 Generation Summary:")
    print(f"  🌳 Paths processed: {knowledge_summary.get('total_paths_processed', 0)}")
    print(f"  ✅ Successful: {knowledge_summary.get('successful_generations', 0)}")
    print(f"  ❌ Failed: {knowledge_summary.get('failed_generations', 0)}")
    print(f"  ❓ Total questions: {knowledge_summary.get('total_questions', 0)}")
    print(f"  💡 Total answers: {knowledge_summary.get('total_answers', 0)}")

    # Show domain coverage structure
    coverage_summary = result.get("coverage_summary", {})
    print("\n🌳 Domain Coverage:")
    print(f"  📂 Subdomains: {coverage_summary.get('total_subdomains', 0)}")
    print(f"  📝 Topics: {coverage_summary.get('total_topics', 0)}")
    print(f"  🎯 Tree paths: {coverage_summary.get('total_tree_paths', 0)}")
    print(f"  ✅ Validation: {coverage_summary.get('validation_quality', 'N/A')}")

    # Show sample generated knowledge
    generated_knowledge = result.get("generated_knowledge", {})
    if generated_knowledge:
        print("\n📋 Sample Generated Knowledge:")
        first_path_key = list(generated_knowledge.keys())[0]
        first_path_data = generated_knowledge[first_path_key]

        if "error" not in first_path_data:
            print(f"  🛤️ Path: {first_path_data.get('area_description', 'N/A')}")
            print(f"  ❓ Questions: {first_path_data.get('total_questions', 0)}")
            print(f"  💡 Answers: {first_path_data.get('total_answers', 0)}")

            # Show a sample question and answer
            questions_by_path = first_path_data.get("questions_by_path", {})
            if questions_by_path:
                sample_path = list(questions_by_path.values())[0]
                sample_questions = sample_path.get("questions", [])
                if sample_questions:
                    print(f"  📝 Sample question: {sample_questions[0][:80]}...")

    print("\n✨ Interface compatible with curate_general_kb maintained!")
    print("🔄 Use create_domain_structure() and generate_all_domain_knowledges() methods")
