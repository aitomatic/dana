"""Resource for file read/write operations.

Provides read() and write() tools mirroring Claude Code's file I/O signatures.
Supports text files, images (PNG, JPG, GIF, WebP, BMP), and PDFs.
"""

import base64
from pathlib import Path

from dana.common.protocols.war import named_tool
from dana.core.resource.base_resource import BaseResource


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
IMAGE_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}
PDF_EXTENSION = ".pdf"
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB (Anthropic API limit)
MAX_PDF_PAGES = 20
LARGE_PDF_THRESHOLD = 10  # pages


class FileIOResource(BaseResource):
    """Resource for file read/write operations."""

    def __init__(self, resource_id: str, base_path: str | Path | None = None, supports_vision: bool = True, **kwargs):
        """Initialize the FileIOResource.

        Args:
            resource_id: Unique identifier for this resource instance.
            base_path: Base directory for relative path resolution.
            supports_vision: Whether the LLM supports image/PDF content blocks.
                When False, uses VisionParser to extract text instead of base64.
            **kwargs: Additional arguments passed to the base resource.
        """
        super().__init__(resource_id=resource_id, **kwargs)
        self._base_path = Path(base_path) if base_path else Path.cwd()
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._supports_vision = supports_vision
        self._vision_parser = None  # lazy init

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path, supporting both absolute and relative paths.

        Args:
            file_path: Path to resolve (absolute or relative to base_path).

        Returns:
            Resolved absolute Path.
        """
        path = Path(file_path)
        if path.is_absolute():
            return path
        return self._base_path / path

    @named_tool(name="Read")
    async def read(
        self,
        file_path: str,
        offset: int | None = None,
        limit: int | None = 2000,
        pages: str | None = None,
    ) -> str | dict:
        """Read file contents. Supports text files (cat -n format), images, and PDFs.

        Args:
            file_path: Absolute path to the file to read
            offset: Line number to start reading from (1-indexed, text files only)
            limit: Maximum number of lines to read (default: 2000, text files only)
            pages: Page range for PDF files (e.g., "1-5", "3", "10-20")

        Returns:
            File contents with line numbers (text), or dict with inject_as_user (images/PDFs).
        """
        resolved_path = self._resolve_path(file_path)

        if not resolved_path.exists():
            return f"Error: File does not exist: {resolved_path}"

        if not resolved_path.is_file():
            return f"Error: Path is not a file: {resolved_path}"

        suffix = resolved_path.suffix.lower()

        if suffix in IMAGE_EXTENSIONS:
            if self._supports_vision:
                return self._read_image(resolved_path, suffix)
            else:
                return await self._read_image_extracted(resolved_path)
        elif suffix == PDF_EXTENSION:
            if self._supports_vision:
                return self._read_pdf(resolved_path, pages)
            else:
                return await self._read_pdf_extracted(resolved_path, pages)
        else:
            return self._read_text(resolved_path, offset, limit)

    def _read_text(self, resolved_path: Path, offset: int | None, limit: int | None) -> str:
        """Read a text file with line numbers (cat -n format)."""
        try:
            content = resolved_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            # Apply offset (1-indexed)
            start_line = 0
            if offset is not None:
                start_line = max(0, offset - 1)  # Convert to 0-indexed

            # Apply limit
            end_line = len(lines)
            if limit is not None:
                end_line = min(start_line + limit, len(lines))

            # Format with line numbers (cat -n style)
            result_lines = []
            for i in range(start_line, end_line):
                line_num = i + 1  # Convert back to 1-indexed for display
                # Truncate lines longer than 2000 characters
                line_content = lines[i]
                if len(line_content) > 2000:
                    line_content = line_content[:2000] + "..."
                result_lines.append(f"{line_num:6}\t{line_content}")

            if not result_lines:
                return f"File is empty: {resolved_path}"

            return "\n".join(result_lines)

        except UnicodeDecodeError:
            return f"Error: Cannot read file as text (binary file?): {resolved_path}"
        except PermissionError:
            return f"Error: Permission denied: {resolved_path}"
        except Exception as e:
            return f"Error reading file: {e}"

    def _read_image(self, path: Path, suffix: str) -> str | dict:
        """Read an image file and return as base64 content block for LLM consumption."""
        file_size = path.stat().st_size
        if file_size > MAX_IMAGE_SIZE:
            return f"Error: Image too large ({file_size / 1024 / 1024:.1f}MB). Max: 20MB"

        try:
            image_bytes = path.read_bytes()
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except Exception as e:
            return f"Error reading image: {e}"

        b64_data = base64.b64encode(image_bytes).decode("ascii")
        media_type = IMAGE_MEDIA_TYPES.get(suffix, "image/png")

        return {
            "message": f"Image: {path.name} ({file_size / 1024:.1f}KB, {media_type})",
            "inject_as_user": [
                {"type": "text", "text": f"Visual contents of {path.name}:"},
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": b64_data},
                },
            ],
        }

    def _read_pdf(self, path: Path, pages: str | None) -> str | dict:
        """Read a PDF file and return as base64 content block for LLM consumption."""
        file_size = path.stat().st_size

        if pages:
            return self._read_pdf_pages(path, pages)

        # Check page count for large PDFs
        try:
            import fitz

            doc = fitz.open(str(path))
            page_count = doc.page_count
            doc.close()
            if page_count > LARGE_PDF_THRESHOLD:
                return (
                    f"Error: PDF has {page_count} pages (>{LARGE_PDF_THRESHOLD}). "
                    f"Use pages parameter to select a range (e.g., pages='1-{min(page_count, MAX_PDF_PAGES)}')"
                )
        except ImportError:
            pass  # pymupdf not available, send full PDF

        try:
            pdf_bytes = path.read_bytes()
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except Exception as e:
            return f"Error reading PDF: {e}"

        b64_data = base64.b64encode(pdf_bytes).decode("ascii")

        return {
            "message": f"PDF: {path.name} ({file_size / 1024:.1f}KB)",
            "inject_as_user": [
                {"type": "text", "text": f"Contents of {path.name}:"},
                {
                    "type": "document",
                    "source": {"type": "base64", "media_type": "application/pdf", "data": b64_data},
                },
            ],
        }

    def _read_pdf_pages(self, path: Path, pages: str) -> str | dict:
        """Read specific pages from a PDF using pymupdf."""
        try:
            import fitz
        except ImportError:
            return "Error: pymupdf (fitz) required for page selection. Install with: pip install pymupdf"

        try:
            start, end = self._parse_page_range(pages)
        except ValueError:
            return f"Error: Invalid page range '{pages}'. Use format like '1-5', '3', or '10-20'."

        if end - start + 1 > MAX_PDF_PAGES:
            return f"Error: Max {MAX_PDF_PAGES} pages per request. Requested {end - start + 1}."

        doc = fitz.open(str(path))
        if start > doc.page_count:
            page_count = doc.page_count
            doc.close()
            return f"Error: Page {start} exceeds document length ({page_count} pages)"

        end = min(end, doc.page_count)

        # Create a new PDF with selected pages
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start - 1, to_page=end - 1)  # 0-indexed
        pdf_bytes = new_doc.tobytes()
        new_doc.close()
        doc.close()

        b64_data = base64.b64encode(pdf_bytes).decode("ascii")

        return {
            "message": f"PDF: {path.name} pages {start}-{end} ({len(pdf_bytes) / 1024:.1f}KB)",
            "inject_as_user": [
                {"type": "text", "text": f"Contents of {path.name} (pages {start}-{end}):"},
                {
                    "type": "document",
                    "source": {"type": "base64", "media_type": "application/pdf", "data": b64_data},
                },
            ],
        }

    @staticmethod
    def _parse_page_range(pages: str) -> tuple[int, int]:
        """Parse page range string: '1-5' -> (1, 5), '3' -> (3, 3)."""
        pages = pages.strip()
        if "-" in pages:
            parts = pages.split("-", 1)
            return int(parts[0]), int(parts[1])
        page = int(pages)
        return page, page

    # ========================================================================
    # VisionParser fallback (non-vision models)
    # ========================================================================

    def _get_vision_parser(self):
        """Lazy-init VisionParser for non-vision model fallback."""
        if self._vision_parser is None:
            from aicapture.vision_parser import VisionParser

            self._vision_parser = VisionParser()
        return self._vision_parser

    async def _read_image_extracted(self, path: Path) -> str:
        """Extract text content from an image using VisionParser."""
        try:
            parser = self._get_vision_parser()
            result = await parser.process_image_async(str(path))
            pages = result.get("file_object", {}).get("pages", [])
            content = "\n\n".join(p["page_content"] for p in pages)
            return f"[Extracted content from {path.name}]\n\n{content}"
        except Exception as e:
            return f"Error extracting image content: {e}"

    async def _read_pdf_extracted(self, path: Path, pages: str | None) -> str:
        """Extract text content from a PDF using VisionParser."""
        if pages:
            return await self._read_pdf_pages_extracted(path, pages)
        try:
            parser = self._get_vision_parser()
            result = await parser.process_pdf_async(str(path))
            file_obj = result.get("file_object", {})
            page_list = file_obj.get("pages", [])
            parts = []
            for p in page_list:
                parts.append(f"===== Page: {p['page_number']} =====\n{p['page_content']}")
            return f"[Extracted content from {path.name}]\n\n" + "\n\n".join(parts)
        except Exception as e:
            return f"Error extracting PDF content: {e}"

    async def _read_pdf_pages_extracted(self, path: Path, pages: str) -> str:
        """Extract specific pages from a PDF using VisionParser."""
        import asyncio

        try:
            import fitz
        except ImportError:
            return "Error: pymupdf (fitz) required for page selection. Install with: pip install pymupdf"

        try:
            start, end = self._parse_page_range(pages)
        except ValueError:
            return f"Error: Invalid page range '{pages}'. Use format like '1-5', '3', or '10-20'."

        if end - start + 1 > MAX_PDF_PAGES:
            return f"Error: Max {MAX_PDF_PAGES} pages per request. Requested {end - start + 1}."

        doc = fitz.open(str(path))
        if start > doc.page_count:
            page_count = doc.page_count
            doc.close()
            return f"Error: Page {start} exceeds document length ({page_count} pages)"
        end = min(end, doc.page_count)

        try:
            from aicapture.utils.hash_utils import HashUtils

            parser = self._get_vision_parser()
            file_hash = HashUtils.calculate_file_hash(str(path))
            page_extractions = parser._extract_text_from_pdf(str(path))

            async def extract_one(page_idx):
                page_info = page_extractions[page_idx]
                img = await parser._get_or_create_page_image(doc, page_idx, page_info["hash"], file_hash)
                result = await parser.process_page_async(
                    img,
                    page_number=page_info["page_number"],
                    page_hash=page_info["hash"],
                    text_content=page_info["text"],
                )
                img.close()
                return result

            tasks = [extract_one(i) for i in range(start - 1, end)]  # 0-indexed
            results = await asyncio.gather(*tasks)

            parts = []
            for r in results:
                parts.append(f"===== Page: {r['page_number']} =====\n{r['page_content']}")
            return f"[Extracted from {path.name} pages {start}-{end}]\n\n" + "\n\n".join(parts)
        except Exception as e:
            return f"Error extracting PDF pages: {e}"
        finally:
            doc.close()
