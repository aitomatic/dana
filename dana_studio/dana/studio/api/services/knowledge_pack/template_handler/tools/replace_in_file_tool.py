from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
    ToolResult,
)
import os
import re
import logging
from pathlib import Path
from difflib import SequenceMatcher
from dana.studio.api.services.knowledge_pack.template_handler.utils import normalize_template_separators

logger = logging.getLogger(__name__)


class AmbiguousSearchPatternError(Exception):
    """Raised when a search pattern matches multiple locations."""

    def __init__(self, suggestions: list[dict]):
        self.suggestions = suggestions
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        msg = "⚠️ Ambiguous search pattern(s) detected. Multiple matches found:\n\n"
        for i, suggestion in enumerate(self.suggestions, 1):
            pattern_preview = suggestion["pattern"][:50]
            if len(suggestion["pattern"]) > 50:
                pattern_preview += "..."
            msg += f"Block {i}: Pattern '{pattern_preview}' found {suggestion['count']} times\n"
            msg += "Suggestions for more specific patterns:\n"
            for j, specific in enumerate(suggestion["specific_patterns"], 1):
                msg += f"  {j}. Include more context (at {specific['location']}):\n"
                msg += "     ------- SEARCH\n" + specific["search"] + "\n=======\n" + specific["replace"] + "\n++++++ REPLACE\n\n"
        msg += "Please use a more specific search pattern that uniquely identifies the target location."
        return msg


class ReplaceInFileTool(BaseTool):
    def __init__(self, template_path: str):
        tool_info = BaseToolInformation(
            name="replace_in_template",
            description="""Make targeted edits to specific sections of the interview template without overwriting the entire file.

⚠️ BEST PRACTICE: Always use view_template first to see the current template content before making changes. 
This ensures your search patterns match the actual template structure.

This tool enables precise modifications while preserving the overall template structure.

⚠️ IMPORTANT: Search patterns must be UNIQUE within the template. If a pattern appears multiple times, 
the tool will return suggestions for more specific patterns with surrounding context.

The diff parameter should contain search and replace blocks in the following format:
```
------- SEARCH
<exact content to find preserving structure and formatting including line breaks and tabs/spaces>
=======
<new content to replace with>
++++++ REPLACE

------- SEARCH
<exact content to find preserving structure and formatting including line breaks and tabs/spaces>
=======
<new content to replace with>
++++++ REPLACE
```

You can include multiple search/replace blocks in a single operation using exact string matching.

Use this tool for:
- Modifying specific topic sections
- Updating question wording
- Changing interview approach details
- Adjusting relationship exploration prompts
- Refining follow-up framework questions
- Adding or updating topic background information
- Modifying topic connection hints

Example use cases:
- Reword a specific opening question for clarity
- Update the interview duration in the approach section
- Add additional context to a topic's background
- Modify connection hints between topics
- Refine relationship exploration prompts

The tool automatically preserves the template markdown structure and formatting.""",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="diff",
                        type="string",
                        description="Search and replace blocks using the format: ------- SEARCH\n<content>\n=======\n<content>\n++++++ REPLACE",
                        example="------- SEARCH\n1. How do you ensure product quality throughout the manufacturing process?\n=======\n1. What specific quality control measures do you implement at each stage of the manufacturing process?\n++++++ REPLACE",
                    ),
                ],
                required=["diff"],
            ),
        )
        self.template_path = template_path
        super().__init__(tool_info)

    async def _execute(self, **kwargs) -> ToolResult:
        diff = kwargs.get("diff", "")
        abs_path = os.path.abspath(self.template_path)
        result = self.replace_in_file(abs_path, diff)
        return ToolResult(name=self.name, result=result, require_user=False)

    def replace_in_file(self, file_path: str, diff: str) -> str:
        """
        Apply search and replace operations to a file.

        Args:
            file_path: Path to the file to modify
            diff: Search and replace blocks in the specified format

        Returns:
            Result message with details of changes made
        """
        file_path_obj = Path(file_path)

        # Create directory if it doesn't exist
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Read existing file content if it exists
        if file_path_obj.exists():
            try:
                with open(file_path_obj) as f:
                    content = f.read()
            except Exception as e:
                return f"❌ Error reading file '{file_path}': {e}"
        else:
            content = ""
            logger.info(f"File '{file_path}' doesn't exist, will be created")

        # Parse and apply the diff
        try:
            new_content, changes_made, fuzzy_matches = self._apply_diff(content, diff)
        except AmbiguousSearchPatternError as e:
            # Return the suggestion message
            return str(e)
        except ValueError as e:
            # Atomic abort - return the error message directly
            return str(e)
        except Exception as e:
            return f"❌ Error applying diff: {e}"

        # Normalize template separators to remove orphaned "---" lines and excessive blank lines
        # This ensures clean templates after modifications (especially topic removals)
        new_content = normalize_template_separators(new_content)

        # Write the modified content back to the file
        try:
            with open(file_path_obj, "w") as f:
                f.write(new_content)
        except Exception as e:
            return f"❌ Error writing file '{file_path}': {e}"

        # Generate result message with fuzzy match transparency
        if changes_made:
            msg = (
                f"✅ TEMPLATE FILE UPDATED - {changes_made} change(s) applied\n"
                f"The actual template file on disk has been modified.\n"
                f"The right-side preview pane now reflects these changes.\n"
                f"Any <current_template_file> or <current_topic_content> from earlier in this "
                f"conversation is now OUTDATED - use view_template to see the new state if needed."
            )
            if fuzzy_matches:
                msg += f"\n\n⚡ Note: {len(fuzzy_matches)} block(s) used fuzzy matching:\n"
                for block_num, similarity in fuzzy_matches:
                    msg += f"  - Block {block_num}: {similarity:.1%} similarity\n"
            return msg
        else:
            return f"⚠️ No changes were applied to '{file_path}' (search patterns not found)"

    def _apply_diff(self, content: str, diff: str) -> tuple[str, int, list[tuple[int, float]]]:
        """
        Apply search and replace operations to content.
        Uses two-phase validation with fuzzy matching for atomic all-or-nothing behavior.

        Phase 1: Validate ALL blocks first (no changes to content)
        Phase 2: Apply all blocks only if validation passed

        Args:
            content: Original file content
            diff: Search and replace blocks

        Returns:
            Tuple of (new_content, changes_made, fuzzy_matches)
            - new_content: The modified content
            - changes_made: Number of successful replacements
            - fuzzy_matches: List of (block_number, similarity) for blocks that used fuzzy matching

        Raises:
            AmbiguousSearchPatternError: If a pattern matches multiple locations
            ValueError: If any pattern is not found (atomic abort)
        """
        # Split diff into blocks
        blocks = self._parse_diff_blocks_new(diff)

        # ========== PHASE 1: VALIDATE ALL BLOCKS ==========
        validation_errors = []
        ambiguous_suggestions = []
        validated_blocks = []  # Store validated (search, replace, actual_match, fuzzy, similarity) dicts

        for i, block in enumerate(blocks, 1):
            search_content = block["search"]
            replace_content = block["replace"]
            occurrences = content.count(search_content)

            if occurrences > 1:
                # Ambiguous exact match
                suggestion = self._create_ambiguity_suggestion(content, search_content, replace_content, occurrences)
                ambiguous_suggestions.append(suggestion)
                logger.warning(f"Block {i}: Ambiguous pattern found {occurrences} times: {search_content[:50]}...")
                continue

            if occurrences == 1:
                # Exact match found
                validated_blocks.append(
                    {
                        "search": search_content,
                        "replace": replace_content,
                        "actual_match": search_content,
                        "fuzzy": False,
                        "similarity": 1.0,
                        "block_num": i,
                    }
                )
                logger.debug(f"Block {i}: Exact match found")
                continue

            # occurrences == 0: Try fuzzy matching
            matched_text, similarity, candidates = self._find_fuzzy_match(content, search_content, threshold=0.90)

            if matched_text is None:
                # No fuzzy match found either
                preview = search_content[:100] + ("..." if len(search_content) > 100 else "")
                validation_errors.append(f"Block {i}: Search pattern not found (even with 90% fuzzy matching):\n" f"  '{preview}'")
                logger.warning(f"Block {i}: Pattern not found, no fuzzy match: {search_content[:50]}...")
            elif len(candidates) > 1 and abs(candidates[0][1] - candidates[1][1]) < 0.01:
                # Multiple equally-good fuzzy matches - ambiguous
                ambiguous_suggestions.append(
                    {
                        "pattern": search_content,
                        "count": len(candidates),
                        "specific_patterns": [
                            {"search": c[0], "replace": replace_content, "location": f"~{c[1]:.0%} match"}
                            for c in candidates[:3]  # Show top 3
                        ],
                    }
                )
                logger.warning(f"Block {i}: Multiple equally-good fuzzy matches found")
            else:
                # Single best fuzzy match found
                validated_blocks.append(
                    {
                        "search": search_content,
                        "replace": replace_content,
                        "actual_match": matched_text,
                        "fuzzy": True,
                        "similarity": similarity,
                        "block_num": i,
                    }
                )
                logger.info(f"Block {i}: Using fuzzy match ({similarity:.1%} similarity)")

        # If ANY validation errors, abort entire operation
        if ambiguous_suggestions:
            raise AmbiguousSearchPatternError(ambiguous_suggestions)

        if validation_errors:
            error_msg = (
                f"❌ ATOMIC OPERATION ABORTED - {len(validation_errors)} pattern(s) not found\n\n"
                f"No changes were made to the template. All {len(blocks)} block(s) must match "
                "for the operation to proceed.\n\n"
                "Errors:\n" + "\n".join(validation_errors) + "\n\n"
                "💡 Tip: Use view_template to see the current template content and verify "
                "your search patterns match exactly."
            )
            raise ValueError(error_msg)

        # ========== PHASE 2: APPLY ALL BLOCKS ==========
        # At this point, all blocks are validated (exact or fuzzy match found)
        new_content = content
        changes_made = 0
        fuzzy_matches = []  # Track which blocks used fuzzy matching

        for block in validated_blocks:
            actual_match = block["actual_match"]  # Use the ACTUAL text found in content
            replace_content = block["replace"]
            block_num = block["block_num"]

            # Apply the smart newline handling for empty replacements
            if replace_content == "":
                new_content = self._apply_empty_replacement(new_content, actual_match)
            else:
                new_content = new_content.replace(actual_match, replace_content, 1)

            changes_made += 1

            if block["fuzzy"]:
                fuzzy_matches.append((block_num, block["similarity"]))

            logger.info(f"Applied block {changes_made}/{len(validated_blocks)}")

        return new_content, changes_made, fuzzy_matches

    def _parse_diff_blocks(self, diff: str) -> list[dict[str, str]]:
        """
        Parse diff string into search/replace blocks.

        Args:
            diff: Raw diff string

        Returns:
            List of dictionaries with 'search' and 'replace' keys
        """
        blocks = []

        # Split by search markers - fixed pattern to match documented format
        search_pattern = r"------- SEARCH\s*\n(.*?)\n=======\n(.*?)\n\+\+\+\+\+\+ REPLACE"
        matches = re.findall(search_pattern, diff, re.DOTALL)

        for search_content, replace_content in matches:
            # Clean up whitespace
            search_content = search_content.rstrip()
            replace_content = replace_content.rstrip()

            blocks.append({"search": search_content, "replace": replace_content})

        if not blocks:
            raise ValueError(
                "No valid search/replace blocks found. Use format:\n------- SEARCH\n<content>\n=======\n<content>\n++++++ REPLACE"
            )

        return blocks

    def _parse_diff_blocks_new(self, diff: str) -> list[dict[str, str]]:
        """
        Parse diff string using flexible regex patterns.

        Supports:
        - Variable marker lengths (3+ dashes, equals, plus signs)
        - Optional > suffix on SEARCH and REPLACE markers

        Args:
            diff: Raw diff string

        Returns:
            List of dictionaries with 'search' and 'replace' keys

        Raises:
            ValueError: If no valid search/replace blocks are found
        """
        # Regex patterns for flexible matching
        search_start_pattern = re.compile(r"^-{3,}\s+SEARCH>?\s*$")
        separator_pattern = re.compile(r"^={3,}\s*$")
        replace_end_pattern = re.compile(r"^\+{3,}\s+REPLACE>?\s*$")

        blocks = []
        state = None  # None, 'in_search', 'in_replace'
        search_content = []
        replace_content = []

        lines = diff.split("\n")

        for line_num, line in enumerate(lines, 1):
            if state is None:
                # Looking for search block start
                if search_start_pattern.match(line):
                    state = "in_search"
                    search_content = []
                    replace_content = []
                    logger.debug(f"Line {line_num}: Found SEARCH marker")

            elif state == "in_search":
                # In search block, looking for separator
                if separator_pattern.match(line):
                    state = "in_replace"
                    logger.debug(f"Line {line_num}: Found separator, switching to REPLACE")
                else:
                    # Accumulate search content
                    search_content.append(line)

            elif state == "in_replace":
                # In replace block, looking for replace end marker
                if replace_end_pattern.match(line):
                    # Complete block found
                    search_str = "\n".join(search_content).rstrip()
                    replace_str = "\n".join(replace_content).rstrip()

                    blocks.append({"search": search_str, "replace": replace_str})

                    logger.debug(f"Line {line_num}: Found REPLACE marker, block complete")
                    logger.debug(f"  Search length: {len(search_str)} chars")
                    logger.debug(f"  Replace length: {len(replace_str)} chars")

                    # Reset state for next block
                    state = None
                    search_content = []
                    replace_content = []
                else:
                    # Accumulate replace content
                    replace_content.append(line)

        # Check for incomplete blocks
        if state is not None:
            if state == "in_search":
                raise ValueError(
                    "Incomplete diff block: Found SEARCH marker but no separator (===). "
                    "Make sure your diff follows the format:\n"
                    "--- SEARCH\n<content>\n===\n<content>\n+++ REPLACE"
                )
            elif state == "in_replace":
                raise ValueError(
                    "Incomplete diff block: Found SEARCH and separator but no REPLACE marker. "
                    "Make sure your diff follows the format:\n"
                    "--- SEARCH\n<content>\n===\n<content>\n+++ REPLACE"
                )

        if not blocks:
            raise ValueError(
                "No valid search/replace blocks found. Use format:\n"
                "--- SEARCH\n<content>\n===\n<content>\n+++ REPLACE\n\n"
                "Flexible formats supported:\n"
                "- Variable marker lengths: ---, -------, -----------\n"
                "- Optional > suffix: --- SEARCH>, +++ REPLACE>"
            )

        logger.info(f"Successfully parsed {len(blocks)} diff block(s) using new parser")
        return blocks

    def _create_ambiguity_suggestion(self, content: str, search_pattern: str, replace_content: str, occurrences: int) -> dict:
        """
        Create suggestion for more specific search pattern.

        Args:
            content: Full template content
            search_pattern: The ambiguous search pattern
            replace_content: The replacement content
            occurrences: Number of times pattern appears

        Returns:
            Dictionary with suggestion details
        """
        # Find all positions where pattern occurs
        positions = []
        start = 0
        while True:
            pos = content.find(search_pattern, start)
            if pos == -1:
                break
            positions.append((pos, pos + len(search_pattern)))
            start = pos + 1

        # Generate specific patterns with surrounding context
        specific_patterns = []
        for pos_start, pos_end in positions:
            # Get context before (up to 3 lines or 200 chars)
            context_start = max(0, pos_start - 200)
            # Find up to 3 newlines before pattern for better context
            newlines_before = 0
            search_start = pos_start - 1
            while search_start >= context_start and newlines_before < 3:
                if content[search_start] == "\n":
                    newlines_before += 1
                    if newlines_before == 3:
                        context_start = search_start + 1
                        break
                search_start -= 1

            # If we found context, make sure we start at the beginning of a line
            if context_start > 0:
                line_start = content.rfind("\n", 0, context_start)
                if line_start != -1 and (context_start - line_start) < 50:
                    context_start = line_start + 1

            # Get context after (up to 2 lines or 100 chars)
            context_end = min(len(content), pos_end + 100)
            # Find up to 2 newlines after pattern
            newlines_after = 0
            search_end = pos_end
            while search_end < context_end and newlines_after < 2:
                if content[search_end] == "\n":
                    newlines_after += 1
                    if newlines_after == 2:
                        context_end = search_end
                        break
                search_end += 1

            # Build specific search pattern with context
            specific_search = content[context_start:context_end].rstrip()

            # Build replacement with same context structure
            before_pattern = content[context_start:pos_start]
            after_pattern = content[pos_end:context_end].rstrip()
            specific_replace = before_pattern + replace_content + after_pattern

            # Calculate line number
            line_num = content[:pos_start].count("\n") + 1

            specific_patterns.append({"search": specific_search, "replace": specific_replace, "location": f"Line {line_num}"})

        return {"pattern": search_pattern, "count": occurrences, "specific_patterns": specific_patterns}

    def _find_fuzzy_match(
        self, content: str, search_pattern: str, threshold: float = 0.90
    ) -> tuple[str | None, float, list[tuple[str, float]]]:
        """
        Find fuzzy match for search pattern in content.

        Args:
            content: The full content to search in
            search_pattern: The pattern to find
            threshold: Minimum similarity ratio (0.0 to 1.0), default 0.90

        Returns:
            Tuple of (matched_text, similarity, all_candidates):
            - matched_text: The actual text from content that matched (or None)
            - similarity: The similarity ratio (0.0 to 1.0)
            - all_candidates: List of (text, similarity) for candidates above threshold
        """
        # Split content into potential matching segments
        # Use lines as natural boundaries, with context windows
        lines = content.split("\n")
        search_lines = search_pattern.split("\n")
        search_line_count = len(search_lines)

        candidates = []

        # Slide a window of search_line_count lines through content
        for i in range(len(lines) - search_line_count + 1):
            window = "\n".join(lines[i : i + search_line_count])
            ratio = SequenceMatcher(None, search_pattern, window).ratio()

            if ratio >= threshold:
                candidates.append((window, ratio))

        if not candidates:
            return None, 0.0, []

        # Sort by similarity (highest first)
        candidates.sort(key=lambda x: x[1], reverse=True)

        # Return the best match
        best_match, best_ratio = candidates[0]
        return best_match, best_ratio, candidates

    def _apply_empty_replacement(self, content: str, search_content: str) -> str:
        """
        Handle empty replacement with smart newline handling.

        When deleting content (replacing with empty string), this method
        intelligently handles trailing newlines to avoid orphan blank lines.

        Args:
            content: The full content
            search_content: The text to remove

        Returns:
            Content with the search_content removed
        """
        match_pos = content.find(search_content)
        match_end = match_pos + len(search_content)

        # Check if this match is followed by a newline
        if match_end < len(content) and content[match_end] == "\n":
            is_line_start = match_pos == 0 or content[match_pos - 1] == "\n"
            if is_line_start:
                # Complete line deletion - include trailing newline
                return content.replace(search_content + "\n", "", 1)

        return content.replace(search_content, "", 1)


if __name__ == "__main__":
    import asyncio
    import tempfile

    # Test the ReplaceInFileTool for template modifications
    print("🔧 ReplaceInFileTool - Template Modification Testing")
    print("=" * 60)

    # Sample template content
    test_template = """# Master Interview Template: Food Manufacturing - Process Operator

## Interview Approach
- **Goal**: Capture deep operational knowledge
- **Style**: Conversational, expert-driven
- **Duration**: 60-90 minutes
- **Topics Covered**: All major production areas

---

## Topic Opening Questions

### Quality Control
**Background**: Understanding quality assurance processes
**Opening Questions**:
1. How do you ensure product quality throughout the manufacturing process?
2. What quality checkpoints do you have in place?

### Safety Procedures
**Background**: Understanding safety protocols and compliance
**Opening Questions**:
1. What safety procedures do you follow daily?
2. How do you handle safety incidents?

### Equipment Maintenance
**Background**: Understanding maintenance workflows
**Opening Questions**:
1. What is your preventive maintenance schedule?
2. How do you troubleshoot equipment issues?

---

## Relationship Exploration Prompts
- When expert mentions safety, explore connection to quality
- If automation is discussed, ask about impact on production flow

---

## Follow-up Framework
- Can you walk me through a specific example?
- What challenges did you encounter with that approach?

---
"""

    # Test cases
    test_cases = [
        {
            "name": "Refine a question for clarity (should succeed - unique pattern)",
            "diff": """------- SEARCH
1. How do you ensure product quality throughout the manufacturing process?
=======
1. What specific quality control measures do you implement at each stage of the manufacturing process?
++++++ REPLACE
""",
        },
        {
            "name": "Update interview duration (should succeed - unique pattern)",
            "diff": """------- SEARCH
- **Duration**: 60-90 minutes
=======
- **Duration**: 90-120 minutes with breaks every 30 minutes
++++++ REPLACE
""",
        },
        {
            "name": "Ambiguous pattern - should FAIL (3 matches of '**Background**:')",
            "diff": """------- SEARCH
**Background**:
=======
**Context**:
++++++ REPLACE
""",
            "expect_suggestions": True,
        },
        {
            "name": "Add specific topic background context (should succeed - unique with context)",
            "diff": """------- SEARCH
### Quality Control
**Background**: Understanding quality assurance processes
=======
### Quality Control
**Background**: Understanding quality assurance processes and how operators identify and address quality issues in real-time
++++++ REPLACE
""",
        },
        {
            "name": "Add new relationship exploration prompt",
            "diff": """------- SEARCH
- If automation is discussed, ask about impact on production flow
=======
- If automation is discussed, ask about impact on production flow
- When equipment maintenance is mentioned, explore connections to quality outcomes
++++++ REPLACE
""",
        },
    ]

    # Test cases for new flexible parser
    test_cases_new_parser = [
        {
            "name": "NEW PARSER: Minimal markers (3 dashes, equals, plus)",
            "diff": """--- SEARCH
1. How do you ensure product quality throughout the manufacturing process?
===
1. What specific quality control measures do you implement at each stage of the manufacturing process?
+++ REPLACE
""",
            "use_new_parser": True,
        },
        {
            "name": "NEW PARSER: Delete complete lines without orphan newlines",
            "diff": """--- SEARCH
1. When starting a new project, how do you typically uncover both explicit and hidden user needs?
===
+++ REPLACE

--- SEARCH
2. How do your findings from task analysis shape the overall design direction and priorities?
===
+++ REPLACE

--- SEARCH
3. What role do prototyping and usability testing play in your iterative design process?
===
+++ REPLACE
""",
            "use_new_parser": True,
            "test_content": """1. When starting a new project, how do you typically uncover both explicit and hidden user needs?
2. How do your findings from task analysis shape the overall design direction and priorities?
3. What role do prototyping and usability testing play in your iterative design process?
4. How do you adapt your methods for particularly novel or rapidly changing environments?""",
            "expected_result": """4. How do you adapt your methods for particularly novel or rapidly changing environments?""",
        },
        {
            "name": "NEW PARSER: Delete inline content (preserve newlines)",
            "diff": """--- SEARCH
**bold**
===
+++ REPLACE

--- SEARCH
 unwanted
===
+++ REPLACE
""",
            "use_new_parser": True,
            "test_content": """Hello **bold** world
This has unwanted text here
Final line""",
            "expected_result": """Hello  world
This has text here
Final line""",
        },
        {
            "name": "NEW PARSER: Mixed - delete full lines and inline content",
            "diff": """--- SEARCH
Line to delete completely
===
+++ REPLACE

--- SEARCH
 [remove this]
===
+++ REPLACE
""",
            "use_new_parser": True,
            "test_content": """Keep this line
Line to delete completely
Another line [remove this] keep rest
Final line""",
            "expected_result": """Keep this line
Another line keep rest
Final line""",
        },
        {
            "name": "NEW PARSER: Variable dash count (11 dashes)",
            "diff": """----------- SEARCH
- **Duration**: 60-90 minutes
===========
- **Duration**: 90-120 minutes with breaks every 30 minutes
+++++++++++ REPLACE
""",
            "use_new_parser": True,
        },
        {
            "name": "NEW PARSER: With optional > suffix on SEARCH",
            "diff": """--- SEARCH>
**Background**:
===
**Context**:
+++ REPLACE
""",
            "use_new_parser": True,
        },
        {
            "name": "NEW PARSER: With optional > suffix on REPLACE",
            "diff": """--- SEARCH
### Quality Control
===
### Quality Assurance
+++ REPLACE>
""",
            "use_new_parser": True,
        },
        {
            "name": "NEW PARSER: With optional > suffix on both",
            "diff": """--- SEARCH>
- If automation is discussed, ask about impact on production flow
===
- If automation is discussed, ask about impact on production flow and efficiency
+++ REPLACE>
""",
            "use_new_parser": True,
        },
        {
            "name": "NEW PARSER: Mixed variations - multiple blocks",
            "diff": """--- SEARCH
**Opening Questions**:
===
**Initial Questions**:
""",
            "use_new_parser": True,
        },
        {
            "name": "NEW PARSER: Standard 7-dash format (backward compatible)",
            "diff": """------- SEARCH
1. What safety procedures do you follow daily?
=======
1. What safety procedures and protocols do you follow daily?
+++++++ REPLACE
""",
            "use_new_parser": True,
        },
    ]

    async def run_tests():
        # Run original parser tests
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}: {test_case['name']}")
            print("-" * 40)

            # Create temporary template file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write(test_template)
                temp_path = f.name

            try:
                tool = ReplaceInFileTool(template_path=temp_path)
                expect_suggestions = test_case.get("expect_suggestions", False)
                result = await tool._execute(diff=test_case["diff"])
                print(result.result)

                # Check if we got suggestions as expected
                if expect_suggestions:
                    if "⚠️ Ambiguous search pattern" in result.result:
                        print("\n✅ Correctly detected ambiguous pattern and provided suggestions!")
                        print("\n📋 First 1000 chars of suggestions:")
                        print("-" * 20)
                        print(result.result[:1000])
                        if len(result.result) > 1000:
                            print("...\n(truncated)")
                        print("-" * 20)
                    else:
                        print("\n❌ Expected suggestions but got different result")
                else:
                    # Show modified section for successful changes
                    if "Successfully" in result.result:
                        with open(temp_path) as f:
                            content = f.read()
                        print("\n📄 Modified template section:")
                        print("-" * 20)
                        # Show first 500 chars to see the change
                        print(content[:500] + "...\n")
                        print("-" * 20)

            except Exception as e:
                print(f"❌ Error: {e}")
            finally:
                # Clean up temp file
                os.unlink(temp_path)

            print("\n" + "=" * 60)

        # Run new parser tests
        print("\n\n" + "=" * 60)
        print("🔬 TESTING NEW FLEXIBLE PARSER")
        print("=" * 60)

        for i, test_case in enumerate(test_cases_new_parser, 1):
            print(f"\n🧪 Test {i}: {test_case['name']}")
            print("-" * 40)

            # Use custom content if provided, otherwise use template
            content = test_case.get("test_content", test_template)

            # Create temporary template file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write(content)
                temp_path = f.name

            try:
                tool = ReplaceInFileTool(template_path=temp_path)

                # If this test has expected result, apply the diff and check
                if "expected_result" in test_case:
                    # Parse blocks
                    blocks = tool._parse_diff_blocks_new(test_case["diff"])
                    print(f"✅ Parsed {len(blocks)} block(s)")

                    # Apply the diff using replace_in_file
                    result = tool.replace_in_file(temp_path, test_case["diff"], mode="text")
                    print(f"Result: {result}")

                    # Read the result
                    with open(temp_path) as f:
                        actual_result = f.read()

                    expected = test_case["expected_result"]

                    print("\n📊 Comparison:")
                    print(f"Expected length: {len(expected)} chars")
                    print(f"Actual length: {len(actual_result)} chars")
                    print(f"\nExpected:\n'{expected}'")
                    print(f"\nActual:\n'{actual_result}'")

                    if actual_result == expected:
                        print("\n✅ PASS: Output matches expected result!")
                    else:
                        print("\n❌ FAIL: Output does not match!")
                        print(f"\nDifference: {len(actual_result) - len(expected)} chars")
                        # Show extra newlines
                        print(f"Extra leading newlines: {len(actual_result) - len(actual_result.lstrip())}")
                else:
                    # Just parse and display blocks
                    blocks = tool._parse_diff_blocks_new(test_case["diff"])
                    print(f"✅ Parsed {len(blocks)} block(s)")

                    # Display parsed blocks
                    for j, block in enumerate(blocks, 1):
                        print(f"\nBlock {j}:")
                        print(f"  Search: {block['search'][:60]}{'...' if len(block['search']) > 60 else ''}")
                        print(f"  Replace: {block['replace'][:60]}{'...' if len(block['replace']) > 60 else ''}")

            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback

                traceback.print_exc()
            finally:
                # Clean up temp file
                os.unlink(temp_path)

            print("\n" + "=" * 60)

    # Run tests
    asyncio.run(run_tests())

    print("\n🎯 Template Modification Tool Ready")
    print("Use this tool to make precise edits to interview templates:")
    print("tool = ReplaceInFileTool(template_path='path/to/template.md')")
    print("result = await tool._execute(diff='your_search_replace_blocks')")
    print("print(result.result)")
