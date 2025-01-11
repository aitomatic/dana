"""Resource implementation for file-based information retrieval."""

from typing import Dict, Any, Optional, Union

from openssa import FileResource as OpenSsaFileResource

from .base_resource import BaseResource, ResourceConfig, ResourceResponse


class FileResource(BaseResource):
    """File-stored Informational Resource."""

    def __init__(
        self,
        path: str,
        re_index: bool = False,
        embed_model: Any = None,
        lm: Any = None,
        resource_config: Optional[Union[Dict[str, Any], ResourceConfig]] = None
    ):  # pylint: disable=too-many-arguments
        """Initialize FileResource.
        
        Args:
            path: Path to file or directory
            re_index: Whether to force reindexing
            embed_model: Optional custom embedding model
            lm: Optional custom language model
            resource_config: Resource configuration
        """
        # Create OpenSSA FileResource instance
        self._openssa_resource = OpenSsaFileResource(
            path=path,
            re_index=re_index,
            embed_model=embed_model,
            lm=lm
        )
        
        # Initialize BaseResource using OpenSSA resource properties
        super().__init__(
            name=self._openssa_resource.name,
            description=self._openssa_resource.overview,
            resource_config=resource_config
        )

    async def initialize(self) -> None:
        """Initialize the resource and build/load the index."""
        await super().initialize()
        self._is_available = True

    async def cleanup(self) -> None:
        """Cleanup resource."""
        await super().cleanup()
        self._is_available = False

    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        """Query the file resource.
        
        Args:
            request: Dictionary containing the query parameters.
                    Must include 'question' key with the query string.
                    Optional 'n_words' key to limit response length.

        Returns:
            ResourceResponse containing the query result
        """
        if not self._is_available:
            return ResourceResponse(success=False, error="Resource not initialized")

        try:
            question = request.get('question')
            if not question:
                return ResourceResponse(
                    success=False,
                    error="Request must include 'question' parameter"
                )

            n_words = request.get('n_words', 1000)
            answer = self._openssa_resource.answer(question=question, n_words=n_words)
            
            return ResourceResponse(success=True, content=answer)

        except Exception as e:
            return ResourceResponse(
                success=False,
                error=f"Error querying file resource: {str(e)}"
            )

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if the resource can handle the given request.
        
        Args:
            request: The request to check

        Returns:
            True if the request contains a 'question' key, False otherwise
        """
        return isinstance(request.get('question'), str)
