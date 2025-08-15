# Dana TUI Log Panel

The Dana TUI includes a hidden log panel that captures and displays all Python logging messages from the Dana logging system in real-time.

## Features

- **Captures existing logs**: Automatically captures all messages from `DANA_LOGGER`, `Loggable` mixin, and any Python logging
- **Real-time display**: Shows logs as they are generated, even from background threads
- **Color-coded levels**: Different colors for DEBUG, INFO, WARNING, ERROR, and CRITICAL messages
- **Toggle visibility**: Can be shown/hidden without affecting the main UI
- **Thread-safe**: Safely captures logs from any thread and displays them in the UI thread

## Usage

### Keyboard Shortcut
- **Ctrl+Shift+L**: Toggle the log panel visibility

### UI Controls
- **Clear button**: Clear all displayed log messages
- **Toggle button**: Show/hide the log panel

## What Gets Captured

The log panel automatically captures messages from:

1. **DANA_LOGGER**: All messages from the main Dana logging system
   ```python
   from dana.common.utils import DANA_LOGGER
   DANA_LOGGER.info("This will appear in the log panel")
   ```

2. **Loggable mixin**: Messages from classes that inherit from `Loggable`
   ```python
   from dana.common.mixins.loggable import Loggable
   
   class MyService(Loggable):
       def __init__(self):
           super().__init__()
           self.info("This will appear in the log panel")
   ```

3. **Dana standard library**: Messages from `py_log()` function
   ```python
   py_log("This will appear in the log panel", "INFO")
   ```

4. **Any Python logger**: Messages from any logger in the `dana.*` namespace
   ```python
   import logging
   logger = logging.getLogger("dana.api")
   logger.info("This will appear in the log panel")
   ```

5. **Root logger**: All messages sent to the root logger
   ```python
   import logging
   logging.info("This will appear in the log panel")
   ```

## Technical Details

### Architecture
- **TextualLogHandler**: Custom logging handler that captures log records
- **Message Queue**: Thread-safe queue for passing messages between logging threads and UI thread
- **Background Thread**: Processes messages from the queue and posts them to the UI
- **RichLog Widget**: Textual widget that displays the formatted log messages

### Message Flow
1. Log message is sent to Python logging system
2. `TextualLogHandler.emit()` captures the log record
3. Message is queued for processing
4. Background thread processes queue and posts `LogMessage` to UI
5. UI thread receives message and displays it in the `RichLog` widget

### Configuration
- **Max messages**: Default 1000 messages (configurable)
- **Format**: `%(asctime)s - [%(name)s] %(levelname)s - %(message)s`
- **Time format**: `%H:%M:%S`
- **Colors**: 
  - DEBUG: cyan
  - INFO: green
  - WARNING: yellow
  - ERROR: red
  - CRITICAL: magenta

## Example

```python
# This will appear in the TUI log panel when you press Ctrl+Shift+L
from dana.common.utils import DANA_LOGGER
from dana.common.mixins.loggable import Loggable

# Direct logging
DANA_LOGGER.info("Starting application")
DANA_LOGGER.warning("Configuration file not found")

# Service logging
class DataProcessor(Loggable):
    def __init__(self):
        super().__init__()
        self.info("DataProcessor initialized")
    
    def process(self, data):
        self.debug(f"Processing {len(data)} items")
        # ... processing logic ...
        self.info("Processing completed")

# All these messages will appear in the log panel
processor = DataProcessor()
processor.process([1, 2, 3, 4, 5])
```

## Testing

Run the demo script to see the log panel in action:

```bash
# Run the Dana script demo
dana demos/tui_logging_demo.na

# Or run the Python test script
python demos/test_tui_logging.py
```

Then start the TUI and press `Ctrl+Shift+L` to see all the log messages that were captured.
