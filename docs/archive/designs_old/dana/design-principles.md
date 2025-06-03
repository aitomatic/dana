# Dana Design Principles

These principles guide the design and evolution of Dana as an agentic language and sandbox. They are intended for Dana creators, AI coding assistants, and advanced users who want to understand or extend the system.

---

## 1. Simplicity & Power

- **Postel's Law:**
  > "Be conservative in what you do, be liberal in what you accept from others."
- **Simple things should be easy. Complex things should be possible.**
- **KISS:** Keep It Simple, Stupid.
- **YAGNI:** You Aren't Gonna Need It.

---

## 2. Fault-Tolerance & Precision

- **Dana Sandbox Operating Model:**
  - Give users the best of fault-tolerance and precision/determinism, using Predict-and-Error Correct as a core principle.
- **Predict-and-Error Correct:**
  - The system should predict user intent and correct errors automatically when possible, but always allow for precise, deterministic control.
- **Fail gracefully:**
  - Errors should be actionable, non-catastrophic, and never leak sensitive information.
- **Infer from context whenever possible:**
  - Reduce boilerplate and cognitive load by making smart, safe inferences.

---

## 3. Security & Clarity

- **Explicit over implicit:**
  - Defaults should be safe; opt-in for sensitive or advanced features.
- **Explainability and auditability:**
  - Every action, inference, and error should be explainable and traceable.
- **Separation of concerns:**
  - Keep language, runtime, and agentic/AI features modular and decoupled.

---

## 4. Extensibility & Composability

- **Extensibility:**
  - The system should be easy to extend, both for new language features and for integration with external tools and AI models.
- **Composability:**
  - Functions, modules, and agents should be easy to compose and reuse.

---

## 5. Human-Centric Design

- **User empowerment:**
  - Prioritize the user's intent and control, but provide "magic" where it increases productivity and safety.
- **Bias for clarity and learning:**
  - Favor designs that are easy to teach, learn, and reason about.
- **Love/hate relationship with language and code:**
  - Dislike natural language for its ambiguity. Dislike code for its brittleness. Love natural language for its fault-tolerance. Love code for its determinism and precision. Strive for a system that combines the best of both worlds.

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../LICENSE.md">MIT License</a>.<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 