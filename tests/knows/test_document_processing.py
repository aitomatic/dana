"""
Tests for document processing components in OpenDXA KNOWS system.

This module tests the document loader, parser, and text extractor functionality.
"""

import os
import json
import tempfile
import pytest
from datetime import datetime
from pathlib import Path

from dana.frameworks.knows.core.base import Document, ParsedDocument
from dana.frameworks.knows.document.loader import DocumentLoader
from dana.frameworks.knows.document.parser import DocumentParser
from dana.frameworks.knows.document.extractor import TextExtractor


class TestDocumentLoader:
    """Test cases for DocumentLoader."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loader = DocumentLoader()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_file(self, filename: str, content: str) -> str:
        """Create a test file with content."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def test_load_text_document(self):
        """Test loading a text document."""
        content = "This is a test document.\nWith multiple lines."
        file_path = self.create_test_file("test.txt", content)
        
        document = self.loader.load_document(file_path)
        
        assert isinstance(document, Document)
        assert document.content == content
        assert document.format == "txt"
        assert document.source == file_path
        assert document.id.startswith("doc_")
        assert isinstance(document.created_at, datetime)
        assert document.metadata["file_name"] == "test.txt"

    def test_load_markdown_document(self):
        """Test loading a markdown document."""
        content = "# Test Header\n\nThis is **markdown** content."
        file_path = self.create_test_file("test.md", content)
        
        document = self.loader.load_document(file_path)
        
        assert document.content == content
        assert document.format == "md"
        assert document.metadata["file_extension"] == "md"

    def test_load_json_document(self):
        """Test loading a JSON document."""
        data = {"key": "value", "number": 42}
        content = json.dumps(data, indent=2)
        file_path = self.create_test_file("test.json", content)
        
        document = self.loader.load_document(file_path)
        
        assert document.format == "json"
        # Content should be formatted JSON string
        loaded_data = json.loads(document.content)
        assert loaded_data == data

    def test_load_csv_document(self):
        """Test loading a CSV document."""
        content = "name,age,city\nAlice,30,New York\nBob,25,London"
        file_path = self.create_test_file("test.csv", content)
        
        document = self.loader.load_document(file_path)
        
        assert document.content == content
        assert document.format == "csv"

    def test_load_multiple_documents(self):
        """Test loading multiple documents."""
        files = []
        for i in range(3):
            content = f"Test document {i}"
            file_path = self.create_test_file(f"test_{i}.txt", content)
            files.append(file_path)
        
        documents = self.loader.load_documents(files)
        
        assert len(documents) == 3
        for i, doc in enumerate(documents):
            assert f"Test document {i}" in doc.content

    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            self.loader.load_document("nonexistent.txt")

    def test_load_unsupported_format(self):
        """Test loading an unsupported file format."""
        file_path = self.create_test_file("test.xyz", "content")
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            self.loader.load_document(file_path)

    def test_file_size_limit(self):
        """Test file size limit enforcement."""
        loader = DocumentLoader(max_size=100)  # 100 bytes limit
        large_content = "x" * 200  # 200 bytes
        file_path = self.create_test_file("large.txt", large_content)
        
        with pytest.raises(ValueError, match="File too large"):
            loader.load_document(file_path)

    def test_validate_document(self):
        """Test document validation."""
        # Valid document
        valid_doc = Document(
            id="test_id",
            source="test.txt",
            content="test content",
            format="txt",
            metadata={},
            created_at=datetime.now()
        )
        assert self.loader.validate_document(valid_doc) is True
        
        # Test validation method directly with a manually created invalid doc
        # Cannot use Document constructor due to __post_init__ validation
        # So we test the validation method directly by creating a mock Document
        class MockDocument:
            def __init__(self):
                self.id = ""
                self.content = "test"
                self.format = "txt"
        
        mock_doc = MockDocument()
        assert self.loader.validate_document(mock_doc) is False  # type: ignore


class TestDocumentParser:
    """Test cases for DocumentParser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = DocumentParser()

    def create_test_document(self, content: str, format: str) -> Document:
        """Create a test document."""
        return Document(
            id="test_doc",
            source="test_file",
            content=content,
            format=format,
            metadata={},
            created_at=datetime.now()
        )

    def test_parse_text_document(self):
        """Test parsing a text document."""
        content = """# Main Header
        
This is the first section.

## Sub Header

This is a subsection with a list:
- Item 1
- Item 2
- Item 3

1. Numbered item 1
2. Numbered item 2
"""
        document = self.create_test_document(content, "txt")
        parsed_doc = self.parser.process(document)
        
        assert isinstance(parsed_doc, ParsedDocument)
        assert parsed_doc.document == document
        assert parsed_doc.text_content == content
        
        structured_data = parsed_doc.structured_data
        assert structured_data["type"] == "text_document"
        assert len(structured_data["headers"]) == 2
        assert structured_data["headers"][0]["title"] == "Main Header"
        assert structured_data["headers"][0]["level"] == 1
        assert len(structured_data["lists"]) == 2
        assert structured_data["lists"][0]["type"] == "unordered"
        assert structured_data["lists"][1]["type"] == "ordered"

    def test_parse_json_document(self):
        """Test parsing a JSON document."""
        data = {
            "name": "Test API",
            "version": "1.0",
            "endpoints": [
                {"path": "/users", "method": "GET"},
                {"path": "/users", "method": "POST"}
            ]
        }
        content = json.dumps(data, indent=2)
        document = self.create_test_document(content, "json")
        
        parsed_doc = self.parser.process(document)
        
        structured_data = parsed_doc.structured_data
        assert structured_data["type"] == "json_document"
        assert structured_data["data"] == data
        assert structured_data["metadata"]["is_object"] is True
        assert "name" in structured_data["metadata"]["keys"]

    def test_parse_csv_document(self):
        """Test parsing a CSV document."""
        content = "name,age,city\nAlice,30,New York\nBob,25,London"
        document = self.create_test_document(content, "csv")
        
        parsed_doc = self.parser.process(document)
        
        structured_data = parsed_doc.structured_data
        assert structured_data["type"] == "csv_document"
        assert structured_data["headers"] == ["name", "age", "city"]
        assert len(structured_data["rows"]) == 2
        assert structured_data["rows"][0]["name"] == "Alice"
        assert structured_data["metadata"]["column_count"] == 3

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON falls back to generic parsing."""
        content = "{ invalid json"
        document = self.create_test_document(content, "json")
        
        parsed_doc = self.parser.process(document)
        
        # Should fall back to generic parsing
        assert parsed_doc.structured_data["type"] == "generic_document"

    def test_validate_input(self):
        """Test input validation."""
        valid_doc = self.create_test_document("content", "txt") 
        assert self.parser.validate_input(valid_doc) is True
        
        # Test with invalid input - need to use type: ignore for intentional type error
        assert self.parser.validate_input("not a document") is False  # type: ignore
        
        # Test with mock empty content document (cannot use Document constructor with empty content)
        class MockDocument:
            def __init__(self):
                self.content = ""
                self.format = "txt"
        
        mock_doc = MockDocument()
        assert self.parser.validate_input(mock_doc) is False  # type: ignore


class TestTextExtractor:
    """Test cases for TextExtractor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = TextExtractor()

    def create_parsed_document(self, structured_data: dict, text_content: str) -> ParsedDocument:
        """Create a test parsed document."""
        document = Document(
            id="test_doc",
            source="test_file",
            content=text_content,
            format="txt",
            metadata={},
            created_at=datetime.now()
        )
        return ParsedDocument(
            document=document,
            text_content=text_content,
            structured_data=structured_data,
            metadata={}
        )

    def test_extract_from_text_document(self):
        """Test extracting text from a structured text document."""
        structured_data = {
            "type": "text_document",
            "headers": [
                {"level": 1, "title": "Main Header", "type": "header"},
                {"level": 2, "title": "Sub Header", "type": "header"}
            ],
            "sections": [
                {"index": 0, "content": "First section content", "type": "section"},
                {"index": 1, "content": "Second section content", "type": "section"}
            ],
            "lists": [
                {"type": "unordered", "items": ["Item 1", "Item 2"]}
            ],
            "metadata": {"word_count": 10}
        }
        
        parsed_doc = self.create_parsed_document(structured_data, "original text")
        extracted_text = self.extractor.process(parsed_doc)
        
        assert "# Main Header" in extracted_text
        assert "## Sub Header" in extracted_text
        assert "First section content" in extracted_text
        assert "• Item 1" in extracted_text
        assert "Document Metadata:" in extracted_text

    def test_extract_from_json_document(self):
        """Test extracting text from a JSON document."""
        structured_data = {
            "type": "json_document",
            "data": {"name": "test", "value": 42},
            "metadata": {"is_object": True}
        }
        
        parsed_doc = self.create_parsed_document(structured_data, '{"name": "test", "value": 42}')
        extracted_text = self.extractor.process(parsed_doc)
        
        assert "JSON Document Structure:" in extracted_text
        assert "name: test" in extracted_text
        assert "value: 42" in extracted_text

    def test_extract_from_csv_document(self):
        """Test extracting text from a CSV document."""
        structured_data = {
            "type": "csv_document",
            "headers": ["name", "age"],
            "rows": [
                {"name": "Alice", "age": "30"},
                {"name": "Bob", "age": "25"}
            ],
            "metadata": {"row_count": 2}
        }
        
        parsed_doc = self.create_parsed_document(structured_data, "csv content")
        extracted_text = self.extractor.process(parsed_doc)
        
        assert "CSV Data:" in extracted_text
        assert "Headers: name, age" in extracted_text
        assert "Row 1: name: Alice, age: 30" in extracted_text

    def test_extract_without_structure_preservation(self):
        """Test extracting text without preserving structure."""
        extractor = TextExtractor(preserve_structure=False)
        structured_data = {
            "type": "text_document",
            "sections": [
                {"index": 0, "content": "Simple content", "type": "section"}
            ],
            "metadata": {"word_count": 2}  # Add some metadata to ensure it's included
        }
        
        parsed_doc = self.create_parsed_document(structured_data, "original text")
        extracted_text = extractor.process(parsed_doc)
        
        assert "Simple content" in extracted_text
        assert "Document Metadata:" in extracted_text  # metadata still included by default

    def test_extract_without_metadata(self):
        """Test extracting text without metadata."""
        extractor = TextExtractor(include_metadata=False)
        structured_data = {
            "type": "text_document",
            "sections": [
                {"index": 0, "content": "Content only", "type": "section"}
            ],
            "metadata": {"word_count": 2}
        }
        
        parsed_doc = self.create_parsed_document(structured_data, "original text")
        extracted_text = extractor.process(parsed_doc)
        
        assert "Content only" in extracted_text
        assert "Document Metadata:" not in extracted_text

    def test_extract_with_length_limit(self):
        """Test extracting text with length limit."""
        extractor = TextExtractor(max_text_length=20)
        structured_data = {
            "type": "text_document",
            "sections": [
                {"index": 0, "content": "This is a very long piece of content that should be truncated", "type": "section"}
            ]
        }
        
        parsed_doc = self.create_parsed_document(structured_data, "original text")
        extracted_text = extractor.process(parsed_doc)
        
        assert len(extracted_text) <= 23  # 20 + "..."
        assert extracted_text.endswith("...")

    def test_validate_input(self):
        """Test input validation."""
        structured_data = {"type": "text_document"}
        valid_parsed_doc = self.create_parsed_document(structured_data, "content")
        
        assert self.extractor.validate_input(valid_parsed_doc) is True
        assert self.extractor.validate_input("not a parsed document") is False  # type: ignore
        
        # Test with mock empty content parsed document 
        class MockParsedDocument:
            def __init__(self):
                self.text_content = ""
                self.structured_data = {"type": "text_document"}
        
        mock_parsed_doc = MockParsedDocument()
        assert self.extractor.validate_input(mock_parsed_doc) is False  # type: ignore


@pytest.fixture
def sample_documents():
    """Fixture providing sample documents for integration testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create sample files
    files = {}
    
    # Text file
    text_content = "# Sample Document\n\nThis is a test document with **markdown** formatting.\n\n- Item 1\n- Item 2"
    text_file = os.path.join(temp_dir, "sample.txt")
    with open(text_file, 'w') as f:
        f.write(text_content)
    files['text'] = text_file
    
    # JSON file
    json_data = {"name": "Test", "items": [1, 2, 3]}
    json_file = os.path.join(temp_dir, "sample.json")
    with open(json_file, 'w') as f:
        json.dump(json_data, f)
    files['json'] = json_file
    
    yield files
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestDocumentProcessingIntegration:
    """Integration tests for the complete document processing pipeline."""

    def test_complete_pipeline(self, sample_documents):
        """Test the complete document processing pipeline."""
        loader = DocumentLoader()
        parser = DocumentParser()
        extractor = TextExtractor()
        
        # Load document
        document = loader.load_document(sample_documents['text'])
        assert isinstance(document, Document)
        
        # Parse document
        parsed_doc = parser.process(document)
        assert isinstance(parsed_doc, ParsedDocument)
        
        # Extract text
        extracted_text = extractor.process(parsed_doc)
        assert isinstance(extracted_text, str)
        assert len(extracted_text) > 0
        
        # Verify text contains expected content
        assert "Sample Document" in extracted_text
        assert "test document" in extracted_text

    def test_pipeline_with_json(self, sample_documents):
        """Test pipeline with JSON document."""
        loader = DocumentLoader()
        parser = DocumentParser()
        extractor = TextExtractor()
        
        # Process JSON document
        document = loader.load_document(sample_documents['json'])
        parsed_doc = parser.process(document)
        extracted_text = extractor.process(parsed_doc)
        
        assert "JSON Document Structure:" in extracted_text
        assert "name: Test" in extracted_text
        assert "items:" in extracted_text

    def test_error_handling_in_pipeline(self):
        """Test error handling throughout the pipeline."""
        loader = DocumentLoader()
        parser = DocumentParser()
        extractor = TextExtractor()
        
        # Test with invalid file
        with pytest.raises(FileNotFoundError):
            loader.load_document("nonexistent.txt")
        
        # Test parser with invalid input
        with pytest.raises(ValueError):
            parser.process("not a document")  # type: ignore
        
        # Test extractor with invalid input
        with pytest.raises(ValueError):
            extractor.process("not a parsed document")  # type: ignore 