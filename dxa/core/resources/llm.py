"""LLM resource implementation."""

from typing import Dict, Any, Optional, List
import asyncio
import json
import logging
from datetime import datetime
from dxa.core.resources.base import BaseResource, ResourceError

class LLMError(ResourceError):
    """Error in LLM interaction."""
    pass

class LLMResource(BaseResource):
    """Resource for interacting with a Language Model as an external resource."""
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize LLM resource."""
        super().__init__(
            name=name,
            description=f"External LLM resource using {llm_config.get('model', 'unknown model')}",
            config=llm_config
        )
        self.system_prompt = system_prompt
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._llm = None
        
        # Set up external LLM-specific logger
        self.llm_logger = logging.getLogger('dxa.llm.external')

    async def _log_interaction(
        self,
        interaction_type: str,
        messages: List[Dict[str, str]],
        response: Optional[Dict] = None,
        error: Optional[Exception] = None
    ):
        """Log an external LLM interaction."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "interaction_type": interaction_type,
            "llm_type": "external_resource",
            "llm_name": self.name,
            "model": self.config.get('model', 'unknown'),
            "messages": messages
        }

        if response:
            log_entry["response"] = response
        if error:
            log_entry["error"] = str(error)

        self.llm_logger.info(json.dumps(log_entry))

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
            raise LLMError(f"LLM initialization failed: {str(e)}")

    async def query(
        self,
        request: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Query the LLM."""
        prompt = request.get('prompt')
        if not prompt:
            raise ValueError("No prompt provided in request")

        system_prompt = request.get('system_prompt', self.system_prompt)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Log the request
        await self._log_interaction(
            interaction_type="request",
            messages=messages
        )

        for attempt in range(self.max_retries):
            try:
                response = await self._llm.chat.completions.create(
                    model=self.config.get('model', 'gpt-4'),
                    messages=messages,
                    temperature=request.get('temperature', 0.7),
                    max_tokens=request.get('max_tokens'),
                    **kwargs
                )
                
                # Convert usage to dict safely
                usage = None
                if hasattr(response, 'usage'):
                    usage = {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    }
                
                result = {
                    "success": True,
                    "content": response.choices[0].message.content,
                    "usage": usage,
                    "model": response.model
                }

                # Log the successful response
                await self._log_interaction(
                    interaction_type="response",
                    messages=messages,
                    response=result
                )
                
                return result
                
            except Exception as e:
                # Log the error
                await self._log_interaction(
                    interaction_type="error",
                    messages=messages,
                    error=e
                )
                
                self.logger.warning(
                    "LLM query attempt %d/%d failed: %s",
                    attempt + 1,
                    self.max_retries,
                    str(e)
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise LLMError(f"LLM query failed: {str(e)}")

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if this LLM can handle the request."""
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