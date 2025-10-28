"""
ViewNoteTool for displaying interview note sections.
"""

from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseArgument,
    BaseTool,
    BaseToolInformation,
    InputSchema,
    ToolResult,
)


class ViewNoteTool(BaseTool):
    """
    Tool for viewing interview note sections or the entire note.
    """

    def __init__(self, note_path: str):
        self.note_path = note_path
        tool_info = BaseToolInformation(
            name="view_note",
            description="Display the current interview note or specific sections to see captured knowledge.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="section",
                        type="string",
                        description="Which section to view: 'all', 'topics', 'insights', 'understanding', 'documents'",
                        example="all",
                    ),
                ],
                required=[],
            ),
        )
        super().__init__(tool_info)

    async def _execute(self, section: str = "all", **kwargs) -> ToolResult:
        """
        Display interview note or specific section.
        """
        try:
            # Read note file
            with open(self.note_path) as f:
                note_content = f.read()

            if section == "all":
                content = note_content
            elif section == "topics":
                content = self._extract_section(note_content, "## Topics to Cover")
            elif section == "insights":
                content = self._extract_section(note_content, "## Topics to Cover")
            elif section == "understanding":
                content = self._extract_section(note_content, "## Topics to Cover")
            elif section == "documents":
                content = self._extract_section(note_content, "## Documents Found")
            else:
                content = f"❌ Unknown section: {section}"

            return ToolResult(
                name="view_note",
                result=content,
                require_user=False,
            )

        except Exception as e:
            return ToolResult(
                name="view_note",
                result=f"❌ Error viewing note: {str(e)}",
                require_user=False,
            )

    def _extract_section(self, note_content: str, section_header: str) -> str:
        """Extract a specific section from the note."""
        lines = note_content.split("\n")
        section_lines = []
        in_section = False

        for line in lines:
            if line.startswith(section_header):
                in_section = True
                section_lines.append(line)
            elif in_section:
                if line.startswith("## ") and line != section_header:
                    # Hit next section
                    break
                section_lines.append(line)

        if not section_lines:
            return f"❌ Section '{section_header}' not found in note."

        return "\n".join(section_lines)


if __name__ == "__main__":
    import asyncio

    # Create test interview note
    temp_path = "knowledge_packs/1/templates/template_2/sessions/session_1/interview_notes.md"
    tool = ViewNoteTool(temp_path)

    print("🔍 Testing ViewNoteTool")
    print("=" * 40)

    # Test viewing all sections
    res = asyncio.run(tool._execute(section="insights"))
    print(res.result)
