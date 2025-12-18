"""
Interview Note Markdown to JSON Converter.

Provides bidirectional conversion between interview_notes.md and JSON format.
"""

import re
from enum import StrEnum
from pathlib import Path
from typing import Any

from dana.studio.api.services.knowledge_pack.interview_handler.utils import similarity_ratio
from dana.studio.api.services.search.bm25 import BM25SearchEngine


class QuestionStatus(StrEnum):
    """Enum for question status values.

    Includes both new system statuses (asking, clarifying, completed) and
    old system statuses (being_asked, answered, skipped) for full compatibility.
    """

    NOT_ASKED = "not_asked"
    ASKING = "asking"
    CLARIFYING = "clarifying"
    COMPLETED = "completed"
    # Old system statuses for backward compatibility
    BEING_ASKED = "being_asked"
    ANSWERED = "answered"
    SKIPPED = "skipped"


class InterviewNoteProcessor:
    """Converter for interview notes between markdown and JSON formats."""

    def __init__(self):
        """Initialize the converter."""
        pass

    def markdown_to_json(self, markdown_content: str) -> dict[str, Any]:
        """
        Parse markdown interview notes to structured JSON.

        Args:
            markdown_content: The markdown content of interview_notes.md

        Returns:
            Dictionary with structured interview note data
        """
        if not markdown_content:
            return self._empty_json_structure()

        result = self._empty_json_structure()

        # Parse header (title and date)
        title_match = re.search(r"^#\s+(.+?)$", markdown_content, re.MULTILINE)
        if title_match:
            result["title"] = title_match.group(1).strip()

        date_match = re.search(r"\*\*Date\*\*:\s*(.+?)(?:\n|$)", markdown_content, re.MULTILINE)
        if date_match:
            result["date"] = date_match.group(1).strip()

        # Parse interview goal
        goal_match = re.search(r"## Interview Goal\s*\n(.+?)(?=\n##|\Z)", markdown_content, re.DOTALL)
        if goal_match:
            result["interview_goal"] = goal_match.group(1).strip()

        # Parse topics
        result["topics"] = self._parse_topics(markdown_content)

        # Parse documents found
        documents_match = re.search(r"## Documents Found\s*\n(.+?)(?=\n##|\Z)", markdown_content, re.DOTALL)
        if documents_match:
            result["documents_found"] = documents_match.group(1).strip()

        # Parse relationship exploration prompts
        prompts_match = re.search(r"## Relationship Exploration Prompts\s*\n(.+?)(?=\n##|\Z)", markdown_content, re.DOTALL)
        if prompts_match:
            prompts_text = prompts_match.group(1).strip()
            result["relationship_exploration_prompts"] = [
                line.strip() for line in prompts_text.split("\n") if line.strip() and line.strip().startswith("-")
            ]

        # Parse follow-up framework
        framework_match = re.search(r"## Follow-up Framework\s*\n(.+?)(?=\n##|\Z)", markdown_content, re.DOTALL)
        if framework_match:
            framework_text = framework_match.group(1).strip()
            result["followup_framework"] = [
                line.strip() for line in framework_text.split("\n") if line.strip() and line.strip().startswith("-")
            ]

        # Parse final assessment
        assessment_match = re.search(r"## Final Assessment\s*\n(.+?)(?=\Z)", markdown_content, re.DOTALL)
        if assessment_match:
            assessment_text = assessment_match.group(1)
            result["final_assessment"] = self._parse_final_assessment(assessment_text)

        return result

    def json_to_markdown(self, json_data: dict[str, Any]) -> str:
        """
        Convert JSON data back to markdown format.

        Args:
            json_data: Dictionary with structured interview note data

        Returns:
            Markdown formatted string
        """
        lines = []

        # Header
        title = json_data.get("title", "Interview Notes")
        date = json_data.get("date", "")
        lines.append(f"# {title}")
        if date:
            lines.append(f"**Date**: {date}")
        lines.append("")

        # Interview Goal
        goal = json_data.get("interview_goal", "")
        if goal:
            lines.append("## Interview Goal")
            lines.append(goal)
            lines.append("")

        # Topics to Cover
        topics = json_data.get("topics", [])
        if topics:
            lines.append("## Topics to Cover")
            lines.append("")
            for topic in topics:
                lines.extend(self._format_topic(topic))
                lines.append("")

        # Documents Found
        documents = json_data.get("documents_found", "")
        if documents:
            lines.append("## Documents Found")
            lines.append(documents)
            lines.append("")

        # Relationship Exploration Prompts
        prompts = json_data.get("relationship_exploration_prompts", [])
        if prompts:
            lines.append("## Relationship Exploration Prompts")
            for prompt in prompts:
                lines.append(prompt)
            lines.append("")

        # Follow-up Framework
        framework = json_data.get("followup_framework", [])
        if framework:
            lines.append("## Follow-up Framework")
            for item in framework:
                lines.append(item)
            lines.append("")

        # Final Assessment
        assessment = json_data.get("final_assessment", {})
        if assessment:
            lines.append("## Final Assessment")
            lines.extend(self._format_final_assessment(assessment))
            lines.append("")

        return "\n".join(lines)

    def from_file(self, file_path: str) -> dict[str, Any]:
        """
        Load and parse interview notes from a file.

        Args:
            file_path: Path to the interview_notes.md file

        Returns:
            Dictionary with structured interview note data
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Interview notes file not found: {file_path}")

        with open(path, encoding="utf-8") as f:
            content = f.read()

        return self.markdown_to_json(content)

    def to_file(self, json_data: dict[str, Any], file_path: str) -> None:
        """
        Write JSON data as markdown to a file.

        Args:
            json_data: Dictionary with structured interview note data
            file_path: Path where to write the interview_notes.md file
        """
        markdown_content = self.json_to_markdown(json_data)
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

    def _empty_json_structure(self) -> dict[str, Any]:
        """Return empty JSON structure."""
        return {
            "title": "",
            "date": "",
            "interview_goal": "",
            "topics": [],
            "documents_found": "",
            "relationship_exploration_prompts": [],
            "followup_framework": [],
            "final_assessment": {
                "overall_completeness": 0,
                "overall_confidence": "",
                "recommended_next_steps": "",
                "expert_insight_summaries": "",
            },
        }

    def _parse_topics(self, content: str) -> list[dict[str, Any]]:
        """Parse all topics from markdown content."""
        topics = []
        topic_pattern = r"### ([^\n]+)"
        topic_matches = list(re.finditer(topic_pattern, content))

        for i, match in enumerate(topic_matches):
            topic_name = match.group(1).strip()

            if "expert insight" in topic_name.lower() or "understanding level" in topic_name.lower():
                continue

            # Find the full section content
            start_pos = match.start()
            if i + 1 < len(topic_matches):
                end_pos = topic_matches[i + 1].start()
            else:
                end_pos = len(content)

            topic_section = content[start_pos:end_pos]
            topic_data = self._parse_single_topic(topic_name, topic_section)
            topics.append(topic_data)

        return topics

    def _parse_single_topic(self, topic_name: str, topic_section: str) -> dict[str, Any]:
        """Parse a single topic section."""
        topic = {
            "topic_name": topic_name,
            "background": "",
            "status": "not_started",
            "key_questions": [],
            "listen_for_connections": "",
            "expert_insights": "",
            "current_understanding_level": {
                "completeness": 0,
                "confidence": "",
                "next_steps": "",
            },
        }

        # Extract background
        background_match = re.search(r"\*\*Background\*\*:\s*(.+?)(?:\n\*\*|\Z)", topic_section, re.DOTALL)
        if background_match:
            topic["background"] = background_match.group(1).strip()

        # Extract status
        status_match = re.search(r"\*\*Status\*\*:\s*(.+?)(?:\n|$)", topic_section)
        if status_match:
            status_text = status_match.group(1).strip().lower()
            if "completed" in status_text:
                topic["status"] = "completed"
            elif "in progress" in status_text or "in-progress" in status_text:
                topic["status"] = "in_progress"
            elif "not started" in status_text:
                topic["status"] = "not_started"

        # Extract key questions
        questions_match = re.search(r"\*\*Key Questions\*\*:\s*(.+?)(?=\n\*\*|\Z)", topic_section, re.DOTALL)
        if questions_match:
            questions_text = questions_match.group(1).strip()
            # Try numbered list format with optional status bracket: "1. [status] Question text?" or "1. Question text?"
            question_items = re.findall(r"\d+\.\s*(?:\[(\w+)\]\s*)?(.+?)(?=\n\d+\.|\n---|\Z)", questions_text, re.DOTALL)
            if question_items:
                topic["key_questions"] = [
                    {"text": q.strip().rstrip("\n---").strip(), "status": status.strip() if status else QuestionStatus.NOT_ASKED.value}
                    for status, q in question_items
                    if q.strip()
                ]
            else:
                # Try bullet points with optional status
                question_items = re.findall(r"^[-*]\s*(?:\[(\w+)\]\s*)?(.+?)(?=\n[-*]|\n---|$)", questions_text, re.MULTILINE)
                if question_items:
                    topic["key_questions"] = [
                        {"text": q.strip().rstrip("\n---").strip(), "status": status.strip() if status else QuestionStatus.NOT_ASKED.value}
                        for status, q in question_items
                        if q.strip()
                    ]

        # Extract listen for connections
        connections_match = re.search(r"\*\*Listen for connections to\*\*:\s*(.+?)(?:\n\*\*|\Z)", topic_section, re.DOTALL)
        if connections_match:
            topic["listen_for_connections"] = connections_match.group(1).strip()

        # Extract expert insights
        insights_match = re.search(r"\*\*Expert Insights\*\*[:\s]*\n(.*?)(?=\n\*\*[A-Z]|\Z)", topic_section, re.DOTALL)
        if insights_match:
            topic["expert_insights"] = insights_match.group(1).strip()

        # Extract current understanding level
        understanding_match = re.search(r"\*\*Current Understanding Level\*\*[:\s]*\n(.*?)(?=\n---|\n###|\Z)", topic_section, re.DOTALL)
        if understanding_match:
            understanding_text = understanding_match.group(1)
            # Extract completeness (format: "**Completeness**: 0 % – Interview just started")
            completeness_match = re.search(r"\*\*Completeness\*\*:\s*(\d+)", understanding_text)
            if completeness_match:
                topic["current_understanding_level"]["completeness"] = int(completeness_match.group(1))

            # Extract confidence
            confidence_match = re.search(r"\*\*Confidence\*\*:\s*(.+?)(?:\n|$)", understanding_text)
            if confidence_match:
                topic["current_understanding_level"]["confidence"] = confidence_match.group(1).strip()

            # Extract next steps
            next_steps_match = re.search(r"\*\*Next Steps\*\*:\s*(.+?)(?:\n|$)", understanding_text)
            if next_steps_match:
                topic["current_understanding_level"]["next_steps"] = next_steps_match.group(1).strip()

        return topic

    def _parse_final_assessment(self, assessment_text: str) -> dict[str, Any]:
        """Parse final assessment section."""
        assessment = {
            "overall_completeness": 0,
            "overall_confidence": "",
            "recommended_next_steps": "",
            "expert_insight_summaries": "",
        }

        # Extract overall completeness
        completeness_match = re.search(r"\*\*Overall Completeness\*\*:\s*(\d+)", assessment_text)
        if completeness_match:
            assessment["overall_completeness"] = int(completeness_match.group(1))

        # Extract overall confidence
        confidence_match = re.search(r"\*\*Overall Confidence\*\*:\s*(.+?)(?:\n|$)", assessment_text)
        if confidence_match:
            assessment["overall_confidence"] = confidence_match.group(1).strip()

        # Extract recommended next steps
        next_steps_match = re.search(r"\*\*Recommended Next Steps\*\*:\s*(.+?)(?:\n###|\Z)", assessment_text, re.DOTALL)
        if next_steps_match:
            assessment["recommended_next_steps"] = next_steps_match.group(1).strip()

        # Extract expert insight summaries
        summaries_match = re.search(r"### Expert Insight Summaries\s*\n(.+?)(?=\Z)", assessment_text, re.DOTALL)
        if summaries_match:
            assessment["expert_insight_summaries"] = summaries_match.group(1).strip()

        return assessment

    def _format_topic(self, topic: dict[str, Any]) -> list[str]:
        """Format a topic as markdown."""
        lines = []
        lines.append(f"### {topic.get('topic_name', '')}")

        background = topic.get("background", "")
        if background:
            lines.append(f"**Background**: {background}")

        status = topic.get("status", "not_started")
        status_display = status.replace("_", " ").title()
        lines.append(f"**Status**: {status_display}")

        questions = topic.get("key_questions", [])
        if questions:
            lines.append("**Key Questions**:")
            for i, question in enumerate(questions, 1):
                # Handle both dict format (with status) and string format (backward compatibility)
                if isinstance(question, dict):
                    status = question.get("status", QuestionStatus.NOT_ASKED.value)
                    text = question.get("text", question.get("question_text", ""))
                    if status and status != QuestionStatus.NOT_ASKED.value:
                        lines.append(f"{i}. [{status}] {text}")
                    else:
                        lines.append(f"{i}. {text}")
                else:
                    # Backward compatibility: string format
                    lines.append(f"{i}. {question}")

        connections = topic.get("listen_for_connections", "")
        if connections:
            lines.append(f"**Listen for connections to**: {connections}")

        lines.append("")
        lines.append("**Expert Insights**")
        insights = topic.get("expert_insights", "")
        if insights:
            lines.append(insights)
        else:
            lines.append("*No insights captured yet*")

        lines.append("")
        lines.append("**Current Understanding Level**")
        understanding = topic.get("current_understanding_level", {})
        completeness = understanding.get("completeness", 0)
        confidence = understanding.get("confidence", "")
        next_steps = understanding.get("next_steps", "")

        lines.append(f"- **Completeness**: {completeness} %")
        if confidence:
            lines.append(f"- **Confidence**: {confidence}")
        if next_steps:
            lines.append(f"- **Next Steps**: {next_steps}")

        lines.append("")
        lines.append("---")

        return lines

    def _format_final_assessment(self, assessment: dict[str, Any]) -> list[str]:
        """Format final assessment as markdown."""
        lines = []
        lines.append("### Current Understanding Level")

        completeness = assessment.get("overall_completeness", 0)
        confidence = assessment.get("overall_confidence", "")
        next_steps = assessment.get("recommended_next_steps", "")

        lines.append(f"- **Overall Completeness**: {completeness} %")
        if confidence:
            lines.append(f"- **Overall Confidence**: {confidence}")
        if next_steps:
            lines.append(f"- **Recommended Next Steps**: {next_steps}")

        lines.append("")
        lines.append("### Expert Insight Summaries")
        summaries = assessment.get("expert_insight_summaries", "")
        if summaries:
            lines.append(summaries)
        else:
            lines.append("*No insights captured yet – to be completed as interview progresses*")

        return lines

    def _find_question_in_content(self, markdown_content: str, question_text: str) -> tuple[str, int] | None:
        """
        Find question in markdown content using BM25 search then similarity matching.

        Args:
            markdown_content: The markdown content to search
            question_text: The question text to find

        Returns:
            Tuple of (topic_name, question_index) or None if not found
        """
        # Parse to get topics and questions
        json_data = self.markdown_to_json(markdown_content)

        # Build question corpus with metadata for tracking
        question_corpus = []
        question_metadata = []  # List of (topic_name, question_index, question_text)

        for topic in json_data.get("topics", []):
            questions = topic.get("key_questions", [])
            for idx, question in enumerate(questions):
                # Handle both dict and string formats
                if isinstance(question, dict):
                    q_text = question.get("text", question.get("question_text", ""))
                else:
                    q_text = str(question)

                question_corpus.append(q_text)
                question_metadata.append((topic["topic_name"], idx, q_text))

        if not question_corpus:
            return None

        # Use BM25 to get top 3 candidates
        search_engine = BM25SearchEngine(question_corpus)
        top_indices = search_engine.get_top_n_indices(question_text, n=3)

        # Check exact match first
        for idx in top_indices:
            topic_name, question_idx, q_text = question_metadata[idx]
            if q_text.strip().lower() == question_text.strip().lower():
                return (topic_name, question_idx)

        # Check similarity ratio for top 3 results
        best_match = None
        best_similarity = 0.0
        best_topic_name = None
        best_index = -1

        for idx in top_indices:
            topic_name, question_idx, q_text = question_metadata[idx]
            similarity = similarity_ratio(q_text, question_text)
            if similarity > best_similarity and similarity > 0.5:  # Threshold for matching
                best_similarity = similarity
                best_match = q_text
                best_topic_name = topic_name
                best_index = question_idx

        if best_match and best_topic_name is not None:
            return (best_topic_name, best_index)
        return None

    def update_question_status(self, question_text: str, status: QuestionStatus, note_path: str) -> None:
        """
        Update question status in both markdown and JSON formats.

        Args:
            question_text: The question text to update
            status: The new status (QuestionStatus enum)
            note_path: Path to the interview_notes.md file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If question not found
        """
        path = Path(note_path)
        if not path.exists():
            raise FileNotFoundError(f"Interview notes file not found: {note_path}")

        # Load markdown content
        with open(path, encoding="utf-8") as f:
            markdown_content = f.read()

        # Find question
        result = self._find_question_in_content(markdown_content, question_text)
        if not result:
            raise ValueError(f"Question not found: {question_text}")

        topic_name, question_index = result

        # Find the topic section in markdown
        topic_pattern = rf"### {re.escape(topic_name)}\s*\n(.*?)(?=\n### |\n## |\Z)"
        topic_match = re.search(topic_pattern, markdown_content, re.DOTALL)
        if not topic_match:
            raise ValueError(f"Topic '{topic_name}' not found in markdown")

        topic_section = topic_match.group(0)
        topic_start = topic_match.start()
        topic_end = topic_match.end()

        # Find the questions section within the topic
        questions_match = re.search(r"\*\*Key Questions\*\*:\s*\n(.*?)(?=\n\*\*|\Z)", topic_section, re.DOTALL)
        if not questions_match:
            raise ValueError(f"Key Questions section not found in topic '{topic_name}'")

        questions_text = questions_match.group(1)

        # Parse questions to find the one to update
        # Pattern matches: "1. [status] question text" or "1. question text"
        question_lines = re.findall(r"(\d+\.\s*(?:\[(\w+)\]\s*)?(.+?))(?=\n\d+\.|\Z)", questions_text, re.DOTALL)

        if question_index >= len(question_lines):
            raise ValueError(f"Question index {question_index} out of range")

        # Get the question content (text without status)
        question_content = question_lines[question_index][2].strip()

        # Build new question line
        if status.value == QuestionStatus.NOT_ASKED.value:
            new_question_line = f"{question_index + 1}. {question_content}"
        else:
            new_question_line = f"{question_index + 1}. [{status.value}] {question_content}"

        # Split questions_text into lines and replace the specific line
        # Find all question line positions
        question_positions = []
        for match in re.finditer(r"\d+\.\s*(?:\[(\w+)\]\s*)?(.+?)(?=\n\d+\.|\Z)", questions_text, re.DOTALL):
            question_positions.append((match.start(), match.end(), match.group(0)))

        if question_index >= len(question_positions):
            raise ValueError(f"Question index {question_index} out of range")

        # Replace the specific question line
        old_start, old_end, old_line = question_positions[question_index]
        updated_questions_text = questions_text[:old_start] + new_question_line + questions_text[old_end:]

        # Replace questions section in topic
        questions_start = questions_match.start(1)
        questions_end = questions_match.end(1)
        updated_topic_section = topic_section[:questions_start] + updated_questions_text + topic_section[questions_end:]

        # Replace topic section in full markdown
        updated_markdown = markdown_content[:topic_start] + updated_topic_section + markdown_content[topic_end:]

        # Write back to file
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated_markdown)

    def get_question_status(self, question_text: str, note_path: str) -> QuestionStatus | None:
        path = Path(note_path)
        if not path.exists():
            raise FileNotFoundError(f"Interview notes file not found: {note_path}")

        # Load markdown content
        with open(path, encoding="utf-8") as f:
            markdown_content = f.read()

        actual_question = self._find_question_in_content(markdown_content, question_text)
        if not actual_question:
            return None

        topic_name, question_index = actual_question

        # Find the question in the markdown content
        note_data = self.markdown_to_json(markdown_content)
        for topic in note_data.get("topics", []):
            if topic.get("topic_name") == topic_name:
                return topic.get("key_questions", [])[question_index].get("status", None)
        return None

    def mark_question_as_asking(self, question_text: str, note_path: str) -> None:
        """
        Mark a question as asking (interview_note question being asked).

        Args:
            question_text: The question text to mark
            note_path: Path to the interview_notes.md file
        """
        self.update_question_status(question_text, QuestionStatus.ASKING, note_path)

    def mark_question_as_clarifying(self, question_text: str, note_path: str) -> None:
        """
        Mark a question as clarifying (followup question being asked).

        Args:
            question_text: The question text to mark
            note_path: Path to the interview_notes.md file
        """
        self.update_question_status(question_text, QuestionStatus.CLARIFYING, note_path)

    def mark_last_question_as_clarifying(self, note_path: str) -> None:
        """
        Mark the last asking question as clarifying (followup question being asked).

        Args:
            note_path: Path to the interview_notes.md file

        Raises:
            ValueError: If no asking question found
        """
        path = Path(note_path)
        if not path.exists():
            raise FileNotFoundError(f"Interview notes file not found: {note_path}")

        # Load markdown content
        with open(path, encoding="utf-8") as f:
            markdown_content = f.read()

        # Find all topics and their questions
        json_data = self.markdown_to_json(markdown_content)

        # Find the last question with asking status
        last_asking_question = None

        for topic in json_data.get("topics", []):
            questions = topic.get("key_questions", [])
            for question in questions:
                if isinstance(question, dict):
                    if question.get("status") == QuestionStatus.ASKING.value:
                        last_asking_question = question.get("text", "")

        if not last_asking_question:
            raise ValueError("No asking question found to mark as clarifying")

        # Update to clarifying
        self.update_question_status(last_asking_question, QuestionStatus.CLARIFYING, note_path)

    def mark_question_as_completed(self, question_text: str, note_path: str) -> None:
        """
        Mark a question as completed (moved to next question).

        Args:
            question_text: The question text to mark
            note_path: Path to the interview_notes.md file
        """
        self.update_question_status(question_text, QuestionStatus.COMPLETED, note_path)

    def update_topic_status(self, topic_name: str, status: str, note_path: str) -> None:
        """
        Update topic status in markdown file.

        Args:
            topic_name: The topic name to update
            status: The new status ("not_started", "in_progress", "completed")
            note_path: Path to the interview_notes.md file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If topic not found
        """
        path = Path(note_path)
        if not path.exists():
            raise FileNotFoundError(f"Interview notes file not found: {note_path}")

        # Load markdown content
        with open(path, encoding="utf-8") as f:
            markdown_content = f.read()

        # Find the topic section in markdown
        topic_pattern = rf"### {re.escape(topic_name)}\s*\n(.*?)(?=\n### |\n## |\Z)"
        topic_match = re.search(topic_pattern, markdown_content, re.DOTALL)
        if not topic_match:
            raise ValueError(f"Topic '{topic_name}' not found in markdown")

        topic_section = topic_match.group(0)

        # Find the status line
        status_match = re.search(r"\*\*Status\*\*:\s*(.+?)(?:\n|$)", topic_section)
        if not status_match:
            raise ValueError(f"Status field not found in topic '{topic_name}'")

        # Map status values to display format
        status_display_map = {
            "not_started": "Not started",
            "in_progress": "In Progress",
            "completed": "Completed",
        }
        status_display = status_display_map.get(status, status.replace("_", " ").title())

        # Replace the status line
        updated_topic_section = topic_section.replace(status_match.group(0), f"**Status**: {status_display}\n")
        updated_markdown = markdown_content.replace(topic_section, updated_topic_section)

        # Write back to file
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated_markdown)

    def update_topic_completeness(self, topic_name: str, completeness: int, note_path: str) -> None:
        """
        Update topic completeness percentage in markdown file.

        Args:
            topic_name: The topic name to update
            completeness: The new completeness percentage (0-100)
            note_path: Path to the interview_notes.md file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If topic not found
        """
        path = Path(note_path)
        if not path.exists():
            raise FileNotFoundError(f"Interview notes file not found: {note_path}")

        # Load markdown content
        with open(path, encoding="utf-8") as f:
            markdown_content = f.read()

        # Find the topic section in markdown
        topic_pattern = rf"### {re.escape(topic_name)}\s*\n(.*?)(?=\n### |\n## |\Z)"
        topic_match = re.search(topic_pattern, markdown_content, re.DOTALL)
        if not topic_match:
            raise ValueError(f"Topic '{topic_name}' not found in markdown")

        topic_section = topic_match.group(0)
        topic_start = topic_match.start()
        topic_end = topic_match.end()

        # Find the "Current Understanding Level" section
        understanding_match = re.search(r"\*\*Current Understanding Level\*\*[:\s]*\n(.*?)(?=\n---|\n###|\Z)", topic_section, re.DOTALL)
        if not understanding_match:
            raise ValueError(f"Current Understanding Level section not found in topic '{topic_name}'")

        understanding_text = understanding_match.group(1)

        # Find the completeness line
        completeness_match = re.search(r"-\s*\*\*Completeness\*\*:\s*(\d+)\s*%", understanding_text)
        if not completeness_match:
            raise ValueError(f"Completeness field not found in topic '{topic_name}'")

        # Replace the completeness value
        completeness_start = completeness_match.start()
        completeness_end = completeness_match.end()
        new_completeness_line = f"- **Completeness**: {completeness} %"
        updated_understanding_text = understanding_text[:completeness_start] + new_completeness_line + understanding_text[completeness_end:]

        # Replace understanding section in topic
        updated_topic_section = (
            topic_section[: understanding_match.start(1)] + updated_understanding_text + topic_section[understanding_match.end(1) :]
        )

        # Replace topic section in full markdown
        updated_markdown = markdown_content[:topic_start] + updated_topic_section + markdown_content[topic_end:]

        # Write back to file
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated_markdown)

    def update_topic_expert_insights(self, topic_name: str, insights: str, note_path: str) -> None:
        """
        Update expert insights for a topic in markdown file.

        Args:
            topic_name: The topic name to update
            insights: The new expert insights content (can be markdown formatted)
            note_path: Path to the interview_notes.md file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If topic not found
        """
        path = Path(note_path)
        if not path.exists():
            raise FileNotFoundError(f"Interview notes file not found: {note_path}")

        json_data = self.from_file(str(note_path))
        for topic in json_data.get("topics", []):
            if topic.get("topic_name") == topic_name:
                topic["expert_insights"] = insights
                break

        self.to_file(json_data, str(note_path))

    def _get_topic_name_for_question(self, question_text: str, note_path: str) -> str | None:
        """
        Get topic name for a given question text.

        Args:
            question_text: The question text to find
            note_path: Path to the interview_notes.md file

        Returns:
            Topic name if found, None otherwise
        """
        path = Path(note_path)
        if not path.exists():
            return None

        with open(path, encoding="utf-8") as f:
            markdown_content = f.read()

        result = self._find_question_in_content(markdown_content, question_text)
        if result:
            return result[0]
        return None

    def recalculate_topic_progress(self, topic_name: str, note_path: str) -> None:
        """
        Recalculate and update topic status and completeness based on question statuses.

        Args:
            topic_name: The topic name to recalculate
            note_path: Path to the interview_notes.md file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If topic not found
        """
        path = Path(note_path)
        if not path.exists():
            raise FileNotFoundError(f"Interview notes file not found: {note_path}")

        # Parse markdown to get topic data
        json_data = self.from_file(str(note_path))

        # Find the topic
        topic_data = None
        for topic in json_data.get("topics", []):
            if topic.get("topic_name") == topic_name:
                topic_data = topic
                break

        if not topic_data:
            raise ValueError(f"Topic '{topic_name}' not found in markdown")

        # Get all questions for the topic
        questions = topic_data.get("key_questions", [])

        # Count completed questions
        total_questions = len(questions)
        completed_count = 0

        for question in questions:
            if isinstance(question, dict):
                status = question.get("status", QuestionStatus.NOT_ASKED.value)
                if status == QuestionStatus.COMPLETED.value:
                    completed_count += 1
            # String format questions are treated as not_asked

        # Calculate completeness percentage
        if total_questions > 0:
            completeness = int((completed_count / total_questions) * 100)
        else:
            completeness = 0

        # Determine status
        if total_questions == 0:
            status = "not_started"
        elif completed_count == total_questions:
            status = "completed"
        elif completed_count > 0:
            status = "in_progress"
        else:
            status = "not_started"

        # Update status and completeness
        self.update_topic_status(topic_name, status, str(note_path))
        self.update_topic_completeness(topic_name, completeness, str(note_path))


if __name__ == "__main__":
    converter = InterviewNoteProcessor()
    json_data = converter.from_file("knowledge_packs/18/templates/template_40/sessions/session_22/interview_notes.md")

    # Test: Update question statuses to demonstrate status tracking
    if json_data["topics"]:
        first_topic = json_data["topics"][0]
        if first_topic.get("key_questions"):
            # Update first question to "asking" status
            first_topic["key_questions"][0]["status"] = QuestionStatus.ASKING.value
            # Update second question to "completed" status
            if len(first_topic["key_questions"]) > 1:
                first_topic["key_questions"][1]["status"] = QuestionStatus.COMPLETED.value

    print("=== JSON Data (showing status in questions) ===")
    # Show first topic's questions with status
    if json_data["topics"]:
        first_topic = json_data["topics"][0]
        print(f"Topic: {first_topic['topic_name']}")
        for i, q in enumerate(first_topic.get("key_questions", [])[:3], 1):
            if isinstance(q, dict):
                print(f"  {i}. Status: {q.get('status')} - {q.get('text', '')[:60]}...")

    print("\n=== Markdown Output (status brackets shown for non-not_asked) ===")
    markdown_output = converter.json_to_markdown(json_data)
    # Show first topic section
    lines = markdown_output.split("\n")
    in_first_topic = False
    topic_lines_shown = 0
    for line in lines:
        if "### Colour_Measurement_Techniques_and_Instrumentation" in line:
            in_first_topic = True
        if in_first_topic:
            print(line)
            if "Key Questions" in line:
                topic_lines_shown = 0
            if topic_lines_shown < 5 and (
                "Key Questions" in line or line.strip().startswith("1.") or line.strip().startswith("2.") or line.strip().startswith("3.")
            ):
                topic_lines_shown += 1
            if topic_lines_shown >= 5 and "---" in line:
                break

    print("\n=== Status Verification ===")
    if "[asking]" in markdown_output:
        print("✅ Status bracket [asking] appears in markdown")
    if "[completed]" in markdown_output:
        print("✅ Status bracket [completed] appears in markdown")
    if "[not_asked]" not in markdown_output:
        print("ℹ️  Status bracket [not_asked] is intentionally omitted for clean markdown (by design)")
    print("\nNote: Questions with 'not_asked' status don't show brackets to keep markdown clean.")
    print("Only non-default statuses (asking, clarifying, completed) show brackets in markdown.")
