"""Tests for visual document extraction endpoints."""

import os
import tempfile

from fastapi.testclient import TestClient


class TestVisualDocumentExtraction:
    """Test cases for visual document extraction endpoints."""

    def test_extract_visual_document_success(self, client: TestClient):
        """Test successful visual document extraction."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(b"fake image data")
            temp_file_path = temp_file.name

        try:
            # Test request
            request_data = {
                "file_path": temp_file_path,
                "prompt": "Extract all text and diagrams from this image",
                "config": {"ocr_mode": "accurate"},
            }

            response = client.post("/api/extract-documents/deep-extract", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "file_object" in data
            file_obj = data["file_object"]

            assert file_obj["file_name"] == os.path.basename(temp_file_path)
            assert file_obj["total_pages"] == 1
            assert file_obj["total_words"] > 0
            assert file_obj["file_full_path"] == os.path.abspath(temp_file_path)
            assert "cache_key" in file_obj

            # Verify pages structure
            assert "pages" in file_obj
            assert len(file_obj["pages"]) == 1

            page = file_obj["pages"][0]
            assert page["page_number"] == 1
            assert "page_content" in page
            assert "page_hash" in page
            assert len(page["page_content"]) > 0

        finally:
            # Clean up
            os.unlink(temp_file_path)

    def test_extract_visual_document_file_not_found(self, client: TestClient):
        """Test extraction with non-existent file."""
        request_data = {"file_path": "/path/to/nonexistent/file.png", "prompt": "Extract content"}

        response = client.post("/api/extract-documents/deep-extract", json=request_data)

        assert response.status_code == 404
        data = response.json()
        assert "File not found" in data["detail"]

    def test_extract_visual_document_unsupported_type(self, client: TestClient):
        """Test extraction with unsupported file type."""
        # Create a temporary test file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as temp_file:
            temp_file.write(b"fake data")
            temp_file_path = temp_file.name

        try:
            request_data = {"file_path": temp_file_path, "prompt": "Extract content"}

            response = client.post("/api/extract-documents/deep-extract", json=request_data)

            assert response.status_code == 400
            data = response.json()
            assert "Unsupported file type" in data["detail"]

        finally:
            # Clean up
            os.unlink(temp_file_path)

    def test_extract_visual_document_without_prompt(self, client: TestClient):
        """Test extraction without providing a prompt."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"fake pdf data")
            temp_file_path = temp_file.name

        try:
            request_data = {
                "file_path": temp_file_path
                # No prompt provided
            }

            response = client.post("/api/extract-documents/deep-extract", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Should still work without prompt
            assert "file_object" in data
            file_obj = data["file_object"]
            assert file_obj["file_name"] == os.path.basename(temp_file_path)

        finally:
            # Clean up
            os.unlink(temp_file_path)

    def test_extract_visual_document_with_config(self, client: TestClient):
        """Test extraction with configuration options."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
            temp_file.write(b"fake docx data")
            temp_file_path = temp_file.name

        try:
            request_data = {
                "file_path": temp_file_path,
                "prompt": "Extract all text and tables",
                "config": {"ocr_mode": "fast", "include_tables": True, "preserve_formatting": False},
            }

            response = client.post("/api/extract-documents/deep-extract", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Should work with config
            assert "file_object" in data
            file_obj = data["file_object"]
            assert file_obj["file_name"] == os.path.basename(temp_file_path)

        finally:
            # Clean up
            os.unlink(temp_file_path)

    def test_get_supported_file_types(self, client: TestClient):
        """Test getting supported file types."""
        response = client.get("/api/extract-documents/deep-extract/supported-types")

        assert response.status_code == 200
        data = response.json()

        assert "supported_extensions" in data
        assert "description" in data

        # Check that common extensions are included
        extensions = data["supported_extensions"]
        assert ".png" in extensions
        assert ".jpg" in extensions
        assert ".pdf" in extensions
        assert ".docx" in extensions
        assert ".pptx" in extensions
        assert ".xlsx" in extensions

    def test_heart_diagram_special_case(self, client: TestClient):
        """Test the special case for heart diagram (mock response)."""
        # Create a temporary test file with "heart" in the name
        with tempfile.NamedTemporaryFile(suffix=".png", prefix="Diagram_of_the_human_heart_", delete=False) as temp_file:
            temp_file.write(b"fake heart diagram data")
            temp_file_path = temp_file.name

        try:
            request_data = {"file_path": temp_file_path, "prompt": "Describe the heart anatomy"}

            response = client.post("/api/extract-documents/deep-extract", json=request_data)

            assert response.status_code == 200
            data = response.json()

            file_obj = data["file_object"]
            page_content = file_obj["pages"][0]["page_content"]

            # Should contain heart-specific content
            assert "Anatomical diagram of the human heart" in page_content
            assert "Superior vena cava" in page_content
            assert "Right atrium" in page_content
            assert "Left ventricle" in page_content

        finally:
            # Clean up
            os.unlink(temp_file_path)
