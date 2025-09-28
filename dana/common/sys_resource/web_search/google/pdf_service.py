"""PDF content extraction service."""

import asyncio
import logging
from io import BytesIO

import httpx
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFService:
    """Handles PDF document processing and text extraction."""

    def __init__(self, timeout: int = 30):
        """
        Initialize PDF service.

        Args:
            timeout: HTTP timeout for PDF download in seconds
        """
        self.timeout = timeout

    async def extract_text_from_pdf_url(self, url: str) -> str:
        """
        Extract text from a PDF at the given URL.

        Args:
            url: URL of the PDF document

        Returns:
            Extracted text content
        """
        logger.info(f"📄 Extracting text from PDF: {url}")

        try:
            # Download PDF content
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=self.timeout)) as client:
                response = await client.get(url)
                response.raise_for_status()
                pdf_data = response.content

            # Extract text from PDF
            text = await self._extract_text_from_pdf_data(pdf_data)

            logger.info(f"✅ Extracted {len(text)} characters from PDF")
            return text

        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to download PDF: {e}")
            return ""
        except Exception as e:
            logger.error(f"❌ PDF extraction failed: {e}")
            return ""

    async def _extract_text_from_pdf_data(self, pdf_data: bytes) -> str:
        """
        Extract text from PDF data using PyPDF2.

        Args:
            pdf_data: PDF file data

        Returns:
            Extracted text
        """
        try:
            # Run PDF processing in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._process_pdf_sync, pdf_data)

        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ""

    def _process_pdf_sync(self, pdf_data: bytes) -> str:
        """Synchronous PDF processing (run in executor)."""
        try:
            pdf_file = BytesIO(pdf_data)
            pdf_reader = PdfReader(pdf_file)

            text_parts = []
            num_pages = len(pdf_reader.pages)

            logger.debug(f"Processing PDF with {num_pages} pages")

            for i, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {i + 1}: {e}")
                    continue

            full_text = "\n".join(text_parts)
            return full_text.strip()

        except Exception as e:
            logger.error(f"Synchronous PDF processing failed: {e}")
            return ""
