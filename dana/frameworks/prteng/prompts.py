"""
Prompt templates for the PromptEngineer framework.

This module contains all the prompt templates used for LLM-based evaluation,
feedback parsing, and template evolution.
"""

# LLM Evaluation Prompt Template
LLM_EVALUATION_PROMPT = """You are an expert evaluator. Analyze how well the SYSTEM PROMPT worked to generate a good response to the user's query.

SYSTEM PROMPT (the prompt we want to improve):
{system_message}

USER PROMPT (what the user actually asked for):
{user_message}

AI RESPONSE (generated using the system prompt):
{response}{criteria_text}{objective_text}

Please provide qualitative feedback on:
1. How well did the system prompt help generate a response that addresses the user's actual query?
2. Is the system prompt clear and effective in guiding the AI?
3. What specific improvements could be made to the system prompt?

Provide constructive feedback that will help improve the system prompt for better responses."""

# Feedback Parsing Prompt Template
FEEDBACK_PARSING_PROMPT = """You are an expert at analyzing user feedback for AI responses. Parse the following user feedback and provide a structured evaluation.

USER FEEDBACK: "{feedback}"

Please analyze this feedback and provide:
1. Overall satisfaction score (0.0 to 1.0, where 1.0 is perfect)
2. Specific improvement suggestions
3. Scores for different criteria (clarity, completeness, style, length)

Respond in this exact JSON format:
{{
    "overall_score": 0.7,
    "criteria_scores": {{
        "clarity": 0.8,
        "completeness": 0.6,
        "style": 0.7,
        "length": 0.5
    }},
    "improvement_suggestions": [
        "Make response more concise",
        "Provide more relatable examples"
    ],
    "confidence": 0.8
}}

Only return the JSON, no other text."""

# Template Evolution Prompt Template
TEMPLATE_EVOLUTION_PROMPT = """You are a prompt engineering expert. Your task is to evolve a prompt template based on user feedback and evaluation results.

CURRENT TEMPLATE:
{current_template}

{interaction_history}

LATEST USER FEEDBACK:
{latest_feedback}

LATEST EVALUATION:
{latest_evaluation}

{version_context}

INSTRUCTIONS:
1. Analyze the complete interaction history above to understand patterns in user feedback
2. Identify recurring issues and what has/hasn't worked in previous iterations
3. Create an improved version that addresses the specific issues mentioned in the latest feedback
4. Consider the evolution of responses and feedback over time
5. Keep the core intent of the original template while incorporating lessons learned
6. Add specific instructions to address the feedback patterns you observe
7. Make the template more effective for generating better responses
8. Return ONLY the improved template text, no explanations

IMPROVED TEMPLATE:"""

# Evaluation Criteria Descriptions
EVALUATION_CRITERIA = {
    "accuracy": "factual correctness and reliability of information",
    "clarity": "how clear and easy to understand the response is",
    "completeness": "whether the response fully addresses the user's question",
    "conciseness": "whether the response is appropriately brief and to the point",
    "helpfulness": "how useful and actionable the response is for the user",
    "relevance": "how well the response relates to what the user actually asked",
    "tone": "whether the tone and style are appropriate for the context",
    "structure": "how well-organized and logically structured the response is",
}

# Default evaluation criteria
DEFAULT_CRITERIA = ["length", "structure", "completeness", "clarity"]
DEFAULT_LLM_CRITERIA = ["accuracy", "clarity", "completeness", "helpfulness"]

# Template evolution instructions
TEMPLATE_EVOLUTION_INSTRUCTIONS = [
    "Analyze the complete interaction history above to understand patterns in user feedback",
    "Identify recurring issues and what has/hasn't worked in previous iterations",
    "Create an improved version that addresses the specific issues mentioned in the latest feedback",
    "Consider the evolution of responses and feedback over time",
    "Keep the core intent of the original template while incorporating lessons learned",
    "Add specific instructions to address the feedback patterns you observe",
    "Make the template more effective for generating better responses",
    "Return ONLY the improved template text, no explanations",
]
