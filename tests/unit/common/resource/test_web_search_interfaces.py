"""Tests for web search protocol interfaces."""

import pytest
from typing import runtime_checkable

from dana.common.sys_resource.web_search.core.interfaces import (
    DomainHandler,
    ResultValidator,
    SearchService,
)
from dana.common.sys_resource.web_search.core.models import (
    DomainResult,
    ProductInfo,
    ResearchRequest,
    SearchRequest,
    SearchResults,
    SearchSource,
    SearchDepth,
)


@runtime_checkable
class MockSearchService:
    """Mock implementation of SearchService protocol."""

    async def search(self, request: SearchRequest) -> SearchResults:
        """Mock search implementation."""
        source = SearchSource(
            url=f"https://example.com/search?q={request.query}",
            content=f"Mock search results for: {request.query}",
        )
        return SearchResults(success=True, sources=[source])


@runtime_checkable
class MockDomainHandler:
    """Mock implementation of DomainHandler protocol."""

    def build_search_request(self, request: ResearchRequest) -> SearchRequest:
        """Mock search request builder."""
        query = f"{request.product.manufacturer} {request.product.part_number} {request.product.description}".strip()
        return SearchRequest(
            query=query,
            search_depth=request.search_depth,
            with_full_content=request.with_full_content,
        )

    async def synthesize_results(self, search_results: SearchResults, request: ResearchRequest) -> DomainResult:
        """Mock result synthesis."""
        if not search_results.success or not search_results.sources:
            return DomainResult(
                success=False,
                data={},
                error_message="No search results to synthesize",
            )

        # Mock domain-specific data extraction
        data = {
            "product_name": str(request.product),
            "sources_count": len(search_results.sources),
            "extracted_info": "Mock extracted information",
        }

        return DomainResult(
            success=True,
            data=data,
            confidence="medium",
            sources=[source.url for source in search_results.sources],
            reasoning="Mock synthesis based on search results",
        )


@runtime_checkable
class MockResultValidator:
    """Mock implementation of ResultValidator protocol."""

    def validate_result(self, result: DomainResult, request: ResearchRequest) -> DomainResult:
        """Mock result validation."""
        if not result.success:
            return result

        # Mock validation logic
        validated_data = result.data.copy()
        validated_data["validation_status"] = "validated"
        validated_data["validation_timestamp"] = "2024-01-01T00:00:00Z"

        return DomainResult(
            success=result.success,
            data=validated_data,
            confidence=result.confidence,
            sources=result.sources,
            reasoning=f"{result.reasoning} | Validation: Passed basic checks",
            error_message=result.error_message,
        )


class TestSearchServiceProtocol:
    """Tests for SearchService protocol."""

    def test_search_service_protocol_compliance(self):
        """Test that mock implementation satisfies SearchService protocol."""
        service = MockSearchService()
        assert isinstance(service, SearchService)

    @pytest.mark.asyncio
    async def test_search_service_interface(self):
        """Test SearchService interface contract."""
        service = MockSearchService()

        request = SearchRequest(
            query="Intel i7-12700K specifications",
            search_depth=SearchDepth.STANDARD,
        )

        results = await service.search(request)

        # Verify return type and structure
        assert isinstance(results, SearchResults)
        assert results.success is True
        assert len(results.sources) == 1
        assert isinstance(results.sources[0], SearchSource)
        assert "Intel i7-12700K specifications" in results.sources[0].content

    @pytest.mark.asyncio
    async def test_search_service_with_different_depths(self):
        """Test SearchService with different search depths."""
        service = MockSearchService()

        for depth in [SearchDepth.BASIC, SearchDepth.STANDARD, SearchDepth.EXTENSIVE]:
            request = SearchRequest(
                query="test query",
                search_depth=depth,
                with_full_content=True,
            )

            results = await service.search(request)
            assert isinstance(results, SearchResults)
            assert results.success is True


class TestDomainHandlerProtocol:
    """Tests for DomainHandler protocol."""

    def test_domain_handler_protocol_compliance(self):
        """Test that mock implementation satisfies DomainHandler protocol."""
        handler = MockDomainHandler()
        assert isinstance(handler, DomainHandler)

    def test_build_search_request_interface(self):
        """Test DomainHandler build_search_request interface."""
        handler = MockDomainHandler()

        product = ProductInfo(
            manufacturer="Intel",
            part_number="i7-12700K",
            description="Desktop CPU",
        )

        research_request = ResearchRequest(
            product=product,
            search_depth=SearchDepth.EXTENSIVE,
            with_full_content=True,
        )

        search_request = handler.build_search_request(research_request)

        # Verify return type and structure
        assert isinstance(search_request, SearchRequest)
        assert "Intel i7-12700K Desktop CPU" in search_request.query
        assert search_request.search_depth == SearchDepth.EXTENSIVE
        assert search_request.with_full_content is True

    @pytest.mark.asyncio
    async def test_synthesize_results_interface(self):
        """Test DomainHandler synthesize_results interface."""
        handler = MockDomainHandler()

        # Create mock search results
        sources = [
            SearchSource(
                url="https://intel.com/specs",
                content="Intel i7-12700K specifications: 12 cores, 3.6GHz base",
            )
        ]
        search_results = SearchResults(success=True, sources=sources)

        # Create research request
        product = ProductInfo(manufacturer="Intel", part_number="i7-12700K")
        research_request = ResearchRequest(product=product)

        # Test synthesis
        domain_result = await handler.synthesize_results(search_results, research_request)

        # Verify return type and structure
        assert isinstance(domain_result, DomainResult)
        assert domain_result.success is True
        assert "product_name" in domain_result.data
        assert domain_result.data["sources_count"] == 1
        assert len(domain_result.sources) == 1

    @pytest.mark.asyncio
    async def test_synthesize_results_with_failed_search(self):
        """Test DomainHandler synthesis with failed search results."""
        handler = MockDomainHandler()

        # Create failed search results
        search_results = SearchResults(
            success=False,
            sources=[],
            error_message="Search failed",
        )

        product = ProductInfo(manufacturer="Intel", part_number="i7-12700K")
        research_request = ResearchRequest(product=product)

        domain_result = await handler.synthesize_results(search_results, research_request)

        assert isinstance(domain_result, DomainResult)
        assert domain_result.success is False
        assert domain_result.error_message == "No search results to synthesize"


class TestResultValidatorProtocol:
    """Tests for ResultValidator protocol."""

    def test_result_validator_protocol_compliance(self):
        """Test that mock implementation satisfies ResultValidator protocol."""
        validator = MockResultValidator()
        assert isinstance(validator, ResultValidator)

    def test_validate_result_interface(self):
        """Test ResultValidator validate_result interface."""
        validator = MockResultValidator()

        # Create mock result to validate
        original_data = {"product": "Intel i7-12700K", "cores": 12}
        result = DomainResult(
            success=True,
            data=original_data,
            confidence="high",
            sources=["https://intel.com"],
            reasoning="Extracted from official specs",
        )

        product = ProductInfo(manufacturer="Intel", part_number="i7-12700K")
        research_request = ResearchRequest(product=product)

        # Test validation
        validated_result = validator.validate_result(result, research_request)

        # Verify return type and structure
        assert isinstance(validated_result, DomainResult)
        assert validated_result.success is True
        assert "validation_status" in validated_result.data
        assert validated_result.data["validation_status"] == "validated"
        assert "Validation:" in validated_result.reasoning

    def test_validate_result_with_failed_result(self):
        """Test ResultValidator with failed domain result."""
        validator = MockResultValidator()

        failed_result = DomainResult(
            success=False,
            data={},
            error_message="Domain processing failed",
        )

        product = ProductInfo(manufacturer="Intel", part_number="i7-12700K")
        research_request = ResearchRequest(product=product)

        validated_result = validator.validate_result(failed_result, research_request)

        # Should return original failed result unchanged
        assert validated_result is failed_result
        assert validated_result.success is False


class TestProtocolIntegration:
    """Tests for protocol integration and composition."""

    @pytest.mark.asyncio
    async def test_full_protocol_workflow(self):
        """Test complete workflow using all protocols together."""
        # Initialize components
        search_service = MockSearchService()
        domain_handler = MockDomainHandler()
        validator = MockResultValidator()

        # Create research request
        product = ProductInfo(
            manufacturer="Intel",
            part_number="i7-12700K",
            description="Desktop CPU",
        )
        research_request = ResearchRequest(
            product=product,
            search_depth=SearchDepth.STANDARD,
        )

        # Step 1: Build search request
        search_request = domain_handler.build_search_request(research_request)
        assert isinstance(search_request, SearchRequest)

        # Step 2: Execute search
        search_results = await search_service.search(search_request)
        assert isinstance(search_results, SearchResults)
        assert search_results.success is True

        # Step 3: Synthesize domain results
        domain_result = await domain_handler.synthesize_results(search_results, research_request)
        assert isinstance(domain_result, DomainResult)
        assert domain_result.success is True

        # Step 4: Validate results
        validated_result = validator.validate_result(domain_result, research_request)
        assert isinstance(validated_result, DomainResult)
        assert validated_result.success is True
        assert "validation_status" in validated_result.data

        # Verify data flow integrity
        assert validated_result.data["product_name"] == "Intel i7-12700K Desktop CPU"
        assert validated_result.data["sources_count"] == 1


class TestProtocolTypeChecking:
    """Tests for protocol type checking and validation."""

    def test_search_service_type_checking(self):
        """Test SearchService type checking."""
        # Valid implementation
        valid_service = MockSearchService()
        assert isinstance(valid_service, SearchService)

        # Invalid implementation (missing search method)
        class InvalidService:
            pass

        invalid_service = InvalidService()
        assert not isinstance(invalid_service, SearchService)

    def test_domain_handler_type_checking(self):
        """Test DomainHandler type checking."""
        # Valid implementation
        valid_handler = MockDomainHandler()
        assert isinstance(valid_handler, DomainHandler)

        # Invalid implementation (missing methods)
        class InvalidHandler:
            def build_search_request(self, request):
                pass

            # Missing synthesize_results method

        invalid_handler = InvalidHandler()
        assert not isinstance(invalid_handler, DomainHandler)

    def test_result_validator_type_checking(self):
        """Test ResultValidator type checking."""
        # Valid implementation
        valid_validator = MockResultValidator()
        assert isinstance(valid_validator, ResultValidator)

        # Invalid implementation (missing validate_result method)
        class InvalidValidator:
            pass

        invalid_validator = InvalidValidator()
        assert not isinstance(invalid_validator, ResultValidator)


if __name__ == "__main__":
    pytest.main([__file__])
