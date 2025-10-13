**Author:** Dana Language Team  
**Date:** 2025-01-22  
**Version:** 4.0.0  
**Status:** Example

# POET MVP Use Cases

This document outlines the MVP use cases for POET, demonstrating how the framework enhances functions with reliability, validation, and domain-specific improvements.

## Use Cases

### 1. Unreliable API Call (Retry Logic)
- **Function:** Simulates an API call that randomly fails.
- **Enhancement:** POET adds retry logic to handle failures.
- **Example:**
  ```python
  @poet()
  def unreliable_api_call():
      import random
      if random.random() < 0.7:
          raise Exception("API failed!")
      return "Success!"
  ```
- **Execution Flow:**
  ```mermaid
  sequenceDiagram
      User->>POET: Decorate function with @poet()
      POET->>CodeGenerator: Intercept function on first call
      CodeGenerator->>POET: Return enhanced function (retry logic)
      POET->>Storage: Store enhanced function in .poet/unreliable_api_call/v1/code.py
      User->>POET: Call function
      POET->>EnhancedFunction: Execute enhanced function
      EnhancedFunction->>POET: Return result or retry on failure
      POET->>User: Return result
      POET->>Feedback: Emit event and prompt for feedback
      User->>Feedback: Provide feedback
      Feedback->>Storage: Store feedback in .poet/unreliable_api_call/feedback/pending/
  ```

### 2. Input Validation (Type/Range Checking)
- **Function:** Adds two positive numbers.
- **Enhancement:** POET ensures inputs are positive numbers.
- **Example:**
  ```python
  @poet()
  def add_positive_numbers(a, b):
      return a + b
  ```
- **Execution Flow:**
  ```mermaid
  sequenceDiagram
      User->>POET: Decorate function with @poet()
      POET->>CodeGenerator: Intercept function on first call
      CodeGenerator->>POET: Return enhanced function (input validation)
      POET->>Storage: Store enhanced function in .poet/add_positive_numbers/v1/code.py
      User->>POET: Call function
      POET->>EnhancedFunction: Execute enhanced function
      EnhancedFunction->>POET: Return result or raise error if inputs invalid
      POET->>User: Return result
      POET->>Feedback: Emit event and prompt for feedback
      User->>Feedback: Provide feedback
      Feedback->>Storage: Store feedback in .poet/add_positive_numbers/feedback/pending/
  ```

### 3. Output Validation (Result Checking)
- **Function:** Divides two numbers.
- **Enhancement:** POET checks for division by zero and invalid results.
- **Example:**
  ```python
  @poet()
  def divide(a, b):
      return a / b
  ```
- **Execution Flow:**
  ```mermaid
  sequenceDiagram
      User->>POET: Decorate function with @poet()
      POET->>CodeGenerator: Intercept function on first call
      CodeGenerator->>POET: Return enhanced function (output validation)
      POET->>Storage: Store enhanced function in .poet/divide/v1/code.py
      User->>POET: Call function
      POET->>EnhancedFunction: Execute enhanced function
      EnhancedFunction->>POET: Return result or raise error if result invalid
      POET->>User: Return result
      POET->>Feedback: Emit event and prompt for feedback
      User->>Feedback: Provide feedback
      Feedback->>Storage: Store feedback in .poet/divide/feedback/pending/
  ```

### 4. Prompt Optimization (User Feedback)
- **Function:** Generates a summary using an LLM.
- **Enhancement:** POET adds prompt cleaning, retries, and collects user feedback.
- **Example:**
  ```python
  @poet(domain="prompt_optimization")
  def generate_summary(prompt):
      return llm_call(prompt)
  ```
- **Execution Flow:**
  ```mermaid
  sequenceDiagram
      User->>POET: Decorate function with @poet(domain="prompt_optimization")
      POET->>CodeGenerator: Intercept function on first call
      CodeGenerator->>POET: Return enhanced function (prompt cleaning, retries, logging)
      POET->>Storage: Store enhanced function in .poet/generate_summary/v1/code.py
      User->>POET: Call function
      POET->>EnhancedFunction: Execute enhanced function
      EnhancedFunction->>POET: Return result
      POET->>User: Return result
      POET->>Feedback: Emit event and prompt for feedback
      User->>Feedback: Provide feedback
      Feedback->>Storage: Store feedback in .poet/generate_summary/feedback/pending/
  ```

### 5. Credit Approval Decision Support
- **Use Case:** A function that evaluates credit applications and suggests approval or rejection.
- **Learning:** POET learns which factors (e.g., credit score, income, debt-to-income ratio) are most predictive of successful credit approvals and refines its decision logic over time.
- **Example:**
  ```python
  @poet(domain="credit_approval")
  def evaluate_credit_application(application):
      # Naive implementation: approve if credit score > 700
      return application["credit_score"] > 700
  ```
- **Enhancement:** POET enhances the function to consider multiple factors, adds logging, validation, and a learning loop.
- **Execution Flow:**
  ```mermaid
  sequenceDiagram
      User->>POET: Decorate function with @poet(domain="credit_approval")
      POET->>CodeGenerator: Intercept function on first call
      CodeGenerator->>POET: Return enhanced function (multiple factors, logging, validation)
      POET->>Storage: Store enhanced function in .poet/evaluate_credit_application/v1/code.py
      User->>POET: Call function
      POET->>EnhancedFunction: Execute enhanced function
      EnhancedFunction->>POET: Return approval decision
      POET->>User: Return decision
      POET->>Feedback: Emit event and prompt for feedback
      User->>Feedback: Provide feedback
      Feedback->>Storage: Store feedback in .poet/evaluate_credit_application/feedback/pending/
      POET->>Learning: Use feedback to refine approval logic over time
  ```

## Feedback Flow
- After each function execution, the user is prompted for feedback.
- Feedback is stored in `.poet/<function_name>/feedback/pending/`.
- Feedback can trigger further enhancements or regeneration of the function.

## How to Run
1. Ensure POET is installed and configured.
2. Run any example:
   ```bash
   python unreliable_api_call.py
   ```

## Next Steps
- Extend feedback processing to trigger automated improvements.
- Integrate with a real-time event system for feedback collection. 