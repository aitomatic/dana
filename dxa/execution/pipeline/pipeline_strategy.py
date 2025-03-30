"""Pipeline execution strategies."""

from enum import Enum

class PipelineStrategy(Enum):
    """Strategies for pipeline execution."""
    
    DEFAULT = "default"  # Default sequential execution
    PARALLEL = "parallel"  # Execute steps in parallel where possible
    BATCH = "batch"  # Process data in batches
    STREAM = "stream"  # Stream data through pipeline 