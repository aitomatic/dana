# PAV: Perceive → Act → Validate Execution Model

## 📜 Motivation: PAV – A Robust Execution Protocol for the GenAI Era

> "**Be liberal in what you accept, and conservative in what you send.**"
> — *Jon Postel, RFC 761 (1980)*

This simple but profound principle, coined in the early days of internet protocol design, remains one of the most enduring foundations for building resilient systems. In today's world of probabilistic AI and structured computation, its relevance has never been greater.

As we enter the **GenAI era**, we are witnessing a rapid convergence of **natural language understanding, symbolic reasoning, tool-use, and program synthesis**. Language models can now infer vague intent, generate structured plans, and execute arbitrary code. But they do so with **unpredictable semantics**, **fragile formatting**, and **opaque failure modes**.

### ❗ The Problem

Generative systems—especially LLM-based agents—tend to be:

* **Liberal in input**, but also **liberal in output**
* **Probabilistic**, not **principled**
* **Powerful**, but **unstable** without scaffolding

This makes integration into **symbolic, software, or API-driven systems** extremely difficult. Outputs may be:

* Incorrect in format
* Semantically incoherent
* Missing required fields
* Failing silently or behaving nondeterministically

This is not a peripheral issue. It is the **central challenge** of turning generative models into **reliable system components**.

---

## 🧠 The Neurosymbolic Opportunity

The promise of **neurosymbolic systems** is to **combine the flexibility of learning-based models with the rigor of symbolic computation**.

* Language models excel at **understanding messy, underspecified, human-centric input**.
* Symbolic components excel at **structured execution, error-checking, and guarantees**.

But today's tooling lacks a unifying control structure to bridge the two safely.

What's missing is an **execution framework** that:

* **Tolerates fuzziness** on the input side
* **Enables intelligent action** at the core
* **Enforces structure and validation** on the output side
* **Retries, recovers, and learns from failure**

---

## ✅ PAV: A Universal Contract for Robust Agent Execution

The **Perceive → Act → Validate (PAV)** protocol embodies this pattern:

1. **Perceive**: Accept inputs with fault tolerance and context sensitivity. Normalize ambiguous user input, language, or unstructured data into a form your system can understand. This phase can involve sophisticated context gathering, potentially including:
    *   **Code-Site Context**: Information derived from the function's call site in Dana code (e.g., comments, surrounding variable names/types, type hints on assignment).
    *   **Ambient System Context**: Relevant information from the broader execution environment (e.g., `system:__current_task_id`, `system:__user_id`, `system:__locale`, active operational domains).
    The output of this phase, the `perceived_input`, can therefore be a rich structure containing not just the normalized primary input but also this gathered context, which is then available to the `Act` and `Validate` phases.

2. **Act**: Execute the core function or plan. This can be a tool call, LLM generation, symbolic program, or composite chain, utilizing the (potentially rich) `perceived_input`.

3. **Validate**: Strictly check the output against `pav_status.expected_output_type` and other criteria. Ensure it meets structural, semantic, or type-based expectations. If it doesn't, retry the act stage with introspective awareness of failure context.

---

## 🛠 Why PAV Is Necessary Now

In a world where:

* LLMs hallucinate
* APIs break with malformed payloads
* Tool-using agents generate invalid commands
* Users issue ambiguous queries
* Planning and execution are lossy

...we need a **robust, extensible execution model** that embraces the **flexibility of generative inference** *without compromising the guarantees of structured computation*.

PAV is that model.

---

## 🌉 Positioning PAV as the Core Neurosymbolic Bridge

PAV becomes the **core abstraction** for runtime control in modern AI systems:

| Use Case                | PAV Behavior                                                                  |
| ----------------------- | ----------------------------------------------------------------------------- |
| LLM agent tool call     | Perceive (NL → args), Act (tool call), Validate (schema)                      |
| Natural language → code | Perceive (prompt parse), Act (generate code), Validate (syntax/type check)    |
| Autonomous planner      | Perceive (goal framing), Act (plan/step), Validate (plan constraints met)     |
| Semantic search         | Perceive (query), Act (retrieve), Validate (enough results, no contradiction) |

PAV provides a **first-class retry loop**, **extensible Perceive and Validate logic**, and a runtime introspection context (`pav_status`)—all of which are critical for **safe AI deployment**, **tool chaining**, and **adaptive agent behavior**.

---

## 🔗 Final Word

> **PAV operationalizes Postel's principle in the age of generative systems.**
> It allows us to tolerate ambiguity, act intelligently, and enforce correctness—**bridging the neural and the symbolic, reliably.**

PAV isn't just a wrapper.
It's the execution protocol at the **center of modern neurosymbolic intelligence**.

---

## 🔧 PAV Design and Specification

### ✨ PAV in Action: `reason()` Adapting to Context

The power and everyday utility of the PAV execution model are clearly demonstrated by Dana's built-in `reason()` function. `reason()` leverages PAV to adapt its output based on the context provided by the Dana engineer, particularly through type hints. Consider the following interaction:

```python
>>> pi_description = reason("what is pi?")
# pi_description is now a string:
# "Pi (π) is a mathematical constant representing the ratio of a circle's circumference to its diameter. Its approximate value is:
# π ≈ 3.14159
# But it is an irrational number, meaning: ..."

>>> pi_float: float = reason("what is pi?")
# pi_float is now the float: 3.14159265

>>> radius = 2 ; area = pi_float * radius**2
# area is now the float: 12.5663706
```

In the first call, with no specific type hint for `pi_description` (or if `-> any` or `-> str` was implied), `reason()` returns a descriptive string. In the second call, the explicit type hint `pi_float: float` signals to PAV that a floating-point number is desired. The PAV framework, underpinning `reason()`:

1.  **Perceives** the request "what is pi?" and critically, the `expected_output_type` of `float` from the type hint.
2.  **Acts** by querying its underlying AI model, likely instructing it to provide a numerical value for Pi.
3.  **Validates** that the AI's output can be (or is) a float, ensuring the assignment to `pi_float` is type-safe and that `pi_float` can be immediately used in numerical calculations like `area = pi_float * radius**2`.

This dynamic adaptation based on context, especially the desired output type, without changing the core textual prompt, is a hallmark of the PAV model and a key to Dana's expressive power and developer convenience.

---

This section outlines the PAV (Perceive → Act → Validate) framework, designed for implementation in Python as part of the Dana runtime.

* The **PAV control logic** and retry loop is implemented in Python.
* The **custom P and V functions** are authored in **Dana**.
* The **Act function** is decorated in Python and becomes the execution anchor.
* The framework retries execution based on validation outcomes, with a default of **`max_retries = 3`**.
* The `pav_status` object is available to all stages as part of the **sandbox context**, enabling adaptive behavior or introspection.

---

### 🔹 `@pav(...)` Decorator

Wraps a Python-defined **Act** function with PAV lifecycle logic. Accepts:

| Parameter     | Type                    | Description                                                                                                |
| ------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------- |
| `perceive`    | DanaExpr or DanaFuncRef | Optional Dana function that maps raw input to perceived input                                              |
| `validate`    | DanaExpr or DanaFuncRef | Optional Dana function that returns `true` if output is valid                                              |
| `max_retries` | `int`                   | Number of retries on validation failure (default = `3`)                                                    |
| `expected_output_type` | `Any`          | Optional. The expected type or structure of the final output. Used by `Validate` and can inform `Perceive`/`Act`. |

---

### 🔹 Dana ↔ Python Interface Contracts

| Stage      | Input Type                      | Output Type                           |
| ---------- | ------------------------------- | ------------------------------------- |
| `Perceive` | Dana value (`Any`)              | Dana-typed input for `Act`            |
| `Act`      | Python or Dana-compatible input | Python output (`Any`)                 |
| `Validate` | Python output (`Any`)           | Boolean Dana result (`true` if valid) |

Python will:

* Convert inputs/outputs as needed to/from Dana's runtime types
* Provide `pav_status` as a local variable in Dana context

---

### 🔹 `pav_status` in Dana

Exposed in the Dana local scope (per invocation), structured as:

```python
{
  "attempt": int,
  "last_failure": str or null,
  "max_retries": int,
  "successful": bool,
  "perceived_input": Any,    # Output of the Perceive phase. Can be a simple transformed value or a richer structure/dictionary \
                             # containing the normalized input along with relevant code-site and ambient system context \
                             # gathered during perception.
  "raw_output": Any,         # Python object output by the Act phase.
  "expected_output_type": Any # The type/structure expected for the final output. Populated from decorator arg or Perceive phase.
}
```

Can be used in Dana validation functions for adaptive logic (e.g. "on second retry, try a stricter check").

---

###  Kontext Rich Context in PAV

The power of the PAV model is significantly enhanced by its ability to leverage rich contextual information within each phase, particularly during `Perceive` but also accessible during `Act` and `Validate` (via `pav_status.perceived_input`). This allows for more intelligent and adaptive behavior. Key types of context include:

*   **Code-Site Context**: Derived from the Dana source code where the PAV-enabled function is called. This is akin to how a human developer understands a function call by looking at its surroundings. Examples include:
    *   `comments`: Block or inline comments near the call site that might explain intent or provide hints.
    *   `variable_context`: Names and inferred types of nearby variables.
    *   `type_hints_at_call`: If the function call is part of an assignment with a type hint (e.g., `my_var: ExpectedType = pav_function(...)`), this `ExpectedType` can be crucial for the `Perceive` phase to determine the `expected_output_type` if not explicitly provided to the decorator.
    *   `surrounding_code_lines`: A few lines of code before and after the call.
    *   `parent_function_name`: The name of the Dana function enclosing the PAV call.
    The mechanism for gathering this (e.g., a conceptual `CodeContextAnalyzer` invoked by the PAV framework during the Perceive phase) is an important implementation detail.

*   **Ambient System Context**: Broader operational parameters available from the Dana sandbox or system environment. These provide overarching guidance or constraints. Examples:
    *   `system:__pav_profile` (or `system:__dana_ipv_profile` if aligning with older concepts): An identifier for an active PAV execution profile (e.g., "default", "strict_validation", "creative_generation", "fault_tolerant_integration"). This can dictate the behavior of P, A, and V stages.
    *   `system:__pav_settings_override`: A dictionary allowing fine-grained overrides for specific PAV behaviors.
    *   `system:__current_task_id`, `system:__current_task_description`: Information about the ongoing agent task.
    *   `system:__session_id`, `system:__user_id`: Session and user identifiers.
    *   `system:__locale`: Preferred locale for localization or language-specific behavior.
    *   `system:__active_domains`: A list of active knowledge domains (e.g., `["finance", "medical_records"]`) to help scope or specialize the P/A/V logic.

By making this context available (primarily through the `perceived_input` object passed from `Perceive` to `Act`, and available in `pav_status`), the PAV framework enables functions to be highly adaptive to their specific invocation circumstances and the broader operational environment.

---

## ✅ Example Usage (in Python)

```python
@pav(
    perceive="Dana::parse_input",
    validate="Dana::check_valid_summary",
    max_retries=3
)
def summarize(perceived_input):
    return llm_generate(perceived_input)
```

Where:

* `Dana::parse_input` might coerce natural language into a prompt object
* `Dana::check_valid_summary` ensures the result is JSON with a `summary` field

---

## 🔁 Retry Semantics

* Perception runs **once**
* Validation can run up to `max_retries + 1` times
* On each failure:

  * `Act` is called again with the same `perceived_input`
  * `pav_status["attempt"]` is incremented
* After max retries:

  * Raise error OR optionally call `on_fail` fallback (future enhancement)

---

## 🧠 Future-Proofing Considerations

* Support for async `Act` functions
* Support for post-`Structure` transformation hooks (optional)
* Retry strategy abstraction (`exponential_backoff`, `adaptive`, etc.)
* Integration with Dana state containers for cross-call memory
*   **PAV Execution Profiles/Strategies**: Building on the `system:__pav_profile` idea, formally define different PAV execution profiles. For example:
    *   `LLMInteractionPAV`: `Perceive` phase focuses on detailed prompt engineering using code-site and ambient context; `Act` calls an LLM; `Validate` checks for hallucinations or structural compliance.
    *   `DataValidationPAV`: `Perceive` might identify data source and schema; `Act` performs data retrieval/transformation; `Validate` performs rigorous schema and integrity checks.
    *   `SafeToolCallPAV`: `Perceive` understands tool input requirements; `Act` executes an external tool; `Validate` checks for successful execution and expected output structure.
    These profiles could be implemented by allowing different Dana functions (or even specialized Python logic) to be specified for the P, A, and V stages based on the active profile.
*   **Advanced `CodeContextAnalyzer`**: Developing a sophisticated `CodeContextAnalyzer` that can robustly extract meaningful information from Dana code, potentially handling minified or uncommented code through heuristics or lightweight parsing.

---

## 🔁 Retry Semantics

* Perception runs **once**
* Validation can run up to `max_retries + 1` times
* On each failure:

  * `Act` is called again with the same `perceived_input`
  * `pav_status["attempt"]` is incremented
* After max retries:

  * Raise error OR optionally call `on_fail` fallback (future enhancement)

---

## 🧠 Future-Proofing Considerations

* Support for async `Act` functions
* Support for post-`Structure` transformation hooks (optional)
* Retry strategy abstraction (`exponential_backoff`, `adaptive`, etc.)
* Integration with Dana state containers for cross-call memory 