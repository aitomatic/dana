<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md)


# Reasoning in OpenDXA

## Overview

Reasoning in OpenDXA enables agents to analyze situations, make decisions, and solve problems using available knowledge and context. Through DANA programs and the `reason()` function, the reasoning system combines logical analysis with domain expertise to support effective decision-making.

## Core Concepts

### 1. Reasoning Components
- Logical Analysis
  - Pattern recognition
  - Rule application
  - Inference making
  - Conclusion drawing
- Context Analysis
  - Situation assessment
  - Constraint evaluation
  - Option generation
  - Impact analysis
- Decision Making
  - Option evaluation
  - Risk assessment
  - Trade-off analysis
  - Action selection

### 2. Reasoning Operations
- Situation analysis
- Knowledge application
- Option generation
- Decision making
- Action planning

## Architecture

The OpenDXA reasoning system is centered around the DANA `reason()` function, which provides a direct interface to LLM-powered reasoning. The reasoning architecture includes:

1. **DANA Reasoning Layer**: Primary interface through the `reason()` function
2. **LLM Integration Layer**: Connects to language models for reasoning tasks
3. **Knowledge Integration Layer**: Provides access to domain knowledge
4. **Context Management Layer**: Maintains state and context for reasoning
5. **Action Planning Layer**: Translates reasoning outcomes to executable actions

## Implementation

### 1. Basic Reasoning with DANA
```python
from opendxa.dana import run
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Define DANA reasoning program
reasoning_program = """
# Initialize reasoning state
agent.situation = "Machine shows high temperature alerts of 85°C"
agent.domain = "HVAC systems"

# Analyze the situation
temp.analysis = reason("Analyze this situation in the context of {agent.domain}: {agent.situation}")

# Generate possible causes
temp.causes = reason("What are the most likely causes of {agent.situation} in {agent.domain} systems?")

# Evaluate each cause
temp.evaluations = []
for cause in temp.causes:
    temp.likelihood = reason("Evaluate the likelihood of '{cause}' being the cause of '{agent.situation}' and explain why")
    temp.evaluations.append({
        "cause": cause,
        "likelihood": temp.likelihood
    })

# Determine most likely cause
agent.diagnosis = reason("Based on these evaluations, what is the most likely cause of the problem? {temp.evaluations}")

# Recommend actions
agent.recommendation = reason("Recommend actions to address this cause: {agent.diagnosis}")

# Log results
log.info("Diagnosis: {agent.diagnosis}")
log.info("Recommendation: {agent.recommendation}")
"""

# Create context with initial state
context = SandboxContext(
    agent={"name": "diagnostic_agent"},
    world={},
    temp={}
)

# Execute reasoning program
result = run(reasoning_program, context)
```

### 2. Decision Making
```python
# DANA program for decision making
decision_program = """
# Initialize decision state
agent.options = world.available_options
agent.criteria = ["cost", "performance", "reliability", "maintenance"]
temp.evaluations = []

# Evaluate each option against criteria
for option in agent.options:
    temp.option_evaluation = {}
    temp.option_evaluation["option"] = option
    temp.option_evaluation["scores"] = {}
    
    for criterion in agent.criteria:
        temp.score = reason("Evaluate {option} on {criterion} on a scale of 1-10")
        temp.option_evaluation["scores"][criterion] = temp.score
    
    temp.evaluations.append(temp.option_evaluation)

# Calculate total scores
for evaluation in temp.evaluations:
    temp.total = 0
    for criterion, score in evaluation["scores"].items():
        temp.total += int(score)
    evaluation["total_score"] = temp.total

# Make decision
temp.best_option = max(temp.evaluations, key=lambda x: x["total_score"])
agent.decision = temp.best_option["option"]
agent.justification = reason("Justify why {agent.decision} is the best option based on these evaluations: {temp.evaluations}")

# Log decision
log.info("Decision: {agent.decision}")
log.info("Justification: {agent.justification}")
"""
```

### 3. Problem Solving
```python
# DANA program for problem solving
problem_solving_program = """
# Define problem
agent.problem = world.current_problem
agent.constraints = world.constraints
temp.solutions = []

# Generate possible solutions
temp.potential_solutions = reason("Generate 3-5 possible solutions for this problem: {agent.problem}")

# Evaluate each solution against constraints
for solution in temp.potential_solutions:
    temp.evaluation = {}
    temp.evaluation["solution"] = solution
    temp.evaluation["constraint_check"] = {}
    
    for constraint in agent.constraints:
        temp.check = reason("Does the solution '{solution}' satisfy the constraint '{constraint}'? Explain.")
        temp.evaluation["constraint_check"][constraint] = temp.check
    
    temp.evaluation["feasibility"] = reason("Overall, how feasible is this solution considering all constraints?")
    temp.solutions.append(temp.evaluation)

# Select best solution
agent.solution = reason("Which solution is best overall based on these evaluations? {temp.solutions}")
agent.implementation_plan = reason("Create a step-by-step implementation plan for this solution: {agent.solution}")

# Log solution
log.info("Selected solution: {agent.solution}")
log.info("Implementation plan: {agent.implementation_plan}")
"""
```

## Key Differentiators

1. **Integrated Reasoning in DANA**
   - First-class `reason()` function
   - Seamless LLM integration
   - Context-aware reasoning
   - State-based information flow

2. **Contextual Analysis**
   - Situation assessment
   - Domain knowledge integration
   - Constraint evaluation
   - Impact analysis

3. **Decision Support**
   - Option evaluation
   - Risk assessment
   - Trade-off analysis
   - Action planning

## Best Practices

1. **Effective Reasoning Prompts**
   - Be specific and focused
   - Provide relevant context
   - Define clear objectives
   - Include necessary constraints

2. **Knowledge Integration**
   - Reference domain knowledge
   - Apply appropriate context
   - Validate reasoning outputs
   - Consider alternative perspectives

3. **Decision Making**
   - Define clear criteria
   - Evaluate options thoroughly
   - Consider risks and tradeoffs
   - Document justifications

## Common Patterns

1. **Analysis Pattern**
   ```python
   # DANA pattern for situation analysis
   analysis_pattern = """
   # Define situation
   temp.situation = world.current_situation
   
   # Perform multi-step analysis
   temp.observations = reason("What are the key observations in this situation: {temp.situation}")
   temp.implications = reason("What are the implications of these observations: {temp.observations}")
   temp.root_causes = reason("What are the potential root causes behind these observations: {temp.observations}")
   
   # Generate final analysis
   agent.analysis = reason("Synthesize a comprehensive analysis based on: Observations: {temp.observations}, Implications: {temp.implications}, Root causes: {temp.root_causes}")
   """
   ```

2. **Decision Pattern**
   ```python
   # DANA pattern for decision making
   decision_pattern = """
   # Define decision context
   temp.options = world.available_options
   temp.criteria = world.decision_criteria
   
   # Evaluate options
   temp.evaluations = []
   for option in temp.options:
       temp.evaluation = reason("Evaluate option '{option}' against these criteria: {temp.criteria}")
       temp.evaluations.append({"option": option, "evaluation": temp.evaluation})
   
   # Make decision
   agent.decision = reason("Based on these evaluations, which option is best? {temp.evaluations}")
   agent.justification = reason("Justify why {agent.decision} is the best choice")
   """
   ```

3. **Problem-Solving Pattern**
   ```python
   # DANA pattern for problem solving
   problem_solving_pattern = """
   # Define problem
   temp.problem = world.current_problem
   
   # Problem solving steps
   temp.analysis = reason("Analyze this problem: {temp.problem}")
   temp.solutions = reason("Generate possible solutions for this problem: {temp.problem}")
   temp.evaluation = reason("Evaluate each solution: {temp.solutions}")
   temp.best_solution = reason("Which solution is best and why? {temp.evaluation}")
   
   # Implementation planning
   agent.solution = temp.best_solution
   agent.implementation_plan = reason("Create a step-by-step plan to implement: {agent.solution}")
   """
   ```

## Reasoning Examples

1. **Diagnostic Reasoning**
   - Symptom analysis
   - Cause identification
   - Evidence evaluation
   - Diagnosis formulation

2. **Risk Assessment**
   - Risk identification
   - Impact analysis
   - Probability evaluation
   - Mitigation planning

3. **Solution Development**
   - Problem definition
   - Option generation
   - Impact evaluation
   - Implementation planning

## Next Steps

- Learn about [Planning](./planning.md)
- Understand [Execution Flow](../core-concepts/execution-flow.md)
- Explore [DANA Language](../dana/language.md)

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>