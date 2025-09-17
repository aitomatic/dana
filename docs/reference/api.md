<!-- Compatible with Dana v0.5 -->
![Dana Version](https://img.shields.io/pypi/v/dana)

### Dana Runtime API Reference (v0.5)

Public surface validated against GitHub `v0.5` and PyPI `dana==0.5`.

#### CLI
- `dana --version`
- `dana run <path-to-file.na>`
  - Example: `dana run examples/agents/agent_with_resources_and_workflows/agent_with_resources.na`
- `dana studio`

#### Environment
- `DANA_LOG_LEVEL`: `info` (default), `debug`, `warn`, `error`

#### Exit codes
- `0`: success
- `1`: general error

#### Python interop
- If available in v0.5, see `examples/` for usage patterns.



