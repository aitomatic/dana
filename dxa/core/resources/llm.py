"""LLM resource implementation."""

from typing import Dict, Any, Optional
import asyncio
from dxa.core.resources.base import (
    BaseResource,
    ResourceError,
    ResourceUnavailableError,
    ResourceAccessError
)

class LLMError(ResourceError):
    """Error in LLM interaction."""
    pass

class LLMResource(BaseResource):
    """Resource for interacting with a Language Model."""
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize LLM resource.
        
        Args:
            name: Name of this LLM resource
            llm_config: Configuration for the LLM
            system_prompt: Optional system prompt
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        super().__init__(
            name=name,
            description=f"LLM resource using {llm_config.get('model', 'unknown model')}",
            config=llm_config
        )
        self.system_prompt = system_prompt
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._llm = None

    async def initialize(self) -> None:
        """Initialize the LLM client."""
        try:
            from openai import AsyncOpenAI
            self._llm = AsyncOpenAI(**self.config)
            self._is_available = True
            self.logger.info("LLM resource initialized successfully")
        except Exception as e:
            self._is_available = False
            self.logger.error("Failed to initialize LLM resource: %s", str(e))
            raise ResourceUnavailableError(f"LLM initialization failed: {str(e)}")

    async def query(
        self,
        request: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Query the LLM.
        
        Args:
            request: The request containing:
                - prompt: The prompt to send
                - system_prompt: Optional override for system prompt
                - temperature: Optional temperature setting
                - max_tokens: Optional max tokens setting
            **kwargs: Additional arguments for the LLM
            
        Returns:
            Dict containing LLM response
            
        Raises:
            ResourceUnavailableError: If LLM is not available
            ResourceAccessError: If LLM query fails
        """
        await super().query(request)  # Check availability
        
        prompt = request.get('prompt')
        if not prompt:
            raise ValueError("No prompt provided in request")

        system_prompt = request.get('system_prompt', self.system_prompt)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(self.max_retries):
            try:
                response = await self._llm.chat.completions.create(
                    model=self.config.get('model', 'gpt-4'),
                    messages=messages,
                    temperature=request.get('temperature', 0.7),
                    max_tokens=request.get('max_tokens'),
                    **kwargs
                )
                
                return {
                    "success": True,
                    "content": response.choices[0].message.content,
                    "usage": response.usage._asdict() if hasattr(response, 'usage') else None,
                    "model": response.model
                }
                
            except Exception as e:
                self.logger.warning(
                    "LLM query attempt %d/%d failed: %s",
                    attempt + 1,
                    self.max_retries,
                    str(e)
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise ResourceAccessError(f"LLM query failed: {str(e)}")

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if this LLM can handle the request.
        
        Args:
            request: Request to check
            
        Returns:
            True if this LLM can handle the request, False otherwise
        """
        # Check if request has required fields
        if 'prompt' not in request:
            return False
            
        # Check if model is specified and matches
        if 'model' in request:
            return request['model'] == self.config.get('model')
            
        return True

    async def cleanup(self) -> None:
        """Clean up LLM resources."""
        self._llm = None
        self._is_available = False
        self.logger.info("LLM resource cleaned up") 