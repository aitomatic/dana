# CodeContextAnalyzer Design

## 1. Purpose and Goals

The `CodeContextAnalyzer` is a critical component of the Dana runtime, specifically designed to support the **Perceive** phase of the PAV (Perceive → Act → Validate) execution model. Its primary goal is to extract rich, actionable context from the Dana source code surrounding a function call, particularly for PAV-enabled functions.

This contextual information allows the `Perceive` phase to:

*   **Infer implicit intent**: Understand what the user likely wants based on how a function is called, even if the direct arguments are ambiguous.
*   **Optimize inputs**: Tailor prompts or arguments for the `Act` phase based on expected output types or surrounding logic. For example, it can inform prompt engineering for LLM calls by providing constraints or desired output formats.
*   **Enhance fault tolerance**: Provide clues for how to interpret or recover from potentially malformed inputs.
*   **Enable adaptive behavior**: Allow PAV-decorated functions to behave differently based on where and how they are invoked in the code.

Essentially, the `CodeContextAnalyzer` provides the "eyes" for the `Perceive` stage, allowing it to "read" the code and make more intelligent decisions.

## 2. Inputs

The `CodeContextAnalyzer` will require the following inputs to perform its analysis:

*   **`file_path`**: `str` - The absolute or relative path to the Dana source file being analyzed.
*   **`line_number`**: `int` - The 1-indexed line number where the function call of interest occurs.
*   **`column_number`**: `int` - The 1-indexed column number where the function call of interest begins.
*   **`source_code_snapshot`**: `str` - A snippet of the source code around the call site. This could be the entire file content or a relevant chunk. The analyzer might have its own heuristics for how much code it needs.
*   **`ast_node` (Optional)**: `Any` - If a pre-parsed Abstract Syntax Tree (AST) node corresponding to the call site is available, it can be provided for more precise analysis. This depends on the Dana parsing and compilation pipeline.
*   **`current_scope_details` (Optional)**: `dict` - Information about the current lexical scope, such as visible local variables and their inferred types, if available from the runtime.

## 3. Output Structure (`CodeSiteContext`)

The `CodeContextAnalyzer` will produce a dictionary or structured object, let's call it `CodeSiteContext`, containing the extracted information.

```python
# Conceptual structure of CodeSiteContext
{
    "file_info": {
        "path": "str", # Full path to the file
        "line": "int", # Line number of the call
        "column": "int" # Column number of the call
    },
    "source_extracts": {
        "preceding_lines": ["str"], # Lines of code immediately before the call
        "call_line": "str", # The line of code containing the call
        "succeeding_lines": ["str"], # Lines of code immediately after the call
        "block_comment_above": "str | None", # Nearest significant block comment preceding the call
        "inline_comment_on_call_line": "str | None" # Inline comment on the same line as the call
    },
    "call_structure": {
        "function_name_called": "str", # Name of the function being called
        "parent_construct": { # Information about the immediate syntactic parent
            "type": "str", # e.g., "assignment", "if_statement", "return_statement", "expression_statement"
            "details": {
                # "variable_name_assigned_to": "str" (if type is "assignment")
                # "variable_type_hint": "str | None" (if type is "assignment" with type hint)
                # "condition_expression": "str" (if type is "if_statement")
                # ... other relevant details based on parent_construct.type
            }
        },
        "is_part_of_pipeline": "bool", # True if the call is part of a Dana pipeline (e.g., input | func_call)
        "pipeline_predecessor_type": "str | None" # If part of pipeline, inferred type of data being piped in
    },
    "lexical_context": {
        "enclosing_function_name": "str | None", # Name of the Dana function that contains this call
        "enclosing_class_name": "str | None", # Name of the Dana class (if any)
        "local_variables_in_scope": { # Potentially limited to those relevant or recently used
            # "var_name": "inferred_type_str_or_any"
        }
    },
    "inferred_intent_hints": {
        "expected_output_type_from_assignment": "str | None", # e.g., from `x: MyType = func()`
        "is_discarded_result": "bool", # True if func() is called without assignment and not as part of another expression's args
        "keywords_in_comments": ["str"], # e.g., ["summary", "translate", "critical"]
        "purpose_heuristics": ["str"] # e.g., ["data_transformation", "side_effect_call", "validation_check"]
    }
}
```

This structure is illustrative and can be refined. The key is to provide a rich, multi-faceted view of the call's context.

## 4. Core Logic/Strategies

The `CodeContextAnalyzer` will employ a combination of strategies to extract information:

*   **Lexical Analysis/Regex**: For quickly finding comments, keywords, and basic code structures around the call site, especially if an AST is not available or too slow for rapid C.P.A.V. cycles. This is good for `source_extracts`.
*   **Lightweight Parsing/Heuristics**: To identify the `call_structure` (e.g., if it's an assignment, what variable is it assigned to, any type hints). This might involve pattern matching on common Dana syntax constructs without full parsing.
*   **AST Traversal (if AST node is provided)**: If an AST node for the call site (or the whole file) is available, this would be the most robust way to determine `call_structure`, `lexical_context` (like enclosing function/class), and relationships between code elements.
*   **Scope Analysis (if `current_scope_details` provided)**: Leverages runtime information about visible variables and their types.
*   **Heuristic-Based Intent Inference**: Combining information from comments, variable names, type hints (e.g., `x: list[str] = my_pav_func(...)` strongly suggests `expected_output_type` is `list[str]`), and surrounding code patterns to populate `inferred_intent_hints`.

The analyzer should be designed to be:
*   **Fast**: Context analysis should not significantly slow down PAV execution.
*   **Robust**: Gracefully handle incomplete or unusual code patterns.
*   **Configurable/Extensible**: Allow new heuristics or analysis techniques to be added.

## 5. Integration with PAV

The PAV execution framework will invoke the `CodeContextAnalyzer` during its **Perceive** phase.

1.  When a PAV-decorated Python function is called, the PAV machinery (before calling the user's `perceive` Dana function) would gather the necessary inputs (file path, line/col of the *Dana call site* that ultimately invoked the Python function).
2.  It calls `CodeContextAnalyzer.analyze(file_path, line, col, source_code_snapshot, ...)`
3.  The resulting `CodeSiteContext` object is then made available to the Dana `perceive` function, typically as part of the `perceived_input` structure or a dedicated context variable (e.g., `code_site_context`).
4.  The `perceive` Dana function can then use this `CodeSiteContext` to inform its logic (e.g., extract `expected_output_type_from_assignment` to set `pav_status.expected_output_type`, or use `keywords_in_comments` to modify a prompt).

## 6. Examples

### Example 1: Inferring Expected Output Type

**Dana Code:**
```dana
# Function to get user details
@pav(perceive="Perceive::UserDetails", validate="Validate::UserDetails")
def get_user_data(user_id: string) -> dict:
  # Act: Python code to fetch from DB
  pass

# Calling code
user_profile: dict[string, string] = get_user_data("user123")
```

**`CodeContextAnalyzer` Output (simplified for `user_profile` line):**
```json
{
  // ...
  "call_structure": {
    "parent_construct": {
      "type": "assignment",
      "details": {
        "variable_name_assigned_to": "user_profile",
        "variable_type_hint": "dict[string, string]"
      }
    }
  },
  "inferred_intent_hints": {
    "expected_output_type_from_assignment": "dict[string, string]"
  }
  // ...
}
```
The `Perceive::UserDetails` Dana function could then use `code_site_context.inferred_intent_hints.expected_output_type_from_assignment` to populate `pav_status.expected_output_type`.

### Example 2: Using Comments to Guide Behavior

**Dana Code:**
```dana
# Needs a very concise summary for the mobile app view
mobile_summary: string = reason("Summarize this long article: " + article_content)

# Needs a more detailed summary for archival
archive_summary: string = reason("Summarize this long article: " + article_content)
```

**`CodeContextAnalyzer` Output (simplified for `mobile_summary` line):**
```json
{
  // ...
  "source_extracts": {
    "block_comment_above": "Needs a very concise summary for the mobile app view"
  },
  "inferred_intent_hints": {
    "keywords_in_comments": ["concise", "summary", "mobile"]
  }
  // ...
}
```
The `Perceive` stage for `reason` (which is PAV-enabled) could use these `keywords_in_comments` to modify the prompt sent to the LLM, e.g., "Summarize this long article *very concisely for a mobile view*: ..."

## 7. Open Questions & Future Considerations

*   Performance implications of detailed analysis, especially AST parsing.
*   Caching strategies for `CodeSiteContext` if the source code hasn't changed.
*   Handling macros or other code generation steps in Dana that might obscure the original call site.
*   Extensibility for language-specific (Dana) parsing features.
*   Security implications if source code snippets are passed around. 