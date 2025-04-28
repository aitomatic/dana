# OpenDXA Logging

OpenDXA uses a structured logging system for consistent and configurable logging across the framework.

## Basic Configuration

```python
from opendxa.common import DXA_LOGGER

# Configure logging level and output
DXA_LOGGER.configure(level=DXA_LOGGER.INFO, console=True, filename="opendxa.log")

# Use logger within the framework
DXA_LOGGER.info("This is an info message.")
DXA_LOGGER.debug("This is a debug message.")
```

## Logging Levels

- `DEBUG`: Detailed information for debugging
- `INFO`: General operational information
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for recoverable errors
- `CRITICAL`: Critical errors that may prevent operation

## Configuration Options

See `opendxa/common/logger.py` for more configuration options, including:
- Log format customization
- Multiple output destinations
- Log rotation
- Contextual logging
- Performance optimization 

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 