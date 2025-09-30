"""
Protocol definitions for the product research system.

These interfaces define the contracts that domains and search services must implement,
enabling perfect separation between the two dimensions of variation.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Protocol

from .models import DomainResult, ResearchRequest, SearchRequest, SearchResults


class SearchService(Protocol):
    """
    Protocol for search service implementations.

    Search services are responsible for executing searches and returning standardized results.
    They should be completely agnostic to domain logic - they just execute queries and
    return raw search results.

    Examples: OpenAIService, LlamaService, GoogleService
    """

    @abstractmethod
    async def search(self, request: SearchRequest) -> SearchResults:
        """
        Execute a search query and return standardized results.

        Args:
            request: Standardized search request with query, depth, and options

        Returns:
            SearchResults: Standardized search results with sources and metadata

        Raises:
            SearchError: If search fails for any reason
        """
        pass


class DomainHandler(Protocol):
    """
    Protocol for domain-specific handlers.

    Domain handlers contain all the domain-specific knowledge:
    - How to build effective search queries for their domain
    - How to interpret and synthesize search results into structured data
    - Domain-specific validation and confidence assessment

    Examples: HSCodeHandler, BatteryInfoHandler, ProductSpecHandler
    """

    @abstractmethod
    def build_search_request(self, request: ResearchRequest) -> SearchRequest:
        """
        Build a domain-specific search request from a research request.

        This method encapsulates all domain knowledge about:
        - What terms to search for
        - How to structure queries for best results
        - How to use the provided search options (depth, content, etc.)

        Args:
            request: Research request containing product info and search options

        Returns:
            SearchRequest: Optimized search request for this domain
        """
        pass

    @abstractmethod
    async def synthesize_results(self, search_results: SearchResults, request: ResearchRequest) -> DomainResult:
        """
        Process search results into domain-specific structured data.

        This method encapsulates domain expertise about:
        - How to extract relevant information from search results
        - How to structure the data for this domain
        - How to assess confidence in the results
        - Domain-specific validation rules

        Args:
            search_results: Raw search results from search service
            request: Original research request for context

        Returns:
            DomainResult: Structured domain-specific result with confidence assessment
        """
        pass


# Additional protocol for future extensibility
class ResultValidator(Protocol):
    """
    Optional protocol for domain-specific result validation.

    This can be implemented by domains that need additional validation
    beyond the basic synthesize_results logic.
    """

    @abstractmethod
    def validate_result(self, result: DomainResult, request: ResearchRequest) -> DomainResult:
        """
        Validate and potentially modify a domain result.

        Args:
            result: The result to validate
            request: Original research request for context

        Returns:
            DomainResult: Validated (and potentially modified) result
        """
        pass
