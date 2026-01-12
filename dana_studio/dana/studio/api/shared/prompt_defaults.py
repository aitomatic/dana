"""Default prompt configurations for initialization."""

DEFAULT_PROMPTS = {
    "template_generation": {
        "prompt": {
            "name": "Template Generation Prompt",
            "description": "Prompt for generating interview templates from knowledge summaries",
            "placeholders": ["{formatted_summaries}", "{domain}", "{role}"],
            "placeholder_examples": {
                "{formatted_summaries}": "### Topic 1: Colour Measurement\n**Path**: Operations -> Quality Control\n\nSummary of colour measurement techniques and best practices...\n\n---\n\n### Topic 2: Process Optimization\n**Path**: Operations -> Efficiency\n\nSummary of process optimization strategies...",
                "{domain}": "Sugar Manufacturing",
                "{role}": "Process Engineer",
            },
            "default_value": """Based on the following knowledge summaries from multiple topics:

{formatted_summaries}

Generate a conversational interview template for a {role} expert in {domain}.

Requirements:
1. Create 3-5 natural, open-ended opening questions per topic
2. Add relationship listening prompts (what connections to listen for between topics)
3. Include a follow-up question framework
4. Keep it conversational and expert-driven
5. No rigid detailed questions - let expert guide the conversation
6. Focus questions strictly on the domain and topics provided - avoid generic or off-topic questions
7. Ensure all questions are directly relevant to the specific knowledge summaries provided

Template Structure:
```markdown
# Master Interview Template: {domain} - {role}

## Topic Opening Questions

For each topic, provide:
### [Topic Name]
**Background**: [1-2 sentence context from summary]

**Opening Questions**:
1. [Natural, open-ended question]
2. [Natural, open-ended question]
3. [Natural, open-ended question]

---

## Relationship Exploration Prompts
- When expert mentions [Topic A], explore connection to [Topic B]
- If they discuss [specific concept], ask how it applies elsewhere
- Listen for natural transitions between topics

## Follow-up Framework
- Can you tell me more about that?
- What's an example of when that happened?
- How do you typically handle that situation?
- What else should I know about this?
```
""",
        }
    },
    "interview_agent": {
        "max_followups_per_opener": {
            "name": "Max Follow-ups Per Opener",
            "description": "Maximum follow-up questions allowed per opening question before auto-transitioning (hard limit)",
            "default_value": "2",
        },
        "user_preference": {
            "name": "User Preference",
            "description": "Customize interview tone and focus. Use this to guide how the agent interacts and what knowledge it prioritizes.",
            "default_value": """INTERVIEW TONE:
- Reduce "gotcha" tone when document answers and SME responses differ - treat discrepancies as opportunities to learn, not to correct
- Frame follow-ups as curiosity ("That's interesting - the docs mention X, can you help me understand...") rather than challenges
- Respect SME expertise - they may have context or updates not in the documents

TACIT KNOWLEDGE FOCUS:
- Prioritize capturing expertise: shortcuts, workarounds, and "tricks of the trade"
- Ask about edge cases, exceptions, and "what they don't teach you" scenarios
- Explore the "why" behind decisions - what experience taught them that formal training didn't
- Capture warning signs, red flags, and intuition-based judgments that come from years of practice
- Focus on knowledge that would be lost if this expert left tomorrow
- the expert who do the interview doesn't have access to the document provided to you. So don't assume that they know what inside the document. In fact, things in the document might be outdated compared to what is in the expert mind""",
        },
    },
}


async def initialize_default_prompts(db):
    """Initialize default prompts in the database."""
    from dana.studio.api.repositories import get_application_settings_repo

    repo = get_application_settings_repo()

    for category, prompts in DEFAULT_PROMPTS.items():
        for key, config in prompts.items():
            # Check if already exists
            existing = await repo.get_setting_with_metadata(category, key, db)
            if not existing:
                await repo.set_setting(
                    category=category,
                    key=key,
                    value=config.get("default_value", ""),
                    name=config["name"],
                    description=config["description"],
                    placeholders=config.get("placeholders", []),
                    placeholder_examples=config.get("placeholder_examples", {}),
                    default_value=config.get("default_value"),
                    db=db,
                )
