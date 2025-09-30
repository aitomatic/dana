# Quickstart (v0.5)

Get a working agent and launch Dana Agent Studio in under 5 minutes.

## 1) Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install dana
dana --version
```

<Check>
You should see a version like `Dana 0.5` or higher.
</Check>

## 2) Run your first agent

```bash
dana run examples/agents/agent_with_resources_and_workflows/agent_with_resources.na
```

<Expected>
The agent runs locally and prints a simple response.
</Expected>

## 3) Open Dana Agent Studio

```bash
dana studio
```

<Tip>
Keep the terminal running while you explore Dana Agent Studio. If `dana` is not on PATH, use `python -m dana`.
</Tip>

For environment prerequisites and from-source setup, see Tech Setup.
