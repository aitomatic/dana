"""Demonstrates the Loggable base class for standardized logging."""

import time
import logging
from dxa.common.utils.logging import Loggable, DXA_LOGGER

# Configure root logger to show all logs
logging.basicConfig(level=logging.INFO)

# Configure global logging level with console output
DXA_LOGGER.configure(level=logging.INFO, console=True)

print("Logging example started")


class SimpleService(Loggable):
    """A simple service class that inherits from Loggable."""
    
    def __init__(self, name):
        # Just call super().__init__() - that's it!
        super().__init__()
        self.name = name
        self.logger.info("Service initialized with name: %s", name)
    
    def process(self, data):
        """Process some data and log the activity."""
        self.logger.debug("Processing data: %s", data)
        result = f"Processed: {data}"
        self.logger.info("Processing complete")
        return result


class DataProcessor(Loggable):
    """A more complex example with custom logger name and prefix."""
    
    def __init__(self):
        # Customize logger with a prefix
        super().__init__(prefix="DataProcessor")
        self.logger.info("Data processor initialized")
        
    def analyze(self, dataset):
        """Analyze a dataset with detailed logging."""
        self.logger.info("Starting analysis of dataset with %d items", len(dataset))
        
        try:
            # Simulate processing with timing
            start_time = time.time()
            time.sleep(0.5)  # Simulate work
            
            # Log a warning
            if len(dataset) < 3:
                self.logger.warning("Dataset is small, results may be unreliable")
                
            result = sum(dataset) / len(dataset)
            duration = time.time() - start_time
            
            self.logger.info("Analysis completed in %.2f seconds", duration)
            return result
            
        except Exception as e:
            self.logger.error("Analysis failed: %s", str(e))
            raise


class NestedComponent(Loggable):
    """Demonstrates how nested components get appropriate logger names."""
    
    def __init__(self):
        super().__init__()
        self.logger.info("Nested component initialized")
        
    def execute(self):
        """Execute the component."""
        self.logger.debug("Executing nested component")
        return "Executed"


class ExecutionLayer(Loggable):
    """Demonstrates how execution layer classes get appropriate logger names."""
    
    def __init__(self):
        self.layer = "custom_layer"
        super().__init__()
        self.logger.info("Execution layer initialized")
        
    def execute(self):
        """Execute the layer."""
        self.logger.debug("Executing layer")
        return "Executed"


def main():
    """Run the example."""
    print("\n=== SIMPLE SERVICE EXAMPLE ===")
    service = SimpleService("auth-service")
    result = service.process("user-data")
    print(f"Result: {result}")
    
    print("\n=== DATA PROCESSOR EXAMPLE ===")
    processor = DataProcessor()
    try:
        avg = processor.analyze([1, 2, 3, 4, 5])
        print(f"Average: {avg}")
        
        # This will trigger a warning
        small_avg = processor.analyze([1, 2])
        print(f"Small average: {small_avg}")
        
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error: {e}")
    
    print("\n=== NESTED COMPONENT EXAMPLE ===")
    component = NestedComponent()
    component.execute()
    
    print("\n=== EXECUTION LAYER EXAMPLE ===")
    layer = ExecutionLayer()
    layer.execute()
    
    # Demonstrate class logger
    print("\n=== CLASS LOGGER EXAMPLE ===")
    logger = SimpleService.get_class_logger()
    logger.info("This is a class-level log message")


if __name__ == "__main__":
    main() 