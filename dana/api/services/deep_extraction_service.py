"""
Visual Document Service Module

This module provides business logic for visual document extraction and processing.
Supports various file types that aicapture can handle.
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Any

from dana.api.core.schemas import DeepExtractionRequest, DeepExtractionResponse, FileObject, PageContent

logger = logging.getLogger(__name__)


class DeepExtractionService:
    """
    Service for handling visual document extraction operations.
    """

    def __init__(self):
        """Initialize the visual document service."""
        self.supported_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".tiff",
            ".tif",  # Images
            ".pdf",  # PDFs
            ".docx",
            ".doc",  # Word documents
            ".pptx",
            ".ppt",  # PowerPoint presentations
            ".xlsx",
            ".xls",  # Excel spreadsheets
            ".txt",
            ".md",
            ".rtf",  # Text documents
        }

    def is_supported_file_type(self, file_path: str) -> bool:
        """
        Check if the file type is supported for extraction.

        Args:
            file_path: Path to the file

        Returns:
            True if file type is supported, False otherwise
        """
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.supported_extensions

    def generate_cache_key(self, file_path: str, prompt: str | None = None) -> str:
        """
        Generate a cache key for the file and prompt combination.

        Args:
            file_path: Path to the file
            prompt: Optional prompt for extraction

        Returns:
            Cache key string
        """
        # Create a hash of file path and prompt
        content = f"{file_path}:{prompt or ''}"
        return hashlib.sha256(content.encode()).hexdigest()

    def generate_page_hash(self, page_content: str) -> str:
        """
        Generate a hash for page content.

        Args:
            page_content: Content of the page

        Returns:
            Hash string
        """
        return hashlib.sha256(page_content.encode()).hexdigest()

    def count_words(self, text: str) -> int:
        """
        Count words in text.

        Args:
            text: Text to count words in

        Returns:
            Number of words
        """
        return len(text.split())

    async def deep_extract(self, request: DeepExtractionRequest) -> DeepExtractionResponse:
        """
        Extract data from a visual document.

        Args:
            request: Extraction request containing file_path, prompt, and config

        Returns:
            VisualDocumentExtractionResponse with extracted data
        """
        try:
            file_path = request.file_path
            prompt = request.prompt
            config = request.config or {}

            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Check if file type is supported
            if not self.is_supported_file_type(file_path):
                raise ValueError(f"Unsupported file type: {Path(file_path).suffix}")

            # Generate cache key
            cache_key = self.generate_cache_key(file_path, prompt)

            # Get file info
            file_name = Path(file_path).name
            file_full_path = os.path.abspath(file_path)

            # Mock extraction logic - in real implementation, this would call aicapture
            # For now, we'll create a mock response based on the file type
            extracted_content = self._mock_extract_content(file_path, prompt, config)

            # Generate page hash
            page_hash = self.generate_page_hash(extracted_content)

            # Count words
            total_words = self.count_words(extracted_content)

            # Create page content
            page_content = PageContent(page_number=1, page_content=extracted_content, page_hash=page_hash)

            # Create file object
            file_object = FileObject(
                file_name=file_name,
                cache_key=cache_key,
                total_pages=1,
                total_words=total_words,
                file_full_path=file_full_path,
                pages=[page_content],
            )

            return DeepExtractionResponse(file_object=file_object)

        except Exception as e:
            logger.error(f"Error extracting visual document: {e}")
            raise

    def _mock_extract_content(self, file_path: str, prompt: str | None, config: dict[str, Any]) -> str:
        """
        Mock content extraction based on file type.
        In real implementation, this would call aicapture or similar service.

        Args:
            file_path: Path to the file
            prompt: Optional extraction prompt
            config: Optional configuration

        Returns:
            Extracted content as markdown
        """
        file_ext = Path(file_path).suffix.lower()
        file_name = Path(file_path).name

        # Mock content based on file type
        if file_ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif"]:
            if "heart" in file_name.lower():
                return """```markdown
Diagram type: Anatomical diagram of the human heart (cross-sectional view)

Components and their functions:
- Superior vena cava: Large vein carrying deoxygenated blood from the upper body to the right atrium.
- Inferior vena cava: Large vein carrying deoxygenated blood from the lower body to the right atrium.
- Right atrium: Receives deoxygenated blood from the body via the superior and inferior vena cava.
- Right ventricle: Pumps deoxygenated blood to the lungs via the pulmonary artery.
- Pulmonary valve: Valve between the right ventricle and pulmonary artery, prevents backflow of blood.
- Tricuspid valve: Valve between the right atrium and right ventricle, prevents backflow of blood.
- Pulmonary artery: Carries deoxygenated blood from the right ventricle to the lungs.
- Pulmonary vein: Carries oxygenated blood from the lungs to the left atrium.
- Left atrium: Receives oxygenated blood from the lungs via the pulmonary veins.
- Left ventricle: Pumps oxygenated blood to the body via the aorta.
- Mitral valve: Valve between the left atrium and left ventricle, prevents backflow of blood.
- Aortic valve: Valve between the left ventricle and aorta, prevents backflow of blood.
- Aorta: Main artery carrying oxygenated blood from the left ventricle to the body.

Connections and relationships:
- Blood flows from the superior and inferior vena cava into the right atrium.
- From the right atrium, blood passes through the tricuspid valve into the right ventricle.
- The right ventricle pumps blood through the pulmonary valve into the pulmonary artery, which leads to the lungs.
- Oxygenated blood returns from the lungs via the pulmonary veins to the left atrium.
- Blood flows from the left atrium through the mitral valve into the left ventricle.
- The left ventricle pumps blood through the aortic valve into the aorta, distributing it to the body.

Labels and annotations:
- Arrows indicate the direction of blood flow through the heart chambers, valves, and vessels.
- Each heart chamber and valve is clearly labeled.
- Major blood vessels (superior vena cava, inferior vena cava, pulmonary artery, pulmonary vein, aorta) are labeled.

Purpose and operation:
- The diagram illustrates the structure of the human heart and the flow of blood through its chambers, valves, and major vessels.
- It shows the separation of oxygenated and deoxygenated blood and the role of valves in preventing backflow.
- The diagram is useful for understanding cardiovascular anatomy and physiology.
```"""
            else:
                return f"""```markdown
Image type: {file_ext.upper()[1:]} image file

File information:
- Filename: {file_name}
- File type: {file_ext.upper()[1:]} image
- Extraction prompt: {prompt or "No specific prompt provided"}

Content description:
This appears to be an image file. The content would be extracted based on the visual elements present in the image, including any text, diagrams, charts, or other visual information.

Note: This is a mock response. In a real implementation, this would contain the actual extracted content from the image using computer vision and OCR techniques.
```"""

        elif file_ext == ".pdf":
            return f"""```markdown
Document type: PDF document

File information:
- Filename: {file_name}
- File type: PDF document
- Extraction prompt: {prompt or "No specific prompt provided"}

Content description:
This is a PDF document. The content would be extracted using PDF parsing techniques, including text extraction, table recognition, and image analysis if present.

Note: This is a mock response. In a real implementation, this would contain the actual extracted text and structured content from the PDF.
```"""

        elif file_ext in [".docx", ".doc"]:
            return f"""```markdown
Document type: Microsoft Word document

File information:
- Filename: {file_name}
- File type: Word document ({file_ext.upper()[1:]})
- Extraction prompt: {prompt or "No specific prompt provided"}

Content description:
This is a Microsoft Word document. The content would be extracted using document parsing libraries, preserving formatting, tables, and embedded objects.

Note: This is a mock response. In a real implementation, this would contain the actual extracted text and formatting from the Word document.
```"""

        elif file_ext in [".pptx", ".ppt"]:
            return f"""```markdown
Document type: Microsoft PowerPoint presentation

File information:
- Filename: {file_name}
- File type: PowerPoint presentation ({file_ext.upper()[1:]})
- Extraction prompt: {prompt or "No specific prompt provided"}

Content description:
This is a Microsoft PowerPoint presentation. The content would be extracted slide by slide, including text, images, charts, and speaker notes.

Note: This is a mock response. In a real implementation, this would contain the actual extracted content from each slide of the presentation.
```"""

        elif file_ext in [".xlsx", ".xls"]:
            return f"""```markdown
Document type: Microsoft Excel spreadsheet

File information:
- Filename: {file_name}
- File type: Excel spreadsheet ({file_ext.upper()[1:]})
- Extraction prompt: {prompt or "No specific prompt provided"}

Content description:
This is a Microsoft Excel spreadsheet. The content would be extracted including cell data, formulas, charts, and formatting information.

Note: This is a mock response. In a real implementation, this would contain the actual extracted data from the spreadsheet, including tables and charts.
```"""

        else:
            return f"""```markdown
Document type: Text document

File information:
- Filename: {file_name}
- File type: {file_ext.upper()[1:]} text document
- Extraction prompt: {prompt or "No specific prompt provided"}

Content description:
This is a text document. The content would be extracted directly from the file, preserving formatting and structure.

Note: This is a mock response. In a real implementation, this would contain the actual text content from the document.
```"""
