"""
Agent templates for Dana stdlib.

This module provides pre-built agent templates that require explicit imports.
Core agent functionality is available automatically.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.agent.agent_struct_system import AgentStructInstance


def agent_from_template(template_name: str, **kwargs) -> AgentStructInstance:
    """
    Create an agent from a pre-built template.

    Args:
        template_name: Name of the template to use
        **kwargs: Template-specific parameters

    Returns:
        Configured agent instance

    Example:
        import agent

        # Create a customer service agent from template
        cs_agent = agent_from_template("customer_service", domain="billing")

        # Create a technical support agent
        tech_agent = agent_from_template("technical_support", expertise="networking")
    """
    templates = {
        "customer_service": {
            "type": "CustomerService",
            "default_fields": {"domain": "general", "response_style": "friendly", "escalation_threshold": 3},
        },
        "technical_support": {
            "type": "TechnicalSupport",
            "default_fields": {"expertise": "general", "troubleshooting_level": "basic", "documentation_access": True},
        },
        "data_analyst": {
            "type": "DataAnalyst",
            "default_fields": {
                "specialization": "general",
                "visualization_tools": ["matplotlib", "seaborn"],
                "statistical_methods": ["descriptive", "inferential"],
            },
        },
        "quality_inspector": {
            "type": "QualityInspector",
            "default_fields": {"domain": "manufacturing", "tolerance_threshold": 0.02, "inspection_methods": ["visual", "measurement"]},
        },
    }

    if template_name not in templates:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(templates.keys())}")

    template = templates[template_name]
    agent_type = template["type"]
    fields = template["default_fields"].copy()
    fields.update(kwargs)

    # Create agent using core function
    return agent(agent_type, fields)


# Pre-built agent creation functions for common use cases
def create_customer_service_agent(domain: str = "general", **kwargs) -> AgentStructInstance:
    """
    Create a customer service agent with common configuration.

    Args:
        domain: Service domain (billing, technical, general, etc.)
        **kwargs: Additional configuration

    Returns:
        Customer service agent instance
    """
    return agent_from_template("customer_service", domain=domain, **kwargs)


def create_technical_support_agent(expertise: str = "general", **kwargs) -> AgentStructInstance:
    """
    Create a technical support agent with common configuration.

    Args:
        expertise: Technical expertise area
        **kwargs: Additional configuration

    Returns:
        Technical support agent instance
    """
    return agent_from_template("technical_support", expertise=expertise, **kwargs)


def create_data_analyst_agent(specialization: str = "general", **kwargs) -> AgentStructInstance:
    """
    Create a data analyst agent with common configuration.

    Args:
        specialization: Data analysis specialization
        **kwargs: Additional configuration

    Returns:
        Data analyst agent instance
    """
    return agent_from_template("data_analyst", specialization=specialization, **kwargs)


def create_quality_inspector_agent(domain: str = "manufacturing", **kwargs) -> AgentStructInstance:
    """
    Create a quality inspector agent with common configuration.

    Args:
        domain: Inspection domain
        **kwargs: Additional configuration

    Returns:
        Quality inspector agent instance
    """
    return agent_from_template("quality_inspector", domain=domain, **kwargs)
