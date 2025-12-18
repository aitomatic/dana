"""
Tests for InterviewNoteProcessor class.

Following TDD principles with atomic steps.
"""

import pytest
import tempfile
from pathlib import Path
from dana.studio.api.services.knowledge_pack.interview_handler.converter import InterviewNoteProcessor


class TestInterviewNoteProcessor:
    """Test suite for InterviewNoteProcessor class."""

    def test_class_can_be_instantiated(self):
        """Test Step 1: Class can be instantiated."""
        converter = InterviewNoteProcessor()
        assert converter is not None
        assert isinstance(converter, InterviewNoteProcessor)

    def test_parse_header_title_and_date(self):
        """Test Step 2: Parse header (title and date)."""
        converter = InterviewNoteProcessor()
        markdown = """# Interview Notes - Test Domain
**Date**: 2025-11-15

## Interview Goal
Some goal text
"""
        result = converter.markdown_to_json(markdown)
        assert result["title"] == "Interview Notes - Test Domain"
        assert result["date"] == "2025-11-15"

    def test_parse_interview_goal(self):
        """Test Step 3: Parse interview goal."""
        converter = InterviewNoteProcessor()
        markdown = """# Interview Notes
**Date**: 2025-11-15

## Interview Goal
Extract and document expert knowledge on test domain.
"""
        result = converter.markdown_to_json(markdown)
        assert result["interview_goal"] == "Extract and document expert knowledge on test domain."

    def test_parse_single_topic(self):
        """Test Step 4: Parse single topic with all fields."""
        converter = InterviewNoteProcessor()
        markdown = """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: This is a test topic background.
**Status**: Not started
**Key Questions**:
1. What is the first question?
2. What is the second question?
**Listen for connections to**: Related topics

**Expert Insights**
*No insights captured yet*

**Current Understanding Level**
- **Completeness**: 0 %
- **Confidence**: Low
- **Next Steps**: Begin with opening questions
---
"""
        result = converter.markdown_to_json(markdown)
        assert len(result["topics"]) == 1
        topic = result["topics"][0]
        assert topic["topic_name"] == "Test Topic"
        assert topic["background"] == "This is a test topic background."
        assert topic["status"] == "not_started"
        assert len(topic["key_questions"]) == 2
        # Questions are now dicts with text and status
        assert topic["key_questions"][0]["text"] == "What is the first question?"
        assert topic["key_questions"][0]["status"] == "not_asked"
        assert topic["key_questions"][1]["text"] == "What is the second question?"
        assert topic["key_questions"][1]["status"] == "not_asked"
        assert topic["listen_for_connections"] == "Related topics"
        assert topic["expert_insights"] == "*No insights captured yet*"
        assert topic["current_understanding_level"]["completeness"] == 0
        assert topic["current_understanding_level"]["confidence"] == "Low"
        assert topic["current_understanding_level"]["next_steps"] == "Begin with opening questions"

    def test_parse_multiple_topics(self):
        """Test Step 5: Parse multiple topics."""
        converter = InterviewNoteProcessor()
        markdown = """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Topic One
**Background**: First topic
**Status**: Not started
**Key Questions**:
1. Question one?
---
### Topic Two
**Background**: Second topic
**Status**: In progress
**Key Questions**:
1. Question two?
---
"""
        result = converter.markdown_to_json(markdown)
        assert len(result["topics"]) == 2
        assert result["topics"][0]["topic_name"] == "Topic One"
        assert result["topics"][1]["topic_name"] == "Topic Two"
        assert result["topics"][1]["status"] == "in_progress"

    def test_parse_remaining_sections(self):
        """Test Step 6: Parse remaining sections."""
        converter = InterviewNoteProcessor()
        markdown = """# Interview Notes
**Date**: 2025-11-15

## Documents Found
Some documents found

## Relationship Exploration Prompts
- Prompt one
- Prompt two

## Follow-up Framework
- Can you tell me more?
- What's an example?

## Final Assessment
### Current Understanding Level
- **Overall Completeness**: 25 %
- **Overall Confidence**: Medium
- **Recommended Next Steps**: Continue interviews

### Expert Insight Summaries
Some summaries here
"""
        result = converter.markdown_to_json(markdown)
        assert result["documents_found"] == "Some documents found"
        assert len(result["relationship_exploration_prompts"]) == 2
        assert result["relationship_exploration_prompts"][0] == "- Prompt one"
        assert len(result["followup_framework"]) == 2
        assert result["followup_framework"][0] == "- Can you tell me more?"
        assert result["final_assessment"]["overall_completeness"] == 25
        assert result["final_assessment"]["overall_confidence"] == "Medium"
        assert result["final_assessment"]["recommended_next_steps"] == "Continue interviews"
        assert result["final_assessment"]["expert_insight_summaries"] == "Some summaries here"

    def test_json_to_markdown_header(self):
        """Test Step 7: JSON to markdown header."""
        converter = InterviewNoteProcessor()
        json_data = {
            "title": "Test Interview",
            "date": "2025-11-15",
            "interview_goal": "",
            "topics": [],
            "documents_found": "",
            "relationship_exploration_prompts": [],
            "followup_framework": [],
            "final_assessment": {},
        }
        markdown = converter.json_to_markdown(json_data)
        assert "# Test Interview" in markdown
        assert "**Date**: 2025-11-15" in markdown

    def test_json_to_markdown_full(self):
        """Test Step 8: JSON to markdown full document."""
        converter = InterviewNoteProcessor()
        json_data = {
            "title": "Test Interview",
            "date": "2025-11-15",
            "interview_goal": "Test goal",
            "topics": [
                {
                    "topic_name": "Test Topic",
                    "background": "Test background",
                    "status": "not_started",
                    "key_questions": [
                        {"text": "Question 1?", "status": "not_asked"},
                        {"text": "Question 2?", "status": "not_asked"},
                    ],
                    "listen_for_connections": "Connections",
                    "expert_insights": "Some insights",
                    "current_understanding_level": {
                        "completeness": 50,
                        "confidence": "Medium",
                        "next_steps": "Continue",
                    },
                }
            ],
            "documents_found": "No documents",
            "relationship_exploration_prompts": ["- Prompt 1"],
            "followup_framework": ["- Follow up 1"],
            "final_assessment": {
                "overall_completeness": 50,
                "overall_confidence": "Medium",
                "recommended_next_steps": "Continue",
                "expert_insight_summaries": "Summaries",
            },
        }
        markdown = converter.json_to_markdown(json_data)
        assert "# Test Interview" in markdown
        assert "## Interview Goal" in markdown
        assert "Test goal" in markdown
        assert "## Topics to Cover" in markdown
        assert "### Test Topic" in markdown
        assert "**Background**: Test background" in markdown
        assert "1. Question 1?" in markdown
        assert "2. Question 2?" in markdown
        assert "## Documents Found" in markdown
        assert "## Relationship Exploration Prompts" in markdown
        assert "## Follow-up Framework" in markdown
        assert "## Final Assessment" in markdown

    def test_round_trip_conversion(self):
        """Test Step 9: Round-trip conversion preserves structure."""
        converter = InterviewNoteProcessor()
        original_markdown = """# Interview Notes - Test
**Date**: 2025-11-15

## Interview Goal
Test goal text

## Topics to Cover

### Topic One
**Background**: Background text
**Status**: Not started
**Key Questions**:
1. Question one?
2. Question two?
**Listen for connections to**: Connections

**Expert Insights**
Some insights here

**Current Understanding Level**
- **Completeness**: 25 %
- **Confidence**: Medium
- **Next Steps**: Continue

---

## Documents Found
No documents

## Relationship Exploration Prompts
- Prompt one
- Prompt two

## Follow-up Framework
- Follow up one

## Final Assessment
### Current Understanding Level
- **Overall Completeness**: 25 %
- **Overall Confidence**: Medium
- **Recommended Next Steps**: Continue

### Expert Insight Summaries
Some summaries
"""
        # Convert to JSON and back
        json_data = converter.markdown_to_json(original_markdown)
        converted_markdown = converter.json_to_markdown(json_data)

        # Verify key elements are preserved
        assert "Interview Notes - Test" in converted_markdown
        assert "2025-11-15" in converted_markdown
        assert "Test goal text" in converted_markdown
        assert "Topic One" in converted_markdown
        assert "Question one?" in converted_markdown
        assert "Question two?" in converted_markdown

        # Verify JSON structure is correct
        assert json_data["title"] == "Interview Notes - Test"
        assert json_data["date"] == "2025-11-15"
        assert len(json_data["topics"]) == 1
        assert json_data["topics"][0]["topic_name"] == "Topic One"
        # Verify questions are in dict format
        questions = json_data["topics"][0]["key_questions"]
        assert isinstance(questions[0], dict)
        assert "text" in questions[0]
        assert "status" in questions[0]

    def test_from_file(self):
        """Test Step 10: from_file method."""
        converter = InterviewNoteProcessor()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("""# Test Interview
**Date**: 2025-11-15

## Interview Goal
Test goal
""")
            temp_path = f.name

        try:
            result = converter.from_file(temp_path)
            assert result["title"] == "Test Interview"
            assert result["date"] == "2025-11-15"
            assert result["interview_goal"] == "Test goal"
        finally:
            Path(temp_path).unlink()

    def test_to_file(self):
        """Test Step 10: to_file method."""
        converter = InterviewNoteProcessor()
        json_data = {
            "title": "Test Interview",
            "date": "2025-11-15",
            "interview_goal": "Test goal",
            "topics": [],
            "documents_found": "",
            "relationship_exploration_prompts": [],
            "followup_framework": [],
            "final_assessment": {},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_notes.md"
            converter.to_file(json_data, str(file_path))
            assert file_path.exists()
            content = file_path.read_text(encoding="utf-8")
            assert "# Test Interview" in content
            assert "2025-11-15" in content
            assert "Test goal" in content

    def test_file_not_found_error(self):
        """Test Step 11: Handle file not found."""
        converter = InterviewNoteProcessor()
        with pytest.raises(FileNotFoundError):
            converter.from_file("/nonexistent/path/file.md")

    def test_empty_markdown(self):
        """Test Step 11: Handle empty markdown."""
        converter = InterviewNoteProcessor()
        result = converter.markdown_to_json("")
        assert result["title"] == ""
        assert result["date"] == ""
        assert result["topics"] == []

    def test_missing_sections(self):
        """Test Step 11: Handle missing sections gracefully."""
        converter = InterviewNoteProcessor()
        markdown = """# Test Interview
**Date**: 2025-11-15
"""
        result = converter.markdown_to_json(markdown)
        assert result["title"] == "Test Interview"
        assert result["interview_goal"] == ""
        assert result["topics"] == []
        assert result["documents_found"] == ""

    def test_topic_status_variations(self):
        """Test Step 11: Handle different status formats."""
        converter = InterviewNoteProcessor()
        markdown = """# Test
**Date**: 2025-11-15

## Topics to Cover

### Topic Completed
**Status**: Completed
---
### Topic In Progress
**Status**: In progress
---
### Topic Not Started
**Status**: Not started
---
"""
        result = converter.markdown_to_json(markdown)
        assert result["topics"][0]["status"] == "completed"
        assert result["topics"][1]["status"] == "in_progress"
        assert result["topics"][2]["status"] == "not_started"

    def test_complex_insights_parsing(self):
        """Test Step 11: Parse complex expert insights."""
        converter = InterviewNoteProcessor()
        markdown = """# Test
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test
**Status**: Not started
**Key Questions**:
1. Question?
**Expert Insights**
- Insight one
- Insight two
  - Sub-insight
- Insight three

**Current Understanding Level**
- **Completeness**: 0 %
---
"""
        result = converter.markdown_to_json(markdown)
        assert len(result["topics"]) == 1
        insights = result["topics"][0]["expert_insights"]
        assert "Insight one" in insights
        assert "Insight two" in insights
        assert "Insight three" in insights


class TestQuestionStatus:
    """Test suite for QuestionStatus Enum and status marking mechanism."""

    def test_question_status_enum_exists(self):
        """Test Step 1: QuestionStatus Enum can be imported and has correct values."""
        from dana.studio.api.services.knowledge_pack.interview_handler.converter import QuestionStatus

        assert QuestionStatus is not None
        assert hasattr(QuestionStatus, "NOT_ASKED")
        assert hasattr(QuestionStatus, "ASKING")
        assert hasattr(QuestionStatus, "CLARIFYING")
        assert hasattr(QuestionStatus, "COMPLETED")

        # Verify enum values
        assert QuestionStatus.NOT_ASKED.value == "not_asked"
        assert QuestionStatus.ASKING.value == "asking"
        assert QuestionStatus.CLARIFYING.value == "clarifying"
        assert QuestionStatus.COMPLETED.value == "completed"

    def test_parse_question_with_status_bracket(self):
        """Test Step 2: Parse question with status bracket [asking]."""
        converter = InterviewNoteProcessor()
        markdown = """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test background
**Status**: Not started
**Key Questions**:
1. [asking] What is the first question?
2. [completed] What is the second question?
---
"""
        result = converter.markdown_to_json(markdown)
        assert len(result["topics"]) == 1
        questions = result["topics"][0]["key_questions"]
        assert len(questions) == 2
        assert questions[0]["text"] == "What is the first question?"
        assert questions[0]["status"] == "asking"
        assert questions[1]["text"] == "What is the second question?"
        assert questions[1]["status"] == "completed"

    def test_parse_question_without_status(self):
        """Test Step 3: Parse question without status bracket defaults to not_asked."""
        converter = InterviewNoteProcessor()
        markdown = """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test background
**Status**: Not started
**Key Questions**:
1. What is the first question?
2. What is the second question?
---
"""
        result = converter.markdown_to_json(markdown)
        questions = result["topics"][0]["key_questions"]
        assert questions[0]["text"] == "What is the first question?"
        assert questions[0]["status"] == "not_asked"
        assert questions[1]["text"] == "What is the second question?"
        assert questions[1]["status"] == "not_asked"

    def test_format_question_with_status(self):
        """Test Step 4: Format question with status bracket."""
        converter = InterviewNoteProcessor()
        json_data = {
            "title": "Test Interview",
            "date": "2025-11-15",
            "interview_goal": "",
            "topics": [
                {
                    "topic_name": "Test Topic",
                    "background": "Test background",
                    "status": "not_started",
                    "key_questions": [
                        {"text": "Question 1?", "status": "asking"},
                        {"text": "Question 2?", "status": "completed"},
                    ],
                    "listen_for_connections": "",
                    "expert_insights": "",
                    "current_understanding_level": {"completeness": 0, "confidence": "", "next_steps": ""},
                }
            ],
            "documents_found": "",
            "relationship_exploration_prompts": [],
            "followup_framework": [],
            "final_assessment": {},
        }
        markdown = converter.json_to_markdown(json_data)
        assert "1. [asking] Question 1?" in markdown
        assert "2. [completed] Question 2?" in markdown

    def test_format_question_without_status(self):
        """Test Step 5: Format question with not_asked status has no bracket."""
        converter = InterviewNoteProcessor()
        json_data = {
            "title": "Test Interview",
            "date": "2025-11-15",
            "interview_goal": "",
            "topics": [
                {
                    "topic_name": "Test Topic",
                    "background": "Test background",
                    "status": "not_started",
                    "key_questions": [
                        {"text": "Question 1?", "status": "not_asked"},
                        {"text": "Question 2?", "status": "asking"},
                    ],
                    "listen_for_connections": "",
                    "expert_insights": "",
                    "current_understanding_level": {"completeness": 0, "confidence": "", "next_steps": ""},
                }
            ],
            "documents_found": "",
            "relationship_exploration_prompts": [],
            "followup_framework": [],
            "final_assessment": {},
        }
        markdown = converter.json_to_markdown(json_data)
        assert "1. Question 1?" in markdown
        assert "[not_asked]" not in markdown  # Should not appear for not_asked
        assert "2. [asking] Question 2?" in markdown

    def test_json_structure_question_objects(self):
        """Test Step 6: JSON structure uses question objects with text and status."""
        converter = InterviewNoteProcessor()
        markdown = """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test
**Status**: Not started
**Key Questions**:
1. Question one?
2. [asking] Question two?
---
"""
        result = converter.markdown_to_json(markdown)
        questions = result["topics"][0]["key_questions"]
        assert isinstance(questions, list)
        assert isinstance(questions[0], dict)
        assert "text" in questions[0]
        assert "status" in questions[0]
        assert questions[0]["text"] == "Question one?"
        assert questions[0]["status"] == "not_asked"
        assert questions[1]["text"] == "Question two?"
        assert questions[1]["status"] == "asking"

    def test_backward_compatibility_string_questions(self):
        """Test Step 7: Backward compatibility - string questions convert to objects."""
        converter = InterviewNoteProcessor()
        # Test that old format (without status) still works
        markdown = """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test
**Status**: Not started
**Key Questions**:
1. Old format question?
---
"""
        result = converter.markdown_to_json(markdown)
        questions = result["topics"][0]["key_questions"]
        assert isinstance(questions[0], dict)
        assert questions[0]["text"] == "Old format question?"
        assert questions[0]["status"] == "not_asked"

    def test_find_question_exact_match(self):
        """Test Step 8: Find question in content with exact match."""
        converter = InterviewNoteProcessor()
        markdown = """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test
**Status**: Not started
**Key Questions**:
1. What is the exact question?
---
"""
        result = converter._find_question_in_content(markdown, "What is the exact question?")
        assert result is not None
        assert result[0] == "Test Topic"  # topic_name
        assert result[1] == 0  # question_index

    def test_find_question_fuzzy_match(self):
        """Test Step 9: Find question using fuzzy matching."""
        converter = InterviewNoteProcessor()
        markdown = """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test
**Status**: Not started
**Key Questions**:
1. What is the original question text here?
---
"""
        # Fuzzy match with slight variation
        result = converter._find_question_in_content(markdown, "What is the original question text?")
        assert result is not None
        assert result[0] == "Test Topic"

    def test_update_question_status_markdown(self):
        """Test Step 10: Update question status in markdown."""
        converter = InterviewNoteProcessor()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("""# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test
**Status**: Not started
**Key Questions**:
1. Question one?
---
""")
            temp_path = f.name

        try:
            from dana.studio.api.services.knowledge_pack.interview_handler.converter import QuestionStatus

            converter.update_question_status("Question one?", QuestionStatus.ASKING, temp_path)
            content = Path(temp_path).read_text(encoding="utf-8")
            assert "[asking] Question one?" in content
        finally:
            Path(temp_path).unlink()

    def test_update_question_status_json(self):
        """Test Step 11: Update question status persists in JSON."""
        converter = InterviewNoteProcessor()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("""# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test
**Status**: Not started
**Key Questions**:
1. Question one?
---
""")
            temp_path = f.name

        try:
            from dana.studio.api.services.knowledge_pack.interview_handler.converter import QuestionStatus

            converter.update_question_status("Question one?", QuestionStatus.ASKING, temp_path)
            result = converter.markdown_to_json(Path(temp_path).read_text(encoding="utf-8"))
            questions = result["topics"][0]["key_questions"]
            assert questions[0]["status"] == "asking"
        finally:
            Path(temp_path).unlink()

    def test_update_question_status_file_io(self):
        """Test Step 12: Update question status saves to file."""
        converter = InterviewNoteProcessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_notes.md"
            file_path.write_text(
                """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test
**Status**: Not started
**Key Questions**:
1. Question one?
---
""",
                encoding="utf-8",
            )

            from dana.studio.api.services.knowledge_pack.interview_handler.converter import QuestionStatus

            converter.update_question_status("Question one?", QuestionStatus.COMPLETED, str(file_path))
            content = file_path.read_text(encoding="utf-8")
            assert "[completed] Question one?" in content

    def test_error_question_not_found(self):
        """Test Step 13: Error handling when question not found."""
        converter = InterviewNoteProcessor()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("""# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test
**Status**: Not started
**Key Questions**:
1. Question one?
---
""")
            temp_path = f.name

        try:
            from dana.studio.api.services.knowledge_pack.interview_handler.converter import QuestionStatus

            with pytest.raises(ValueError, match="Question not found"):
                converter.update_question_status("Some random Non-existent question?", QuestionStatus.ASKING, temp_path)
        finally:
            Path(temp_path).unlink()

    def test_error_file_not_found(self):
        """Test Step 14: Error handling when file not found."""
        converter = InterviewNoteProcessor()
        from dana.studio.api.services.knowledge_pack.interview_handler.converter import QuestionStatus

        with pytest.raises(FileNotFoundError):
            converter.update_question_status("Question?", QuestionStatus.ASKING, "/nonexistent/path/file.md")

    def test_mark_question_as_asking(self):
        """Test Step 15: mark_question_as_asking helper method."""
        converter = InterviewNoteProcessor()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("""# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test
**Status**: Not started
**Key Questions**:
1. Question one?
---
""")
            temp_path = f.name

        try:
            converter.mark_question_as_asking("Question one?", temp_path)
            content = Path(temp_path).read_text(encoding="utf-8")
            assert "[asking] Question one?" in content
        finally:
            Path(temp_path).unlink()

    def test_mark_question_as_clarifying(self):
        """Test Step 16: mark_question_as_clarifying finds last asking question."""
        converter = InterviewNoteProcessor()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("""# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test
**Status**: Not started
**Key Questions**:
1. [asking] Question one?
2. Question two?
---
""")
            temp_path = f.name

        try:
            converter.mark_last_question_as_clarifying(temp_path)
            content = Path(temp_path).read_text(encoding="utf-8")
            assert "[clarifying] Question one?" in content
            assert "[asking]" not in content
        finally:
            Path(temp_path).unlink()

    def test_mark_question_as_completed(self):
        """Test Step 17: mark_question_as_completed helper method."""
        converter = InterviewNoteProcessor()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("""# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test
**Status**: Not started
**Key Questions**:
1. [asking] Question one?
---
""")
            temp_path = f.name

        try:
            converter.mark_question_as_completed("Question one?", temp_path)
            content = Path(temp_path).read_text(encoding="utf-8")
            assert "[completed] Question one?" in content
        finally:
            Path(temp_path).unlink()

    def test_round_trip_status_update(self):
        """Test Step 18: Round-trip status update persistence."""
        converter = InterviewNoteProcessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_notes.md"
            file_path.write_text(
                """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test
**Status**: Not started
**Key Questions**:
1. Question one?
---
""",
                encoding="utf-8",
            )

            from dana.studio.api.services.knowledge_pack.interview_handler.converter import QuestionStatus

            # Update status
            converter.update_question_status("Question one?", QuestionStatus.ASKING, str(file_path))

            # Read back and verify
            result = converter.from_file(str(file_path))
            questions = result["topics"][0]["key_questions"]
            assert questions[0]["status"] == "asking"

            # Update again
            converter.update_question_status("Question one?", QuestionStatus.COMPLETED, str(file_path))

            # Verify final state
            result = converter.from_file(str(file_path))
            questions = result["topics"][0]["key_questions"]
            assert questions[0]["status"] == "completed"

    def test_update_topic_status_not_started_to_in_progress(self):
        """Test: Update topic status from not_started to in_progress."""
        converter = InterviewNoteProcessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_notes.md"
            file_path.write_text(
                """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test background
**Status**: Not started
**Key Questions**:
1. Question one?
---
""",
                encoding="utf-8",
            )

            converter.update_topic_status("Test Topic", "in_progress", str(file_path))
            content = file_path.read_text(encoding="utf-8")
            assert "**Status**: In Progress" in content
            assert "**Status**: Not started" not in content

    def test_update_topic_status_in_progress_to_completed(self):
        """Test: Update topic status from in_progress to completed."""
        converter = InterviewNoteProcessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_notes.md"
            file_path.write_text(
                """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test background
**Status**: In Progress
**Key Questions**:
1. Question one?
---
""",
                encoding="utf-8",
            )

            converter.update_topic_status("Test Topic", "completed", str(file_path))
            content = file_path.read_text(encoding="utf-8")
            assert "**Status**: Completed" in content
            assert "**Status**: In Progress" not in content

    def test_update_topic_status_preserves_other_fields(self):
        """Test: Update topic status preserves other markdown fields."""
        converter = InterviewNoteProcessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_notes.md"
            file_path.write_text(
                """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Important background info
**Status**: Not started
**Key Questions**:
1. Question one?
**Listen for connections to**: Related topics

**Expert Insights**
Some insights here

**Current Understanding Level**
- **Completeness**: 0 %
- **Confidence**: Low
---
""",
                encoding="utf-8",
            )

            converter.update_topic_status("Test Topic", "in_progress", str(file_path))
            content = file_path.read_text(encoding="utf-8")
            assert "**Status**: In Progress" in content
            assert "**Background**: Important background info" in content
            assert "Question one?" in content
            assert "**Listen for connections to**: Related topics" in content
            assert "Some insights here" in content
            assert "**Completeness**: 0 %" in content

    def test_error_topic_not_found(self):
        """Test: Error handling when topic not found."""
        converter = InterviewNoteProcessor()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("""# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Status**: Not started
---
""")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Topic 'Non-existent Topic' not found"):
                converter.update_topic_status("Non-existent Topic", "in_progress", temp_path)
        finally:
            Path(temp_path).unlink()

    def test_error_file_not_found_topic_status(self):
        """Test: Error handling when file not found for update_topic_status."""
        converter = InterviewNoteProcessor()

        with pytest.raises(FileNotFoundError):
            converter.update_topic_status("Test Topic", "in_progress", "/nonexistent/path/file.md")

    def test_update_topic_completeness_zero_to_fifty(self):
        """Test: Update topic completeness from 0 to 50."""
        converter = InterviewNoteProcessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_notes.md"
            file_path.write_text(
                """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test background
**Status**: Not started
**Key Questions**:
1. Question one?

**Expert Insights**
*No insights captured yet*

**Current Understanding Level**
- **Completeness**: 0 %
- **Confidence**: Low
---
""",
                encoding="utf-8",
            )

            converter.update_topic_completeness("Test Topic", 50, str(file_path))
            content = file_path.read_text(encoding="utf-8")
            assert "- **Completeness**: 50 %" in content
            assert "- **Completeness**: 0 %" not in content

    def test_update_topic_completeness_fifty_to_hundred(self):
        """Test: Update topic completeness from 50 to 100."""
        converter = InterviewNoteProcessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_notes.md"
            file_path.write_text(
                """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test background
**Status**: In Progress
**Key Questions**:
1. Question one?

**Expert Insights**
Some insights

**Current Understanding Level**
- **Completeness**: 50 %
- **Confidence**: Medium
---
""",
                encoding="utf-8",
            )

            converter.update_topic_completeness("Test Topic", 100, str(file_path))
            content = file_path.read_text(encoding="utf-8")
            assert "- **Completeness**: 100 %" in content
            assert "- **Completeness**: 50 %" not in content

    def test_update_topic_completeness_preserves_other_fields(self):
        """Test: Update topic completeness preserves other markdown fields."""
        converter = InterviewNoteProcessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_notes.md"
            file_path.write_text(
                """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Important background info
**Status**: In Progress
**Key Questions**:
1. Question one?
**Listen for connections to**: Related topics

**Expert Insights**
Some insights here

**Current Understanding Level**
- **Completeness**: 25 %
- **Confidence**: Medium
- **Next Steps**: Continue exploring
---
""",
                encoding="utf-8",
            )

            converter.update_topic_completeness("Test Topic", 75, str(file_path))
            content = file_path.read_text(encoding="utf-8")
            assert "- **Completeness**: 75 %" in content
            assert "**Background**: Important background info" in content
            assert "Question one?" in content
            assert "**Listen for connections to**: Related topics" in content
            assert "Some insights here" in content
            assert "- **Confidence**: Medium" in content
            assert "- **Next Steps**: Continue exploring" in content

    def test_error_topic_not_found_completeness(self):
        """Test: Error handling when topic not found for update_topic_completeness."""
        converter = InterviewNoteProcessor()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("""# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Status**: Not started
---
""")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Topic 'Non-existent Topic' not found"):
                converter.update_topic_completeness("Non-existent Topic", 50, temp_path)
        finally:
            Path(temp_path).unlink()

    def test_error_file_not_found_topic_completeness(self):
        """Test: Error handling when file not found for update_topic_completeness."""
        converter = InterviewNoteProcessor()

        with pytest.raises(FileNotFoundError):
            converter.update_topic_completeness("Test Topic", 50, "/nonexistent/path/file.md")

    def test_recalculate_topic_progress_all_completed(self):
        """Test: Recalculate topic progress when all questions are completed."""
        converter = InterviewNoteProcessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_notes.md"
            file_path.write_text(
                """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test background
**Status**: Not started
**Key Questions**:
1. [completed] Question one?
2. [completed] Question two?
3. [completed] Question three?

**Expert Insights**
*No insights captured yet*

**Current Understanding Level**
- **Completeness**: 0 %
- **Confidence**: Low
---
""",
                encoding="utf-8",
            )

            converter.recalculate_topic_progress("Test Topic", str(file_path))
            content = file_path.read_text(encoding="utf-8")
            assert "**Status**: Completed" in content
            assert "- **Completeness**: 100 %" in content

    def test_recalculate_topic_progress_some_completed(self):
        """Test: Recalculate topic progress when some questions are completed."""
        converter = InterviewNoteProcessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_notes.md"
            file_path.write_text(
                """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test background
**Status**: Not started
**Key Questions**:
1. [completed] Question one?
2. [completed] Question two?
3. Question three?

**Expert Insights**
*No insights captured yet*

**Current Understanding Level**
- **Completeness**: 0 %
- **Confidence**: Low
---
""",
                encoding="utf-8",
            )

            converter.recalculate_topic_progress("Test Topic", str(file_path))
            content = file_path.read_text(encoding="utf-8")
            assert "**Status**: In Progress" in content
            assert "- **Completeness**: 66 %" in content or "- **Completeness**: 67 %" in content

    def test_recalculate_topic_progress_none_completed(self):
        """Test: Recalculate topic progress when no questions are completed."""
        converter = InterviewNoteProcessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_notes.md"
            file_path.write_text(
                """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test background
**Status**: In Progress
**Key Questions**:
1. [asking] Question one?
2. Question two?
3. Question three?

**Expert Insights**
*No insights captured yet*

**Current Understanding Level**
- **Completeness**: 50 %
- **Confidence**: Medium
---
""",
                encoding="utf-8",
            )

            converter.recalculate_topic_progress("Test Topic", str(file_path))
            content = file_path.read_text(encoding="utf-8")
            assert "**Status**: Not started" in content
            assert "- **Completeness**: 0 %" in content

    def test_recalculate_topic_progress_empty_topic(self):
        """Test: Recalculate topic progress for topic with no questions."""
        converter = InterviewNoteProcessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_notes.md"
            file_path.write_text(
                """# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Background**: Test background
**Status**: Not started
**Key Questions**:

**Expert Insights**
*No insights captured yet*

**Current Understanding Level**
- **Completeness**: 0 %
- **Confidence**: Low
---
""",
                encoding="utf-8",
            )

            converter.recalculate_topic_progress("Test Topic", str(file_path))
            content = file_path.read_text(encoding="utf-8")
            assert "**Status**: Not started" in content
            assert "- **Completeness**: 0 %" in content

    def test_error_topic_not_found_recalculate(self):
        """Test: Error handling when topic not found for recalculate_topic_progress."""
        converter = InterviewNoteProcessor()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("""# Interview Notes
**Date**: 2025-11-15

## Topics to Cover

### Test Topic
**Status**: Not started
---
""")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Topic 'Non-existent Topic' not found"):
                converter.recalculate_topic_progress("Non-existent Topic", temp_path)
        finally:
            Path(temp_path).unlink()
