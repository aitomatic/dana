# Dana Modules and Imports

This document describes how Dana code can be organized into modules (separate files) and how these modules can be imported and used in other Dana programs.

## 1. Motivation

As Dana programs grow in complexity, a mechanism for organizing code into reusable and manageable units becomes essential. Modules allow for:

*   **Code Reusability**: Define functions, structs, and constants in one place and use them across multiple programs.
*   **Namespacing**: Avoid naming conflicts by organizing code into distinct namespaces.
*   **Logical Organization**: Group related code (e.g., a set of utility functions, definitions for a specific data domain) into separate files.
*   **Collaboration**: Allow different developers or teams to work on different modules independently.

## 2. Defining a Module

A Dana module is simply a `.dna` file (or the conventional future extension for Dana files) containing Dana code (struct definitions, function definitions, and potentially top-level variable assignments that act as constants or module-level state if appropriate to the design).

**Example: `string_utils.dna`**

```dana
# Module: string_utils.dna

struct StringMetrics:
    length: int
    word_count: int

def calculate_metrics(text: str) -> StringMetrics:
    local:len = len(text)
    # Basic word count, can be made more sophisticated
    local:words = 0
    if local:len > 0:
        # This is a simplistic word count
        local:parts = text.split(' ') # Assuming a string split method
        local:words = len(local:parts)
    
    return StringMetrics(length=local:len, word_count=local:words)

def to_uppercase(text: str) -> str:
    # This would ideally call a built-in string method or a resource providing this.
    # For now, conceptual:
    return text # Placeholder - actual uppercasing TBD

public:DEFAULT_GREETING: str = "Hello, Dana!"
```

## 3. Importing Modules

Dana modules are imported using the `import` statement.

### 3.1. Basic Import

Imports the module and requires a fully qualified name to access its members.

**Syntax:**

```dana
import <module_path>
```

**Example:**

```dana
# In main.dna
import path/to/string_utils.dna # Path relative to a defined search path or current file

local:text: str = "Sample text for analysis."
local:metrics: string_utils.dna.StringMetrics = string_utils.dna.calculate_metrics(local:text)
print(f"Length: {local:metrics.length}, Words: {local:metrics.word_count}")

local:greeting: str = string_utils.dna.DEFAULT_GREETING
```

### 3.2. Import with Alias

Imports the module and provides an alias (a shorter name) for it.

**Syntax:**

```dana
import <module_path> as <alias>
```

**Example:**

```dana
# In main.dna
import path/to/string_utils.dna as str_util

local:text: str = "Sample text for analysis."
local:metrics: str_util.StringMetrics = str_util.calculate_metrics(local:text)
print(f"Length: {local:metrics.length}, Words: {local:metrics.word_count}")

local:upper_text: str = str_util.to_uppercase("dana language")
print(local:upper_text)

print(str_util.DEFAULT_GREETING)
```
This is generally the recommended way to import modules to maintain clarity and avoid name clashes.

### 3.3. Importing Specific Members (Consideration for Future)

A `from <module_path> import <member1>, <member2> as <alias2>` syntax, similar to Python, could be considered in the future if there's a strong need. However, to keep initial simplicity and encourage explicit namespacing, the primary import mechanisms are `import <module>` and `import <module> as <alias>`.

## 4. Module Scope and State

*   **Namespacing**: Each imported module creates its own namespace. Members (functions, structs, module-level variables) are accessed via `module_name.member_name` or `alias.member_name`.
*   **Execution**: When a module is imported for the first time in an execution context, its top-level statements are executed once. This allows modules to initialize module-level state if necessary.
*   **Caching**: The Dana runtime should cache imported modules so that subsequent imports of the same module (within the same execution context or session) do not re-execute its top-level code but rather provide a reference to the already loaded module.

## 5. Module Search Path

The Dana runtime will need a defined strategy for locating modules specified in `import` statements:

1.  **Relative to the current file**: Look in the same directory as the importing file.
2.  **Standard Library Path**: A designated directory for Dana's standard library modules (if any).
3.  **User-defined Paths**: Potentially configurable paths where the runtime should look for modules (e.g., via an environment variable or a configuration file for a project).

The exact resolution order needs to be clearly defined.

## 6. Python Module Integration

While this document focuses on Dana-to-Dana modules, Dana also supports importing Python modules. This typically involves the Dana runtime interacting with the Python interpreter. The syntax might be similar, possibly with a differentiator (e.g., `import python my_python_module as py_mod`). The interaction with Python objects and functions would then be managed by the Dana-Python bridge. (This is detailed further in OpenDXA's Python integration design).

## 7. Open Questions and Future Considerations

*   **Circular Imports**: How are circular dependencies between modules handled or prevented?
*   **Dynamic Imports**: Is there a need for importing modules based on a string variable (e.g., `import(local:module_name_var)`)?
*   **Reloading Modules**: For development, a mechanism to reload a module that has changed without restarting the entire application might be useful (e.g., `reload(my_module)`).
*   **Package Structure**: For larger collections of modules, a directory-based package structure (e.g., `import my_package.my_module`) might be needed.

This section will be expanded as the module system design matures. 