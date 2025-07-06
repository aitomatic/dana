# 26 June 2025: AI Alliance Japan 1st Anniversary: Dana Community Launch Technical Workshop

## Agenda

- Introduction: __AI-Powered Runtime Revolution: Superpowers to Engineers__

- Topic 1: __Dana Language & AI-Powered Runtime Highlights__

- Topic 2: __Agent & System of Agents__

- Topic 3: __Knowledge Organization & Workflow System (KNOWS) for Domain-Expert Agents (DXAs)__

- Topic 4: __Perceive-Operate-Enforce-Train (POET) Architecture for Fault Tolerance, Determinism & Adaptive Learning__

- Topic 5: __Python Interoperability__

## Setup Checklist

### Before Workshop Day

- __Operating System__: MacOS, Linux, or Windows Subsystem for Linux (WSL)

- __Python__: 3.12 or 3.13 installed on your operating system
  - Corresponding `python3` executable must be in your system's search path and callable from your command-line terminal

- __Git__: installed and configured on your operating system
  - Corresponding `git` executable must be in your system's search path and callable from your command-line terminal

- [__Visual Studio Code__](https://code.visualstudio.com/download) or [__Cursor__](https://www.cursor.com/downloads) IDE installed

- __OpenDXA Repo Access__: email your GitHub ID to OSS@Aitomatic.com to be granted early access to https://github.com/aitomatic-oss/opendxa

### On Workshop Day

- __OpenDXA Repo Clone__: `git clone https://github.com/aitomatic-oss/opendxa` down to your laptop

- __OpenDXA Repo Open in IDE__: open the cloned OpenDXA repo folder with either Visual Studio Code or Cursor

- __Astral's `uv` Tool__ installed by running `make check-uv` from cloned OpenDXA repo's root directory
  - if that doesn't work, try `python3 -m pip install uv --upgrade --user --break-system-packages`

- __Deactivate/Exit any existing Python virtual environment__ (e.g. Anaconda/Miniconda, PyEnv, etc.): because we will use `uv` for virtual environment management

- __OpenDXA Library Installation__ by running `make install` from cloned OpenDXA repo's root directory

- __Set IDE Workspace Python Interpreter__ to the virtual environment created by `uv` tool

- __LLM API Key__: put a `.env` file with credentials such as `OPENAI_API_KEY=<an-openai-api-key>` into cloned OpenDXA repo's root directory
  - OpenDXA works with all popular LLM backends, including OpenAI, Anthropic, Google, and more;
    for this workshop, we will use OpenAI's API keys as most participants readily have them

- (Optional but Recommended) __Dana Extension for Visual Studio Code or Cursor__ installed by running `make install-vscode` or `make install-cursor` from cloned OpenDXA repo's root directory
  - this requires `npm` to be installed on your operating system,
    with `npm` executable in your system's search path and callable from your command-line terminal

#### MCP Server Installation & Launch for use in examples/exercises

- `cd` to `examples/dana/202506_workshop`
- `util/install-weather-mcp-server`
- `util/launch-weather-mcp-server`

#### Running .na Dana Files in IDE

- Run `.na` files with the __Run and Debug__ button "Run Dana File" in the Visual Studio Code or Cursor
