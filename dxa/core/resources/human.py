"""Human user resource implementation."""

from typing import Dict, Any, Optional
import asyncio
from dxa.core.resources.base import BaseResource
from dxa.core.io.base import BaseIO
from dxa.core.io.console import ConsoleIO  # Default to console

class HumanUserResource(BaseResource):
    """Resource for interacting with human users."""
    
    def __init__(
        self,
        name: str,
        role: str,
        permissions: Optional[Dict[str, bool]] = None,
        timeout: float = 300.0,
        io: Optional[BaseIO] = None  # Add I/O parameter
    ):
        """Initialize human user resource."""
        super().__init__(
            name=name,
            description=f"Human user with role: {role}",
            config={"role": role, "timeout": timeout}
        )
        self.role = role
        self.permissions = permissions or {}
        self.timeout = timeout
        self.io = io or ConsoleIO()  # Default to console I/O

    async def initialize(self) -> None:
        """Initialize the resource."""
        await self.io.initialize()
        self._is_available = True

    async def cleanup(self) -> None:
        """Clean up the resource."""
        await self.io.cleanup()
        self._is_available = False

    async def query(
        self,
        request: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Query the human user."""
        await super().query(request)
        
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
                    raise
            else:
                return {
                    "success": True,
                    "response": None,
                    "role": self.role
                }
                
        except Exception as e:
            self.logger.error("Error in human user interaction: %s", str(e))
            raise

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if this user can handle the request."""
        # Check if request has required fields
        if 'message' not in request:
            return False
            
        # Check if user has required permissions
        required_permission = request.get('required_permission')
        if required_permission:
            return self.permissions.get(required_permission, False)
            
        return True