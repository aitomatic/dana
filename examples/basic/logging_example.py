"""Demonstrates combined basic and LLM logging."""

from dxa.common.utils.logging import DXALogger
import time

def main():
    # Initialize and configure
    logger = DXALogger()
    logger.configure(console=True, level="debug")
    
    # Basic application logging
    logger.debug("Starting processing", module="data_loader")
    logger.info("Connected to database", db="production")
    logger.warning("High memory usage", current="85%", threshold="80%")
    
    try:
        # LLM interaction with timing
        with logger.track("llm_query") as op:
            op.add_meta(user="u123", phase="analysis")
            time.sleep(0.5)  # Simulate processing time
            
            # Log LLM interaction
            logger.log_llm(
                prompt="Analyze this dataset",
                response="Summary: ...",
                model="gpt-4-analytics",
                tokens=2450
            )
            
        # Simulate error
        raise ConnectionError("API timeout")
        
    except Exception as e:
        # LLM error logging
        logger.log_llm_error(
            error_message=str(e),
            model="gpt-4-analytics",
            error_type="api_timeout",
            retries=3,
            endpoint="/v1/completions"
        )
        
        # General error logging
        logger.error("Critical pipeline failure", stage="analysis")

if __name__ == "__main__":
    main() 