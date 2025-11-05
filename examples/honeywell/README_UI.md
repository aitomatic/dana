# HVAC Agent UI Demo

A React-based demonstration UI for the HVAC Agent that showcases autonomous HVAC control planning with learned policies.

## Architecture

- **Backend**: FastAPI server (`api/server.py`) wrapping HVAC agent functions
- **Frontend**: React + TypeScript UI (`ui/`) using Vite
- **Components**: Reused from `dana_lang/contrib/ui` for consistency

## Setup

### Backend Setup

```bash
cd examples/honeywell/api
pip install -r requirements.txt
python server.py
```

Backend runs on `http://localhost:8081`

### Frontend Setup

```bash
cd examples/honeywell/ui
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

## Usage

1. Start the backend server (Terminal 1)
2. Start the frontend dev server (Terminal 2)
3. Open `http://localhost:5173` in your browser
4. Click "Run Agent Flow" to execute the 3-step process:
   - Generate random environment
   - Agent creates HVAC plan
   - Validate plan with feedback

## Features

- **Environment Panel**: Shows current temperature, time, and meeting schedule
- **Timeline Panel**: Visual progress indicator and timeline visualization
- **Results Panel**: Displays agent plan (JSON), validation feedback, and learned policies

## API Endpoints

- `POST /api/hvac/environment` - Generate random environment
- `POST /api/hvac/plan` - Get agent plan from environment
- `POST /api/hvac/validate` - Validate plan and get feedback
- `GET /api/hvac/policies` - Get current policies from HVACAgent.xml

## Development

The UI uses:
- React 19 + TypeScript
- Tailwind CSS (dark theme)
- Zustand for state management
- Recharts for graphs (future)
- Radix UI components

All components are reused from `dana_lang/contrib/ui` for consistency.

