"""Tests for web search core models."""

import pytest

from dana.common.sys_resource.web_search.core.models import (
    DomainResult,
    ProductInfo,
    ResearchRequest,
    SearchDepth,
    SearchRequest,
    SearchResults,
    SearchSource,
)


class TestSearchDepth:
    """Tests for SearchDepth enum."""

    def test_search_depth_values(self):
        """Test that SearchDepth has correct values."""
        assert SearchDepth.BASIC == "basic"
        assert SearchDepth.STANDARD == "standard"
        assert SearchDepth.EXTENSIVE == "extensive"

    def test_search_depth_string_enum(self):
        """Test that SearchDepth is a proper string enum."""
        assert SearchDepth.BASIC.value == "basic"
        assert SearchDepth.BASIC == "basic"


class TestProductInfo:
    """Tests for ProductInfo dataclass."""

    def test_product_info_creation(self):
        """Test basic ProductInfo creation."""
        product = ProductInfo(manufacturer="Intel", part_number="i7-12700K", description="CPU")
        assert product.manufacturer == "Intel"
        assert product.part_number == "i7-12700K"
        assert product.description == "CPU"

    def test_product_info_defaults(self):
        """Test ProductInfo with default values."""
        product = ProductInfo()
        assert product.manufacturer == ""
        assert product.part_number == ""
        assert product.description == ""

    def test_product_info_str_representation(self):
        """Test ProductInfo string representation."""
        product = ProductInfo(manufacturer="Intel", part_number="i7-12700K", description="CPU")
        assert str(product) == "Intel i7-12700K CPU"

        # Test with partial data
        product_partial = ProductInfo(manufacturer="Intel", description="CPU")
        assert str(product_partial) == "Intel CPU"

        # Test with empty data
        product_empty = ProductInfo()
        assert str(product_empty) == ""


class TestResearchRequest:
    """Tests for ResearchRequest dataclass."""

    def test_research_request_creation(self):
        """Test basic ResearchRequest creation."""
        product = ProductInfo(manufacturer="Intel", part_number="i7-12700K")
        request = ResearchRequest(
            product=product,
            search_depth=SearchDepth.EXTENSIVE,
            with_full_content=True,
        )

        assert request.product == product
        assert request.search_depth == SearchDepth.EXTENSIVE
        assert request.with_full_content is True

    def test_research_request_defaults(self):
        """Test ResearchRequest with default values."""
        product = ProductInfo(manufacturer="Intel")
        request = ResearchRequest(product=product)

        assert request.product == product
        assert request.search_depth == SearchDepth.STANDARD
        assert request.with_full_content is False


class TestSearchRequest:
    """Tests for SearchRequest dataclass."""

    def test_search_request_creation(self):
        """Test basic SearchRequest creation."""
        request = SearchRequest(
            query="Intel CPU i7-12700K",
            search_depth=SearchDepth.EXTENSIVE,
            domain="hardware",
            with_full_content=True,
        )

        assert request.query == "Intel CPU i7-12700K"
        assert request.search_depth == SearchDepth.EXTENSIVE
        assert request.domain == "hardware"
        assert request.with_full_content is True

    def test_search_request_defaults(self):
        """Test SearchRequest with default values."""
        request = SearchRequest(query="test query")

        assert request.query == "test query"
        assert request.search_depth == SearchDepth.STANDARD
        assert request.domain == ""
        assert request.with_full_content is False

    def test_search_request_target_sites(self):
        """Test SearchRequest with target_sites."""
        target_sites = ["example.com", "test.com"]
        request = SearchRequest(query="test", target_sites=target_sites)

        assert request.target_sites == target_sites


class TestSearchSource:
    """Tests for SearchSource dataclass."""

    def test_search_source_creation(self):
        """Test basic SearchSource creation."""
        source = SearchSource(
            url="https://example.com",
            content="Sample content",
            full_content="Full sample content",
        )

        assert source.url == "https://example.com"
        assert source.content == "Sample content"
        assert source.full_content == "Full sample content"

    def test_search_source_defaults(self):
        """Test SearchSource with default values."""
        source = SearchSource(url="https://example.com", content="Sample content")

        assert source.url == "https://example.com"
        assert source.content == "Sample content"
        assert source.full_content == ""

    def test_search_source_empty_content_validation(self):
        """Test that SearchSource validates non-empty content."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            SearchSource(url="https://example.com", content="")

        with pytest.raises(ValueError, match="content cannot be empty"):
            SearchSource(url="https://example.com", content="   ")


class TestSearchResults:
    """Tests for SearchResults dataclass."""

    def test_search_results_success(self):
        """Test successful SearchResults creation."""
        sources = [
            SearchSource(url="https://example.com", content="Content 1"),
            SearchSource(url="https://test.com", content="Content 2"),
        ]

        results = SearchResults(
            success=True,
            sources=sources,
            raw_data="Raw search data",
        )

        assert results.success is True
        assert len(results.sources) == 2
        assert results.raw_data == "Raw search data"
        assert results.error_message == ""

    def test_search_results_failure(self):
        """Test failed SearchResults creation."""
        results = SearchResults(
            success=False,
            sources=[],
            error_message="Search failed",
        )

        assert results.success is False
        assert len(results.sources) == 0
        assert results.error_message == "Search failed"

    def test_search_results_validation_success_no_sources(self):
        """Test that successful results must have sources."""
        with pytest.raises(ValueError, match="successful search must have sources"):
            SearchResults(success=True, sources=[])

    def test_search_results_validation_failure_no_error(self):
        """Test that failed results must have error message."""
        with pytest.raises(ValueError, match="failed search must have error_message"):
            SearchResults(success=False, sources=[])

    def test_search_results_defaults(self):
        """Test SearchResults with default values."""
        source = SearchSource(url="https://example.com", content="Content")
        results = SearchResults(success=True, sources=[source])

        assert results.raw_data == ""
        assert results.error_message == ""


class TestDomainResult:
    """Tests for DomainResult dataclass."""

    def test_domain_result_success(self):
        """Test successful DomainResult creation."""
        data = {"hs_code": "1234567890", "description": "Electronic component"}
        sources = ["https://example.com", "https://test.com"]

        result = DomainResult(
            success=True,
            data=data,
            confidence="high",
            sources=sources,
            reasoning="Found detailed specifications",
        )

        assert result.success is True
        assert result.data == data
        assert result.confidence == "high"
        assert result.sources == sources
        assert result.reasoning == "Found detailed specifications"
        assert result.error_message == ""

    def test_domain_result_failure(self):
        """Test failed DomainResult creation."""
        result = DomainResult(
            success=False,
            data={},
            error_message="Domain processing failed",
        )

        assert result.success is False
        assert result.data == {}
        assert result.error_message == "Domain processing failed"

    def test_domain_result_defaults(self):
        """Test DomainResult with default values."""
        result = DomainResult(
            success=True,
            data={"test": "value"},
        )

        assert result.confidence == "medium"
        assert result.sources == []
        assert result.reasoning == ""
        assert result.error_message == ""

    def test_domain_result_sources_none_initialization(self):
        """Test that None sources are converted to empty list."""
        result = DomainResult(
            success=True,
            data={"test": "value"},
            sources=None,
        )

        assert result.sources == []

    def test_domain_result_validation_success_no_data(self):
        """Test that successful results must have data."""
        with pytest.raises(ValueError, match="successful result must have data"):
            DomainResult(success=True, data={})

    def test_domain_result_validation_failure_no_error(self):
        """Test that failed results must have error message."""
        with pytest.raises(ValueError, match="failed result must have error_message"):
            DomainResult(success=False, data={})

    def test_domain_result_confidence_values(self):
        """Test valid confidence values."""
        # Test all valid confidence levels
        for confidence in ["high", "medium", "low"]:
            result = DomainResult(
                success=True,
                data={"test": "value"},
                confidence=confidence,
            )
            assert result.confidence == confidence


if __name__ == "__main__":
    pytest.main([__file__])
