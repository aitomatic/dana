# HVAC Agent Demo - Learning-First UI

A React-based demonstration UI for the HVAC Agent that showcases autonomous HVAC control planning with continuous learning through the STAR learning framework.

## Architecture

- **Backend**: FastAPI server (`api/server.py`) wrapping HVAC agent functions with learning support
- **Frontend**: React + TypeScript UI (`ui/`) using Vite
- **Learning**: STAR learning framework with acquisitive and episodic learning phases

## Prerequisites

- Python 3.9+ with `uv` package manager installed
- Node.js 18+ and npm
- OpenAI API key (or other LLM provider) configured

## Setup

### Backend Setup

1. Navigate to the project root:
```bash
cd /path/to/dana-internal
```

2. The backend uses dependencies from the `uv`-managed virtual environment. Run the server using one of these methods:

**Option 1: Using `uv run` (Recommended)**
```bash
uv run python3 examples/agents/honeywell-hvac/api/server.py
```

**Option 2: Activate venv manually**
```bash
source .venv/bin/activate
cd examples/agents/honeywell-hvac/api
python3 server.py
```

The backend server will run on `http://localhost:8081`

### Frontend Setup

1. Navigate to the UI directory:
```bash
cd examples/agents/honeywell-hvac/ui
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:5173`

## Usage

1. **Start the backend server** (Terminal 1)
   ```bash
   uv run python3 examples/agents/honeywell-hvac/api/server.py
   ```

2. **Start the frontend dev server** (Terminal 2)
   ```bash
   cd examples/agents/honeywell-hvac/ui
   npm run dev
   ```

3. **Open the application** in your browser:
   ```
   http://localhost:5173
   ```

4. **Click "Run Agent"** to execute the flow:
   - Generate random environment
   - Agent creates HVAC plan (triggers acquisitive learning automatically)
   - Validate plan with feedback
   - View learning insights prominently displayed

## Features

### Learning-First Design

- **Learning Growth Tracker**: Visual timeline showing all executions and what was learned from each
- **Current Learning Highlight**: Prominently displays what the agent learned from the current execution
- **Accumulated Knowledge**: Shows episodic learning that accumulates patterns across executions
- **Learning Metrics**: Dashboard showing total learnings, efficiency improvements, and success rates

### Components

- **Environment Panel**: Shows current temperature, time, and meeting schedule with learning indicators
- **Agent Plan Visualization**: Displays the HVAC plan with badges showing which learnings informed it
- **Feedback Detail**: Shows validation results and action breakdowns
- **Session Management**: Create and switch between sessions to view different learning histories

## API Endpoints

### Core Endpoints
- `POST /api/hvac/environment` - Generate random environment
- `POST /api/hvac/plan` - Get agent plan from environment (triggers acquisitive learning)
- `POST /api/hvac/validate` - Validate plan and get feedback

### Learning Endpoints
- `GET /api/hvac/learnings/acquisitive` - Get all acquisitive learnings for session
- `GET /api/hvac/learnings/episodic` - Get episodic learning for session
- `POST /api/hvac/learnings/episodic` - Trigger episodic learning
- `GET /api/hvac/learnings/metrics` - Get learning metrics
- `GET /api/hvac/feedback` - Get stored feedback

### Session Management
- `GET /api/hvac/sessions` - List available sessions
- `POST /api/hvac/sessions` - Create new session

## Development

The UI uses:
- React 19 + TypeScript
- Tailwind CSS (dark theme)
- Zustand for state management
- Recharts for graphs (future)
- Radix UI components

### Troubleshooting

**Backend Issues:**
- If you get `ModuleNotFoundError`, make sure you're using `uv run` or have activated the venv
- Verify dependencies are installed: `uv sync`

**Frontend Issues:**
- If the API calls fail, make sure the backend is running on port 8081
- Check browser console for CORS errors (should be handled by backend CORS middleware)

**Learning Not Showing:**
- Ensure the agent has a learner attached (`agent._learner = WilliamLearner(agent=agent)`)
- Check that acquisitive learning is being triggered after plan creation
- Verify session_id is set correctly

## Learning Storage

Learning data is stored in:
- **Acquisitive learning**: `{workspace_folder}/{codec}/{agent_class}/learnings/{session_id}/acquisitive/loop_*.json`
- **Episodic learning**: `{workspace_folder}/{codec}/{agent_class}/learnings/{session_id}/episodic/learnings.md`
- **Feedback**: `{workspace_folder}/{codec}/{agent_class}/feedback/{session_id}/feedback.md`

Default workspace folder: `.dana/dana_agent/` (in project root)

