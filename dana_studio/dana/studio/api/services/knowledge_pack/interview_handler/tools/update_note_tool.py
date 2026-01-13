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


class UpdateNoteTool(BaseTool):
    def __init__(self, note_path: str):
        tool_info = BaseToolInformation(
            name="update_note",
            description="""Update interview note by applying search/replace operations. 

⚠️ IMPORTANT: Search patterns must be UNIQUE within the note. If a pattern appears multiple times, 
the tool will return suggestions for more specific patterns with surrounding context.
            
The LLM orchestrator analyzes user messages and generates diff blocks to update the note.
Use this to capture new insights, update understanding level, mark topics as covered, etc.

The diff parameter should contain search and replace blocks in the following format:
```
------- SEARCH
<exact content to find>
=======
<new content to replace with>
++++++ REPLACE

------- SEARCH
<exact content to find>
=======
<new content to replace with>
++++++ REPLACE
```

You can include multiple search/replace blocks in a single operation. The mode parameter controls how matching is performed:
- 'text' mode: Exact string matching (default)
- 'regex' mode: Pattern matching with backreferences (e.g., \\1, \\2 for captured groups)

Use this tool for:
- Capturing new expert insights
- Updating understanding level and completeness
- Marking topics as covered or in progress
- Recording document search results
- Tracking interview progress

Example use cases:
- Update "Expert Insights" with new information shared
- Change understanding completeness from 30% to 60%
- Mark topic status from "Not started" to "In progress"
- Add document search results to "Documents Found" section
- Update next steps based on interview progress

The tool automatically preserves the note markdown structure and formatting.""",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="diff",
                        type="string",
                        description="Search and replace blocks to update note sections",
                        example="------- SEARCH\n*No insights captured yet*\n=======\n- Expert works with conveyor systems\n- Focuses on safety procedures\n++++++ REPLACE",
                    ),
                    BaseArgument(
                        name="mode",
                        type="string",
                        description="Matching mode - 'text' for exact string match, 'regex' for pattern matching",
                        example="text",
                    ),
                ],
                required=["diff"],
            ),
        )
        self.note_path = note_path
        super().__init__(tool_info)

    async def _execute(self, **kwargs) -> ToolResult:
        diff = kwargs.get("diff", "")
        mode = kwargs.get("mode", "text")
        abs_path = os.path.abspath(self.note_path)
        result = self.replace_in_file(abs_path, diff, mode)
        return ToolResult(name=self.name, result=result, require_user=False)

    def replace_in_file(self, file_path: str, diff: str, mode: str = "text") -> str:
        """
        Apply search and replace operations to a file.

        Args:
            file_path: Path to the file to modify
            diff: Search and replace blocks in the specified format
            mode: Matching mode - 'text' for exact string match, 'regex' for pattern matching

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
            new_content, changes_made = self._apply_diff(content, diff, mode)
        except AmbiguousSearchPatternError as e:
            # Return the suggestion message
            return str(e)
        except Exception as e:
            return f"❌ Error applying diff: {e}"

        # Write the modified content back to the file
        try:
            with open(file_path_obj, "w") as f:
                f.write(new_content)
        except Exception as e:
            return f"❌ Error writing file '{file_path}': {e}"

        # Generate result message
        if changes_made:
            return f"✅ Successfully applied {changes_made} change(s) to '{file_path}'"
        else:
            return f"⚠️ No changes were applied to '{file_path}' (search patterns not found). Please read the current note state using view_note first to provide accurate diff blocks."

    def _apply_diff(self, content: str, diff: str, mode: str = "text") -> tuple[str, int]:
        """
        Apply search and replace operations to content.

        Args:
            content: Original file content
            diff: Search and replace blocks
            mode: Matching mode - 'text' for exact string match, 'regex' for pattern matching

        Returns:
            Tuple of (new_content, number_of_changes_made)
        """
        new_content = content
        changes_made = 0
        suggestions = []

        # Split diff into blocks
        blocks = self._parse_diff_blocks_new(diff)

        for block in blocks:
            search_content = block["search"]
            replace_content = block["replace"]

            # CRITICAL: Validate insight preservation
            # Check if we're replacing a section that contains expert insights
            if "**Expert Insights**" in search_content or "Expert Insights" in search_content:
                # Extract insights from search content
                search_insights = self._extract_insights_from_text(search_content)
                replace_insights = self._extract_insights_from_text(replace_content)

                if search_insights and not replace_insights:
                    # Insights are being removed - this is likely an error
                    logger.error(
                        f"⚠️ INSIGHT PRESERVATION WARNING: "
                        f"Search pattern contains {len(search_insights)} insight(s) but replacement has none. "
                        f"This will cause insight loss. Search preview: {search_content[:200]}..."
                    )
                    # Return error instead of applying the change
                    raise ValueError(
                        f"❌ Insight Preservation Error: Cannot apply this update because it would remove "
                        f"{len(search_insights)} expert insight(s). When updating topic status or other fields, "
                        f"you MUST preserve all existing insights in the replacement block. "
                        f"Please use view_note to see current insights and include them in your update."
                    )
                elif search_insights and replace_insights:
                    logger.info(
                        f"✓ Insight preservation validated: {len(search_insights)} insights in search, {len(replace_insights)} in replace"
                    )

            if mode == "text":
                # Text mode: exact string replacement
                occurrences = new_content.count(search_content)

                if occurrences > 1:
                    # Multiple matches found - create suggestion
                    suggestion = self._create_ambiguity_suggestion(new_content, search_content, replace_content, occurrences)
                    suggestions.append(suggestion)
                    logger.warning(f"Ambiguous search pattern found {occurrences} times: {search_content[:50]}...")
                    continue  # Skip this block, don't apply changes

                if occurrences == 1:
                    # Single match - safe to replace
                    logger.info("Applying replacement - Preview of change:")
                    logger.info(f"  BEFORE (first 150 chars): {search_content[:150]}...")
                    logger.info(f"  AFTER (first 150 chars): {replace_content[:150]}...")
                    new_content = new_content.replace(search_content, replace_content)
                    changes_made += 1
                    logger.info("✓ Successfully replaced 1 occurrence of search pattern")
                else:
                    logger.warning(f"Search pattern not found in content: {search_content[:100]}...")

            elif mode == "regex":
                # Regex mode: pattern matching with backreferences
                try:
                    # Count occurrences before replacement
                    pattern = re.compile(search_content)
                    matches = pattern.findall(new_content)
                    occurrences = len(matches)

                    if occurrences > 1:
                        # Multiple matches found - create suggestion
                        suggestion = self._create_ambiguity_suggestion(
                            new_content, search_content, replace_content, occurrences, is_regex=True
                        )
                        suggestions.append(suggestion)
                        logger.warning(f"Ambiguous regex pattern found {occurrences} times: {search_content[:50]}...")
                        continue  # Skip this block, don't apply changes

                    if occurrences == 1:
                        # Single match - safe to replace
                        new_content = re.sub(search_content, replace_content, new_content)
                        changes_made += 1
                        logger.info("Replaced 1 occurrence using regex pattern")
                    else:
                        logger.warning(f"Regex pattern not found in content: {search_content[:100]}...")
                except re.error as e:
                    logger.error(f"Invalid regex pattern '{search_content}': {e}")
                    raise ValueError(f"Invalid regex pattern: {e}")

            else:
                raise ValueError(f"Invalid mode '{mode}'. Must be 'text' or 'regex'")

        # If suggestions exist, raise exception with helpful message
        if suggestions:
            raise AmbiguousSearchPatternError(suggestions)

        return new_content, changes_made

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

    def _extract_insights_from_text(self, text: str) -> list[str]:
        """
        Extract insight bullets from text content.

        Args:
            text: Text content that may contain expert insights

        Returns:
            List of insight strings (bullet points)
        """
        insights = []

        # Look for Expert Insights section
        insights_match = re.search(r"\*\*Expert Insights\*\*\s*\n((?:^[-*]\s.+$\n?)+)", text, re.MULTILINE)
        if insights_match:
            insights_text = insights_match.group(1)
            # Extract bullet points
            bullet_points = re.findall(r"^[-*]\s(.+)$", insights_text, re.MULTILINE)
            insights = [bp.strip() for bp in bullet_points if bp.strip()]

        return insights

    def _create_ambiguity_suggestion(
        self, content: str, search_pattern: str, replace_content: str, occurrences: int, is_regex: bool = False
    ) -> dict:
        """
        Create suggestion for more specific search pattern.

        Args:
            content: Full note content
            search_pattern: The ambiguous search pattern
            replace_content: The replacement content
            occurrences: Number of times pattern appears
            is_regex: Whether the pattern is a regex pattern

        Returns:
            Dictionary with suggestion details
        """
        # Find all positions where pattern occurs
        positions = []
        if is_regex:
            # For regex, find all match positions
            pattern = re.compile(search_pattern)
            for match in pattern.finditer(content):
                positions.append((match.start(), match.end()))
        else:
            # For text, find all occurrences
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


if __name__ == "__main__":
    import asyncio
    import tempfile

    # Test the UpdateNoteTool for note modifications
    print("🔧 UpdateNoteTool - Interview Note Modification Testing")
    print("=" * 60)

    # Sample note content
    test_note = """# Interview Notes - Safety Expert
**Date**: 2024-01-15

## Topics to Cover
### Conveyor Safety
**Background**: Safety procedures for conveyor systems
**Status**: Not started

### Quality Control
**Background**: Inspection procedures
**Status**: Not started

### Equipment Maintenance
**Background**: Maintenance workflows
**Status**: Not started

## Expert Insights
*No insights captured yet*

## Current Understanding Level
- **Completeness**: 0% - Interview just started
- **Confidence**: Low
- **Next Steps**: Begin with opening questions

## Documents Found
*No documents searched yet*
"""

    # Test cases
    test_cases = [
        {
            "name": "Add initial expert insights (should succeed - unique pattern)",
            "diff": """------- SEARCH
*No insights captured yet*
=======
- Expert works with conveyor systems
- Focuses on safety procedures
- Initial sharing, need more details
++++++ REPLACE
""",
        },
        {
            "name": "Update understanding level (should succeed - unique pattern)",
            "diff": """------- SEARCH
- **Completeness**: 0% - Interview just started
- **Confidence**: Low
- **Next Steps**: Begin with opening questions
=======
- **Completeness**: 40% - Some initial information gathered
- **Confidence**: Medium
- **Next Steps**: Ask about specific procedures
++++++ REPLACE
""",
        },
        {
            "name": "Mark topic as in progress (should FAIL - ambiguous pattern, appears 3 times)",
            "diff": """------- SEARCH
**Status**: Not started
=======
**Status**: In progress
++++++ REPLACE
""",
            "expect_suggestions": True,
        },
        {
            "name": "Mark specific topic as in progress (should succeed - unique with context)",
            "diff": """------- SEARCH
### Conveyor Safety
**Background**: Safety procedures for conveyor systems
**Status**: Not started
=======
### Conveyor Safety
**Background**: Safety procedures for conveyor systems
**Status**: In progress
++++++ REPLACE
""",
        },
        {
            "name": "Add document search results (should succeed - unique pattern)",
            "diff": """------- SEARCH
*No documents searched yet*
=======
**Search Query**: conveyor safety procedures
**Results**:
- OSHA Manual Section 3.2: Lockout tagout procedures
- Safety Guide: Conveyor safety standards
++++++ REPLACE
""",
        },
    ]

    async def run_tests():
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}: {test_case['name']}")
            print("-" * 40)

            # Create temporary note file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write(test_note)
                temp_path = f.name

            try:
                tool = UpdateNoteTool(note_path=temp_path)
                mode = test_case.get("mode", "text")
                expect_suggestions = test_case.get("expect_suggestions", False)
                result = await tool._execute(diff=test_case["diff"], mode=mode)
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
                        print("\n📄 Modified note section:")
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

    # Run tests
    asyncio.run(run_tests())

    print("\n🎯 Interview Note Update Tool Ready")
    print("Use this tool to update interview notes:")
    print("tool = UpdateNoteTool(note_path='path/to/note.md')")
    print("result = await tool._execute(diff='your_search_replace_blocks')")
    print("print(result.result)")
