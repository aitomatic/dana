"""Memory Resource implementation for DXA.

This module provides memory resource classes that implement
memory storage and retrieval operations using the underlying storage system.

Classes:
    MemoryResource: Base resource for managing memories
    LTMemoryResource: Resource for managing long-term memories
    STMemoryResource: Resource for managing short-term memories
    PermMemoryResource: Resource for managing permanent memories

Memory Decay Mechanism:
    The memory decay system implements a time-based exponential decay model:
    
    1. Decay Rate and Interval:
       - decay_rate: The percentage by which a memory's importance decreases per decay interval
       - decay_interval: The time period (in seconds) between decay checks
       - These parameters work together to create a forgetting curve
    
    2. Decay Calculation:
       - Decay is calculated based on wall clock time, not fixed intervals
       - When a memory operation occurs, we check how much time has passed
       - The decay factor is calculated as: (1 - decay_rate) ^ (time_passed / decay_interval)
       - This ensures memories decay at the correct rate regardless of when checks happen
    
    3. Decay Triggers:
       - Decay is checked on every memory operation (store, retrieve, update)
       - If enough time has passed since last decay, decay is applied
       - Decay runs in a separate thread to avoid blocking operations
    
    4. Memory Removal:
       - Memories with importance below 0.01 are automatically removed
       - This threshold prevents storing effectively forgotten memories
    
    5. Half-Life:
       - The system calculates and reports the half-life of memories
       - Half-life = -ln(2) / ln(1 - decay_rate) * decay_interval
       - This helps users understand how quickly memories decay
    
    Memory Types and Defaults:
        Short-Term Memory (ST):
            - Default decay_rate: 0.1 (10% decay per interval)
            - Default importance: 0.5
            - Default retrieve_limit: 5
            - With default 6-hour interval:
                - Half-life = ~1.8 days
                - Memory importance drops to ~0.01 in ~9 days
                - Designed for memories that should persist for hours to days
        
        Long-Term Memory (LT):
            - Default decay_rate: 0.01 (1% decay per interval)
            - Default importance: 2.0
            - Default retrieve_limit: 10
            - With default 24-hour interval:
                - Half-life = ~69 days
                - Memory importance drops to ~0.01 in ~345 days
                - Designed for memories that should persist for weeks to months
        
        Permanent Memory (Perm):
            - No decay mechanism
            - Default importance: 3.0
            - Default retrieve_limit: 20
            - Memories persist indefinitely
            - Designed for critical information that should never be forgotten
    
    Example:
        decay_rate = 0.1 (10% decay per interval)
        decay_interval = 3600 (1 hour)
        If 2 hours pass:
        - intervals_passed = 2.0
        - decay_factor = (1 - 0.1) ^ 2.0 = 0.81
        - A memory with importance 1.0 would decay to 0.81
"""

from typing import Dict, Any, Optional, TypeVar, Generic, Type
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from opendxa.base.resource.base_resource import BaseResource, ResourceResponse
from opendxa.base.db.models import MemoryDBModel, STMemoryDBModel, LTMemoryDBModel, PermanentMemoryDBModel
from opendxa.base.db.storage import MemoryDBStorage

ModelType = TypeVar('ModelType', bound=MemoryDBModel)
StorageType = TypeVar('StorageType', bound=MemoryDBStorage)

class MemoryResource(BaseResource, Generic[ModelType, StorageType]):
    """Base resource for managing memories.
    
    This resource provides common functionality for memory operations
    using the underlying storage system.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        storage: Optional[StorageType] = None,
        model_class: Optional[Type[ModelType]] = None,
        default_importance: float = 1.0,
        default_decay_rate: float = 0.1,
        default_retrieve_limit: int = 10,
        decay_interval: int = 3600  # Default: 1 hour
    ):
        """Initialize the memory resource.
        
        Args:
            name: Resource name
            storage: Memory storage implementation
            description: Optional resource description
            config: Optional additional configuration
            default_importance: Default importance value for memories
            default_decay_rate: Default decay rate (per interval)
            default_retrieve_limit: Default limit for memory retrieval
            decay_interval: Interval in seconds between decay operations
        """
        super().__init__(name, description, config)
        self._storage = storage
        self._model_class = model_class
        self._default_importance = default_importance
        self._default_decay_rate = default_decay_rate
        self._default_retrieve_limit = default_retrieve_limit
        self._decay_interval = decay_interval
        self._last_decay_time: Optional[datetime] = None
        self._decay_lock = asyncio.Lock()
        self._half_life: Optional[float] = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        
        # Validate decay parameters
        self._validate_decay_parameters()
    
    def _validate_decay_parameters(self) -> None:
        """Validate that decay parameters make sense together.
        
        Raises:
            ValueError: If decay parameters are invalid
        """
        if self._default_decay_rate == 0:
            # Permanent memory
            return

        if not 0 < self._default_decay_rate < 1:
            raise ValueError("Decay rate must be between 0 and 1")
        
        if self._decay_interval <= 0:
            raise ValueError("Decay interval must be positive")
        
        # Calculate expected half-life based on decay rate
        # Using the formula: t_1/2 = -ln(2) / ln(1 - decay_rate)
        if self.half_life < float('inf'):
            expected_interval = self._decay_interval / self.half_life
        else:
            expected_interval = 0
        
        # Warn if the interval seems too long or too short
        if expected_interval > 10:  # More than 10 intervals to reach half-life
            self.warning(
                f"Decay interval ({self._decay_interval}s) seems long relative to decay rate "
                f"({self._default_decay_rate}). Memory will take {expected_interval:.1f} "
                "intervals to reach half-life."
            )
        elif expected_interval < 0.1:  # Less than 0.1 intervals to reach half-life
            self.warning(
                f"Decay interval ({self._decay_interval}s) seems short relative to decay rate "
                f"({self._default_decay_rate}). Memory will reach half-life in {expected_interval:.1f} "
                "intervals."
            )
    
    @property
    def decay_rate(self) -> float:
        """Get the current default decay rate."""
        return self._default_decay_rate
    
    @decay_rate.setter
    def decay_rate(self, value: float) -> None:
        """Set the default decay rate.
        
        Args:
            value: New decay rate value (must be between 0 and 1)
            
        Raises:
            ValueError: If the decay rate is not between 0 and 1
        """
        if not 0 < value < 1:
            raise ValueError("Decay rate must be between 0 and 1")
        self._default_decay_rate = value
        self._validate_decay_parameters()
        self.info(f"Decay rate updated to {value} for resource [{self.name}]")
    
    @property
    def half_life(self) -> float:
        """Get the current half-life in seconds."""
        if self._half_life is None:
            import math
            if self._default_decay_rate > 0 and self._default_decay_rate < 1:
                self._half_life = -math.log(2) / math.log(1 - self._default_decay_rate)
            else:
                self._half_life = float('inf')
        return self._half_life

    @property
    def decay_interval(self) -> int:
        """Get the current decay interval in seconds."""
        return self._decay_interval
    
    @decay_interval.setter
    def decay_interval(self, value: int) -> None:
        """Set the decay interval in seconds.
        
        Args:
            value: New decay interval in seconds (must be positive)
            
        Raises:
            ValueError: If the interval is not positive
        """
        if value <= 0:
            raise ValueError("Decay interval must be positive")
        self._decay_interval = value
        self._validate_decay_parameters()
        self.info(f"Decay interval updated to {value} seconds for resource [{self.name}]")
    
    def _should_decay(self) -> bool:
        """Check if it's time to run decay.
        
        Returns:
            True if decay should be run, False otherwise
        """
        if not self._last_decay_time:
            return True
        
        time_since_last_decay = (datetime.utcnow() - self._last_decay_time).total_seconds()
        return time_since_last_decay >= self._decay_interval
    
    async def _maybe_decay(self) -> None:
        """Check if decay should run and execute it if needed.
        
        This method is called before memory operations to ensure
        memories are decayed appropriately based on wall clock time.
        """
        if self._last_decay_time is None:
            self._last_decay_time = datetime.now()
            return
            
        now = datetime.now()
        time_since_last_decay = (now - self._last_decay_time).total_seconds()
        
        # Only run decay if enough time has passed
        if time_since_last_decay >= self._decay_interval:
            # Calculate how many decay intervals have passed
            intervals_passed = time_since_last_decay / self._decay_interval
            
            # Run decay in a separate thread to avoid blocking
            def run_decay():
                asyncio.run_coroutine_threadsafe(
                    self.decay_memories(intervals_passed),
                    asyncio.get_event_loop()
                ).result()
            
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                run_decay
            )
            
            self._last_decay_time = now

    async def decay_memories(self, intervals_passed: float = 1.0) -> None:
        """Decay memories in the storage.
        
        Args:
            intervals_passed: Number of decay intervals that have passed since last decay
        """
        async with self._decay_lock:
            try:
                # Get all memories that need decay
                memories = await self._storage.get_memories()
                
                # Calculate decay factor for the elapsed time
                # Using compound decay: (1 - decay_rate) ^ intervals_passed
                decay_factor = (1 - self._default_decay_rate) ** intervals_passed
                
                # Update importance for each memory
                for memory in memories:
                    new_importance = memory.importance * decay_factor
                    if new_importance < 0.01:  # Threshold for removal
                        await self._storage.delete_memory(memory.id)
                    else:
                        await self._storage.update_memory_importance(
                            memory.id,
                            new_importance
                        )
                
                self.info(
                    f"Decayed memories for {intervals_passed:.1f} intervals "
                    f"(decay factor: {decay_factor:.3f})"
                )
                
            except Exception as e:
                self.error(f"Error decaying memories: {str(e)}")
                raise
    
    async def initialize(self) -> None:
        """Initialize the memory resource."""
        await super().initialize()
        self._storage.initialize()
        self.info(f"Memory resource [{self.name}] initialized with decay interval of {self._decay_interval} seconds")
    
    async def cleanup(self) -> None:
        """Clean up the memory resource."""
        self._executor.shutdown(wait=True)
        await super().cleanup()
        self._storage.cleanup()
        self.info(f"Memory resource [{self.name}] cleaned up")
    
    async def store(
        self,
        content: Any,
        context: Optional[Dict] = None,
        importance: Optional[float] = None,
        decay_rate: Optional[float] = None
    ) -> ResourceResponse:
        """Store a memory.
        
        Args:
            content: The memory content to store
            context: Optional context about the memory
            importance: Optional importance factor (uses default if not provided)
            decay_rate: Optional decay rate (uses default if not provided)
            
        Returns:
            ResourceResponse indicating success or failure
        """
        try:
            await self._maybe_decay()  # Check for decay before storing
            self.warning(f"self._model_class: {self._model_class}")
            # Create a new instance of the model class
            memory = self._model_class(
                content=content,
                context=context,
                importance=importance or self._default_importance,
                decay_rate=decay_rate or self._default_decay_rate
            )
            self.warning(f"Storing memory: {memory}")
            print(f"self._storage: {self._storage}")
            die
            return ResourceResponse(success=True, content={"content": content})
            self._storage.store(memory)
            return ResourceResponse(success=True, content={"content": content})
        except Exception as e:
            die
            return ResourceResponse.error_response(f"Failed to store memory: {str(e)}")
    
    async def retrieve(
        self,
        query: Optional[str] = None,
        limit: Optional[int] = None
    ) -> ResourceResponse:
        """Retrieve memories.
        
        Args:
            query: Optional query to filter memories
            limit: Optional maximum number of memories to retrieve
            
        Returns:
            ResourceResponse containing the retrieved memories
        """
        try:
            await self._maybe_decay()  # Check for decay before retrieving
            memories = self._storage.retrieve(
                query=query,
                limit=limit or self._default_retrieve_limit
            )
            return ResourceResponse(success=True, content=memories)
        except Exception as e:
            return ResourceResponse.error_response(f"Failed to retrieve memories: {str(e)}")
    
    async def update_importance(self, memory_id: int, importance: float) -> ResourceResponse:
        """Update the importance of a memory.
        
        Args:
            memory_id: The ID of the memory to update
            importance: New importance value
            
        Returns:
            ResourceResponse indicating success or failure
        """
        try:
            await self._maybe_decay()  # Check for decay before updating
            self._storage.update_importance(memory_id, importance)
            return ResourceResponse(success=True, content={"memory_id": memory_id, "importance": importance})
        except Exception as e:
            return ResourceResponse.error_response(f"Failed to update memory importance: {str(e)}")
    
    def get_decay_stats(self) -> Dict[str, Any]:
        """Get statistics about the decay process.
        
        Returns:
            Dictionary containing decay statistics
        """
        import math
        half_life = -math.log(2) / math.log(1 - self._default_decay_rate)
        intervals_to_half_life = self._decay_interval / half_life
        
        return {
            "decay_interval": self._decay_interval,
            "last_decay_time": self._last_decay_time.isoformat() if self._last_decay_time else None,
            "default_decay_rate": self._default_decay_rate,
            "half_life_intervals": intervals_to_half_life,
            "half_life_seconds": intervals_to_half_life * self._decay_interval
        }
    
    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if the resource can handle the request.
        
        Args:
            request: The request to check
            
        Returns:
            True if the resource can handle the request, False otherwise
        """
        return request.get("type") == "memory"

class LTMemoryResource(MemoryResource[LTMemoryDBModel, MemoryDBStorage[LTMemoryDBModel]]):
    """Resource for managing long-term memories.
    
    This resource provides an interface to store and retrieve long-term memories
    using the underlying storage system. Long-term memories have lower decay rates
    and higher importance values by default.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the long-term memory resource.
        
        Args:
            name: Resource name
            storage: Memory storage implementation
            description: Optional resource description
            config: Optional additional configuration
        """
        super().__init__(
            name=name,
            description=description,
            config=config,
            storage=MemoryDBStorage[LTMemoryDBModel](
                vector_db_url=config.get("vector_db_url"),
                embedding_model=config.get("embedding_model"),
                db_model_class=LTMemoryDBModel,
            ),
            model_class=LTMemoryDBModel,
            default_importance=2.0,
            default_decay_rate=0.001,  # 0.1% decay per second
            default_retrieve_limit=10,
            decay_interval=86400  # 24 hours
        )
    
    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if the resource can handle the request.
        
        Args:
            request: The request to check
            
        Returns:
            True if the resource can handle the request, False otherwise
        """
        return super().can_handle(request) and request.get("memory_type") == "long_term"

class STMemoryResource(MemoryResource[STMemoryDBModel, MemoryDBStorage[STMemoryDBModel]]):
    """Resource for managing short-term memories.
    
    This resource provides an interface to store and retrieve short-term memories
    using the underlying storage system. Short-term memories have higher decay rates
    and lower importance values by default.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the short-term memory resource.
        
        Args:
            name: Resource name
            storage: Memory storage implementation
            description: Optional resource description
            config: Optional additional configuration
        """
        super().__init__(
            name=name,
            description=description,
            config=config,
            storage=MemoryDBStorage[STMemoryDBModel](
                vector_db_url=config.get("vector_db_url"),
                embedding_model=config.get("embedding_model"),
                db_model_class=STMemoryDBModel,
            ),
            model_class=STMemoryDBModel,
            default_importance=0.5,
            default_decay_rate=0.01,  # % per second
            default_retrieve_limit=5,
            decay_interval=3600  # 1 hour
        )
    
    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if the resource can handle the request.
        
        Args:
            request: The request to check
            
        Returns:
            True if the resource can handle the request, False otherwise
        """
        return super().can_handle(request) and request.get("memory_type") == "short_term"

class PermMemoryResource(MemoryResource[PermanentMemoryDBModel, MemoryDBStorage[PermanentMemoryDBModel]]):
    """Resource for managing permanent memories.
    
    This resource provides an interface to store and retrieve permanent memories
    using the underlying storage system. Permanent memories have no decay mechanism
    and higher importance values by default.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the permanent memory resource.
        
        Args:
            name: Resource name
            storage: Memory storage implementation
            description: Optional resource description
            config: Optional additional configuration
        """
        super().__init__(
            name=name,
            description=description,
            config=config,
            storage=MemoryDBStorage[PermanentMemoryDBModel](
                vector_db_url=config.get("vector_db_url"),
                embedding_model=config.get("embedding_model"),
                db_model_class=PermanentMemoryDBModel,
            ),
            model_class=PermanentMemoryDBModel,
            default_importance=3.0,
            default_decay_rate=0.0,  # No decay
            default_retrieve_limit=20,
            decay_interval=0  # No decay interval
        )
    
    async def _maybe_decay(self) -> None:
        """Override to disable decay mechanism."""
        pass
    
    async def decay_memories(self, intervals_passed: float = 1.0) -> None:
        """Override to disable decay mechanism."""
        pass
    
    def get_decay_stats(self) -> Dict[str, Any]:
        """Override to return permanent memory stats."""
        return {
            "decay_interval": 0,
            "last_decay_time": None,
            "default_decay_rate": 0.0,
            "half_life_intervals": float('inf'),
            "half_life_seconds": float('inf')
        }
    
    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if the resource can handle the request.
        
        Args:
            request: The request to check
            
        Returns:
            True if the resource can handle the request, False otherwise
        """
        return super().can_handle(request) and request.get("memory_type") == "permanent" 