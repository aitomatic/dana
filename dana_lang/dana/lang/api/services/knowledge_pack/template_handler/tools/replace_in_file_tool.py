from dana.lang.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
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


class ReplaceInFileTool(BaseTool):
    def __init__(self, template_path: str):
        tool_info = BaseToolInformation(
            name="replace_in_template",
            description="""Make targeted edits to specific sections of the interview template without overwriting the entire file. This tool enables precise modifications while preserving the overall template structure.

The diff parameter should contain search and replace blocks in the following format:
```
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
- Modifying specific topic sections
- Updating question wording
- Changing interview approach details
- Adjusting relationship exploration prompts
- Refining follow-up framework questions
- Adding or updating topic background information
- Modifying topic connection hints
- Pattern-based replacements (with regex mode)

Example use cases:
- Reword a specific opening question for clarity
- Update the interview duration in the approach section
- Add additional context to a topic's background
- Modify connection hints between topics
- Refine relationship exploration prompts
- Renumber questions using regex patterns (e.g., (\\d+)\\. → Question \\1:)
- Replace multiple similar patterns at once
- Transform question formats (e.g., (\\d+)\\.\\s*([^?]+)\\? → **Question \\1**: \\2?)
- Update markdown formatting with captured groups

The tool automatically preserves the template markdown structure and formatting.""",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="diff",
                        type="string",
                        description="Search and replace blocks using the format: ------- SEARCH\n<content>\n=======\n<content>\n++++++ REPLACE. For regex mode, use patterns with backreferences (\\1, \\2, etc.)",
                        example="Example 1: \n------- SEARCH\n(\\d+)\\. How do you ensure product quality throughout the manufacturing process\\?\n=======\nQuestion \\1: How do you ensure product quality throughout the manufacturing process\\?\n++++++ REPLACE\n\nExample 2: \n------- SEARCH\n1. How do you ensure product quality throughout the manufacturing process?\n=======\n1. What specific quality control measures do you implement at each stage of the manufacturing process?\n++++++ REPLACE",
                    ),
                    BaseArgument(
                        name="mode",
                        type="string",
                        description="Matching mode - 'text' for exact string match, 'regex' for pattern matching with backreferences",
                        example="text",
                    ),
                ],
                required=["diff"],
            ),
        )
        self.template_path = template_path
        super().__init__(tool_info)

    async def _execute(self, **kwargs) -> ToolResult:
        diff = kwargs.get("diff", "")
        mode = kwargs.get("mode", "text")
        abs_path = os.path.abspath(self.template_path)
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
            return f"⚠️ No changes were applied to '{file_path}' (search patterns not found)"

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

        # Split diff into blocks
        blocks = self._parse_diff_blocks(diff)

        for block in blocks:
            search_content = block["search"]
            replace_content = block["replace"]

            if mode == "text":
                # Text mode: exact string replacement
                occurrences = new_content.count(search_content)
                if occurrences > 0:
                    new_content = new_content.replace(search_content, replace_content)
                    changes_made += occurrences
                    logger.info(f"Replaced {occurrences} occurrence(s) of search pattern")
                else:
                    logger.warning(f"Search pattern not found in content: {search_content[:100]}...")

            elif mode == "regex":
                # Regex mode: pattern matching with backreferences
                try:
                    # Count occurrences before replacement
                    pattern = re.compile(search_content)
                    matches = pattern.findall(new_content)
                    occurrences = len(matches)

                    if occurrences > 0:
                        new_content = re.sub(search_content, replace_content, new_content)
                        changes_made += occurrences
                        logger.info(f"Replaced {occurrences} occurrence(s) using regex pattern")
                    else:
                        logger.warning(f"Regex pattern not found in content: {search_content[:100]}...")
                except re.error as e:
                    logger.error(f"Invalid regex pattern '{search_content}': {e}")
                    raise ValueError(f"Invalid regex pattern: {e}")

            else:
                raise ValueError(f"Invalid mode '{mode}'. Must be 'text' or 'regex'")

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

**Listen for connections to**: Safety Procedures, Equipment Maintenance

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
            "name": "Refine a question for clarity",
            "diff": """------- SEARCH
1. How do you ensure product quality throughout the manufacturing process?
=======
1. What specific quality control measures do you implement at each stage of the manufacturing process?
++++++ REPLACE
""",
        },
        {
            "name": "Update interview duration",
            "diff": """------- SEARCH
- **Duration**: 60-90 minutes
=======
- **Duration**: 90-120 minutes with breaks every 30 minutes
++++++ REPLACE
""",
        },
        {
            "name": "Add topic background context",
            "diff": """------- SEARCH
**Background**: Understanding quality assurance processes
=======
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
        {
            "name": "Regex mode - Renumber questions with backreferences",
            "diff": r"""------- SEARCH
(\d+)\. How do you ensure product quality throughout the manufacturing process\?
=======
Question \1: How do you ensure product quality throughout the manufacturing process\?
++++++ REPLACE
""",
            "mode": "regex",
        },
        {
            "name": "Regex mode - Replace multiple similar patterns",
            "diff": r"""------- SEARCH
- \*\*([^:]+):\*\* ([^\n]+)
=======
- **\1**: \2 (Key focus area)
++++++ REPLACE
""",
            "mode": "regex",
        },
        {
            "name": "Regex mode - Advanced pattern matching with multiple groups",
            "diff": r"""------- SEARCH
(\d+)\.\s*([^?]+)\?
=======
**Question \1**: \2?
++++++ REPLACE
""",
            "mode": "regex",
        },
    ]

    async def run_tests():
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}: {test_case['name']}")
            print("-" * 40)

            # Create temporary template file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write(test_template)
                temp_path = f.name

            try:
                tool = ReplaceInFileTool(template_path=temp_path)
                mode = test_case.get("mode", "text")
                result = await tool._execute(diff=test_case["diff"], mode=mode)
                print(result.result)

                # Show modified section
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

    # Run tests
    asyncio.run(run_tests())

    print("\n🎯 Template Modification Tool Ready")
    print("Use this tool to make precise edits to interview templates:")
    print("tool = ReplaceInFileTool(template_path='path/to/template.md')")
    print("result = await tool._execute(diff='your_search_replace_blocks')")
    print("print(result.result)")
