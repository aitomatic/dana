"""
Manager Agent - Orchestrates the complete knowledge curation workflow

Flow:
1. Use domain coverage agent to generate domain structure
2. Extract key_topics from each knowledge area
3. Use fresher agent to generate questions for each area
4. Use senior agent to answer the generated questions
"""

import asyncio
import json
import logging

from dana.frameworks.knows.corral.curate_general_kb.py.automated_domain_coverage_agent import AutomatedDomainCoverageAgent
from dana.frameworks.knows.corral.curate_general_kb.py.domain_knowledge_fresher_agent import DomainKnowledgeFresherAgent
from dana.frameworks.knows.corral.curate_general_kb.py.senior_agent import SeniorAgent

logger = logging.getLogger(__name__)


class ManagerAgent:
    def __init__(self, topic: str, role: str):
        self.topic = topic
        self.role = role
        self.domain_agent = AutomatedDomainCoverageAgent(topic, role)
        self.fresher_agent = DomainKnowledgeFresherAgent(topic, role)
        self.senior_agent = SeniorAgent(topic, role)

    def create_domain_structure(self):
        domain_structure = self.domain_agent.build_domain_coverage()
        return domain_structure

    def generate_knowledge_for_area(self, area_name: str, key_topics: list):
        questions = self.fresher_agent.generate_domain_questions(area_name, key_topics)
        answers = {}
        semaphore = asyncio.Semaphore(4)

        async def answer_question(topic, question):
            async with semaphore:
                print(f"Generating answer for question: {question}")
                loop = asyncio.get_event_loop()
                answer = await loop.run_in_executor(None, self.senior_agent.answer_domain_question, question)
                print(f"Answer: {answer}")
                return topic, answer

        async def answer_all():
            tasks = []
            for topic, questions_ in questions.get("questions_by_topics", {}).items():
                for question in questions_:
                    tasks.append(answer_question(topic, question))
            results = await asyncio.gather(*tasks)
            grouped = {}
            for topic, answer in results:
                if topic not in grouped:
                    grouped[topic] = []
                grouped[topic].append(answer)
            return grouped

        # Run the async answer_all in the current (possibly sync) context
        try:
            answers = asyncio.run(answer_all())
        except RuntimeError:
            answers = asyncio.get_event_loop().run_until_complete(answer_all())
        questions["answers_by_topics"] = answers
        return questions

    def generate_all_domain_knowledges(self, domain_structure: dict):
        for branch_name, branch_info in domain_structure.get("domain_branches", {}).items():
            knowledge_areas = branch_info.get("knowledge_areas", {})
            for area_name, area_info in knowledge_areas.items():
                key_topics = area_info.get("key_topics", [])
                questions = self.generate_knowledge_for_area(f"{branch_name} - {area_name}", key_topics)
                area_info["knowledge"] = questions
        return domain_structure


if __name__ == "__main__":
    import json

    topic = """
1. Identify the core financial question:
   - What needs to be measured/assessed?
   - What decision will this analysis inform?

2. Determine required financial dimensions:
   - Profitability (Income Statement focus)
   - Liquidity (Balance Sheet + Cash Flow)
   - Efficiency (Cross-statement ratios)
   - Leverage (Balance Sheet structure)
   - Cash Generation (Cash Flow Statement)
   - Valuation (All statements + market data)

3. Establish time frame and comparison basis:
   - Point-in-time vs. trend analysis
   - Company vs. industry vs. historical
"""

    fn = "problem_decomposition.json"
    domain_structure = json.loads(open(fn).read())
    manager = ManagerAgent(topic, "Financial Statement Analyst")
    # domain_structure = manager.create_domain_structure()
    # json.dump(domain_structure, open(fn, "w"), indent=4)
    result = manager.generate_all_domain_knowledges(domain_structure)
    output_fn = fn.replace(".json", "_output.json")
    json.dump(result, open(output_fn, "w"), indent=4)
    # print(json.dumps(domain_structure, indent=4))
