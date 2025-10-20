"""
DeepExtractionResource - Extracts text from PDF and image files using VLM.

This resource handles:
- PDF text extraction using aicapture VisionParser
- Image text extraction using aicapture VisionParser
- VLM-based extraction for enhanced accuracy
- Error handling for unsupported formats
- Returns structured text data
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource

# Import aicapture components
try:
    from aicapture import VisionParser
    from aicapture import OpenAIVisionModel, AnthropicVisionModel, GeminiVisionModel

    AICAPTURE_AVAILABLE = True
except ImportError:
    AICAPTURE_AVAILABLE = False


class DeepExtractionResource(BaseResource):
    """
    Resource for extracting text from PDF and image files using VLM.

    Supports:
    - PDF files (.pdf)
    - Image files (.png, .jpg, .jpeg, .tiff, .bmp)
    - VLM-based extraction for enhanced accuracy
    - Error handling for unsupported formats
    """

    def __init__(self, resource_id: str | None = None, llm_provider: str = "openai", model: str = "gpt-4.1-mini", **kwargs):
        """
        Initialize the DeepExtractionResource.

        Args:
            resource_id: Unique identifier for this resource
            llm_provider: LLM provider (anthropic, openai, gemini)
            model: Model name for the vision model
            **kwargs: Additional arguments passed to BaseResource
        """
        super().__init__(resource_type="deep-extraction", resource_id=resource_id or "deep-extraction", **kwargs)

        self.llm_provider = llm_provider
        self.model = model
        self.parser = None

        # Initialize vision parser if aicapture is available
        if AICAPTURE_AVAILABLE:
            self._initialize_vision_parser()

    def _initialize_vision_parser(self):
        """Initialize the vision parser with the configured VLM provider."""
        try:
            # Map LLM provider to vision model class
            if self.llm_provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY environment variable not set")
                vision_model = AnthropicVisionModel(model=self.model, api_key=api_key)  # type: ignore
            elif self.llm_provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY environment variable not set")
                vision_model = OpenAIVisionModel(model=self.model, api_key=api_key)  # type: ignore
            elif self.llm_provider == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY environment variable not set")
                vision_model = GeminiVisionModel(model=self.model, api_key=api_key)  # type: ignore
            else:
                raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

            # Initialize the vision parser
            self.parser = VisionParser(vision_model=vision_model)  # type: ignore

        except Exception as e:
            # If vision parser initialization fails, we'll fall back to traditional methods
            self.parser = None
            print(f"Warning: Failed to initialize vision parser: {e}")

    @tool_use
    def extract(self, file_path: str, **kwargs) -> DictParams:
        """
        Extract text from PDF or image file using VLM or traditional methods.

        Args:
            file_path: Path to the PDF or image file
            **kwargs: Additional parameters (not used)

        Returns:
            {
                "success": bool,
                "extracted_text": str,
                "file_type": str,
                "error": str (if failed)
            }
        """
        try:
            # Validate file path
            if not file_path or not os.path.exists(file_path):
                return {"success": False, "extracted_text": "", "file_type": "unknown", "error": f"File not found: {file_path}"}

            file_path = Path(file_path)
            file_extension = file_path.suffix.lower()

            # Try VLM-based extraction first if parser is available
            if self.parser and AICAPTURE_AVAILABLE:
                return self._extract_with_vision_parser(str(file_path), file_extension)
            else:
                # Fall back to traditional methods
                return self._extract_with_traditional_methods(str(file_path), file_extension)

        except Exception as e:
            return {"success": False, "extracted_text": "", "file_type": "unknown", "error": f"Extraction failed: {str(e)}"}

    def _extract_with_vision_parser(self, file_path: str, file_extension: str) -> DictParams:
        """Extract text using aicapture VisionParser."""
        try:
            if self.parser is None:
                raise ValueError("Vision parser not initialized")

            if file_extension == ".pdf":
                result = self.parser.process_pdf(file_path)  # type: ignore
            elif file_extension in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
                result = self.parser.process_image(file_path)  # type: ignore
            else:
                return {
                    "success": False,
                    "extracted_text": "",
                    "file_type": file_extension,
                    "error": f"Unsupported file format: {file_extension}",
                }

            # Extract text from VisionParser result
            if result and "file_object" in result:
                file_object = result["file_object"]
                if "pages" in file_object:
                    # Combine all page content
                    extracted_text = "\n".join(page.get("page_content", "") for page in file_object["pages"])
                else:
                    extracted_text = file_object.get("content", "")

                return {"success": True, "extracted_text": extracted_text.strip(), "file_type": file_extension, "error": None}
            else:
                return {"success": False, "extracted_text": "", "file_type": file_extension, "error": "VisionParser returned empty result"}

        except Exception as e:
            return {
                "success": False,
                "extracted_text": "",
                "file_type": file_extension,
                "error": f"Vision parser extraction failed: {str(e)}",
            }

    def _extract_with_traditional_methods(self, file_path: str, file_extension: str) -> DictParams:
        """Extract text using traditional PyPDF2/pytesseract methods."""
        # Determine file type and extract accordingly
        if file_extension == ".pdf":
            return self._extract_from_pdf(file_path)
        elif file_extension in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            return self._extract_from_image(file_path)
        else:
            return {
                "success": False,
                "extracted_text": "",
                "file_type": file_extension,
                "error": f"Unsupported file format: {file_extension}",
            }

    def _extract_from_pdf(self, file_path: str) -> DictParams:
        """Extract text from PDF file."""
        try:
            import PyPDF2  # type: ignore

            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""

                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"

                return {"success": True, "extracted_text": text.strip(), "file_type": "pdf", "error": None}

        except ImportError:
            return {
                "success": False,
                "extracted_text": "",
                "file_type": "pdf",
                "error": "PyPDF2 not installed. Install with: pip install PyPDF2",
            }
        except Exception as e:
            return {"success": False, "extracted_text": "", "file_type": "pdf", "error": f"PDF extraction failed: {str(e)}"}

    def _extract_from_image(self, file_path: str) -> DictParams:
        """Extract text from image using OCR."""
        try:
            import pytesseract  # type: ignore
            from PIL import Image  # type: ignore

            # Open image and extract text
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)

            return {"success": True, "extracted_text": text.strip(), "file_type": "image", "error": None}

        except ImportError:
            return {
                "success": False,
                "extracted_text": "",
                "file_type": "image",
                "error": "pytesseract or PIL not installed. Install with: pip install pytesseract pillow",
            }
        except Exception as e:
            return {"success": False, "extracted_text": "", "file_type": "image", "error": f"OCR extraction failed: {str(e)}"}
