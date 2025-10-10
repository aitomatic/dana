"""
FormatComponents - Structuring and formatting output for presentation.

Provides reusable formatting operations that can be composed into workflows.
"""

from datetime import datetime
import logging

from adana.common.protocols import DictParams
from adana.common.protocols.war import tool_use
from adana.core.resource.base_resource import BaseResource


logger = logging.getLogger(__name__)


class FormatResource(BaseResource):
    """Reusable formatting operations for workflow composition."""

    def __init__(self, **kwargs):
        """Initialize format components."""
        super().__init__(**kwargs)

    @tool_use
    def format_with_citations(self, content: str, sources: list[DictParams], citation_style: str = "numbered") -> DictParams:
        """
        Format content with proper citations.

        Args:
            content: Main content text
            sources: List of source metadata (title, url, author, date)
            citation_style: Citation style (numbered, author-date, footnotes)

        Returns:
            {
                "formatted_content": str,
                "citations": list[str],
                "bibliography": str
            }
        """
        if citation_style == "numbered":
            # Number citations [1], [2], etc.
            citations = []
            bibliography_entries = []

            for i, source in enumerate(sources, 1):
                title = source.get("title", "Untitled")
                url = source.get("url", "")
                author = source.get("author", "Unknown")
                date = source.get("published_date", "n.d.")

                citation = f"[{i}]"
                citations.append(citation)

                bib_entry = f'[{i}] {author}. "{title}". {date}. {url}'
                bibliography_entries.append(bib_entry)

            # Append bibliography
            bibliography = "\n\n## References\n\n" + "\n".join(bibliography_entries)
            formatted_content = content + bibliography

            return {
                "formatted_content": formatted_content,
                "citations": citations,
                "bibliography": bibliography,
                "citation_count": len(citations),
            }

        elif citation_style == "author-date":
            # Format as (Author, Date)
            citations = []
            bibliography_entries = []

            for source in sources:
                author = source.get("author", "Unknown")
                date = source.get("published_date", "n.d.")
                title = source.get("title", "Untitled")
                url = source.get("url", "")

                citation = f"({author}, {date})"
                citations.append(citation)

                bib_entry = f'{author}. {date}. "{title}". {url}'
                bibliography_entries.append(bib_entry)

            bibliography = "\n\n## References\n\n" + "\n".join(sorted(set(bibliography_entries)))
            formatted_content = content + bibliography

            return {
                "formatted_content": formatted_content,
                "citations": citations,
                "bibliography": bibliography,
                "citation_count": len(citations),
            }

        else:
            # Default: no special formatting
            return {"formatted_content": content, "citations": [], "bibliography": "", "citation_count": 0}

    @tool_use
    def format_as_table(self, data: list[dict] | dict, columns: list[str] | None = None, format_type: str = "markdown") -> str:
        """
        Format data as table.

        Args:
            data: Data to format (list of dicts or dict with 'rows'/'headers')
            columns: Column names (if not in data)
            format_type: Output format (markdown, html, ascii)

        Returns:
            Formatted table string
        """
        # Handle different data formats
        if isinstance(data, dict) and "rows" in data:
            headers = data.get("headers", columns or [])
            rows = data.get("rows", [])
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            headers = columns or list(data[0].keys())
            rows = [[str(item.get(col, "")) for col in headers] for item in data]
        else:
            return "Error: Invalid data format for table"

        if format_type == "markdown":
            # Markdown table
            lines = []

            # Header row
            header_line = "| " + " | ".join(headers) + " |"
            lines.append(header_line)

            # Separator
            separator = "| " + " | ".join(["---"] * len(headers)) + " |"
            lines.append(separator)

            # Data rows
            for row in rows:
                row_line = "| " + " | ".join(str(cell) for cell in row) + " |"
                lines.append(row_line)

            return "\n".join(lines)

        elif format_type == "html":
            # HTML table
            lines = ["<table>"]

            # Header
            lines.append("  <thead>")
            lines.append("    <tr>")
            for header in headers:
                lines.append(f"      <th>{header}</th>")
            lines.append("    </tr>")
            lines.append("  </thead>")

            # Body
            lines.append("  <tbody>")
            for row in rows:
                lines.append("    <tr>")
                for cell in row:
                    lines.append(f"      <td>{cell}</td>")
                lines.append("    </tr>")
            lines.append("  </tbody>")

            lines.append("</table>")
            return "\n".join(lines)

        elif format_type == "ascii":
            # ASCII table
            # Calculate column widths
            col_widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

            # Format rows
            lines = []

            # Top border
            lines.append("+" + "+".join("-" * (w + 2) for w in col_widths) + "+")

            # Header
            header_line = "|" + "|".join(f" {h:<{col_widths[i]}} " for i, h in enumerate(headers)) + "|"
            lines.append(header_line)

            # Header separator
            lines.append("+" + "+".join("=" * (w + 2) for w in col_widths) + "+")

            # Data rows
            for row in rows:
                row_line = "|" + "|".join(f" {str(cell):<{col_widths[i]}} " for i, cell in enumerate(row)) + "|"
                lines.append(row_line)

            # Bottom border
            lines.append("+" + "+".join("-" * (w + 2) for w in col_widths) + "+")

            return "\n".join(lines)

        else:
            return "Error: Unknown format type"

    @tool_use
    def format_as_bullet_points(self, items: list[str] | list[dict], indent_level: int = 0, marker: str = "-") -> str:
        """
        Format items as bullet points.

        Args:
            items: Items to format (strings or dicts with 'text' key)
            indent_level: Indentation level
            marker: Bullet marker (-, *, •)

        Returns:
            Formatted bullet list
        """
        lines = []
        indent = "  " * indent_level

        for item in items:
            if isinstance(item, dict):
                text = item.get("text", str(item))
                # Check for sub-items
                if "items" in item:
                    lines.append(f"{indent}{marker} {text}")
                    sub_list = self.format_as_bullet_points(item["items"], indent_level=indent_level + 1, marker=marker)
                    lines.append(sub_list)
                else:
                    lines.append(f"{indent}{marker} {text}")
            else:
                lines.append(f"{indent}{marker} {str(item)}")

        return "\n".join(lines)

    @tool_use
    def format_with_metadata(self, content: str, metadata: DictParams, include_timestamp: bool = True) -> str:
        """
        Format content with metadata header.

        Args:
            content: Main content
            metadata: Metadata to include (title, sources, etc.)
              - title
              - topic
              - sources_count
              - workflow
              - synthesis_type
              - timestamp
            include_timestamp: Whether to add timestamp

        Returns:
            Formatted content with metadata
        """
        lines = []

        # Title
        if "title" in metadata:
            lines.append(f"# {metadata.get('title', '')}")
            lines.append("")

        # Metadata block
        lines.append("---")

        if "topic" in metadata:
            lines.append(f"**Topic:** {metadata.get('topic', '')}")

        if "sources_count" in metadata:
            lines.append(f"**Sources:** {metadata.get('sources_count', '')}")

        if "workflow" in metadata:
            lines.append(f"**Workflow:** {metadata.get('workflow', '')}")

        if include_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timestamp = metadata.get('timestamp', timestamp)
            lines.append(f"**Generated:** {timestamp}")

        lines.append("---")
        lines.append("")

        # Main content
        lines.append(content)

        return "\n".join(lines)

    def format_comparison_table(self, item1: str, item2: str, comparison_data: dict, format_type: str = "markdown") -> str:
        """
        Format comparison as side-by-side table.

        Args:
            item1: First item name
            item2: Second item name
            comparison_data: Comparison data with categories
            format_type: Output format (markdown, html)

        Returns:
            Formatted comparison table
        """
        categories = comparison_data.get("categories", [])
        item1_data = comparison_data.get(item1, [])
        item2_data = comparison_data.get(item2, [])

        # Prepare table data
        headers = ["Category", item1, item2]
        rows = []

        for i, category in enumerate(categories):
            row = [category, item1_data[i] if i < len(item1_data) else "", item2_data[i] if i < len(item2_data) else ""]
            rows.append(row)

        return self.format_as_table({"headers": headers, "rows": rows}, format_type=format_type)

    @tool_use
    def format_timeline(self, timeline_data: list[dict], format_type: str = "markdown") -> str:
        """
        Format timeline data.

        Args:
            timeline_data: List of timeline entries (period, description, sources)
            format_type: Output format

        Returns:
            Formatted timeline
        """
        if format_type == "markdown":
            lines = ["## Timeline\n"]

            for entry in timeline_data:
                period = entry.get("period", "Unknown")
                description = entry.get("description", "")
                sources = entry.get("sources", [])

                lines.append(f"### {period}")
                lines.append(f"{description}")

                if sources:
                    lines.append(f"*Sources: {', '.join(sources)}*")

                lines.append("")

            return "\n".join(lines)

        else:
            # Simple text format
            lines = []
            for entry in timeline_data:
                period = entry.get("period", "Unknown")
                description = entry.get("description", "")
                lines.append(f"{period}: {description}")

            return "\n".join(lines)

    @tool_use
    def format_summary_with_sections(self, sections: list[dict], title: str | None = None) -> str:
        """
        Format content with clear sections.

        Args:
            sections: List of sections (each with 'heading' and 'content')
            title: Optional main title

        Returns:
            Formatted markdown document
        """
        lines = []

        if title:
            lines.append(f"# {title}\n")

        for section in sections:
            heading = section.get("heading", "Section")
            content = section.get("content", "")
            level = section.get("level", 2)  # Default h2

            # Section heading
            lines.append(f"{'#' * level} {heading}\n")

            # Section content
            lines.append(content)
            lines.append("")  # Blank line between sections

        return "\n".join(lines)

    @tool_use
    def format_code_blocks(self, code_blocks: list[dict], include_language: bool = True) -> str:
        """
        Format code blocks with syntax highlighting markers.

        Args:
            code_blocks: List of code blocks (code, language)
            include_language: Whether to specify language

        Returns:
            Formatted code blocks
        """
        lines = []

        for i, block in enumerate(code_blocks, 1):
            code = block.get("code", "")
            language = block.get("language", "")

            if len(code_blocks) > 1:
                lines.append(f"**Code Block {i}**\n")

            if include_language and language:
                lines.append(f"```{language}")
            else:
                lines.append("```")

            lines.append(code.rstrip())
            lines.append("```")
            lines.append("")

        return "\n".join(lines)

    def format_error_message(self, error: str, context: DictParams | None = None) -> str:
        """
        Format error message with context.

        Args:
            error: Error message
            context: Optional context information

        Returns:
            Formatted error message
        """
        lines = ["## Error\n"]
        lines.append(f"**Message:** {error}\n")

        if context:
            lines.append("**Context:**")
            for key, value in context.items():
                lines.append(f"- {key}: {value}")

        return "\n".join(lines)
