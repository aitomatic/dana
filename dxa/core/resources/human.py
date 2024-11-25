"""Human user resource implementation."""

from typing import Dict, Any, Optional
import asyncio
from dxa.core.resources.base_resource import BaseResource, ResourceError
from dxa.core.io.base_io import BaseIO
from dxa.core.io.console import ConsoleIO

class HumanError(ResourceError):
    """Error in human interaction."""
    pass

class HumanUserResource(BaseResource):
    """Resource for interacting with human users."""
    
    def __init__(
        self,
        name: str,
        role: str,
        permissions: Optional[Dict[str, bool]] = None,
        io: Optional[BaseIO] = None,
        timeout: float = 300.0
    ):
        """Initialize human user resource."""
        super().__init__(
            name=name,
            description=f"Human user with role: {role}"
        )
        self.role = role
        self.permissions = permissions or {}
        self.timeout = timeout
        self.io = io or ConsoleIO()

    async def initialize(self) -> None:
        """Initialize the I/O handler."""
        try:
            await self.io.initialize()
            self._is_available = True
            self.logger.info("Human user resource initialized successfully")
        except Exception as e:
            self._is_available = False
            self.logger.error("Failed to initialize I/O: %s", str(e))
            raise HumanError(f"I/O initialization failed: {str(e)}") from e

    async def query(
        self,
        request: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Query the human user."""
        message = request.get('message')
        if not message:
            raise ValueError("No message provided in request")

        require_response = request.get('require_response', True)
        timeout = request.get('timeout', self.timeout)

        try:
            # Send message to user
            await self.io.send_message(f"[{self.role}] {message}")
            
            if require_response:
                try:
                    response = await asyncio.wait_for(
                        self.io.get_input("Your response: "),
                        timeout=timeout
                    )
                    return {
                        "success": True,
                        "response": response,
                        "role": self.role
                    }
                except asyncio.TimeoutError:
                    await self.io.send_message(
                        f"Response timed out after {timeout} seconds"
                    )
                    raise HumanError("Response timeout")
            else:
                return {
                    "success": True,
                    "response": None,
                    "role": self.role
                }
                
        except Exception as e:
            self.logger.error("Error in human interaction: %s", str(e))
            raise HumanError(f"Interaction failed: {str(e)}")

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if this user can handle the request."""
        # Check if request has required fields
        if 'message' not in request:
            return False
            
        # Check if user has required permissions
        required_permission = request.get('required_permission')
        if required_permission and not self.permissions.get(required_permission, False):
            return False
            
        return True

    async def cleanup(self) -> None:
        """Clean up I/O resources."""
        try:
            await self.io.cleanup()
        finally:
            self._is_available = False
            self.logger.info("Human user resource cleaned up")