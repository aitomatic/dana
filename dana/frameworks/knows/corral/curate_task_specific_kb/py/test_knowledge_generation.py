from dana.frameworks.knows.corral.curate_task_specific_kb.py.senior_agent import TaskSpecificSeniorAgent
from dana.frameworks.knows.corral.curate_task_specific_kb.py.domain_coverage_agent import TaskSpecificDomainCoverageAgent
from dana.frameworks.knows.corral.curate_task_specific_kb.py.manager_agent import TaskSpecificManagerAgent
import json

if __name__ == "__main__":
    from dana.frameworks.knows.corral.curate_task_specific_kb.py.domains.financial_stmt_analysis import FinancialStmtAnalysisDomain
    # pipeline = TaskSpecificSeniorAgent(domain="Financial Statement Analysis", role="Senior Financial Analyst", tasks=["Analyze Financial Performance"], domain_cls=FinancialStmtAnalysisDomain)
    # print(pipeline.generate_knowledge("What is the current ratio?"))

    pipeline = TaskSpecificManagerAgent(topic="Financial Statement Analysis", role="Senior Financial Analyst", tasks=["Analyze Company Performance using Financial Statements"], domain_cls=FinancialStmtAnalysisDomain)
    # print(pipeline.build_comprehensive_task_coverage())
    # with open("domain_knowledge.json", "w") as f:
    #     json.dump(pipeline.build_comprehensive_task_coverage(), f)
    structure = json.loads(open("domain_knowledge.json", "r").read())
    result = pipeline.generate_all_domain_knowledges(structure)
    with open("domain_knowledge_output.json", "w") as f:
        json.dump(result, f, indent=4)