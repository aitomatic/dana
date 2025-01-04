# Requirements

## Fab Domain-Aware Neurosymbolic Agent

- Workflow's flexibility
  - Workflow design
    - How to build the workflow combines the expert interview results with multiple Fab APIs?
    - 1 to multiple root cause analysis
    - Design: workflows, plans, facts, heuristics, conditions, etc. should come from a knowledge base of expert knowledge
  - Reasoning capabilities
    - Reasoning capability (with enhanced SEMIKONG integrated)
    - Based on the supporting documents to provide more information about the case and root cause analysis that could not be in the expert interview.
    - Anomaly detection from raw FDC data.

## Enhanced SemiKong LLM

- SemiKong with Llama 3.3 - 1/31/2025
- Finetune the SemiKong with Fab domain know-how (mostly from power point).
  - Data preparation pipeline/Model finetune pipeline/RAG pipeline
  - Evaluation result
  - Finetune with current SEMIKONG
  - New SEMIKONG release date: Before 1/31/2025

## Knowledge Integration Methodology

- Flexibility of the knowledge capture
  - Customized template for different domain knowledge capture.
- Capable to extend the questions based the expert's answer to acquire more knowledge about the case analysis.
- Flexibility to edit the existing knowledge.

## Issues

- The current SEMIKONG is not capable of handling the Fab domain knowledge.
