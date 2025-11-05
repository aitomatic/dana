# Cursor Agent Mode Tools - Complete Documentation

## Table of Contents

- [Introduction](#introduction)
- [How LLMs Call Tools](#how-llms-call-tools)
- [Tool Calling Workflows](#tool-calling-workflows)
- [Tool Availability](#tool-availability)
- [File Operations](#file-operations)
  - [READ_FILE](#read_file)
  - [EDIT_FILE](#edit_file)
  - [CREATE_FILEI](#create_file)
  - [DELETE_FILE](#delete_file)
  - [LIST_DIR](#list_dir)
- [Search & Discovery](#search--discovery)
  - [SEMANTIC_SEARCH_FULL](#semantic_search_full)
  - [RIPGREP_SEARCH](#ripgrep_search)
  - [FILE_SEARCH](#file_search)
  - [SEARCH_SYMBOLS](#search_symbols)
  - [READ_SEMSEARCH_FILES](#read_semsearch_files)
  - [GET_RELATED_FILES](#get_related_files)
- [Execution](#execution)
  - [RUN_TERMINAL_COMMAND](#run_terminal_command)
  - [RUN_TERMINAL_COMMAND_V2](#run_terminal_command_v2)
- [Advanced Operations](#advanced-operations)
  - [PARALLEL_APPLY](#parallel_apply)
  - [REAPPLY](#reapply)
  - [PLANNER](#planner)
  - [IMPLEMENTER](#implementer)
  - [WEB_SEARCH](#web_search)
  - [WEB_VIEWER](#web_viewer)
  - [KNOWLEDGE_BASE](#knowledge_base)
  - [FETCH_RULES](#fetch_rules)
- [Integration Tools](#integration-tools)
  - [MCP](#mcp)
  - [DIFF_HISTORY](#diff_history)
  - [READ_FILE_FOR_IMPORTS](#read_file_for_imports)
  - [BACKGROUND_COMPOSER_FOLLOWUP](#background_composer_followup)

---

## Introduction

Cursor's **Agent Mode** is an autonomous coding assistant that can plan, search, make edits, and run commands with minimal user intervention. Agent Mode has access to 25+ specialized tools that enable it to interact with your codebase, execute commands, search the web, and more.

### What is Agent Mode?

Agent Mode is one of four composer modes in Cursor:
- **Agent**: Autonomous mode with full tool access - "Plan, search, make edits, run commands"
- **Ask**: Read-only mode for questions about the codebase
- **Manual**: User controls context, tools disabled
- **Background**: Asynchronous agent execution

### Key Features

- **Autonomous Operation**: Can automatically use tools without manual approval (configurable)
- **Auto-fix on Lints**: Iteratively fixes linter errors when enabled
- **Auto-save Edits**: Automatically saves files after making changes
- **Multi-file Editing**: Can edit multiple files simultaneously
- **Command Execution**: Can run terminal commands and scripts
- **Web Integration**: Can search the web and interact with web pages

---

## How LLMs Call Tools

When the LLM (Large Language Model) needs to use a tool in Agent Mode, it responds with a specific **XML format**, not JSON, YAML, or other structured formats. This section explains how tool calling works internally.

### Format Structure

LLMs call tools using XML wrapped in a markdown code block. The structure is:

````markdown
```xml
<function_call>
<invoke name="TOOL_NAME">
<parameter name="parameter_name_1">value</parameter>
<parameter name="parameter_name_2">value</parameter>
</invoke>
</function_call>
```
````

### Complete Example: EDIT_FILE Tool Call

Here's a realistic example of how an LLM would call the `EDIT_FILE` tool to add TypeScript types to a function:

````markdown
```xml
<function_call>
<invoke name="EDIT_FILE">
<parameter name="relative_workspace_path">src/utils/math.ts</parameter>
<parameter name="language">typescript</parameter>
<parameter name="blocking">true</parameter>
<parameter name="old_string">function add(a, b) {
  return a + b;
}</parameter>
<parameter name="new_string">function add(a: number, b: number): number {
  return a + b;
}</parameter>
<parameter name="use_whitespace_insensitive_fallback">true</parameter>
</invoke>
</function_call>
```
````

### How It Works

1. **Tool Schema Provided to LLM**: Cursor sends the LLM a JSON Schema describing each available tool:
   ```typescript
   {
     type: "object",
     name: "EDIT_FILE",
     properties: {
       relative_workspace_path: { 
         type: "string", 
         description: "Path to the file relative to workspace root" 
       },
       language: { 
         type: "string", 
         description: "Programming language of the file" 
       },
       old_string: { 
         type: "string", 
         description: "String to search for in the file" 
       },
       new_string: { 
         type: "string", 
         description: "Replacement string" 
       },
       // ... more properties
     },
     required: ["relative_workspace_path", "language", "blocking"]
   }
   ```

2. **LLM Responds with XML**: The LLM generates the XML-formatted tool call as shown above

3. **Cursor Parses the Response**: Cursor uses regex patterns to extract the tool call:
   - Detects opening: `/^```(\s*|xml)\n<function_call>/`
   - Extracts tool name: `/<invoke name="([^"]+)">/`
   - Extracts parameters: `/<parameter name="([^"]+)">([\s\S]*?)<\/parameter>/g`
   - Detects closing: `/^<\/function_call>\s*\n```/`

4. **Parameters Stored**: The raw XML content is stored in the `raw_args` field as a string

5. **Tool Execution**: Cursor converts the XML parameters to the proper protobuf format and executes the tool

6. **Result Returned**: The tool's output is sent back to the LLM to continue the conversation

### Why XML Format?

Cursor uses XML for tool calling for several important reasons:

1. **Claude's Native Format**: This format is based on **Anthropic's Claude** function calling convention, which uses XML-style tags
2. **Human Readable**: XML with clear tag names is easy to read in chat interfaces
3. **Multiline Content**: XML handles multiline strings (like code blocks) naturally without escaping
4. **LLM-Friendly**: Language models trained on diverse web data handle XML markup very well
5. **Flexible Structure**: Easy to parse while supporting nested and complex data structures

### Supported Variations

While the primary format is XML in markdown code blocks, Cursor also supports:
- **Plain XML** (without markdown code block wrapper) for certain contexts
- **Partial tool calls** during streaming responses (for progressive UI updates)
- **Multiple tool calls** in sequence within a single response

### Key Takeaways

- Tools are called using **XML format**, specifically Claude's function calling style
- **Not JSON or YAML** - the format is XML wrapped in markdown code blocks
- Parameters can contain **multiline values** (like code snippets) naturally
- The format is **parsed with regex** and converted to internal protobuf structures
- This design enables **seamless integration** with Claude and other capable LLMs

---

## Tool Calling Workflows

Tool execution in Cursor happens through multiple workflows, not just from LLM autonomous decisions. Understanding these workflows is crucial for leveraging Cursor's full capabilities.

### Three Main Workflows

#### Workflow 1: LLM-Autonomous (Agent Loop)

```
User Prompt → Agent Mode → LLM Analysis → Tool Schema Selection
→ XML Generation → Cursor Parses → Tool Executes → Result to LLM
→ [LOOP: Continue until task complete]
```

The LLM decides which tools to use based on the task and available information.

#### Workflow 2: User-Directed (Explicit Tool Reference)

```
User types #tool_name → Autocomplete → LLM receives tool instruction
→ XML Generation → Tool Executes → Result shown
```

Users can explicitly reference tools in their prompts for more control.

#### Workflow 3: Manual-Triggered (Direct Execution)

```
User clicks Apply/UI button → Direct tool execution
→ Result applied → No LLM involved
```

Direct UI interactions trigger tools without LLM decision-making.

---

### The Iterative Agent Loop

**KEY INSIGHT**: Cursor doesn't call just one tool and stop. It operates in an **iterative loop**, calling multiple tools sequentially until it has sufficient information to complete the user's request.

#### The Complete Loop Diagram

```
┌─────────────────────────────────────────────────────────┐
│  USER INPUT (Initial Request)                           │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
        ╔═══════════════════════════════════╗
        ║   AGENT ITERATIVE LOOP (START)    ║
        ╚═══════════════╤═══════════════════╝
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  LLM ANALYSIS                                            │
│  - Analyze current state                                │
│  - Evaluate available information                       │
│  - Decide: Need more info OR Ready to solve             │
└───────────────────┬─────────────────────────────────────┘
                    │
            ┌───────┴────────┐
            │                │
            ▼                ▼
    [Need More Info]   [Have Sufficient Info]
            │                │
            ▼                │
┌─────────────────────────   │
│  SELECT TOOL(S)         │  │
│  - Choose next tool     │  │
│  - Generate XML call    │  │
└──────────┬──────────────┘  │
           │                 │
           ▼                 │
┌─────────────────────────   │
│  EXECUTE TOOL           │  │
│  - Parse XML            │  │
│  - Run tool             │  │
│  - Get results          │  │
└──────────┬──────────────┘  │
           │                 │
           ▼                 │
┌─────────────────────────   │
│  TOOL RESULT            │  │
│  - Process output       │  │
│  - Add to context       │  │
│  - Update state         │  │
└──────────┬──────────────┘  │
           │                 │
           │ LOOP BACK       │
           └─────────────────┤
                    │        │
                    ▼        ▼
        ╔═══════════════════════════════════╗
        ║  DECISION: Continue or Complete?  ║
        ╚═══════════════╤═══════════════════╝
                        │
            ┌───────────┴───────────┐
            │                       │
            ▼                       ▼
    [Continue Loop]          [Task Complete]
            │                       │
            │                       ▼
            │           ┌──────────────────────┐
            │           │  GENERATE RESPONSE   │
            │           │  - Synthesize answer │
            │           │  - Apply changes     │
            └───────────┤  - Show to user      │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │  END                 │
                        └──────────────────────┘
```

### Real-World Example: Multi-Tool Iteration

**User Request**: "Add authentication to the login endpoint"

The agent doesn't just make one edit. Instead, it iterates through multiple tools:

**Iteration 1**: 
- **Tool**: `SEMANTIC_SEARCH_FULL`
- **Action**: Search for "authentication middleware"
- **Result**: Finds existing auth implementation at `src/middleware/auth.ts`
- **Decision**: Need to read the file to understand implementation

**Iteration 2**:
- **Tool**: `READ_FILE`
- **Action**: Read `src/middleware/auth.ts`
- **Result**: Understands JWT verification logic and middleware structure
- **Decision**: Need to find the login endpoint

**Iteration 3**:
- **Tool**: `RIPGREP_SEARCH`
- **Action**: Search for "login.*endpoint" or "/login"
- **Result**: Locates endpoint in `src/routes/auth.routes.ts` at line 45
- **Decision**: Need to read the routes file

**Iteration 4**:
- **Tool**: `READ_FILE`
- **Action**: Read `src/routes/auth.routes.ts`
- **Result**: Sees current endpoint structure without authentication
- **Decision**: Have enough information, ready to apply changes

**Iteration 5**:
- **Tool**: `EDIT_FILE`
- **Action**: Add authentication middleware to login route
- **Result**: File edited successfully, diff generated
- **Decision**: Should verify with tests

**Iteration 6**:
- **Tool**: `RUN_TERMINAL_COMMAND`
- **Action**: Execute `npm test -- auth.routes.test.ts`
- **Result**: All tests pass
- **Decision**: Task complete, have sufficient information

**Final Step**: Generate comprehensive response explaining what was done.

### Context Accumulation

Each tool call adds information to the agent's working context:

```
Initial Context:
  └─ User Request: "Add authentication to the login endpoint"

After Tool 1 (SEMANTIC_SEARCH):
  ├─ User Request
  └─ Found: auth.ts contains middleware

After Tool 2 (READ_FILE):
  ├─ User Request
  ├─ Found: auth.ts contains middleware
  └─ Learned: How JWT verification works

After Tool 3 (RIPGREP_SEARCH):
  ├─ User Request
  ├─ Found: auth.ts contains middleware
  ├─ Learned: How JWT verification works
  └─ Found: Login endpoint at routes/auth.routes.ts:45

After Tool 4 (READ_FILE):
  ├─ User Request
  ├─ Found: auth.ts contains middleware
  ├─ Learned: How JWT verification works
  ├─ Found: Login endpoint at routes/auth.routes.ts:45
  └─ Learned: Current route structure

After Tool 5 (EDIT_FILE):
  ├─ [All previous context]
  └─ Applied: Authentication middleware to route

After Tool 6 (RUN_TERMINAL_COMMAND):
  ├─ [All previous context]
  └─ Verified: Tests pass

Final Context = Complete understanding → Generate solution
```

This accumulation allows the agent to make informed decisions at each step.

### Stopping Conditions

The iterative loop continues until one of these conditions is met:

1. **Task Completed**: LLM determines it has sufficient information and has completed the requested changes
2. **Max Iterations Reached**: Safety limit prevents infinite loops (implementation-dependent)
3. **Error State**: Critical error that cannot be recovered from
4. **User Intervention**: User stops the process or rejects a tool call
5. **No Useful Tools**: No additional tools can provide helpful information
6. **Context Limit**: Approaching token/context window limits

### Workflow Comparison

| Workflow Type | LLM Involved | Iterative | User Control | Use Case |
|--------------|--------------|-----------|--------------|----------|
| **LLM-Autonomous** | Yes | Yes | Low | Complex tasks requiring exploration |
| **User-Directed** | Yes | Yes | Medium | Specific tool with LLM parameters |
| **Manual-Triggered** | No | No | High | Quick fixes, known operations |

### Mode-Specific Behaviors

Different composer modes affect how the loop operates:

| Mode | Tool Availability | Iterative Loop | User Approval | Auto-save |
|------|------------------|----------------|---------------|-----------|
| **Agent** | All 25+ tools | ✓ Full loop | Optional | Yes (configurable) |
| **Ask** | Read-only tools | ✓ Limited loop | N/A | No |
| **Manual** | No auto tools | ✗ No loop | Always | User decides |
| **Background** | All tools | ✓ Full loop | No (async) | Yes |

### Tool Execution Sources

Cursor tracks where tool executions originate from:

- **`COMPOSER`**: LLM-initiated from composer chat
- **`COMPOSER_AGENT`**: Specific to Agent Mode iteration
- **`CLICKED_APPLY`**: User manually clicked "Apply" button
- **`CACHED_APPLY`**: Reused previous execution results

This tracking helps with analytics and debugging tool call patterns.

### Key Decision Points in the Loop

At each iteration, Cursor evaluates several decision points:

1. **Mode Check**: Is Agent Mode enabled? What tools are available?
2. **Information Sufficiency**: Does the LLM have enough context?
3. **Tool Selection**: Which tool(s) would be most helpful next?
4. **User Approval**: Does this tool require user confirmation?
5. **Auto-save Decision**: Should changes be automatically saved?
6. **Linter Check**: Should linter errors trigger additional iterations?
7. **Continue or Complete**: Loop again or finish?

### Benefits of the Iterative Approach

1. **Adaptive Problem Solving**: Agent discovers information progressively
2. **Reduced Guesswork**: Each tool call is informed by previous results
3. **Complex Task Handling**: Can break down large tasks into steps
4. **Error Recovery**: Can detect issues and iterate to fix them
5. **Comprehensive Solutions**: Gathers all necessary context before acting

### Example: Linter Error Recovery Loop

The iterative loop is especially powerful for auto-fixing errors:

```
User: "Fix the TypeScript errors in Button.tsx"

Iteration 1: READ_FILE → See type errors
Iteration 2: EDIT_FILE → Add type annotations
Iteration 3: [Auto linter check] → New error detected
Iteration 4: EDIT_FILE → Fix import statement
Iteration 5: [Auto linter check] → All clear
Complete: Return success
```

This is enabled by the "Iterate on lints" setting in Agent Mode.

---

## Tool Availability

### Mode-Based Access

- **Agent Mode** and **Chat Mode**: Have access to all tools
- **Edit Mode** and **Manual Mode**: Restricted tool sets based on configuration

### Feature Flags

Some tools require specific settings or feature flags:

| Tool | Requirement |
|------|-------------|
| `WEB_SEARCH` | `isWebSearchToolEnabled3` setting |
| `CREATE_FILE` | Excluded by default in non-agent modes |
| `FETCH_RULES` | Requires `.cursorrules` file configuration |
| `KNOWLEDGE_BASE` | Requires `memoriesEnabled` setting |
| `MCP` | Requires Model Context Protocol server configuration |

### User Approval Settings

The setting "Allow Agent to run tools without asking for confirmation" controls whether tools like `RUN_TERMINAL_COMMAND` and file operations require user approval.

---

## File Operations

### READ_FILE

**ID**: `5` | **Category**: File Operations

Read the contents of a file with optional line range specification.

#### Input Parameters

```typescript
{
  relative_workspace_path: string;          // Required: Path relative to workspace root
  read_entire_file: boolean;                // Required: Whether to read the entire file
  start_line_one_indexed?: number;          // Optional: Starting line (1-indexed)
  end_line_one_indexed_inclusive?: number;  // Optional: Ending line (1-indexed, inclusive)
  file_is_allowed_to_be_read_entirely: boolean; // Required: Safety flag for large files
  max_lines?: number;                       // Optional: Maximum lines to read
  max_chars?: number;                       // Optional: Maximum characters to read
  min_lines?: number;                       // Optional: Minimum lines to read
}
```

#### Internal Logic

1. **Path Resolution**: Resolves the relative path against workspace root
2. **Permission Check**: Validates file is not in `.cursorignore` or `.gitignore`
3. **Size Validation**: Checks against `max_lines` and `max_chars` limits
4. **Range Processing**: 
   - If `read_entire_file` is false, uses line range
   - Automatically downgrades to line range if file is too large
   - Shortens range if exceeds limits
5. **Content Reading**: Reads file contents with proper encoding
6. **Cursor Rules**: Checks for matching `.cursorrules` files

#### Output Format

```typescript
{
  contents: string;                          // File contents (may be partial)
  did_downgrade_to_line_range: boolean;     // True if full read was downgraded
  did_shorten_line_range: boolean;          // True if range was shortened
  did_set_default_line_range: boolean;      // True if default range was used
  relative_workspace_path: string;          // Confirmed path
  did_shorten_char_range: boolean;          // True if char limit was applied
  matching_cursor_rules: CursorRule[];      // Applicable .cursorrules
}
```

#### Example

**Input**:
```json
{
  "relative_workspace_path": "src/components/Button.tsx",
  "read_entire_file": false,
  "start_line_one_indexed": 10,
  "end_line_one_indexed_inclusive": 50,
  "file_is_allowed_to_be_read_entirely": false,
  "max_lines": 100
}
```

**Output**:
```json
{
  "contents": "export function Button({ label, onClick }: ButtonProps) {\n  return (\n    <button onClick={onClick}>\n      {label}\n    </button>\n  );\n}",
  "did_downgrade_to_line_range": false,
  "did_shorten_line_range": false,
  "did_set_default_line_range": false,
  "relative_workspace_path": "src/components/Button.tsx",
  "did_shorten_char_range": false,
  "matching_cursor_rules": []
}
```

---

### EDIT_FILE

**ID**: `7` | **Category**: File Operations

Edit an existing file using either a full code block or search-and-replace.

#### Input Parameters

```typescript
{
  relative_workspace_path: string;               // Required: File path
  language: string;                              // Required: Programming language
  blocking: boolean;                             // Required: Whether to block on completion
  contents: string;                              // Required: New contents (for full replacement)
  line_ranges: LineRange[];                      // Optional: Specific line ranges to edit
  should_edit_file_fail_for_large_files?: boolean; // Optional: Fail if file too large
  old_string?: string;                           // Optional: String to search for (search-replace mode)
  new_string?: string;                           // Optional: Replacement string
  allow_multiple_matches?: boolean;              // Optional: Allow multiple replacements
  use_whitespace_insensitive_fallback?: boolean; // Optional: Ignore whitespace differences
  use_did_you_mean_fuzzy_match?: boolean;        // Optional: Enable fuzzy matching
}
```

#### Internal Logic

1. **Mode Detection**:
   - If `old_string` and `new_string` provided: Search-replace mode
   - Otherwise: Full content replacement mode

2. **File Size Validation**:
   - Max lines: 3500
   - Max characters: 150000
   - If exceeded and `should_edit_file_fail_for_large_files` is true, switches to search-replace

3. **Search-Replace Processing**:
   - Searches for `old_string` in file
   - If `allow_multiple_matches` is false, ensures unique match
   - Applies `use_whitespace_insensitive_fallback` for fuzzy matching
   - Uses `use_did_you_mean_fuzzy_match` for similar strings

4. **Full Replacement Processing**:
   - Applies new contents to file or specified line ranges
   - Generates diff for review

5. **Auto-Save Behavior**:
   - If `getShouldAutoSaveAgenticEdits()` is true, automatically saves
   - Otherwise, requires user confirmation

6. **Linter Integration**:
   - If `autoFix` is enabled and `shouldProcessDiagnostics()` returns true
   - Automatically fetches linter errors after edit
   - Can trigger iterative fixes in Agent Mode

#### Output Format

```typescript
{
  diff: Diff;                    // Generated diff
  is_applied: boolean;           // Whether edit was applied
  apply_failed: boolean;         // Whether application failed
  linter_errors: LinterError[];  // Linter errors after edit
  rejected?: boolean;            // Whether user rejected
  num_matches?: number;          // Number of matches found (search-replace)
}
```

#### Example 1: Search-Replace

**Input**:
```json
{
  "relative_workspace_path": "src/utils/math.ts",
  "language": "typescript",
  "blocking": true,
  "contents": "",
  "old_string": "function add(a, b) {\n  return a + b;\n}",
  "new_string": "function add(a: number, b: number): number {\n  return a + b;\n}",
  "allow_multiple_matches": false,
  "use_whitespace_insensitive_fallback": true,
  "use_did_you_mean_fuzzy_match": true
}
```

**Output**:
```json
{
  "diff": {
    "old_content": "function add(a, b) {\n  return a + b;\n}",
    "new_content": "function add(a: number, b: number): number {\n  return a + b;\n}"
  },
  "is_applied": true,
  "apply_failed": false,
  "linter_errors": [],
  "num_matches": 1
}
```

#### Example 2: Full Content Replacement

**Input**:
```json
{
  "relative_workspace_path": "src/config.ts",
  "language": "typescript",
  "blocking": true,
  "contents": "export const CONFIG = {\n  apiUrl: 'https://api.example.com',\n  timeout: 5000\n};",
  "line_ranges": []
}
```

**Output**:
```json
{
  "diff": {
    "old_content": "export const CONFIG = {...}",
    "new_content": "export const CONFIG = {\n  apiUrl: 'https://api.example.com',\n  timeout: 5000\n};"
  },
  "is_applied": true,
  "apply_failed": false,
  "linter_errors": []
}
```

---

### CREATE_FILE

**ID**: `10` | **Category**: File Operations

Create a new file at the specified path.

#### Input Parameters

```typescript
{
  relative_workspace_path: string;  // Required: Path for new file
}
```

#### Internal Logic

1. **Path Validation**: Ensures path is within workspace
2. **Directory Creation**: Creates parent directories if needed
3. **Existence Check**: Checks if file already exists
4. **File Creation**: Creates empty file with proper permissions
5. **User Approval**: May require confirmation based on settings

#### Output Format

```typescript
{
  file_created_successfully: boolean;  // True if created
  file_already_exists: boolean;        // True if file existed
}
```

#### Example

**Input**:
```json
{
  "relative_workspace_path": "src/components/NewComponent.tsx"
}
```

**Output**:
```json
{
  "file_created_successfully": true,
  "file_already_exists": false
}
```

---

### DELETE_FILE

**ID**: `11` | **Category**: File Operations

Delete an existing file.

#### Input Parameters

```typescript
{
  relative_workspace_path: string;  // Required: Path to file to delete
}
```

#### Internal Logic

1. **Path Validation**: Ensures path is within workspace
2. **Existence Check**: Verifies file exists
3. **Permission Check**: Ensures file is not protected
4. **User Approval**: Requires confirmation (may be auto-approved in Agent Mode)
5. **File Deletion**: Removes file from filesystem

#### Output Format

```typescript
{
  rejected: boolean;                    // True if user rejected
  file_non_existent: boolean;           // True if file didn't exist
  file_deleted_successfully: boolean;   // True if deleted
}
```

#### Example

**Input**:
```json
{
  "relative_workspace_path": "src/legacy/OldComponent.tsx"
}
```

**Output**:
```json
{
  "rejected": false,
  "file_non_existent": false,
  "file_deleted_successfully": true
}
```

---

### LIST_DIR

**ID**: `6` | **Category**: File Operations

List files and directories in a specified directory.

#### Input Parameters

```typescript
{
  directory_path: string;  // Required: Path to directory
}
```

#### Internal Logic

1. **Path Resolution**: Resolves directory path
2. **Permission Check**: Validates directory access
3. **Directory Reading**: Lists all files and subdirectories
4. **Filtering**: Applies `.gitignore` and `.cursorignore` rules
5. **Metadata Collection**: Gathers file/directory information

#### Output Format

```typescript
{
  files: File[];                              // List of files and directories
  directory_relative_workspace_path: string;  // Confirmed directory path
}

interface File {
  name: string;          // File or directory name
  is_directory: boolean; // True if directory
}
```

#### Example

**Input**:
```json
{
  "directory_path": "src/components"
}
```

**Output**:
```json
{
  "files": [
    { "name": "Button.tsx", "is_directory": false },
    { "name": "Input.tsx", "is_directory": false },
    { "name": "Modal.tsx", "is_directory": false },
    { "name": "common", "is_directory": true }
  ],
  "directory_relative_workspace_path": "src/components"
}
```

---

## Search & Discovery

### SEMANTIC_SEARCH_FULL

**ID**: `9` | **Category**: Search & Discovery

Perform semantic code search across the codebase using natural language queries.

#### Input Parameters

```typescript
{
  query: string;               // Required: Natural language search query
  include_pattern?: string;    // Optional: Glob pattern for files to include
  exclude_pattern?: string;    // Optional: Glob pattern for files to exclude
  top_k: number;               // Required: Number of results to return
  index_id?: string;           // Optional: Specific index to search
  grab_whole_file: boolean;    // Required: Whether to return full files
}
```

#### Internal Logic

1. **Query Processing**: Converts natural language to semantic embeddings
2. **Index Search**: Searches codebase embeddings for similar content
3. **Pattern Filtering**: Applies include/exclude patterns
4. **Ranking**: Ranks results by semantic similarity
5. **Content Extraction**: Returns top-K results with context
6. **Full File Option**: If `grab_whole_file` is true, returns complete files

#### Output Format

```typescript
{
  results: SearchResult[];  // Ranked search results
}

interface SearchResult {
  file_path: string;      // Path to file
  content: string;        // Matching content or full file
  score: number;          // Similarity score
  line_start: number;     // Starting line of match
  line_end: number;       // Ending line of match
}
```

#### Example

**Input**:
```json
{
  "query": "authentication middleware that checks user tokens",
  "include_pattern": "**/*.ts",
  "exclude_pattern": "**/*.test.ts",
  "top_k": 5,
  "grab_whole_file": false
}
```

**Output**:
```json
{
  "results": [
    {
      "file_path": "src/middleware/auth.ts",
      "content": "export function authMiddleware(req, res, next) {\n  const token = req.headers.authorization;\n  if (!token) return res.status(401).send('Unauthorized');\n  // verify token...\n}",
      "score": 0.92,
      "line_start": 15,
      "line_end": 25
    },
    {
      "file_path": "src/utils/tokenVerifier.ts",
      "content": "export function verifyToken(token: string): User {...}",
      "score": 0.87,
      "line_start": 8,
      "line_end": 20
    }
  ]
}
```

---

### RIPGREP_SEARCH

**ID**: `3` | **Category**: Search & Discovery

Perform text-based search using ripgrep (similar to grep but faster).

#### Input Parameters

```typescript
{
  options: TextQueryBuilderOptions;  // Required: Search options
  pattern_info: PatternInfo;         // Required: Pattern to search for
}

interface PatternInfo {
  pattern: string;          // Required: Search pattern
  is_reg_exp?: boolean;     // Optional: Is regex pattern
  is_word_match?: boolean;  // Optional: Match whole words only
  word_separators?: string; // Optional: Word separator characters
  is_multiline?: boolean;   // Optional: Multiline matching
  is_unicode?: boolean;     // Optional: Unicode support
  is_case_sensitive?: boolean; // Optional: Case sensitivity
}

interface TextQueryBuilderOptions {
  max_results?: number;           // Optional: Maximum results
  max_file_size?: number;         // Optional: Max file size to search
  file_pattern?: string;          // Optional: File glob pattern
  exclude_pattern?: string;       // Optional: Exclusion pattern
  follow_symlinks?: boolean;      // Optional: Follow symbolic links
  encoding?: string;              // Optional: File encoding
}
```

#### Internal Logic

1. **Pattern Compilation**: Compiles search pattern (regex or literal)
2. **File Discovery**: Finds files matching patterns
3. **Content Search**: Searches file contents using ripgrep
4. **Result Aggregation**: Collects matches with context lines
5. **Limit Enforcement**: Applies max_results limit

#### Output Format

```typescript
{
  matches: Match[];  // Search matches
}

interface Match {
  file_path: string;     // Path to file
  line_number: number;   // Line number of match
  line_text: string;     // Full line text
  match_start: number;   // Start column of match
  match_end: number;     // End column of match
  before_context: string[];  // Lines before match
  after_context: string[];   // Lines after match
}
```

#### Example

**Input**:
```json
{
  "options": {
    "max_results": 50,
    "file_pattern": "**/*.ts",
    "exclude_pattern": "**/node_modules/**"
  },
  "pattern_info": {
    "pattern": "function\\s+handleError",
    "is_reg_exp": true,
    "is_case_sensitive": false
  }
}
```

**Output**:
```json
{
  "matches": [
    {
      "file_path": "src/utils/errorHandler.ts",
      "line_number": 45,
      "line_text": "function handleError(error: Error) {",
      "match_start": 0,
      "match_end": 12,
      "before_context": ["", "// Error handling utility"],
      "after_context": ["  console.error(error);", "  // log to service"]
    }
  ]
}
```

---

### FILE_SEARCH

**ID**: `8` | **Category**: Search & Discovery

Search for files by name or path pattern.

#### Input Parameters

```typescript
{
  query: string;  // Required: File name or pattern to search for
}
```

#### Internal Logic

1. **Pattern Matching**: Matches query against file names and paths
2. **Fuzzy Matching**: Supports fuzzy file name matching
3. **Path Ranking**: Ranks results by relevance
4. **Limit**: Returns top matches

#### Output Format

```typescript
{
  files: FileMatch[];  // Matching files
}

interface FileMatch {
  file_path: string;  // Full path to file
  score: number;      // Match score
}
```

#### Example

**Input**:
```json
{
  "query": "Button.tsx"
}
```

**Output**:
```json
{
  "files": [
    { "file_path": "src/components/Button.tsx", "score": 1.0 },
    { "file_path": "src/components/common/Button.tsx", "score": 0.9 },
    { "file_path": "tests/Button.test.tsx", "score": 0.8 }
  ]
}
```

---

### SEARCH_SYMBOLS

**ID**: `23` | **Category**: Search & Discovery

Search for code symbols (functions, classes, variables, etc.) across the codebase.

#### Input Parameters

```typescript
{
  query: string;  // Required: Symbol name or pattern
}
```

#### Internal Logic

1. **Symbol Index Query**: Searches language server symbol index
2. **Pattern Matching**: Matches against symbol names
3. **Type Filtering**: Can filter by symbol type (function, class, etc.)
4. **Location Resolution**: Resolves symbol locations

#### Output Format

```typescript
{
  matches: SymbolMatch[];  // Symbol matches
  rejected?: boolean;      // True if rejected
}

interface SymbolMatch {
  name: string;             // Symbol name
  uri: string;              // File URI
  secondary_text: string;   // Additional info (type, signature)
  label_matches: number[];  // Match positions in name
  description_matches: number[];  // Match positions in description
  score: number;            // Match score
}
```

#### Example

**Input**:
```json
{
  "query": "useState"
}
```

**Output**:
```json
{
  "matches": [
    {
      "name": "useState",
      "uri": "file:///src/hooks/useAuth.ts",
      "secondary_text": "function: const [state, setState] = useState<User>()",
      "label_matches": [0, 1, 2, 3, 4, 5, 6, 7],
      "description_matches": [],
      "score": 1.0
    }
  ]
}
```

---

### READ_SEMSEARCH_FILES

**ID**: `1` | **Category**: Search & Discovery

Read files discovered through semantic search.

#### Input Parameters

```typescript
{
  files: string[];  // Required: List of file paths from semantic search
}
```

#### Internal Logic

1. **File Reading**: Reads contents of specified files
2. **Content Optimization**: May extract relevant sections
3. **Aggregation**: Combines results for context

#### Output Format

```typescript
{
  file_contents: FileContent[];  // Contents of files
}

interface FileContent {
  file_path: string;  // Path to file
  content: string;    // File contents
}
```

---

### GET_RELATED_FILES

**ID**: `13` | **Category**: Search & Discovery

Find files related to the specified target files (imports, dependencies, etc.).

#### Input Parameters

```typescript
{
  target_files: string[];  // Required: Files to find relations for
}
```

#### Internal Logic

1. **Dependency Analysis**: Analyzes imports and dependencies
2. **Reference Finding**: Finds files that reference target files
3. **Graph Traversal**: Traverses dependency graph
4. **Ranking**: Ranks by relevance

#### Output Format

```typescript
{
  related_files: RelatedFile[];  // Related files
}

interface RelatedFile {
  file_path: string;      // Path to related file
  relationship: string;   // Type of relationship
  score: number;          // Relevance score
}
```

#### Example

**Input**:
```json
{
  "target_files": ["src/components/Button.tsx"]
}
```

**Output**:
```json
{
  "related_files": [
    {
      "file_path": "src/components/Button.test.tsx",
      "relationship": "test_file",
      "score": 1.0
    },
    {
      "file_path": "src/components/Form.tsx",
      "relationship": "imports",
      "score": 0.9
    },
    {
      "file_path": "src/styles/button.css",
      "relationship": "styles",
      "score": 0.8
    }
  ]
}
```

---

## Execution

### RUN_TERMINAL_COMMAND

**ID**: `4` | **Category**: Execution

Execute a shell command in the terminal.

#### Input Parameters

```typescript
{
  command: string;                // Required: Command to execute
  cwd?: string;                   // Optional: Working directory
  new_session?: boolean;          // Optional: Create new terminal session
  require_user_approval: boolean; // Required: Whether to ask user first
  options?: ExecutionOptions;     // Optional: Advanced execution options
}

interface ExecutionOptions {
  timeout?: number;                        // Optional: Command timeout (ms)
  skip_ai_check?: boolean;                 // Optional: Skip AI completion check
  command_run_timeout_ms?: number;         // Optional: Max run time
  command_change_check_interval_ms?: number; // Optional: Check interval
  ai_finish_check_max_attempts?: number;   // Optional: Max AI check attempts
  ai_finish_check_interval_ms?: number;    // Optional: AI check interval
  delayer_interval_ms?: number;            // Optional: Delay interval
}
```

#### Internal Logic

1. **Command Validation**: Validates command safety
2. **User Approval**: If `require_user_approval` is true, prompts user
3. **Session Management**:
   - If `new_session` is true, creates new terminal
   - Otherwise, reuses existing session
4. **Working Directory**: Changes to specified `cwd` if provided
5. **Execution**: Runs command with streaming output
6. **AI Completion Check**: If `skip_ai_check` is false, uses AI to detect completion
7. **Timeout Handling**: Applies timeout limits
8. **Output Capture**: Captures stdout and stderr

#### Output Format

```typescript
{
  output: string;                       // Command output (stdout + stderr)
  exit_code: number;                    // Exit code (0 = success)
  rejected?: boolean;                   // True if user rejected
  popped_out_into_background: boolean;  // True if command was backgrounded
}
```

#### Example

**Input**:
```json
{
  "command": "npm test -- Button.test.tsx",
  "cwd": "/workspace/project",
  "new_session": false,
  "require_user_approval": false,
  "options": {
    "timeout": 30000,
    "skip_ai_check": false
  }
}
```

**Output**:
```json
{
  "output": "PASS  src/components/Button.test.tsx\n  Button Component\n    ✓ renders correctly (45ms)\n    ✓ handles click events (23ms)\n\nTest Suites: 1 passed, 1 total\nTests:       2 passed, 2 total",
  "exit_code": 0,
  "popped_out_into_background": false
}
```

---

### RUN_TERMINAL_COMMAND_V2

**ID**: `15` | **Category**: Execution

Enhanced version of terminal command execution with improved features.

#### Input Parameters

Similar to `RUN_TERMINAL_COMMAND` with additional capabilities:

```typescript
{
  command: string;
  cwd?: string;
  new_session?: boolean;
  require_user_approval: boolean;
  options?: ExecutionOptionsV2;
  shell_type?: ShellType;  // NEW: Specify shell (bash, powershell)
}

enum ShellType {
  BASH = 1,
  POWERSHELL = 2
}
```

#### Internal Logic

Enhanced version includes:
- Better shell detection (bash vs powershell)
- Improved output parsing
- Better error handling
- Enhanced background execution

#### Output Format

Same as `RUN_TERMINAL_COMMAND` with additional metadata.

---

## Advanced Operations

### PARALLEL_APPLY

**ID**: `14` | **Category**: Advanced Operations

Apply edits to multiple files simultaneously.

#### Input Parameters

```typescript
{
  edits: FileEdit[];  // Required: List of file edits to apply
}

interface FileEdit {
  relative_workspace_path: string;  // File to edit
  old_string?: string;              // Search string
  new_string?: string;              // Replacement string
  contents?: string;                // Full contents (alternative)
}
```

#### Internal Logic

1. **Edit Validation**: Validates all edits before applying
2. **Dependency Check**: Ensures no conflicting edits
3. **Parallel Execution**: Applies edits concurrently
4. **Transaction**: All edits succeed or all fail
5. **Linter Check**: Runs linters on all modified files

#### Output Format

```typescript
{
  file_results: FileResult[];  // Results for each file
}

interface FileResult {
  file_path: string;         // File that was edited
  diff: Diff;                // Generated diff
  is_applied: boolean;       // Whether applied successfully
  apply_failed: boolean;     // Whether application failed
  error?: string;            // Error message if failed
  linter_errors: LinterError[];  // Linter errors
}
```

#### Example

**Input**:
```json
{
  "edits": [
    {
      "relative_workspace_path": "src/utils/math.ts",
      "old_string": "function add(a, b)",
      "new_string": "function add(a: number, b: number): number"
    },
    {
      "relative_workspace_path": "src/utils/string.ts",
      "old_string": "function concat(a, b)",
      "new_string": "function concat(a: string, b: string): string"
    }
  ]
}
```

**Output**:
```json
{
  "file_results": [
    {
      "file_path": "src/utils/math.ts",
      "diff": {...},
      "is_applied": true,
      "apply_failed": false,
      "linter_errors": []
    },
    {
      "file_path": "src/utils/string.ts",
      "diff": {...},
      "is_applied": true,
      "apply_failed": false,
      "linter_errors": []
    }
  ]
}
```

---

### REAPPLY

**ID**: `12` | **Category**: Advanced Operations

Reapply a previous edit or operation.

#### Input Parameters

```typescript
{
  edit_id: string;  // Required: ID of previous edit to reapply
}
```

#### Internal Logic

1. **Edit Lookup**: Finds previous edit in history
2. **Context Check**: Validates context hasn't changed significantly
3. **Reapplication**: Applies edit to current file state
4. **Conflict Resolution**: Handles conflicts if file changed

#### Output Format

```typescript
{
  is_applied: boolean;       // Whether reapplication succeeded
  apply_failed: boolean;     // Whether it failed
  error?: string;            // Error message if failed
  diff: Diff;                // Resulting diff
}
```

---

### PLANNER

**ID**: `17` | **Category**: Advanced Operations

Create a structured implementation plan for a given instruction.

#### Input Parameters

```typescript
{
  instruction: string;  // Required: Task description
  plan?: string;        // Optional: Existing plan to refine
}
```

#### Internal Logic

1. **Task Analysis**: Analyzes the instruction
2. **Codebase Context**: Gathers relevant codebase context
3. **Plan Generation**: Creates step-by-step implementation plan
4. **Validation**: Validates plan completeness
5. **Refinement**: If plan provided, refines it

#### Output Format

```typescript
{
  plan: string;  // Structured implementation plan
}
```

#### Example

**Input**:
```json
{
  "instruction": "Add user authentication with JWT tokens to the API"
}
```

**Output**:
```json
{
  "plan": "# Implementation Plan: JWT Authentication\n\n## Phase 1: Dependencies\n1. Install jsonwebtoken and bcrypt packages\n2. Add types for JWT\n\n## Phase 2: User Model\n1. Create User model with password hashing\n2. Add password comparison method\n\n## Phase 3: Auth Middleware\n1. Create JWT generation utility\n2. Create JWT verification middleware\n3. Add auth middleware to protected routes\n\n## Phase 4: Auth Endpoints\n1. Create /login endpoint\n2. Create /register endpoint\n3. Add token refresh endpoint\n\n## Phase 5: Testing\n1. Add unit tests for auth utilities\n2. Add integration tests for endpoints"
}
```

---

### IMPLEMENTER

**ID**: `22` | **Category**: Advanced Operations

Execute a structured implementation plan.

#### Input Parameters

```typescript
{
  instruction: string;      // Required: Original instruction
  implementation: string;   // Required: Implementation details/plan
}
```

#### Internal Logic

1. **Plan Parsing**: Parses implementation steps
2. **Step Execution**: Executes each step sequentially
3. **File Modifications**: Makes necessary code changes
4. **Validation**: Validates each step completion
5. **Error Handling**: Handles failures and retries

#### Output Format

```typescript
{
  diff: Diff;                    // Combined diff of all changes
  is_applied: boolean;           // Whether fully applied
  apply_failed: boolean;         // Whether any step failed
  linter_errors: LinterError[];  // All linter errors
}
```

#### Example

**Input**:
```json
{
  "instruction": "Implement the authentication plan",
  "implementation": "Step 1: Install dependencies\nStep 2: Create auth middleware\nStep 3: Add login endpoint"
}
```

**Output**:
```json
{
  "diff": {...},
  "is_applied": true,
  "apply_failed": false,
  "linter_errors": []
}
```

---

### WEB_SEARCH

**ID**: `18` | **Category**: Advanced Operations

Search the web for information.

#### Input Parameters

```typescript
{
  search_term: string;  // Required: Search query
}
```

#### Internal Logic

1. **Query Processing**: Processes search query
2. **Web Search**: Performs web search (via search engine API)
3. **Result Extraction**: Extracts relevant snippets
4. **Ranking**: Ranks results by relevance
5. **Content Retrieval**: Fetches page content for top results

#### Output Format

```typescript
{
  references: WebReference[];  // Search results
  is_final?: boolean;          // True when search complete
  rejected?: boolean;          // True if user rejected
}

interface WebReference {
  title: string;   // Page title
  url: string;     // Page URL
  chunk: string;   // Relevant excerpt
}
```

#### Example

**Input**:
```json
{
  "search_term": "react hooks useEffect cleanup function"
}
```

**Output**:
```json
{
  "references": [
    {
      "title": "Using the Effect Hook – React",
      "url": "https://react.dev/reference/react/useEffect",
      "chunk": "Effects with Cleanup: Some effects need to specify how to stop, undo, or clean up whatever they were doing. For example, if your Effect subscribes to something, the cleanup function should unsubscribe..."
    },
    {
      "title": "useEffect cleanup function - Stack Overflow",
      "url": "https://stackoverflow.com/questions/...",
      "chunk": "The cleanup function in useEffect runs before the component unmounts and before the effect runs again..."
    }
  ],
  "is_final": true
}
```

---

### WEB_VIEWER

**ID**: `20` | **Category**: Advanced Operations

View and interact with web pages programmatically.

#### Input Parameters

```typescript
{
  url: string;                         // Required: URL to view
  instructions: DOMInstruction[];      // Optional: DOM interactions
  new_session?: boolean;               // Optional: New browser session
  console_log_params?: ConsoleLogParams; // Optional: Console logging
}

interface DOMInstruction {
  target: Target;    // Element selector
  action: Action;    // Action to perform (click, input, hover, etc.)
}
```

#### Internal Logic

1. **Browser Launch**: Opens headless browser
2. **Page Navigation**: Navigates to URL
3. **DOM Interaction**: Executes DOM instructions
4. **Content Extraction**: Extracts page content
5. **Screenshot**: May capture screenshots

#### Output Format

```typescript
{
  content: string;           // Page content (HTML/text)
  console_logs: string[];    // Console output
  screenshot?: string;       // Base64 screenshot
}
```

#### Example

**Input**:
```json
{
  "url": "https://example.com/docs",
  "instructions": [
    {
      "target": { "selector": "#search-input" },
      "action": { "type": "input", "value": "authentication" }
    },
    {
      "target": { "selector": "button[type=submit]" },
      "action": { "type": "click" }
    }
  ],
  "new_session": true
}
```

**Output**:
```json
{
  "content": "<html>...</html>",
  "console_logs": [],
  "screenshot": "base64_encoded_image..."
}
```

---

### KNOWLEDGE_BASE

**ID**: `25` | **Category**: Advanced Operations

Store or retrieve information in the knowledge base (memories).

#### Input Parameters

```typescript
{
  knowledge_to_store: string;  // Required: Information to store
  title: string;               // Required: Title/key for knowledge
}
```

#### Internal Logic

1. **Memory Storage**: Stores information in persistent memory
2. **Embedding Generation**: Creates embeddings for retrieval
3. **Indexing**: Indexes for future semantic search
4. **Confirmation**: Returns confirmation message

#### Output Format

```typescript
{
  success: boolean;            // Whether storage succeeded
  confirmation_message: string; // Confirmation or error message
}
```

#### Example

**Input**:
```json
{
  "knowledge_to_store": "The authentication system uses JWT tokens with 24-hour expiration. Refresh tokens are stored in httpOnly cookies.",
  "title": "Authentication Implementation Details"
}
```

**Output**:
```json
{
  "success": true,
  "confirmation_message": "Successfully stored knowledge: Authentication Implementation Details"
}
```

---

### FETCH_RULES

**ID**: `16` | **Category**: Advanced Operations

Fetch and apply `.cursorrules` files from the workspace.

#### Input Parameters

```typescript
{
  // No parameters - fetches all .cursorrules files
}
```

#### Internal Logic

1. **Rules Discovery**: Finds all `.cursorrules` files in workspace
2. **Hierarchical Resolution**: Applies rules from root to specific directories
3. **Rule Parsing**: Parses rule configurations
4. **Rule Application**: Applies rules to current context

#### Output Format

```typescript
{
  rules: CursorRule[];  // Applicable rules
}

interface CursorRule {
  file_path: string;    // Path to .cursorrules file
  content: string;      // Rule content
  scope: string;        // Directory scope
}
```

#### Example

**Output**:
```json
{
  "rules": [
    {
      "file_path": ".cursorrules",
      "content": "# Global rules\n- Use TypeScript strict mode\n- Follow ESLint configuration",
      "scope": "/"
    },
    {
      "file_path": "src/components/.cursorrules",
      "content": "# Component rules\n- Use functional components\n- Include PropTypes",
      "scope": "/src/components"
    }
  ]
}
```

---

## Integration Tools

### MCP

**ID**: `19` | **Category**: Integration

Execute Model Context Protocol (MCP) tools from configured servers.

#### Input Parameters

```typescript
{
  server_name: string;  // Required: MCP server name
  tool_name: string;    // Required: Tool to execute
  arguments: any;       // Required: Tool arguments
}
```

#### Internal Logic

1. **Server Connection**: Connects to MCP server
2. **Tool Invocation**: Calls specified tool
3. **Result Processing**: Processes tool response
4. **Error Handling**: Handles connection/execution errors

#### Output Format

```typescript
{
  result: any;          // Tool result
  error?: string;       // Error if failed
}
```

#### Example

**Input**:
```json
{
  "server_name": "database-mcp",
  "tool_name": "query_users",
  "arguments": {
    "limit": 10,
    "active": true
  }
}
```

**Output**:
```json
{
  "result": {
    "users": [
      { "id": 1, "name": "Alice", "active": true },
      { "id": 2, "name": "Bob", "active": true }
    ]
  }
}
```

---

### DIFF_HISTORY

**ID**: `21` | **Category**: Integration

View the history of changes made in the current session.

#### Input Parameters

```typescript
{
  // No parameters - returns all session changes
}
```

#### Internal Logic

1. **History Retrieval**: Fetches all changes from current session
2. **Diff Generation**: Generates rendered diffs
3. **Filtering**: Filters for human-made changes vs AI changes
4. **Chronological Order**: Orders changes by timestamp

#### Output Format

```typescript
{
  human_changes: RenderedDiff[];  // List of human-made changes
}

interface RenderedDiff {
  start_line_number: number;      // Starting line
  end_line_number_exclusive: number; // Ending line
  before_context_lines: string[]; // Lines before change
  removed_lines: string[];        // Removed lines
  added_lines: string[];          // Added lines
  after_context_lines: string[];  // Lines after change
}
```

#### Example

**Output**:
```json
{
  "human_changes": [
    {
      "start_line_number": 45,
      "end_line_number_exclusive": 50,
      "before_context_lines": ["function authenticate(user) {"],
      "removed_lines": ["  if (!user.token) return false;"],
      "added_lines": ["  if (!user.token || isTokenExpired(user.token)) return false;"],
      "after_context_lines": ["  return verifyToken(user.token);", "}"]
    }
  ]
}
```

---

### READ_FILE_FOR_IMPORTS

**ID**: `2` | **Category**: Integration

Read file with focus on import statements and dependencies.

#### Input Parameters

```typescript
{
  relative_file_path: string;  // Required: Path to file
}
```

#### Internal Logic

1. **File Reading**: Reads file contents
2. **Import Extraction**: Extracts import statements
3. **Dependency Analysis**: Analyzes import dependencies
4. **Type Information**: Includes type information if available

#### Output Format

```typescript
{
  imports: Import[];      // List of imports
  file_path: string;      // File path
  language: string;       // Programming language
}

interface Import {
  module: string;         // Module name
  imported_names: string[]; // Imported symbols
  import_type: string;    // Type of import (default, named, etc.)
}
```

#### Example

**Input**:
```json
{
  "relative_file_path": "src/components/Button.tsx"
}
```

**Output**:
```json
{
  "imports": [
    {
      "module": "react",
      "imported_names": ["useState", "useEffect"],
      "import_type": "named"
    },
    {
      "module": "./Button.styles",
      "imported_names": ["ButtonContainer"],
      "import_type": "named"
    }
  ],
  "file_path": "src/components/Button.tsx",
  "language": "typescript"
}
```

---

### BACKGROUND_COMPOSER_FOLLOWUP

**ID**: `24` | **Category**: Integration

Handle followup actions for background agent tasks.

#### Input Parameters

```typescript
{
  task_id: string;         // Required: Background task ID
  action: string;          // Required: Followup action
  parameters?: any;        // Optional: Action parameters
}
```

#### Internal Logic

1. **Task Lookup**: Finds background task
2. **Action Execution**: Executes followup action
3. **Result Aggregation**: Combines with previous results
4. **Status Update**: Updates task status

#### Output Format

```typescript
{
  success: boolean;        // Whether action succeeded
  result?: any;            // Action result
  task_status: string;     // Updated task status
}
```

---

## Best Practices

### Using File Operations

1. **Read Before Edit**: Always read files before editing to understand context
2. **Use Search-Replace**: For targeted changes, use `old_string`/`new_string`
3. **Enable Auto-Save**: For autonomous operation, enable auto-save settings
4. **Check Linter Errors**: Review `linter_errors` in responses

### Using Search Tools

1. **Semantic First**: Use `SEMANTIC_SEARCH_FULL` for concept-based searches
2. **Ripgrep for Patterns**: Use `RIPGREP_SEARCH` for exact text/regex
3. **Combine Tools**: Use multiple search tools for comprehensive discovery
4. **Narrow Scope**: Use include/exclude patterns to improve performance

### Using Execution Tools

1. **Approve Commands**: Review commands before execution in production
2. **Set Timeouts**: Always set reasonable timeouts for long-running commands
3. **Use CWD**: Specify working directory to avoid path issues
4. **Background Long Tasks**: Use `popped_out_into_background` for lengthy operations

### Using Advanced Operations

1. **Plan First**: Use `PLANNER` before complex implementations
2. **Parallel When Possible**: Use `PARALLEL_APPLY` for independent edits
3. **Store Knowledge**: Use `KNOWLEDGE_BASE` to remember important patterns
4. **Web Search Last**: Try codebase search before web search

---

## Configuration Settings

### Agent Mode Settings

Located in Cursor Settings → Chat:

- **Iterate on lints**: Auto-fix linter errors iteratively
- **Allow Agent to run tools without asking**: Auto-approve tool execution
- **Auto-save agentic edits**: Automatically save file changes
- **Auto-accept diffs**: Auto-accept changes when no longer in worktree
- **Default new chat mode**: Set default mode for new chats
- **Enable web search**: Allow `WEB_SEARCH` tool
- **Hierarchical Cursor Ignore**: Apply `.cursorignore` to subdirectories

### Advanced Settings

- **Edit file tool max file size**: 3500 lines or 150000 characters
- **Command timeout**: Default timeout for terminal commands
- **Max search results**: Limit for search tool results
- **MCP servers**: Configure Model Context Protocol servers

---

## Troubleshooting

### Common Issues

**Edit Failed - File Too Large**
- Solution: Use `EDIT_FILE` with `old_string`/`new_string` for targeted edits
- Or: Split large file into smaller modules

**Search Returns No Results**
- Check include/exclude patterns
- Verify file paths are relative to workspace root
- Try broadening search query

**Command Requires Approval**
- Enable "Allow Agent to run tools without asking" in settings
- Or: Set `require_user_approval: false` in command parameters

**Linter Errors After Edit**
- Enable "Iterate on lints" to auto-fix
- Review `linter_errors` in output
- Use `EDIT_FILE` again to fix errors

**Web Search Not Available**
- Check `isWebSearchToolEnabled3` setting
- Verify internet connection
- Check Cursor subscription tier

---

## Conclusion

Cursor's Agent Mode provides a powerful set of 25+ tools for autonomous code development. By understanding each tool's parameters, logic, and output format, you can leverage Agent Mode to its full potential for planning, searching, editing, and executing across your entire codebase.

For the latest updates and additional tools, refer to the Cursor documentation and release notes.

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-17  
**Source**: Cursor v0.50.5 Source Maps

