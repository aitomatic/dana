"""
Prompt templates for domain support workflows.

This module contains all the prompt templates used by domain support workflows
to maintain consistency and make prompts easier to modify.
"""

def get_diagnostic_workflow_prompt(issue_description: str, workflow_name: str, artifacts: dict, resources: list[str]) -> str:
    """Get prompt for diagnostic workflow execution."""
    return f"""You are a technical support expert. A user has reported: "{issue_description}"

This is a {workflow_name.lower()} issue. Based on the information provided, generate a diagnostic plan and solution.

Available information:
- Issue: {issue_description}
- Artifacts: {artifacts}
- Available resources: {", ".join(resources)}

Please provide:
1. A brief diagnosis of the likely cause
2. A prioritized checklist of diagnostic steps (5-7 items)
3. Specific troubleshooting actions
4. Expected outcomes for each step

Format your response as:
DIAGNOSIS: [brief diagnosis]
CHECKLIST:
1. [step 1]
2. [step 2]
...
SOLUTION: [specific solution or next steps]"""
