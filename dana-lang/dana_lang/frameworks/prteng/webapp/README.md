# PromptEngineer Web App

A web-based interface for the PromptEngineer framework that allows interactive prompt optimization through user feedback.

## Features

- **Interactive Prompt Selection**: Choose from existing prompt IDs or create new ones
- **Real-time Prompt Evolution**: Provide feedback to improve system prompts
- **Version Tracking**: See prompt version numbers and evolution history
- **LLM Integration**: Uses real LLM resources for prompt generation and evaluation
- **Persistent Storage**: Saves prompt history and template versions

## Quick Start

### Option 1: Direct Python execution
```bash
cd /path/to/dana-internal
python dana/frameworks/prteng/webapp/prompt_engineer_webapp.py
```

### Option 2: Using the launcher script
```bash
cd /path/to/dana-internal
python dana/frameworks/prteng/webapp/run_webapp.py
```

Then open your browser and go to: http://localhost:8080

## Usage

1. **Select or Create Prompt ID**: Use the dropdown to select an existing prompt or create a new one
2. **Ask Questions**: Enter queries to test the current system prompt
3. **Provide Feedback**: Give feedback on AI responses to evolve the prompt
4. **Track Evolution**: Watch the system prompt improve through version numbers

## API Endpoints

- `POST /api/init` - Initialize the session
- `POST /api/start` - Start a conversation with a query
- `POST /api/generate` - Generate AI response
- `POST /api/feedback` - Process user feedback and evolve prompt
- `GET /api/prompt-ids` - Get list of existing prompt IDs
- `GET /api/history` - Get conversation history

## File Structure

```
webapp/
├── __init__.py                    # Module initialization
├── prompt_engineer_webapp.py     # Main Flask application
├── run_webapp.py                 # Launcher script
├── templates/
│   └── index.html               # Web interface template
└── README.md                    # This file
```

## Dependencies

- Flask (web framework)
- Dana framework (PromptEngineer, LLM resources)
- Python 3.8+
