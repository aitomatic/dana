# flake8: noqa: E501

import asyncio
import hashlib
import json
import os
import time
from asyncio import Semaphore
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz  # type: ignore
from loguru import logger
from PIL import Image

from .cache import FileCache, HashUtils, ImageCache, TwoLayerCache
from .content_cleaner import ContentCleaner
from .settings import MAX_CONCURRENT_TASKS, ImageQuality
from .vision_models import VisionModel, create_default_vision_model

DEFAULT_PROMPT = """
<GENERAL_INSTRUCTIONS>
Extract the document content, following these guidelines:

Text Content:
- Extract all text in correct reading order, preserving original formatting and hierarchy
- Maintain section headers, subheaders, and their relationships
- Include all numerical values, units, and technical specifications,
- DO NOT summarize the content or skip any sections, we need all the details as possible.

Tables:
- Convert to markdown format with clear column headers, keep the nested structure as it is.
- Preserve all numerical values, units, and relationships
- Include table title/caption and any reference numbers

Graphs & Charts:
- Identify the visualization type (line graph, bar chart, scatter plot, etc.)
- List all axes labels and their units
- Describe all the insights, trends, or patterns
- Include details for all annotations, legends, labels, etc.
- Explain what the visualization is demonstrating

Diagrams & Schematics:
- Identify the type of diagram (block diagram, circuit schematic, flowchart, etc.)
- List all components and their functions
- Describe all connections and relationships between components
- Include all labels, values, or specifications
- Explain purpose and operation of the diagram

Images:
- Describe what the image shows
- Include all measurements, dimensions, or specifications
- Capture all text, labels, or annotations
- Explain the purpose or meaning of the image

Don't generate repetitive empty lines or empty table rows.
Output in markdown format, with all details, do not include introductory phrases or meta-commentary.
</GENERAL_INSTRUCTIONS>
"""


class PDFValidationError(Exception):
    """Raised when PDF validation fails."""


class ImageValidationError(Exception):
    """Raised when image validation fails."""


class VisionParser:
    """
    A class for extracting content from PDF documents and images using Vision Language Models.
    Supports multiple VLM providers through a pluggable vision model interface.
    Features:
    - Multiple image processing
    - High-quality image support
    - Configurable concurrency
    - Result caching
    - Text extraction for improved accuracy
    - Direct image file processing
    """

    SUPPORTED_IMAGE_FORMATS = {"jpg", "jpeg", "png", "tiff", "tif", "webp", "bmp"}

    # Class variable for global concurrency control
    _semaphore: Semaphore = Semaphore(MAX_CONCURRENT_TASKS)

    def __init__(  # noqa
        self,
        vision_model: VisionModel | None = None,
        cache_dir: str | None = None,
        max_concurrent_tasks: int = MAX_CONCURRENT_TASKS,
        image_quality: str = ImageQuality.DEFAULT,
        invalidate_cache: bool = False,
        cloud_bucket: str | None = None,
        prompt: str = DEFAULT_PROMPT,
        dpi: int = int(os.getenv("VISION_PARSER_DPI", "333")),
    ):
        """
        Initialize the VisionParser.

        Args:
            vision_model (Optional[VisionModel]): Vision model instance to use.
            If None, creates default model based on environment settings.
            cache_dir (Optional[str]): Directory to store cached results
            max_concurrent_tasks (int): maximum concurrent API calls
            image_quality (str): Image quality setting (low/high)
            invalidate_cache (bool): If True, ignore cache and overwrite with new results
            prompt (str): The instruction prompt to use for content extraction
        """
        self.vision_model = vision_model or create_default_vision_model()
        self.vision_model.image_quality = image_quality
        self._invalidate_cache = invalidate_cache
        self.prompt = prompt
        self.dpi = dpi
        self.cloud_bucket = cloud_bucket
        self.content_cleaner = ContentCleaner()
        if max_concurrent_tasks is not None:
            self.__class__._semaphore = Semaphore(max_concurrent_tasks)

        self._image_cache = ImageCache(cache_dir, cloud_bucket)
        s3_cache = None
        if self.cloud_bucket:
            from .cache import S3Cache

            s3_cache = S3Cache(bucket=self.cloud_bucket, prefix="production/data/cache-documents")
        self.cache = TwoLayerCache(
            # type: ignore
            file_cache=FileCache(cache_dir),
            s3_cache=s3_cache,
            invalidate_cache=invalidate_cache,
        )

    @property
    def invalidate_cache(self) -> bool:
        """Get the invalidate_cache value."""
        return self._invalidate_cache

    @invalidate_cache.setter
    def invalidate_cache(self, value: bool) -> None:
        """
        Set the invalidate_cache value and update the cache accordingly.

        Args:
            value (bool): Whether to invalidate the cache
        """
        self._invalidate_cache = value
        if hasattr(self, "cache"):
            self.cache.invalidate_cache = value

    async def _get_or_create_page_image(self, doc: fitz.Document, page_idx: int, page_hash: str, file_hash: str) -> Image.Image:
        """Get a page image from cache or create it if not cached.

        Args:
            doc: The PyMuPDF document
            page_idx: Zero-based page index
            page_hash: Hash of the page content
            file_hash: Hash of the PDF file

        Returns:
            PIL Image object of the page
        """
        # Check if the file_hash directory exists in cache
        cache_dir = self._image_cache._get_local_cache_path(file_hash)
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Check if this specific page is cached
        page_image_path = cache_dir / f"{page_hash}.png"

        if page_image_path.exists():
            try:
                # Load cached image and ensure data is loaded into memory
                with Image.open(page_image_path) as cached_img:
                    # Load the image data to avoid file handle issues
                    cached_img.load()
                    logger.info(f"Using cached image for page {page_idx + 1} from {page_image_path}")
                    return cached_img  # type: ignore
            except Exception as e:
                logger.warning(f"Cached image {page_image_path} is corrupted: {e}. Regenerating...")
                # Remove the corrupted file and regenerate
                try:
                    page_image_path.unlink()
                except Exception:
                    pass

        # Generate the image if not cached or cache was corrupted
        logger.info(f"Generating image for page {page_idx + 1}")
        page = doc[page_idx]
        zoom = self.dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)

        # Convert pixmap to PIL Image
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # Cache the image locally
        try:
            img.save(page_image_path, "PNG")
            logger.info(f"Cached page image to {page_image_path}")
        except Exception as e:
            logger.error(f"Error caching page image: {e}")

        return img

    def _validate_pdf(self, pdf_path: str) -> None:
        """
        Validate that the file has a PDF extension.

        Args:
            pdf_path (str): Path to the PDF file

        Raises:
            PDFValidationError: If the file doesn't have a .pdf extension
        """
        if not str(pdf_path).lower().endswith(".pdf"):
            raise PDFValidationError("File must have a .pdf extension")

    def _extract_text_from_pdf(self, pdf_path: str) -> list[dict]:
        """Extract text content and calculate page hashes from PDF using PyMuPDF.

        Returns:
            List of dictionaries with 'text' and 'hash' for each page
        """
        results = []
        with fitz.open(pdf_path) as doc:
            for page_idx, page in enumerate(doc):
                # Extract text
                text = page.get_text()

                # Calculate page hash based on file hash, page number and text content
                page_number = page_idx + 1
                page_text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
                page_hash = f"p{page_number}_{page_text_hash}"

                results.append({"text": text, "hash": page_hash, "page_number": page_number})
        return results

    def _make_user_message(self, text_content: str) -> str:
        """Create enhanced user message with text extraction reference."""
        return f"{self.prompt}\n\nText content extracted from this page by using PyMuPDF, use this for reference and improve accuracy:\n<text_content>\n{text_content}\n</text_content>"

    async def process_page_async(
        self,
        image: Image.Image,
        page_number: int,
        page_hash: str,
        text_content: str = "",
    ) -> dict:
        """Process a single page asynchronously and return structured content."""
        try:
            logger.debug(f"Waiting for semaphore to process page {page_number}")
            # Process with vision model
            async with self.__class__._semaphore:
                logger.debug(f"Acquired semaphore - Started processing page {page_number}")
                enhanced_prompt = self._make_user_message(text_content)

                content = await self.vision_model.process_image_async(
                    image,
                    prompt=enhanced_prompt,
                )
                logger.debug(f"Completed processing page {page_number} - Releasing semaphore")

            # Clean the content to remove base64 and repetitive spaces
            cleaned_content = self.content_cleaner.clean_content(content.strip())

            return {
                "page_number": page_number,
                "page_content": cleaned_content,
                "page_hash": page_hash,
                # "page_objects": [
                #     {
                #         "md": cleaned_content,
                #         "has_image": False,  # not used for now
                #     }
                # ],
            }

        except Exception as e:
            logger.error(f"Error processing page {page_number}: {str(e)}")
            raise

    def save_markdown_output(self, result: dict, output_dir: str = "tmp/md") -> None:
        """Save the processing result to a Markdown file.

        Args:
            result (Dict): The processing result
            output_dir (str): Directory to save the markdown file
        """
        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Get the original filename and create markdown filename
            original_filename = Path(result["file_object"]["file_name"]).stem
            markdown_file = output_path / f"{original_filename}.md"

            with open(markdown_file, "w", encoding="utf-8") as f:
                for page in result["file_object"]["pages"]:
                    f.write(f"\n===== Page: {page['page_number']} =====\n\n")
                    f.write(page["page_content"])
                    f.write("\n\n")

            logger.info(f"Markdown output saved to {markdown_file}")
        except Exception as e:
            logger.error(f"Error saving markdown output: {str(e)}")
            raise

    def _get_partial_cache_path(self, cache_key: str) -> Path:
        """Get the path for partial results cache file."""
        return self.cache.file_cache.cache_dir / f"{cache_key}_partial.json"

    async def _load_partial_results(self, cache_key: str) -> dict[int, dict]:
        """Load partial processing results if they exist."""
        cache_path = self._get_partial_cache_path(cache_key)
        try:
            if cache_path.exists():
                with open(cache_path, encoding="utf-8") as f:
                    return {int(k): v for k, v in json.load(f).items()}
        except Exception as e:
            logger.warning(f"Error loading partial results: {str(e)}")
        return {}

    async def _save_partial_results(self, cache_key: str, pages: list[dict]) -> None:
        """Save partial processing results."""
        cache_path = self._get_partial_cache_path(cache_key)
        try:
            # Convert list of pages to dict with page_number as key
            pages_dict = {page["page_number"]: page for page in pages}

            # Load existing results and update with new pages
            existing_results = await self._load_partial_results(cache_key)
            existing_results.update(pages_dict)

            # Save updated results
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(existing_results, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved partial results to {cache_path}")
        except Exception as e:
            logger.warning(f"Error saving partial results: {str(e)}")

    async def _validate_and_setup(self, pdf_path: str) -> tuple[Path, str]:
        """Validate PDF file and setup initial processing."""
        pdf_file = Path(pdf_path)
        logger.debug(f"Starting to process PDF file: {pdf_file.name}")

        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_file}")

        # Validate PDF
        self._validate_pdf(str(pdf_file))

        # Calculate file hash
        file_hash = HashUtils.calculate_file_hash(str(pdf_file))
        logger.debug(f"Calculated file hash: {file_hash}")

        return pdf_file, file_hash

    async def _process_pdf_chunk(  # noqa
        self,
        doc: fitz.Document,
        chunk_start: int,
        chunk_end: int,
        page_extractions: list[dict],
        partial_results: dict[int, dict],
        cache_key: str,
        all_pages: list[dict],
        file_hash: str,
    ) -> tuple[list[dict], int]:
        """
        Process a specific chunk of pages from a PDF document.

        Args:
            doc: The open PDF document
            chunk_start: Starting page index (0-based)
            chunk_end: Ending page index (exclusive)
            page_extractions: Text and hash extracted from PDF pages
            partial_results: Previously processed pages
            cache_key: Cache key for the PDF file
            all_pages: Current list of processed pages
            file_hash: Hash of the PDF file

        Returns:
            Tuple of (updated all_pages list, total words in this chunk)
        """
        logger.info(f"Processing chunk from page {chunk_start + 1} to {chunk_end}")

        total_words = 0
        tasks = []
        page_images = []

        try:
            # Process each page in the chunk
            for page_idx in range(chunk_start, chunk_end):
                page_number = page_idx + 1

                # Skip if page is already in partial results
                if page_number in partial_results:
                    logger.info(f"Page {page_number} already in partial results, skipping")
                    continue

                # Get page info with text and hash
                page_info = page_extractions[page_idx]
                page_hash = page_info["hash"]
                text_content = page_info["text"]

                # Get the page image from cache or generate it
                img = await self._get_or_create_page_image(doc, page_idx, page_hash, file_hash)
                page_images.append(img)

                # Create task to process the page
                task = asyncio.create_task(self.process_page_async(img, page_number, page_hash, text_content))
                tasks.append(task)

            # Process all tasks concurrently
            if tasks:
                start_time = time.time()
                batch_results = await asyncio.gather(*tasks)
                duration = time.time() - start_time

                # Calculate words in batch
                batch_words = sum(len(page["page_content"].split()) for page in batch_results)
                logger.info(f"Completed batch in {duration:.2f} seconds")

                # Add batch results to all pages
                all_pages.extend(batch_results)
                total_words += batch_words

                # Save partial results after each batch
                await self._save_partial_results(cache_key, all_pages)

        finally:
            # Clean up page images to free memory
            for img in page_images:
                try:
                    img.close()
                except Exception:
                    pass  # Continue cleanup even if one image fails

        # Add already processed pages from partial results for this chunk
        for page_idx in range(chunk_start, chunk_end):
            page_number = page_idx + 1
            if page_number in partial_results and not any(p["page_number"] == page_number for p in all_pages):
                logger.info(f"Adding cached result for page {page_number}")
                all_pages.append(partial_results[page_number])
                total_words += len(partial_results[page_number]["page_content"].split())

        return all_pages, total_words

    async def process_pdf_async(self, pdf_path: str) -> dict:
        """
        Process a PDF file asynchronously and return structured content.

        Handles loading, processing, and caching of PDF document contents
        using vision models to extract and structure the information.

        Args:
            pdf_path: Path to the PDF file to process

        Returns:
            A dictionary containing the structured content of the PDF

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            PDFValidationError: If the file is not a valid PDF
            Exception: For other processing errors
        """
        pdf_file: Path | None = None
        file_hash: str | None = None
        cache_key: str | None = None
        doc = None

        try:
            # Initial validation and setup
            pdf_file, file_hash = await self._validate_and_setup(pdf_path)
            cache_key = HashUtils.get_cache_key(file_hash, self.prompt)

            doc = fitz.open(str(pdf_file))
            total_pages = len(doc)

            # Check if image cache is available for this file hash
            # If not, try to download it from cloud storage
            # logger.info(f"Checking image cache for file hash: {file_hash}")

            # Try to download image cache if not already available locally
            # skip for now to save time and disk space
            # await self._image_cache.download_images_to_local_cache(
            #     file_hash, total_pages
            # )

            # Check cache unless invalidate_cache is True
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                logger.debug("Found cached results - using cached data")
                self.save_markdown_output(cached_result)
                return cached_result

            # Load any partial results
            partial_results = await self._load_partial_results(cache_key)
            logger.info(f"Found {len(partial_results)} cached pages")

            # Extract text content and page hashes from PDF
            logger.info(f"Extracting text content and calculating page hashes for {pdf_file}")
            page_extractions = self._extract_text_from_pdf(str(pdf_file))

            # Process PDF in chunks to avoid memory issues with large PDFs
            logger.info(f"Processing PDF in chunks: {pdf_file}")

            chunk_size = MAX_CONCURRENT_TASKS
            all_pages: list[dict] = []
            total_words = 0

            # Process PDF in chunks equal to MAX_CONCURRENT_TASKS
            try:
                logger.info(f"PDF has {total_pages} pages")

                # Process PDF in chunks equal to MAX_CONCURRENT_TASKS
                for chunk_start in range(0, total_pages, chunk_size):
                    chunk_end = min(chunk_start + chunk_size, total_pages)

                    all_pages, chunk_words = await self._process_pdf_chunk(
                        doc,
                        chunk_start,
                        chunk_end,
                        page_extractions,
                        partial_results,
                        cache_key,
                        all_pages,
                        file_hash,
                    )
                    total_words += chunk_words
            finally:
                # Ensure the document is closed even if processing fails
                if doc:
                    doc.close()

            # Compile final results
            result = await self._compile_results(pdf_file, cache_key, all_pages, total_words, total_pages)

            # Cache the results
            logger.info("Saving results to cache")
            await self.cache.set(cache_key, result)

            # Generate markdown output
            self.save_markdown_output(result)

            # Upload any newly generated images to S3
            # image_cache_path = self._image_cache._get_local_cache_path(file_hash)
            # await self._image_cache.cache_images(image_cache_path, file_hash)

            return result

        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            raise
        except PDFValidationError as e:
            logger.error(f"PDF validation failed for {pdf_path}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            raise

    def process_pdf(self, pdf_path: str) -> dict:
        """
        Synchronous wrapper for process_pdf_async.

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            dict: Structured content following the specified schema
        """

        async def _run() -> dict:
            try:
                return await self.process_pdf_async(pdf_path)
            except Exception as e:
                logger.error(f"Error processing PDF: {e}")
                return {}

        return asyncio.run(_run())

    def save_output(self, result: dict, output_path: str) -> None:
        """Save the processing result to a JSON file."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"Output saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving output: {str(e)}")

    def _validate_image(self, image_path: str) -> None:
        """
        Validate that the file has a supported image extension.

        Args:
            image_path (str): Path to the image file

        Raises:
            ImageValidationError: If the file doesn't have a supported image extension
        """
        ext = Path(image_path).suffix.lower().lstrip(".")
        if ext not in self.SUPPORTED_IMAGE_FORMATS:
            raise ImageValidationError(f"Unsupported image format: {ext}. Supported formats: {', '.join(self.SUPPORTED_IMAGE_FORMATS)}")

    def _optimize_image(self, image: Image.Image) -> Image.Image:
        """
        Optimize image for processing while preserving quality.

        Args:
            image (Image.Image): Input image

        Returns:
            Image.Image: Optimized image
        """
        # Calculate target size while maintaining aspect ratio
        max_dimension = 2000
        ratio = min(max_dimension / max(image.size), 1.0)
        if ratio < 1.0:
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)  # type: ignore

        return image

    async def process_image_async(self, image_path: str) -> dict:
        """Process an image file asynchronously and return structured content.

        Args:
            image_path (str): Path to the image file

        Returns:
            Dict: Structured content following the same schema as PDF processing

        Raises:
            FileNotFoundError: If the image file doesn't exist
            ImageValidationError: If the image format is not supported
            Exception: For other processing errors
        """
        # Initial validation and setup
        image_file = Path(image_path)
        logger.debug(f"Starting to process image file: {image_file.name}")

        if not image_file.exists():
            raise FileNotFoundError(f"Image file not found: {image_file}")

        # Validate image format
        self._validate_image(str(image_file))

        # Calculate file hash
        file_hash = HashUtils.calculate_file_hash(str(image_file))
        cache_key = HashUtils.get_cache_key(file_hash, self.prompt)
        logger.debug(f"Calculated cache key: {cache_key}")

        try:
            # Check cache unless invalidate_cache is True
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                logger.debug("Found cached results - using cached data")
                self.save_markdown_output(cached_result)
                return cached_result

            # Load and optimize image
            with Image.open(image_file) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                # Optimize image
                img = self._optimize_image(img)

                # Process the image
                page_result = await self.process_page_async(
                    img,
                    page_number=1,
                    page_hash=f"{file_hash}",
                    text_content="",  # No text content for direct image processing
                )

            # Compile results
            result = {
                "file_object": {
                    "file_name": image_file.name,
                    "cache_key": cache_key,
                    "total_pages": 1,
                    "total_words": len(page_result["page_content"].split()),
                    "file_full_path": str(image_file.absolute()),
                    "pages": [page_result],
                }
            }

            # Save to cache
            logger.info("Saving results to cache")
            await self.cache.set(cache_key, result)

            # Generate markdown output
            self.save_markdown_output(result)

            return result

        except FileNotFoundError:
            logger.error(f"Image file not found: {image_file}")
            raise
        except ImageValidationError as e:
            logger.error(f"Image validation failed for {image_file}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing image {image_file}: {str(e)}")
            raise

    def process_image(self, image_path: str) -> dict:
        """
        Synchronous wrapper for process_image_async.

        Args:
            image_path (str): Path to the image file

        Returns:
            dict: Structured content following the same schema as PDF processing
        """

        async def _run() -> dict:
            try:
                return await self.process_image_async(image_path)
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                return {}

        return asyncio.run(_run())

    def process_file(self, file_path: str) -> dict:
        """Process a file synchronously and return structured content."""
        return asyncio.run(self.process_file_async(file_path))

    async def process_file_async(self, file_path: str) -> dict:
        """Process a file asynchronously and return structured content."""
        if file_path.lower().endswith(".pdf"):
            return await self.process_pdf_async(file_path)
        elif Path(file_path).suffix.lower().lstrip(".") in self.SUPPORTED_IMAGE_FORMATS:
            return await self.process_image_async(file_path)
        else:
            logger.error(f"Unsupported file format: {file_path}")
            return {}

    def process_folder(self, folder_path: str) -> list[dict]:
        """Process all PDF and image files in a folder synchronously."""
        return asyncio.run(self.process_folder_async(folder_path))

    async def process_folder_async(self, folder_path: str) -> list[dict]:
        """Process all PDF and image files in a folder asynchronously.

        Args:
            folder_path (str): Path to the folder containing files to process

        Returns:
            List[Dict]: List of processed results

        Raises:
            FileNotFoundError: If the folder doesn't exist
        """
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            logger.error(f"Folder not found or not a directory: {folder_path}")
            raise FileNotFoundError(f"Folder not found or not a directory: {folder_path}")

        results = []

        for file_path in folder.iterdir():
            try:
                if file_path.is_file():
                    if file_path.suffix.lower() == ".pdf":
                        logger.info(f"Processing PDF file: {file_path.name}")
                        result = await self.process_pdf_async(str(file_path))
                        results.append(result)
                    elif file_path.suffix.lower().lstrip(".") in self.SUPPORTED_IMAGE_FORMATS:
                        logger.info(f"Processing image file: {file_path.name}")
                        result = await self.process_image_async(str(file_path))
                        results.append(result)
                    else:
                        logger.debug(f"Skipping unsupported file: {file_path.name}")
            except Exception as e:
                logger.error(f"Error processing file {file_path.name}: {str(e)}")
                continue

        logger.info(f"Completed processing folder: {folder_path} - Processed {len(results)} files")
        return results

    async def _compile_results(  # noqa
        self,
        pdf_file: Path,
        cache_key: str,
        pages: list[dict],
        total_words: int,
        total_pages: int,
    ) -> dict:
        """Compile final results and clean up temporary files."""
        # Sort pages by page number (as integer) to ensure correct order
        pages.sort(key=lambda x: int(x["page_number"]))

        # Clean up partial results file
        partial_cache = self._get_partial_cache_path(cache_key)
        if partial_cache.exists():
            partial_cache.unlink()

        # Prepare final output
        return {
            "file_object": {
                "file_name": pdf_file.name,
                "cache_key": cache_key,
                "total_pages": total_pages,
                "total_words": total_words,
                "file_full_path": str(pdf_file.absolute()),
                "pages": pages,
            }
        }

    @classmethod
    async def analyze_pdf_file(cls, pdf_path: str) -> dict[str, Any]:
        """
        Analyze a PDF file and return metadata information.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing PDF metadata (page count, size, version, etc.)
            or error information if analysis fails.
        """
        # Check if file exists
        if not Path(pdf_path).exists():
            return {
                "status": "error",
                "message": f"PDF file not found: {pdf_path}",
            }

        try:
            # Validate file extension
            if not str(pdf_path).lower().endswith(".pdf"):
                raise PDFValidationError("File must have a .pdf extension")

            # Get file stats
            file_stat = Path(pdf_path).stat()
            file_size = file_stat.st_size
            modification_time = datetime.fromtimestamp(file_stat.st_mtime).isoformat()

            # Extract PDF metadata
            metadata = {"file_size_bytes": file_size, "modified_at": modification_time}

            with fitz.open(pdf_path) as doc:
                number_of_pages = len(doc)
                metadata["number_of_pages"] = number_of_pages

                # Try to extract PDF version and metadata if available
                if doc.metadata:
                    for key, value in doc.metadata.items():
                        if value:
                            metadata[key.lower()] = value

                # Get page sizes
                if number_of_pages > 0:
                    first_page = doc[0]
                    metadata["page_width"] = first_page.rect.width
                    metadata["page_height"] = first_page.rect.height
                    metadata["page_size"] = f"{first_page.rect.width}x{first_page.rect.height}"

            return {"status": "success", **metadata}

        except PDFValidationError as e:
            return {
                "status": "error",
                "message": str(e),
            }
        except fitz.FileDataError as e:
            return {
                "status": "error",
                "message": f"Invalid PDF file: {str(e)}",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error analyzing PDF: {str(e)}",
            }
