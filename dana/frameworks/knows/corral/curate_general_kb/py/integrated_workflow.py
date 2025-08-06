"""
Integrated Workflow: Domain Coverage + Fresher Agent
Combines comprehensive domain mapping with question generation for workflow nodes
"""

import json
from pathlib import Path
from .domain_knowledge_fresher_agent import DomainKnowledgeFresherAgent
import logging

logger = logging.getLogger(__name__)


def extract_knowledge_areas_from_coverage(coverage_file_path: str) -> list[dict]:
    """Extract knowledge areas from domain coverage output as workflow nodes"""
    logger.info(f"Extracting knowledge areas from coverage file: {coverage_file_path}")

    # Read the domain coverage JSON
    file_content = Path(coverage_file_path).read_text()
    coverage_data: dict = json.loads(file_content)

    # Extract all knowledge areas as workflow nodes
    workflow_nodes = []
    domain_branches = coverage_data.get("domain_branches", {})

    for branch_name in domain_branches:
        branch_data = domain_branches[branch_name]
        branch_info = branch_data.get("branch_info", {})
        knowledge_areas = branch_data.get("knowledge_areas", {})

        for area_name in knowledge_areas:
            area_data = knowledge_areas[area_name]

            # Create workflow node description
            node_description = f"Implement {area_data.get('name', area_name)}: {area_data.get('description', '')}. Key topics include: {', '.join(area_data.get('key_topics', []))}. Knowledge level: {area_data.get('knowledge_level', 'mixed')}. Practical relevance: {area_data.get('practical_relevance', '')}"

            workflow_node = {
                "branch": branch_name,
                "branch_info": branch_info,
                "area_name": area_name,
                "area_data": area_data,
                "workflow_description": node_description,
            }

            workflow_nodes.append(workflow_node)

    logger.info(f"Extracted {len(workflow_nodes)} workflow nodes from domain coverage")
    return workflow_nodes


def generate_questions_for_domain_coverage(coverage_file_path: str, topic: str, role: str, sample_size: int = 3) -> dict:
    """Generate questions for all knowledge areas from domain coverage using domain knowledge fresher agent"""

    print("🚀 Starting Integrated Workflow: Domain Coverage + Question Generation")
    print("=" * 70)

    # Extract workflow nodes from domain coverage
    workflow_nodes = extract_knowledge_areas_from_coverage(coverage_file_path)

    # Create domain knowledge fresher agent
    fresher_agent = DomainKnowledgeFresherAgent(topic=topic, role=role)
    fresher_agent.confidence_threshold = 85.0
    fresher_agent.max_iterations = 5  # Limit iterations for efficiency

    print("🤖 Domain Knowledge Fresher Agent Configuration:")
    print(f"   Topic: {fresher_agent.topic}")
    print(f"   Role: {fresher_agent.role}")
    print(f"   Confidence Threshold: {fresher_agent.confidence_threshold}%")
    print(f"   Max Iterations: {fresher_agent.max_iterations}")
    print()

    # Process sample of workflow nodes
    if sample_size > 0 and len(workflow_nodes) > sample_size:
        print(f"📊 Processing sample of {sample_size} nodes (out of {len(workflow_nodes)} total)")
        workflow_nodes = workflow_nodes[:sample_size]

    results = []

    # Generate questions for each workflow node
    for i, node in enumerate(workflow_nodes):
        print()
        print(f"🎯 Processing Node {i + 1}/{len(workflow_nodes)}: {node['area_data']['name']}")
        print(f"   Branch: {node['branch']}")
        print(f"   Description: {node['workflow_description'][:100]}...")
        print("-" * 50)

        # Generate questions using domain knowledge fresher agent with key topics
        key_topics = node["area_data"]["key_topics"]
        question_result = fresher_agent.generate_domain_questions(node["workflow_description"], key_topics)

        # Combine with domain coverage metadata
        integrated_result = {
            "domain_coverage": node,
            "question_generation": question_result,
            "integration_metadata": {
                "branch": node["branch"],
                "area_name": node["area_name"],
                "knowledge_level": node["area_data"]["knowledge_level"],
                "key_topics": node["area_data"]["key_topics"],
                "total_questions_generated": question_result["total_questions"],
                "final_confidence": question_result["final_confidence"],
                "iterations_used": question_result["iterations_used"],
            },
        }

        results.append(integrated_result)

        print(f"✅ Node completed: {question_result['total_questions']} questions, {question_result['final_confidence']}% confidence")

    # Generate summary
    total_questions = sum(result["question_generation"]["total_questions"] for result in results)
    total_confidence = sum(result["question_generation"]["final_confidence"] for result in results)
    avg_confidence = total_confidence / len(results) if results else 0

    summary = {
        "workflow_summary": {
            "total_nodes_processed": len(results),
            "total_questions_generated": total_questions,
            "average_confidence": avg_confidence,
            "integration_approach": "domain_coverage_to_workflow_nodes",
        },
        "detailed_results": results,
    }

    print()
    print("🎉 Integrated Workflow Complete!")
    print(f"✅ Nodes Processed: {len(results)}")
    print(f"✅ Total Questions Generated: {total_questions}")
    print(f"✅ Average Confidence: {avg_confidence:.1f}%")

    return summary


def save_integrated_results(results: dict, output_file: str) -> str:
    """Save integrated results to JSON file"""

    Path(output_file).write_text(json.dumps(results, indent=2))

    print(f"💾 Results saved to: {output_file}")
    return output_file


def run_full_integration_demo(domain_coverage_file: str, topic: str, role: str, output_file: str) -> dict:
    """Run the complete integration demo"""

    print("🌟 Running Full Integration Demo")
    print(f"   Domain Coverage: {domain_coverage_file}")
    print(f"   Topic: {topic}")
    print(f"   Role: {role}")
    print()

    # Generate questions for domain coverage (process all nodes when sample_size=-1)
    results = generate_questions_for_domain_coverage(coverage_file_path=domain_coverage_file, topic=topic, role=role, sample_size=-1)

    # Save results
    save_integrated_results(results, output_file)

    return results


if __name__ == "__main__":
    # Example usage
    domain_coverage_file = "dana/frameworks/knows/corral/curate_general_kb/output/general_kb_topics.json"
    topic = "Investing in stock market"
    role = "Financial Analyst"
    output_file = "integrated_workflow_results.json"

    results = run_full_integration_demo(domain_coverage_file, topic, role, output_file)
