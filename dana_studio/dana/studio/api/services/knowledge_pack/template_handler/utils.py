"""
Template parsing and manipulation utilities for interview template fine-tuning.
"""

from __future__ import annotations

import re
from pathlib import Path
from dana.studio.api.services.search.bm25 import BM25SearchEngine


def parse_template(template_path: str) -> dict[str, any]:
    """
    Parse markdown template into structured dict of sections.

    Returns:
        Dict with keys: 'approach', 'topics', 'relationship_prompts', 'followup_framework'
    """
    with open(template_path, encoding="utf-8") as f:
        content = f.read()

    result = {
        "approach": extract_approach_section(content),
        "topics": extract_all_topics(content),
        "relationship_prompts": extract_relationship_prompts(content),
        "followup_framework": extract_followup_framework(content),
        "raw_content": content,
    }

    return result


def extract_approach_section(content: str) -> dict[str, str]:
    """Parse Interview Approach section into fields."""
    approach_match = re.search(r"## Interview Approach\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)

    if not approach_match:
        return {}

    approach_text = approach_match.group(1)

    # Extract key fields
    goal_match = re.search(r"Goal[:\s]*([^\n]+)", approach_text)
    style_match = re.search(r"Style[:\s]*([^\n]+)", approach_text)
    duration_match = re.search(r"Duration[:\s]*([^\n]+)", approach_text)
    topics_match = re.search(r"Topics Covered[:\s]*([^\n]+)", approach_text)

    return {
        "goal": goal_match.group(1).strip() if goal_match else "",
        "style": style_match.group(1).strip() if style_match else "",
        "duration": duration_match.group(1).strip() if duration_match else "",
        "topics_covered": topics_match.group(1).strip() if topics_match else "",
        "raw_text": approach_text.strip(),
    }


def extract_all_topics(content: str) -> list[dict[str, any]]:
    """Extract all topic sections from template."""
    topics = []

    # Find all topic sections (### Topic Name)
    topic_pattern = r"### ([^\n]+)\n(.*?)(?=\n### |\n## |\Z)"
    matches = re.finditer(topic_pattern, content, re.DOTALL)

    for match in matches:
        topic_name = match.group(1).strip()
        topic_content = match.group(2).strip()
        raw_content = match.group(0)

        # Parse topic content
        background_match = re.search(r"\*\*Background\*\*:\s*([^\n]+)", topic_content)
        questions_match = re.search(r"\*\*Opening Questions\*\*:\s*\n(.*?)(?=\*\*Listen for connections|\Z)", topic_content, re.DOTALL)

        topic_data = {
            "name": topic_name,
            "background": background_match.group(1).strip() if background_match else "",
            "questions": [],
            "raw_content": raw_content,
        }

        # Extract questions
        if questions_match:
            questions_text = questions_match.group(1)
            question_items = re.findall(r"\d+\.\s*([^\n]+)", questions_text)
            topic_data["questions"] = [q.strip() for q in question_items]

        topics.append(topic_data)

    return topics


def extract_relationship_prompts(content: str) -> str:
    """Extract relationship exploration prompts."""
    prompts_match = re.search(r"## Relationship Exploration Prompts\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)

    if not prompts_match:
        return ""

    return prompts_match.group(0)


def extract_followup_framework(content: str) -> str:
    """Extract follow-up framework questions."""
    framework_match = re.search(r"## Follow-up Framework\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)

    if not framework_match:
        return ""

    return framework_match.group(0)


def extract_topic_section(content: str, topic_name: str) -> tuple[str, int, int]:
    """Find topic section with start/end positions."""
    # Escape special regex characters in topic name
    escaped_name = re.escape(topic_name)
    pattern = rf"### {escaped_name}\s*\n(.*?)(?=\n### |\n## |\Z)"

    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return "", -1, -1

    start_pos = match.start()
    end_pos = match.end()
    section_content = match.group(0)

    return section_content, start_pos, end_pos


def format_topic_section(topic_name: str, background: str, questions: list[str], connections: str) -> str:
    """Format topic as markdown."""
    if not questions:
        return f"""### {topic_name}
*(No questions defined for this topic yet)*

---"""

    questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

    return f"""### {topic_name}
**Background**: {background}
**Opening Questions**:
{questions_text}

---"""


def reorder_topics(template_content: str, new_order: list[str]) -> str:
    """Reconstruct template with new topic order."""
    # Extract all sections
    approach_section = extract_approach_section(template_content)
    topics = extract_all_topics(template_content)
    relationship_prompts = extract_relationship_prompts(template_content)
    followup_framework = extract_followup_framework(template_content)

    # Create new content with reordered topics
    new_content = []

    # Add header
    new_content.append("# Master Interview Template: Food Manufacturing - Process Operator")
    new_content.append("")

    # Add approach section
    if approach_section.get("raw_text"):
        new_content.append("## Interview Approach")
        new_content.append(approach_section["raw_text"])
        new_content.append("")
        new_content.append("---")
        new_content.append("")

    # Add reordered topics
    new_content.append("## Topic Opening Questions")
    new_content.append("")

    # Create topic lookup
    topic_lookup = {topic["name"]: topic for topic in topics}

    for topic_name in new_order:
        if topic_name in topic_lookup:
            topic = topic_lookup[topic_name]
            formatted = format_topic_section(topic["name"], topic["background"], topic["questions"], topic["connections"])
            new_content.append(formatted)
            new_content.append("")

    # Add relationship prompts
    if relationship_prompts:
        new_content.append("## Relationship Exploration Prompts")
        for prompt in relationship_prompts:
            new_content.append(f"- {prompt}")
        new_content.append("")

    # Add follow-up framework
    if followup_framework:
        new_content.append("## Follow-up Framework")
        for question in followup_framework:
            new_content.append(f'- "{question}"')
        new_content.append("")

    return "\n".join(new_content)


def create_backup(template_path: str) -> str:
    """Create backup of template file."""
    import shutil

    backup_path = f"{template_path}.bak"
    shutil.copy2(template_path, backup_path)
    return backup_path


def write_template(template_path: str, content: str, backup: bool = True) -> None:
    """Write template content to file with optional backup."""
    if backup and Path(template_path).exists():
        create_backup(template_path)

    with open(template_path, "w", encoding="utf-8") as f:
        f.write(content)


def find_topic_fuzzy(topics: list[dict], topic_name: str) -> tuple[dict | None, str]:
    """
    Find topic by name with fuzzy matching support.

    Returns:
        (topic, message) where:
        - topic: Matched topic dict or None
        - message: Success/error/suggestion message
    """
    search_engine = BM25SearchEngine([topic["name"] for topic in topics])
    top_n = search_engine.get_top_n_indices(topic_name, n=1)

    if top_n:
        return topics[top_n[0]], f"✓ Matched: {topics[top_n[0]]['name']}"
    else:
        return None, f"❌ Topic '{topic_name}' not found. Available topics: {'\n- '.join([topic['name'] for topic in topics])}"


def find_topic_by_name(topics: list[dict], topic_name: str) -> dict | None:
    """Find topic by name with fuzzy matching fallback."""
    topic, _ = find_topic_fuzzy(topics, topic_name)
    return topic


def insert_topic_at_position(content: str, topic_section: str, position: str, reference_topic: str = None) -> str:
    """Insert topic section at specified position."""
    if position == "beginning":
        # Insert after "## Topic Opening Questions"
        pattern = r"(## Topic Opening Questions\s*\n)"
        replacement = r"\1" + topic_section + "\n\n"
        return re.sub(pattern, replacement, content)

    elif position == "end":
        # Insert before "## Relationship Exploration Prompts"
        pattern = r"(## Relationship Exploration Prompts)"
        replacement = topic_section + "\n\n" + r"\1"
        return re.sub(pattern, replacement, content)

    elif position.startswith("after:"):
        # Insert after specific topic
        ref_topic = position.split(":", 1)[1]
        pattern = rf"(### {re.escape(ref_topic)}.*?)(?=\n### |\n## |\Z)"
        replacement = r"\1" + "\n\n" + topic_section
        return re.sub(pattern, replacement, content, flags=re.DOTALL)

    return content


def reconstruct_template_content(parsed_data: dict[str, any]) -> str:
    """
    Reconstruct template content from parsed data.

    Args:
        parsed_data: Dictionary with parsed template sections

    Returns:
        Reconstructed template content
    """
    content_parts = []

    # Header
    content_parts.append("# Master Interview Template: Food Manufacturing - Process Operator")
    content_parts.append("")

    # Approach section
    if parsed_data.get("approach"):
        content_parts.append("## Interview Approach")
        approach = parsed_data["approach"]
        if approach.get("goal"):
            content_parts.append(f"- **Goal**: {approach['goal']}")
        if approach.get("style"):
            content_parts.append(f"- **Style**: {approach['style']}")
        if approach.get("duration"):
            content_parts.append(f"- **Duration**: {approach['duration']}")
        if approach.get("topics_covered"):
            content_parts.append(f"- **Topics Covered**: {approach['topics_covered']}")
        content_parts.append("")
        content_parts.append("---")
        content_parts.append("")

    # Topics section
    content_parts.append("## Topic Opening Questions")
    content_parts.append("")

    for topic in parsed_data.get("topics", []):
        content_parts.append(f"### {topic['name']}")
        if topic.get("questions"):
            # Only show metadata if questions exist
            if topic.get("background"):
                content_parts.append(f"**Background**: {topic['background']}")
            content_parts.append("**Opening Questions**:")
            for i, question in enumerate(topic["questions"], 1):
                content_parts.append(f"{i}. {question}")
        else:
            # Show empty note if no questions
            content_parts.append("*(No questions defined for this topic yet)*")
        content_parts.append("")
        content_parts.append("---")
        content_parts.append("")

    # Relationship prompts
    if parsed_data.get("relationship_prompts"):
        content_parts.append("## Relationship Exploration Prompts")
        for prompt in parsed_data["relationship_prompts"]:
            content_parts.append(prompt)
        content_parts.append("")
        content_parts.append("---")
        content_parts.append("")

    # Follow-up framework
    if parsed_data.get("followup_framework"):
        content_parts.append("## Follow-up Framework")
        for question in parsed_data["followup_framework"]:
            content_parts.append(question)
        content_parts.append("")
        content_parts.append("---")
        content_parts.append("")

    return "\n".join(content_parts)
