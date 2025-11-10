# Running the HVAC Agent API Server

This server requires dependencies from the `uv`-managed virtual environment. The `dana_agent` package (and its dependencies like `structlog`) are installed in `.venv`.

## Why `python3 server.py` fails

When you run `python3 server.py` directly, it uses your system Python (or another environment) which doesn't have the required dependencies installed. You'll see errors like:

```
ModuleNotFoundError: No module named 'structlog'
```

## ✅ Correct Ways to Run

### Option 1: Using `uv run` (Recommended)

```bash
cd /path/to/dana-internal
uv run python3 examples/honeywell/api/server.py
```

### Option 2: Using the run script

```bash
cd examples/honeywell/api
./run_server.sh
```

### Option 3: Using the Python wrapper

```bash
cd examples/honeywell/api
python3 run_server.py
```

### Option 4: Activate venv manually

```bash
cd /path/to/dana-internal
source .venv/bin/activate
cd examples/honeywell/api
python3 server.py
```

## Server Endpoints

Once running, the server will be available at `http://localhost:8081`:

- `GET /health` - Health check
- `POST /api/hvac/environment` - Generate random environment
- `POST /api/hvac/plan` - Get agent plan from environment
- `POST /api/hvac/validate` - Validate plan and get feedback
- `GET /api/hvac/policies` - Get current policies from HVACAgent.xml

## Troubleshooting

If you still get import errors:

1. Make sure dependencies are installed: `uv sync`
2. Check that you're using `uv run` or have activated the venv
3. Verify the venv exists: `ls -la .venv/bin/python3`

