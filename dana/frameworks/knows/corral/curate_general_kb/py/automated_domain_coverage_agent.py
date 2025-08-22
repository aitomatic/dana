from dana.frameworks.knows.corral.curate_general_kb.py.prompts import CREATE_ROOT_PROMPT, EXTENSION_PROMPT
from dana.libs.corelib.py_wrappers.py_reason import py_reason as reason_function
from dana.core.lang.sandbox_context import SandboxContext


def reason(prompt: str, target_type: type | None = None) -> str:
    context = SandboxContext()
    context.set("system:__current_assignment_type", target_type)
    return reason_function(context, prompt)


class AutomatedDomainCoverageAgent:
    def __init__(self, topic: str, role: str) -> None:
        self.topic = topic
        self.role = role

    def create_domain_root_structure(self) -> dict:
        prompt = CREATE_ROOT_PROMPT.format(role=self.role, topic=self.topic)
        return reason(prompt, target_type=dict)

    def expand_branch_knowledge_areas(self, branch_name: str, branch_info: dict) -> dict:
        prompt = EXTENSION_PROMPT.format(
            branch_name=branch_name,
            topic=self.topic,
            scope=branch_info.get("scope", ""),
            importance=branch_info.get("importance", ""),
            role=self.role,
        )
        return reason(prompt, target_type=dict)

    def process_branch(self, branch_name: str, branch_info: dict) -> dict:
        """Process a single branch into knowledge areas"""
        branch_expansion = self.expand_branch_knowledge_areas(branch_name, branch_info)
        return {"branch_info": branch_info, "knowledge_areas": branch_expansion.get("knowledge_areas", {})}

    def build_domain_coverage(self) -> dict:
        """Build domain knowledge coverage"""
        domain_structure = self.create_domain_root_structure()
        main_branches = domain_structure.get("main_branches", {})

        domain_branches = {}
        total_areas = 0

        for branch_name, branch_info in main_branches.items():
            branch_result = self.process_branch(branch_name, branch_info)
            domain_branches[branch_name] = branch_result
            total_areas += len(branch_result["knowledge_areas"])

        return {
            "domain": self.topic,
            "role_perspective": self.role,
            "domain_branches": domain_branches,
            "coverage_summary": {"total_branches": len(main_branches), "total_knowledge_areas": total_areas},
        }


if __name__ == "__main__":
    import json

    agent = AutomatedDomainCoverageAgent("Investing in stock market", "Financial Analyst")
    result = agent.build_domain_coverage()
    with open("general_kb_topics.json", "w") as f:
        json.dump(result, f, indent=4)
