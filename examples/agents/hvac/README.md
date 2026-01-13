# HVAC Agent

A React-based demonstration UI for the HVAC Agent that showcases autonomous HVAC control planning with continuous learning through the STAR learning framework.

## Architecture

- **Backend**: FastAPI server (`api/server.py`) wrapping HVAC agent functions with learning support
- **LlamaStack**: Provides the inference endpoint (http://localhost:8321) for LLM API calls
- **Frontend**: React + TypeScript UI (`ui/`) using Vite
- **Learning**: STAR learning framework with acquisitive and episodic learning phases

## Setup

### Prerequisites

- uv
- Node.js 18+ and npm
- OpenAI API key configured in project root `.env` file

### Quick Setup (Recommended)

The easiest way to set up and run the application is using the provided scripts.

```bash
cd examples/agents/hvac
./install.sh   # Run the installation script once
./start.sh     # Start all services
```

All services run in the background and can be stopped with Ctrl+C. Logs are available at:

- LlamaStack: `tail -f /tmp/llamastack.log`
- HVAC API: `tail -f /tmp/hvac-api.log`
- UI: `tail -f /tmp/hvac-ui.log`

### Manual Setup

If you prefer to do each step manually, here's what each script does and how to run the commands yourself.

```bash
cd dana-internal           # Navigate to project root
source .env                # Load environment variables
uv sync                    # Sync venv. This includes LlamaStack libary
source .venv/bin/activate  # Activate venv
cd examples/agents/hvac    # Navigate to app directory

# LlamaStack starter dependencies (without altering pyproject.toml)
llama stack list-deps starter | xargs -L1 uv pip install

# Install app UI dependencies
npm -C ui install

# Start servers in the background, output logs, and save PID for later cleanup
llama stack run starter > /tmp/llamastack.log 2>&1 &
LLAMASTACK_PID=$!
python api/server.py > /tmp/hvac-api.log 2>&1 &
API_PID=$!
npm -C ui run dev > /tmp/hvac-ui.log 2>&1 &
UI_PID=$!

# Stop all services (when done)
kill $LLAMASTACK_PID $API_PID $UI_PID
```

**Note:** The `start.sh` script automatically handles cleanup on Ctrl+C, but when running manually, you'll need to stop each process individually or use `kill` with the PIDs.

Now you can access the app at http://localhost:5173.

## The App

**What it does:**
The HVAC Agent creates temperature control plans for conference rooms based on current conditions and scheduled meetings. It uses an LLM to make intelligent decisions about when to turn HVAC systems on/off, what temperature to target, and whether to use energy-intensive "turbo" mode.

**Inputs:**

- **Current indoor temperature** (°F) - Current room temperature
- **Outdoor temperature** (°F) - Outside temperature affecting heat transfer
- **Current time** (HH:MM) - When the plan is being created
- **Meeting schedule** - List of upcoming meetings with start/end times

**Decisions the agent makes:**

1. **Mode selection**: Whether to heat or cool (based on indoor vs target temperature)
2. **Target temperature**: What temperature to reach (typically 72°F for comfort)
3. **Timing**: When to start HVAC (e.g., 10 minutes before first meeting) and when to stop
4. **Turbo mode**: Whether to use high-power mode (faster but more expensive) or normal mode
5. **Multiple actions**: How to handle multiple meetings throughout the day

**Outputs:**

- **HVAC Plan** (JSON): A schedule of HVAC actions with:
  - `time_on` / `time_off`: When to start/stop each action
  - `use_turbo`: Whether to use turbo mode
  - `target_temps`: Target temperature for each action
  - `mode`: "cool" or "heat"
- **Validation Feedback**: After the plan is created, it's validated against a physics simulation that checks:
  - Whether target temperatures are reached in time
  - Total energy consumption (kWh)
  - Final temperature after all actions
  - Success/failure status for each action

**The flow:**

1. **Generate Environment**: Creates a random scenario with temperatures and meeting schedule
2. **Agent Planning**: LLM analyzes the environment and creates an HVAC control plan
3. **Validation**: Physics simulation validates the plan and provides feedback
4. **Learning**: Agent learns from the results to improve future plans

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

## Development Scripts

**Note:** All development scripts that use the agent require a LlamaStack server to be running first for LLM inference. Ensure its depenencies are installed and start it with:

```bash
llama stack run starter > /tmp/llamastack.log 2>&1 &
```

- `learn_playground.py`: A playground script for testing and exploring the learning system.
  - Loads acquisitive learnings from previous agent runs
  - Triggers episodic learning to analyze patterns across all executions
  - Displays stored episodic learning content
  - Shows feedback and timeline entries
  - Useful for debugging and understanding what the agent has learned
- `environment/agent_example.py`: Simple demonstration script showing the two main HVAC API functions:
  - `get_env_status()` - Get current environment (temperature, time, meetings)
  - `get_feedback()` - Validate an HVAC plan and get detailed feedback
- `environment/ac_test.py`: Test file for HVAC physics calculations. Contains functions for:
  - Calculating time needed to reach target temperatures
  - Estimating temperature changes over time
  - Validating HVAC schedules
  - Calculating energy costs
  - Includes extensive examples and test cases

## Learning Storage

Learning data is stored in this folder's `.dana`.

- **Acquisitive learning**: `{workspace_folder}/{codec}/{agent_class}__{filename}/learnings/{session_id}/acquisitive/loop_*.json`
- **Episodic learning**: `{workspace_folder}/{codec}/{agent_class}__{filename}/learnings/{session_id}/episodic/learnings.md`
- **Feedback**: `{workspace_folder}/{codec}/{agent_class}__{filename}/feedback/{session_id}/feedback.md`

Where:

- `{workspace_folder}`: Default is `.dana/dana_agent/` (in project root)
- `{codec}`: Codec prefix (or "default" if no codec)
- `{agent_class}`: Agent class name (e.g., "HVACAgent")
- `{filename}`: Stem of the file where the agent class is defined (e.g., "hvac_agent")
- `{session_id}`: Session identifier
