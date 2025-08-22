CREATE_ROOT_PROMPT = """
As a {role} expert, create 4-6 main knowledge branches for {topic}.

Return JSON with this structure:
{{
    "domain": "{topic}",
    "role_perspective": "{role}",
    "main_branches": {{
        "branch_1": {{
            "name": "Branch name",
            "scope": "What this covers",
            "importance": "Why essential for {role}"
        }},
        ...
    }}
}}
Make branches comprehensive and non-overlapping.
"""

EXTENSION_PROMPT = """
Expand "{branch_name}" into 4-6 knowledge areas for {topic}.

Branch scope: {scope}
Importance: {importance}
Role: {role}

Return JSON:
{{
    "branch_name": "{branch_name}",
    "knowledge_areas": {{
        "area_1": {{
            "name": "Area name",
            "description": "What this contains",
            "key_topics": ["topic1", "topic2"],
            "knowledge_level": "foundational|intermediate|advanced",
            "practical_relevance": "Real-world use"
        }},
        ...
    }}
}}
"""
