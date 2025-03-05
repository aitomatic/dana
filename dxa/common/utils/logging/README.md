# DXA Logging

This module provides standardized logging capabilities for the DXA framework.

## Components

- **DXALogger**: Core logging class with enhanced functionality
- **DXA_LOGGER**: Global logger instance
- **Loggable**: Abstract base class for objects that need logging capabilities
- **LLMInteractionAnalyzer**: Utility for analyzing LLM interactions

## Using the Loggable Base Class

The `Loggable` abstract base class provides a standardized way to add logging capabilities to your classes with minimal boilerplate code.

### Basic Usage

```python
from dxa.common.utils.logging import Loggable

class MyService(Loggable):
    def __init__(self):
        # Just call super().__init__() - that's it!
        super().__init__()
        self.logger.info("Service initialized")
    
    def process(self, data):
        self.logger.debug("Processing data: %s", data)
        # ... processing logic ...
        self.logger.info("Processing complete")
```

### Features

1. **Automatic Logger Naming**: The logger is automatically named based on the class's module hierarchy and class name.

2. **Execution Layer Support**: For execution layer classes (with a `layer` attribute), the logger is automatically named `dxa.execution.<layer>`.

3. **Convenience Methods**: Direct access to logging methods:

   ```python
   self.debug("Debug message")
   self.info("Info message")
   self.warning("Warning message")
   self.error("Error message")
   ```

4. **Class-level Logging**: Static method for class-level logging:

   ```python
   logger = MyClass.get_class_logger()
   logger.info("Class-level log message")
   ```

5. **Customization Options**: Optional parameters for custom logger names and prefixes:

   ```python
   super().__init__(logger_name="custom.logger", prefix="MyComponent")
   ```

### Migration Guide

To migrate existing classes to use `Loggable`:

1. Add `Loggable` to your class's inheritance list
2. Replace your logger initialization code with a call to `super().__init__()`
3. For classes with a `layer` attribute, ensure it's set before calling `super().__init__()`

#### Before

```python
class Executor:
    def __init__(self):
        self.layer = "executor"
        self.logger = logging.getLogger(f"dxa.execution.{self.layer}")
```

#### After

```python
class Executor(Loggable):
    def __init__(self):
        self.layer = "executor"
        super().__init__()  # Logger is automatically set up
```

### Multiple Inheritance

When using `Loggable` with multiple inheritance, ensure that:

1. `Loggable.__init__()` is called after any attributes it depends on are set
2. The MRO (Method Resolution Order) is appropriate for your class hierarchy

```python
class ResourceExecutor(Resource, Loggable):
    def __init__(self):
        Resource.__init__(self)
        # Set any attributes Loggable depends on
        self.layer = "resource_executor"
        # Then initialize Loggable
        Loggable.__init__(self)
```

## Examples

See the example files in `examples/basic/`:

- `loggable_example.py`: Demonstrates basic and advanced usage
- `loggable_migration.py`: Shows how to migrate existing classes
