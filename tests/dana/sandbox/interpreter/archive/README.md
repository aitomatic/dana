# Archived Interpreter Tests

This directory contains **archived** interpreter and infrastructure tests for the DANA language. These tests are no longer maintained and have been disabled from the test suite.

- **New pipeline-driven interpreter tests** are located in the parent directory (`tests/dana/sandbox/interpreter/`).
- Tests here are preserved for reference, migration, and regression purposes.
- If you are adding or updating interpreter tests, please use the new pipeline-driven structure (e.g., `test_ast-execution.py`, `test_parse_tree-ast-execution.py`, `test_code-execution.py`).

---

**How to use this archive:**
- Borrow/adapt useful test cases as you build out the new test suite.
- Do not re-enable these tests unless specifically needed for regression.

---

_Last updated: Archive created as part of test suite modernization._ 