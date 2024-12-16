<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA I/O System

The I/O system manages all interactions between agents and their environment.

## Available Handlers

- **Console I/O**: Command-line interaction
- **WebSocket I/O**: Real-time network communication
- **File I/O**: File system operations
- **API I/O**: Web service integration

## Interface

All I/O handlers implement BaseIO:

```python
class CustomIO(BaseIO):
    async def send_message(self, message: str) -> None:
        """Send output message"""
        pass
        
    async def get_input(self, prompt: Optional[str] = None) -> str:
        """Get input with optional prompt"""
        pass
```

## Usage

```python
from dxa.core.io import ConsoleIO

agent = Agent("assistant")\
    .with_io(ConsoleIO())
```

See tests for implementation examples. 