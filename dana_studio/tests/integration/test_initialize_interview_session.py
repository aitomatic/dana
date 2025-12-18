"""
Integration tests for _initialize_interview_session function.

These tests use actual LLM calls to validate that the function correctly
converts various template formats into structured interview notes.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from dana.studio.api.routers.v2.knowledge_pack.kp_interview_session import _initialize_interview_session
from dana.studio.api.services.knowledge_pack.interview_handler.converter import InterviewNoteProcessor, QuestionStatus


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_template_dir(tmp_path):
    """Create a temporary directory for template files."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    return template_dir


@pytest.fixture
def temp_session_dir(tmp_path):
    """Create a temporary directory for session output."""
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    return session_dir


@pytest.fixture
def processor():
    """Create an InterviewNoteProcessor instance for validation."""
    return InterviewNoteProcessor()


# ============================================================================
# Template Fixtures
# ============================================================================

@pytest.fixture
def template_numbered_questions():
    """Template with numbered questions format."""
    return """# Interview Template: Test Domain

## 1. Topic One
**Background**: Test background information for topic one.
**Opening Questions**:
1. First question about the topic?
2. Second question to explore further?
3. Third question to understand details?
"""


@pytest.fixture
def template_bullet_points():
    """Template with bullet point questions format."""
    return """# Interview Template: Test Domain

## 1. Topic One
**Background**: Test background information for topic one.
**Tacit Knowledge Prompts**:
- First question about the topic?
- Second question to explore further?
- Third question to understand details?
"""


@pytest.fixture
def template_tacit_knowledge():
    """Template with Tacit Knowledge Prompts (from user's example)."""
    return """# Refined Interview Template: Process Engineering – Process Engineer (Tacit Knowledge Focus)

## 1. Storage Strategies, Integration & Adaptation
**Background**: Explore how storage decisions are made in practice, including adaptations to real-world constraints and integration with other processes.
**Tacit Knowledge Prompts**:
- Can you walk me through how you actually decide between bulk and intermediate storage for thick juice on your site? Are there any unwritten rules or local preferences?
- What informal strategies or workarounds have you used to integrate storage with upstream or downstream processes, especially when things don't go as planned?
- How do you adapt your seasonal storage planning when unexpected changes occur (e.g., weather, demand shifts)?
- Are there any "tricks of the trade" with automation or digital tools that help you manage storage more effectively?
"""


@pytest.fixture
def template_placeholder_text():
    """Template with placeholder text that should be excluded."""
    return """# Interview Template: Test Domain

## 1. Topic Without Questions
**Background**: Test background information.
**Opening Questions**:
[No specific opening questions provided in the template—prepare to probe based on background and relationship prompts.]
"""


@pytest.fixture
def template_empty_questions():
    """Template with empty questions section."""
    return """# Interview Template: Test Domain

## 1. Topic Without Questions
**Background**: Test background information.
**Opening Questions**:
"""


@pytest.fixture
def template_mixed_formats():
    """Template with multiple topics using different formats."""
    return """# Interview Template: Test Domain

## 1. Topic with Numbered Questions
**Background**: First topic background.
**Opening Questions**:
1. Question one?
2. Question two?

## 2. Topic with Bullet Points
**Background**: Second topic background.
**Tacit Knowledge Prompts**:
- Question A?
- Question B?

## 3. Topic with Placeholder (Should be Excluded)
**Background**: Third topic background.
**Opening Questions**:
[No specific opening questions provided...]
"""


# ============================================================================
# Edge Case Template Fixtures
# ============================================================================

@pytest.fixture
def template_mixed_numbering():
    """Template with both numbered and bulleted questions in same section."""
    return """# Interview Template: Test Domain

## 1. Mixed Format Topic
**Background**: Test background.
**Questions**:
1. Numbered question one?
2. Numbered question two?
- Bullet question one?
- Bullet question two?
"""


@pytest.fixture
def template_questions_in_paragraphs():
    """Template with questions embedded in paragraph text."""
    return """# Interview Template: Test Domain

## 1. Topic with Paragraph Questions
**Background**: Test background.
**Opening Questions**:
The first question we need to ask is: How do you approach this problem? 
Another important question is: What challenges have you faced? 
Finally, we should ask: What solutions have worked best?
"""


@pytest.fixture
def template_multi_line_questions():
    """Template with questions spanning multiple lines."""
    return """# Interview Template: Test Domain

## 1. Topic with Multi-line Questions
**Background**: Test background.
**Opening Questions**:
1. This is a very long question that spans multiple lines
   and continues here with more details about what we want
   to understand from the expert?
2. Another multi-line question that has
   multiple parts and needs to be preserved
   in its entirety?
"""


@pytest.fixture
def template_special_characters():
    """Template with questions containing special characters and markdown."""
    return """# Interview Template: Test Domain

## 1. Topic with Special Characters
**Background**: Test background.
**Opening Questions**:
1. Question with **bold** text and *italic* text?
2. Question with `code` snippets and [links](http://example.com)?
3. Question with > quotes and # headers?
"""


@pytest.fixture
def template_non_standard_headers():
    """Template with non-standard section headers."""
    return """# Interview Template: Test Domain

## 1. Topic with Questions Header
**Background**: Test background.
**Questions**:
1. First question?
2. Second question?

## 2. Topic with Key Points Header
**Background**: Test background.
**Key Points**:
- Point one?
- Point two?

## 3. Topic with Discussion Topics Header
**Background**: Test background.
**Discussion Topics**:
1. Topic one?
2. Topic two?
"""


@pytest.fixture
def template_code_blocks():
    """Template with questions containing code blocks."""
    return """# Interview Template: Test Domain

## 1. Topic with Code
**Background**: Test background.
**Opening Questions**:
1. How do you use this code snippet?
```python
def example():
    return "test"
```
2. What does this configuration mean?
```yaml
key: value
```
"""


@pytest.fixture
def template_very_long_questions():
    """Template with extremely long questions."""
    return """# Interview Template: Test Domain

## 1. Topic with Long Questions
**Background**: Test background.
**Opening Questions**:
1. This is an extremely long question that contains many words and details about a complex topic that requires extensive explanation and context to understand fully, including various aspects and considerations that need to be explored in depth to get a comprehensive understanding of the subject matter and all its nuances and implications for the overall process and workflow?
2. Another very long question that goes on for many sentences and paragraphs to test whether the LLM can properly handle and preserve the complete question text without truncation or splitting it into multiple parts incorrectly?
"""


@pytest.fixture
def template_very_short_questions():
    """Template with very short questions."""
    return """# Interview Template: Test Domain

## 1. Topic with Short Questions
**Background**: Test background.
**Opening Questions**:
1. Why?
2. How?
3. When?
"""


@pytest.fixture
def template_nested_lists():
    """Template with nested lists."""
    return """# Interview Template: Test Domain

## 1. Topic with Nested Lists
**Background**: Test background.
**Opening Questions**:
1. Main question one?
   - Sub-question A?
   - Sub-question B?
2. Main question two?
   - Sub-question C?
"""


@pytest.fixture
def template_emojis():
    """Template with questions containing emojis."""
    return """# Interview Template: Test Domain

## 1. Topic with Emojis
**Background**: Test background.
**Opening Questions**:
1. How do you handle ⚠️ warnings?
2. What about ✅ success cases?
3. Any ❌ error scenarios?
"""


@pytest.fixture
def template_different_languages():
    """Template with questions in different languages."""
    return """# Interview Template: Test Domain

## 1. Topic with Spanish Questions
**Background**: Test background.
**Opening Questions**:
1. ¿Cómo se hace esto?
2. ¿Cuál es el proceso?

## 2. Topic with French Questions
**Background**: Test background.
**Opening Questions**:
1. Comment faites-vous cela?
2. Quel est le processus?
"""


@pytest.fixture
def template_ambiguous_placeholder():
    """Template with text that looks like placeholder but isn't."""
    return """# Interview Template: Test Domain

## 1. Topic with Bracket Text
**Background**: Test background.
**Opening Questions**:
1. In production, we use [specific tool] for this. How do you configure it?
2. The process involves [step A] and [step B]. Can you explain?
"""


@pytest.fixture
def template_no_background():
    """Template without explicit Background section."""
    return """# Interview Template: Test Domain

## 1. Topic Without Background
**Opening Questions**:
1. First question?
2. Second question?
"""


@pytest.fixture
def template_large():
    """Template with many topics and questions."""
    topics = []
    for i in range(1, 21):
        topics.append(f"""## {i}. Topic {i}
**Background**: Background for topic {i}.
**Opening Questions**:
""")
        for j in range(1, 6):
            topics.append(f"{j}. Question {j} for topic {i}?\n")
        topics.append("\n")
    
    return "# Interview Template: Large Test Domain\n\n" + "\n".join(topics)


@pytest.fixture
def template_inconsistent_formatting():
    """Template with inconsistent formatting."""
    return """# Interview Template: Test Domain

## 1. Topic with Inconsistent Formatting
	**Background**: Test background (tab indented).
**Opening Questions**:
   1. Question with spaces?
2. Question with no space?
 3. Question with extra spaces?
- Bullet with dash?
• Bullet with dot?
"""


@pytest.fixture
def template_links():
    """Template with questions containing links."""
    return """# Interview Template: Test Domain

## 1. Topic with Links
**Background**: Test background.
**Opening Questions**:
1. Have you seen [this resource](https://example.com/resource)?
2. What about [this documentation](https://example.com/docs)?
"""


@pytest.fixture
def template_tables():
    """Template with questions referencing tables."""
    return """# Interview Template: Test Domain

## 1. Topic with Tables
**Background**: Test background.
**Opening Questions**:
1. How do you interpret this table?
| Column A | Column B |
|----------|----------|
| Value 1  | Value 2  |
2. What does this data mean?
"""


# ============================================================================
# Validation Helper Functions
# ============================================================================

def validate_note_structure(note_content: str, processor: InterviewNoteProcessor) -> dict[str, Any]:
    """
    Validate note can be parsed and has required structure.
    
    Returns:
        Parsed JSON data if valid, raises AssertionError if invalid
    """
    assert note_content, "Note content should not be empty"
    
    json_data = processor.markdown_to_json(note_content)
    
    assert "title" in json_data, "Note should have title"
    assert "date" in json_data, "Note should have date"
    assert "interview_goal" in json_data, "Note should have interview_goal"
    assert "topics" in json_data, "Note should have topics"
    assert isinstance(json_data["topics"], list), "Topics should be a list"
    
    return json_data


def validate_questions_format(note_content: str, processor: InterviewNoteProcessor) -> None:
    """Validate all questions are in numbered format in the markdown."""
    import re
    
    # Find all Key Questions sections
    questions_sections = re.findall(r"\*\*Key Questions\*\*:\s*(.+?)(?=\n\*\*|\n---|\Z)", note_content, re.DOTALL)
    
    for section_idx, section in enumerate(questions_sections):
        # Split into lines and check each question line
        lines = [line.strip() for line in section.strip().split('\n') if line.strip()]
        
        question_num = 1
        for line in lines:
            # Skip empty lines and section headers
            if not line or line.startswith('#'):
                continue
            
            # Check if line is a question (starts with number or has status bracket)
            # Questions should be in format: "1. Question text?" or "[status] 1. Question text?"
            is_numbered = (
                line.startswith(f"{question_num}.") or
                f"{question_num}." in line or
                (line.startswith("[") and f"{question_num}." in line)
            )
            
            if is_numbered:
                question_num += 1
            elif line and not line.startswith("-") and not line.startswith("*"):
                # If it's not a numbered question and not a bullet point, it might be a question without number
                # This is an error - all questions should be numbered
                assert False, (
                    f"Question in section {section_idx + 1} should be in numbered format. "
                    f"Expected format: '{question_num}. Question text?' but got: '{line[:100]}'"
                )


def validate_topics_included(json_data: dict[str, Any], expected_topics: list[str]) -> None:
    """Validate expected topics are included in the note."""
    topic_names = [topic.get("topic_name", "") for topic in json_data.get("topics", [])]
    
    for expected_topic in expected_topics:
        assert expected_topic in topic_names, f"Expected topic '{expected_topic}' not found in topics: {topic_names}"


def validate_topics_excluded(json_data: dict[str, Any], excluded_topics: list[str]) -> None:
    """Validate excluded topics are not present in the note."""
    topic_names = [topic.get("topic_name", "") for topic in json_data.get("topics", [])]
    
    for excluded_topic in excluded_topics:
        assert excluded_topic not in topic_names, f"Excluded topic '{excluded_topic}' was incorrectly included in topics: {topic_names}"


def report_edge_case_result(test_name: str, passed: bool, issues: Optional[list[str]] = None) -> None:
    """
    Report edge case test result in structured format.
    
    Args:
        test_name: Name of the test
        passed: Whether the test passed
        issues: List of issues found (if any)
    """
    issues = issues or []
    status = "✅ PASS" if passed else "❌ FAIL"
    if issues and passed:
        status = "⚠️ PARTIAL"
    
    print(f"\n{status}: {test_name}")
    if issues:
        for issue in issues:
            print(f"  - {issue}")


# ============================================================================
# Basic Format Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_initialize_with_numbered_questions(
    temp_template_dir, temp_session_dir, processor, template_numbered_questions
):
    """Test template with numbered questions format."""
    # Create template file
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_numbered_questions, encoding="utf-8")
    
    # Create session directory
    session_dir = temp_session_dir / "session_1"
    session_dir.mkdir()
    
    # Initialize session
    note_path, note_content = await _initialize_interview_session(
        session_id=1,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    # Validate file was created
    assert Path(note_path).exists(), "Note file should be created"
    assert note_content, "Note content should not be empty"
    
    # Validate structure
    json_data = validate_note_structure(note_content, processor)
    
    # Validate questions format
    validate_questions_format(note_content, processor)
    
    # Validate topic is included
    validate_topics_included(json_data, ["Topic One"])
    
    # Validate questions are present
    topic = next(t for t in json_data["topics"] if t["topic_name"] == "Topic One")
    assert len(topic["key_questions"]) >= 3, "Should have at least 3 questions"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_initialize_with_bullet_point_questions(
    temp_template_dir, temp_session_dir, processor, template_bullet_points
):
    """Test template with bullet point questions format."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_bullet_points, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_2"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=2,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    assert Path(note_path).exists()
    json_data = validate_note_structure(note_content, processor)
    validate_questions_format(note_content, processor)
    validate_topics_included(json_data, ["Topic One"])
    
    topic = next(t for t in json_data["topics"] if t["topic_name"] == "Topic One")
    assert len(topic["key_questions"]) >= 3, "Should have at least 3 questions"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_initialize_with_tacit_knowledge_prompts(
    temp_template_dir, temp_session_dir, processor, template_tacit_knowledge
):
    """Test template with Tacit Knowledge Prompts section."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_tacit_knowledge, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_3"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=3,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Process Engineering",
        role="Process Engineer"
    )
    
    assert Path(note_path).exists()
    json_data = validate_note_structure(note_content, processor)
    validate_questions_format(note_content, processor)
    validate_topics_included(json_data, ["Storage Strategies, Integration & Adaptation"])
    
    topic = next(t for t in json_data["topics"] if "Storage Strategies" in t["topic_name"])
    assert len(topic["key_questions"]) >= 4, "Should have at least 4 questions"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_initialize_excludes_placeholder_text(
    temp_template_dir, temp_session_dir, processor, template_placeholder_text
):
    """Test template with placeholder text is excluded."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_placeholder_text, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_4"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=4,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    assert Path(note_path).exists()
    json_data = validate_note_structure(note_content, processor)
    validate_topics_excluded(json_data, ["Topic Without Questions"])


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_initialize_excludes_empty_questions(
    temp_template_dir, temp_session_dir, processor, template_empty_questions
):
    """Test template with empty questions section is excluded."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_empty_questions, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_5"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=5,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    assert Path(note_path).exists()
    json_data = validate_note_structure(note_content, processor)
    validate_topics_excluded(json_data, ["Topic Without Questions"])


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_initialize_with_mixed_formats(
    temp_template_dir, temp_session_dir, processor, template_mixed_formats
):
    """Test template with multiple topics using different formats."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_mixed_formats, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_6"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=6,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    assert Path(note_path).exists()
    json_data = validate_note_structure(note_content, processor)
    validate_questions_format(note_content, processor)
    
    # Valid topics should be included
    validate_topics_included(json_data, ["Topic with Numbered Questions", "Topic with Bullet Points"])
    # Invalid topic should be excluded
    validate_topics_excluded(json_data, ["Topic with Placeholder (Should be Excluded)"])


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_initialize_creates_valid_note_structure(
    temp_template_dir, temp_session_dir, processor, template_numbered_questions
):
    """Test that output can be parsed and has required fields."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_numbered_questions, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_7"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=7,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    # Verify each topic has key_questions array
    for topic in json_data["topics"]:
        assert "key_questions" in topic, f"Topic '{topic.get('topic_name')}' should have key_questions"
        assert isinstance(topic["key_questions"], list), "key_questions should be a list"
        assert len(topic["key_questions"]) > 0, f"Topic '{topic.get('topic_name')}' should have at least one question"
    
    validate_questions_format(note_content, processor)


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_initialize_writes_note_file(
    temp_template_dir, temp_session_dir, processor, template_numbered_questions
):
    """Test that note file is created and matches returned content."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_numbered_questions, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_8"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=8,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    # Verify file exists
    note_file = Path(note_path)
    assert note_file.exists(), "Note file should exist"
    
    # Verify file content matches returned content
    file_content = note_file.read_text(encoding="utf-8")
    assert file_content == note_content, "File content should match returned content"
    
    # Verify file can be parsed
    json_data = processor.from_file(str(note_file))
    assert json_data, "File should be parseable"


# ============================================================================
# Edge Case Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_mixed_numbering_in_section(
    temp_template_dir, temp_session_dir, processor, template_mixed_numbering
):
    """Test LLM handles mixed numbering formats in same section."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_mixed_numbering, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_1"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=101,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    # Count questions - should be 4 total
    topic = json_data["topics"][0]
    questions = topic["key_questions"]
    
    issues = []
    if len(questions) != 4:
        issues.append(f"Expected 4 questions, got {len(questions)}. LLM may have missed questions in mixed format sections.")
    
    # All should be numbered format
    validate_questions_format(note_content, processor)
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_mixed_numbering_in_section", passed, issues)
    
    assert len(questions) == 4, f"Expected 4 questions, got {len(questions)}"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_questions_in_paragraphs(
    temp_template_dir, temp_session_dir, processor, template_questions_in_paragraphs
):
    """Test LLM recognizes questions embedded in paragraph text."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_questions_in_paragraphs, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_2"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=102,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    topic = json_data["topics"][0]
    questions = topic["key_questions"]
    
    issues = []
    if len(questions) < 3:
        issues.append(f"Expected at least 3 questions from paragraphs, got {len(questions)}. LLM may not recognize questions not in list format.")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_questions_in_paragraphs", passed, issues)
    
    # At least some questions should be extracted
    assert len(questions) > 0, "Should extract at least some questions from paragraphs"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_multi_line_questions(
    temp_template_dir, temp_session_dir, processor, template_multi_line_questions
):
    """Test LLM preserves multi-line questions correctly."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_multi_line_questions, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_3"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=103,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    topic = json_data["topics"][0]
    questions = topic["key_questions"]
    
    issues = []
    if len(questions) < 2:
        issues.append(f"Expected 2 multi-line questions, got {len(questions)}. LLM may have split them incorrectly.")
    
    # Check if questions contain newlines (indicating multi-line preservation)
    for q in questions:
        q_text = q.get("text", "") if isinstance(q, dict) else str(q)
        if "\n" not in q_text and len(q_text) < 100:
            issues.append(f"Question may have been truncated: {q_text[:50]}...")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_multi_line_questions", passed, issues)
    
    assert len(questions) >= 2, "Should have at least 2 questions"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_special_characters_in_questions(
    temp_template_dir, temp_session_dir, processor, template_special_characters
):
    """Test LLM preserves special characters and markdown in questions."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_special_characters, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_4"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=104,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    topic = json_data["topics"][0]
    questions = topic["key_questions"]
    
    issues = []
    # Check if special characters are preserved
    special_chars = ["**", "*", "`", "[", "]", ">", "#"]
    for q in questions:
        q_text = q.get("text", "") if isinstance(q, dict) else str(q)
        found_chars = [char for char in special_chars if char in q_text]
        if not found_chars and len(questions) > 0:
            issues.append(f"Special characters may have been stripped from question: {q_text[:50]}...")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_special_characters_in_questions", passed, issues)
    
    assert len(questions) >= 3, "Should have at least 3 questions"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_non_standard_section_headers(
    temp_template_dir, temp_session_dir, processor, template_non_standard_headers
):
    """Test LLM extracts questions from non-standard section headers."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_non_standard_headers, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_5"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=105,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    issues = []
    expected_topics = ["Topic with Questions Header", "Topic with Key Points Header", "Topic with Discussion Topics Header"]
    found_topics = [t["topic_name"] for t in json_data["topics"]]
    
    for expected in expected_topics:
        if expected not in found_topics:
            issues.append(f"Topic '{expected}' not found. LLM may miss questions under non-standard headers.")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_non_standard_section_headers", passed, issues)
    
    # At least some topics should be included
    assert len(json_data["topics"]) > 0, "Should extract at least some topics from non-standard headers"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_questions_with_code_blocks(
    temp_template_dir, temp_session_dir, processor, template_code_blocks
):
    """Test LLM handles questions with code blocks."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_code_blocks, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_6"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=106,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    topic = json_data["topics"][0]
    questions = topic["key_questions"]
    
    issues = []
    # Check if code blocks are preserved
    for q in questions:
        q_text = q.get("text", "") if isinstance(q, dict) else str(q)
        if "```" not in q_text and "def" not in q_text.lower():
            issues.append("Code blocks may not be preserved in questions")
            break
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_questions_with_code_blocks", passed, issues)
    
    assert len(questions) >= 2, "Should have at least 2 questions"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_very_long_questions(
    temp_template_dir, temp_session_dir, processor, template_very_long_questions
):
    """Test LLM preserves very long questions without truncation."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_very_long_questions, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_7"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=107,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    topic = json_data["topics"][0]
    questions = topic["key_questions"]
    
    issues = []
    # Check if questions are long enough (indicating they weren't truncated)
    for q in questions:
        q_text = q.get("text", "") if isinstance(q, dict) else str(q)
        if len(q_text) < 100:
            issues.append(f"Question appears truncated (length {len(q_text)}): {q_text[:50]}...")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_very_long_questions", passed, issues)
    
    assert len(questions) >= 2, "Should have at least 2 questions"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_very_short_questions(
    temp_template_dir, temp_session_dir, processor, template_very_short_questions
):
    """Test LLM recognizes very short questions as valid."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_very_short_questions, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_8"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=108,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    topic = json_data["topics"][0]
    questions = topic["key_questions"]
    
    issues = []
    if len(questions) < 3:
        issues.append(f"Expected 3 short questions, got {len(questions)}. LLM may not recognize very short questions as valid.")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_very_short_questions", passed, issues)
    
    assert len(questions) >= 3, "Should have at least 3 questions"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_nested_lists(
    temp_template_dir, temp_session_dir, processor, template_nested_lists
):
    """Test LLM handles nested lists correctly."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_nested_lists, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_9"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=109,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    topic = json_data["topics"][0]
    questions = topic["key_questions"]
    
    issues = []
    # Should have at least the main questions (may or may not include sub-questions)
    if len(questions) < 2:
        issues.append(f"Expected at least 2 main questions, got {len(questions)}. LLM may have issues with nested lists.")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_nested_lists", passed, issues)
    
    assert len(questions) >= 2, "Should have at least 2 main questions"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_questions_with_emojis(
    temp_template_dir, temp_session_dir, processor, template_emojis
):
    """Test LLM preserves emojis and special unicode in questions."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_emojis, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_10"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=110,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    topic = json_data["topics"][0]
    questions = topic["key_questions"]
    
    issues = []
    emojis = ["⚠️", "✅", "❌"]
    for q in questions:
        q_text = q.get("text", "") if isinstance(q, dict) else str(q)
        found_emojis = [emoji for emoji in emojis if emoji in q_text]
        if not found_emojis and len(questions) > 0:
            issues.append("Emojis may have been stripped or corrupted from questions")
            break
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_questions_with_emojis", passed, issues)
    
    assert len(questions) >= 3, "Should have at least 3 questions"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_questions_in_different_languages(
    temp_template_dir, temp_session_dir, processor, template_different_languages
):
    """Test LLM handles questions in different languages."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_different_languages, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_11"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=111,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    issues = []
    expected_topics = ["Topic with Spanish Questions", "Topic with French Questions"]
    found_topics = [t["topic_name"] for t in json_data["topics"]]
    
    for expected in expected_topics:
        if expected not in found_topics:
            issues.append(f"Topic '{expected}' not found. LLM may have issues with non-English content.")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_questions_in_different_languages", passed, issues)
    
    # At least some topics should be included
    assert len(json_data["topics"]) > 0, "Should extract at least some topics with non-English questions"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_ambiguous_placeholder_detection(
    temp_template_dir, temp_session_dir, processor, template_ambiguous_placeholder
):
    """Test LLM doesn't incorrectly exclude valid questions with bracket text."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_ambiguous_placeholder, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_12"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=112,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    issues = []
    # Topic should be included (not excluded as placeholder)
    topic_names = [t["topic_name"] for t in json_data["topics"]]
    if "Topic with Bracket Text" not in topic_names:
        issues.append("Topic with bracket text was incorrectly excluded. LLM may have mistaken it for placeholder.")
    
    if "Topic with Bracket Text" in topic_names:
        topic = next(t for t in json_data["topics"] if t["topic_name"] == "Topic with Bracket Text")
        if len(topic["key_questions"]) < 2:
            issues.append("Questions with bracket text may have been excluded incorrectly.")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_ambiguous_placeholder_detection", passed, issues)
    
    # Topic should be included
    validate_topics_included(json_data, ["Topic with Bracket Text"])


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_missing_background_sections(
    temp_template_dir, temp_session_dir, processor, template_no_background
):
    """Test LLM creates proper structure even without Background section."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_no_background, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_13"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=113,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    issues = []
    if len(json_data["topics"]) == 0:
        issues.append("No topics created. LLM may require Background section to create structure.")
    
    if len(json_data["topics"]) > 0:
        topic = json_data["topics"][0]
        if not topic.get("background"):
            issues.append("Topic missing background field. Structure may be incomplete.")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_missing_background_sections", passed, issues)
    
    # Should still create structure
    assert len(json_data["topics"]) > 0, "Should create topics even without Background section"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_very_large_template(
    temp_template_dir, temp_session_dir, processor, template_large
):
    """Test LLM handles very large templates without truncation."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_large, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_14"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=114,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    issues = []
    # Should have many topics (may not get all 20, but should get most)
    if len(json_data["topics"]) < 15:
        issues.append(f"Expected at least 15 topics from large template, got {len(json_data['topics'])}. LLM may have truncated or missed topics.")
    
    # Count total questions
    total_questions = sum(len(t.get("key_questions", [])) for t in json_data["topics"])
    if total_questions < 50:
        issues.append(f"Expected at least 50 questions total, got {total_questions}. LLM may have missed questions in large template.")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_very_large_template", passed, issues)
    
    # Should have substantial content
    assert len(json_data["topics"]) >= 10, f"Should have at least 10 topics, got {len(json_data['topics'])}"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_inconsistent_formatting(
    temp_template_dir, temp_session_dir, processor, template_inconsistent_formatting
):
    """Test LLM handles inconsistent formatting (spaces, tabs, indentation)."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_inconsistent_formatting, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_15"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=115,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    issues = []
    topic = json_data["topics"][0]
    questions = topic["key_questions"]
    
    # Should extract questions despite formatting issues
    if len(questions) < 3:
        issues.append(f"Expected at least 3 questions despite formatting issues, got {len(questions)}. LLM may miss questions due to formatting.")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_inconsistent_formatting", passed, issues)
    
    # Should extract at least some questions
    assert len(questions) > 0, "Should extract questions despite formatting inconsistencies"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_questions_with_links(
    temp_template_dir, temp_session_dir, processor, template_links
):
    """Test LLM preserves markdown links in questions."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_links, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_16"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=116,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    topic = json_data["topics"][0]
    questions = topic["key_questions"]
    
    issues = []
    # Check if links are preserved
    for q in questions:
        q_text = q.get("text", "") if isinstance(q, dict) else str(q)
        if "[" in q_text and "]" in q_text and "(" in q_text and ")" in q_text:
            # Link format detected
            break
    else:
        issues.append("Markdown links may not be preserved in questions")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_questions_with_links", passed, issues)
    
    assert len(questions) >= 2, "Should have at least 2 questions"


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_edge_case_questions_with_tables(
    temp_template_dir, temp_session_dir, processor, template_tables
):
    """Test LLM handles questions referencing markdown tables."""
    template_path = temp_template_dir / "template.md"
    template_path.write_text(template_tables, encoding="utf-8")
    
    session_dir = temp_session_dir / "session_edge_17"
    session_dir.mkdir()
    
    note_path, note_content = await _initialize_interview_session(
        session_id=117,
        template_path=str(template_path),
        session_dir=str(session_dir),
        domain="Test Domain",
        role="Expert"
    )
    
    json_data = validate_note_structure(note_content, processor)
    
    topic = json_data["topics"][0]
    questions = topic["key_questions"]
    
    issues = []
    # Check if table references are preserved
    for q in questions:
        q_text = q.get("text", "") if isinstance(q, dict) else str(q)
        if "table" in q_text.lower() or "|" in q_text:
            # Table reference detected
            break
    else:
        issues.append("Table references may not be preserved in questions")
    
    passed = len(issues) == 0
    report_edge_case_result("test_edge_case_questions_with_tables", passed, issues)
    
    assert len(questions) >= 2, "Should have at least 2 questions"


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_initialize_with_nonexistent_template_path(temp_session_dir):
    """Test that function raises FileNotFoundError for non-existent template."""
    session_dir = temp_session_dir / "session_error_1"
    session_dir.mkdir()
    
    with pytest.raises(FileNotFoundError):
        await _initialize_interview_session(
            session_id=201,
            template_path="/nonexistent/path/template.md",
            session_dir=str(session_dir),
            domain="Test Domain",
            role="Expert"
        )

