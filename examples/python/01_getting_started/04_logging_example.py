"""Demonstrates both basic and advanced DXALogger usage."""

import time
from opendxa.common import DXA_LOGGER

def demo_basic_usage():
    """Simplest possible logging setup"""
    DXA_LOGGER.info("Basic example started")
    DXA_LOGGER.log_llm(
        prompt="Hi there!",
        response="Hello!",
        model="gpt-3.5-turbo"
    )

def demo_combined_logging():
    """More comprehensive example with error handling"""
    logger = DXA_LOGGER.getLogger(__name__)
    logger.configure(console=True, level=DXA_LOGGER.DEBUG)
    
    # Application monitoring
    logger.debug("Starting data processing", module="analyzer")
    logger.info("Connected to cloud storage", provider="AWS S3")
    
    try:
        # Complex LLM operation
        with logger.track("data_analysis"):
            logger.log_llm(
                prompt="Analyze quarterly sales",
                response="Sales increased by 15%",
                model="gpt-4",
                tokens=1200
            )
            time.sleep(0.3)  # Simulate processing
            
        raise ConnectionError("API timeout")
        
    except ConnectionError as e:
        logger.log_llm_error(
            message=str(e),
            model="gpt-4",
            error_type="api_failure",
            retries=2
        )

if __name__ == "__main__":
    print("=== BASIC USAGE ===")
    demo_basic_usage()
    
    print("\n=== ADVANCED USAGE ===")
    demo_combined_logging() 