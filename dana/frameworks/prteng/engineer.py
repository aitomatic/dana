"""
PromptEngineer - A framework for iterative prompt optimization.
"""

import re
import uuid
from datetime import datetime
from typing import Any
from dana.common.mixins.loggable import Loggable

from .models import Prompt, Interaction, Evaluation
from .persistence import PromptEngineerPersistence


class PromptEngineer(Loggable):
    """
    A framework for iterative prompt optimization that learns from LLM responses
    and user feedback to continuously improve prompt templates and generation strategies.
    """

    def __init__(self, base_dir: str = "~/.dana/prteng"):
        """Initialize the PromptEngineer with persistence layer."""
        super().__init__()
        self.persistence = PromptEngineerPersistence(base_dir)
        self._template_cache: dict[str, str] = {}
        self._prompt_cache: dict[str, Prompt] = {}

    def generate(
        self, user_query: str, prompt_id: str | None = None, system_template: str | None = None, template_data: dict[str, Any] | None = None
    ) -> Prompt:
        """
        Generate a prompt with user_query as the user message and system_template as the system message.

        Args:
            user_query: The user's query/message
            prompt_id: Explicit name and/or UUID for tracking
            system_template: Template string for the system prompt with optional <prompt_id>UUID</prompt_id> metadata
            template_data: Data to substitute into system template

        Returns:
            Prompt: Object with .id, .system_message, and .user_message attributes
        """
        if not user_query:
            raise ValueError("user_query must be provided")

        # Determine the final prompt ID
        if system_template:
            # Extract UUID from template metadata if present
            clean_template, extracted_id = self._parse_template(system_template)
            final_prompt_id = prompt_id or extracted_id or self._generate_uuid()
        else:
            final_prompt_id = prompt_id or self._generate_uuid()

        # Check if there's already a saved template for this prompt_id
        existing_template = self.persistence.get_latest_template(final_prompt_id)
        print(f"DEBUG ENGINEER: prompt_id={final_prompt_id}, existing_template='{existing_template}', system_template='{system_template}'")

        if existing_template:
            # Use the existing template as the system prompt
            system_prompt = existing_template
            print(f"DEBUG ENGINEER: Using existing template: '{system_prompt}'")
        elif system_template:
            # Use the provided system template
            clean_template, _ = self._parse_template(system_template)

            # Substitute data if provided
            if template_data:
                try:
                    system_prompt = clean_template.format(**template_data)
                except KeyError as e:
                    raise ValueError(f"Missing required template variable: {e}")
                except ValueError as e:
                    raise ValueError(f"Template formatting error: {e}")
            else:
                system_prompt = clean_template

            # Save the new template version
            self.persistence.save_template_version(final_prompt_id, clean_template, 1)
        else:
            # No system template provided and no existing template - start with no system prompt
            system_prompt = None
            # Save empty system prompt as initial template version for tracking
            self.persistence.save_template_version(final_prompt_id, "", 1)

        # Create the prompt with separate system and user messages
        prompt = Prompt(id=final_prompt_id, system_message=system_prompt, user_message=user_query)
        self._prompt_cache[final_prompt_id] = prompt
        return prompt

    def update(self, response: str, prompt_id: str, feedback: str | None = None, ask_for_feedback: bool = False) -> None:
        """
        Update prompt based on LLM response and optional feedback.

        Args:
            response: LLM response to learn from
            prompt_id: UUID of the prompt that generated this response
            feedback: User-provided feedback string
            ask_for_feedback: Whether to request user feedback
        """
        # Get or create prompt
        prompt = self._prompt_cache.get(prompt_id)
        if not prompt:
            # Try to load from persistence
            template = self.persistence.get_latest_template(prompt_id)
            if template:
                # Parse the template to extract system and user messages
                if template.startswith("System: ") and "\n\nUser: " in template:
                    parts = template.split("\n\nUser: ", 1)
                    system_message = parts[0][8:]  # Remove "System: " prefix
                    user_message = parts[1]
                    prompt = Prompt(id=prompt_id, system_message=system_message, user_message=user_message)
                else:
                    prompt = Prompt(id=prompt_id, user_message=template)
            else:
                raise ValueError(f"Prompt with ID {prompt_id} not found")

        # Handle user feedback request
        if ask_for_feedback and not feedback:
            feedback = self._request_user_feedback(response)

        # Evaluate response
        if feedback:
            evaluation = self._parse_user_feedback(feedback)
        else:
            evaluation = self._self_evaluate(response, prompt)

        # Create interaction record
        interaction = Interaction(
            prompt_id=prompt_id,
            response=response,
            feedback=feedback,
            evaluation=evaluation,
            timestamp=datetime.now(),
            success_score=evaluation.overall_score if evaluation else 0.5,
        )

        # Save interaction
        self.persistence.save_interaction(prompt_id, interaction)

        # Update template if needed
        if evaluation and evaluation.overall_score < 0.7:  # Threshold for improvement
            self._evolve_template(prompt_id, evaluation)

    def _parse_template(self, template: str) -> tuple[str, str | None]:
        """
        Extract UUID from template metadata and return clean template.

        Format: <prompt_id>UUID</prompt_id> at start of template
        Returns: (clean_template, extracted_uuid)
        """
        uuid_pattern = r"<prompt_id>([a-f0-9-]{36})</prompt_id>"
        match = re.search(uuid_pattern, template, re.IGNORECASE)

        if match:
            extracted_uuid = match.group(1)
            # Validate UUID format
            try:
                uuid.UUID(extracted_uuid)
                clean_template = re.sub(r"<prompt_id>[^<]+</prompt_id>\s*", "", template)
                return clean_template.strip(), extracted_uuid
            except ValueError:
                # Invalid UUID format, treat as regular template
                pass

        return template, None

    def _generate_uuid(self) -> str:
        """Generate a new UUID4 string."""
        return str(uuid.uuid4())

    def _request_user_feedback(self, response: str) -> str:
        """Request user feedback on response."""
        print(f"\nLLM Response:\n{response}\n")
        feedback = input("Please provide feedback on this response (or press Enter to skip): ")
        return feedback.strip() if feedback else ""

    def _parse_user_feedback(self, feedback: str) -> Evaluation:
        """Parse user feedback into structured evaluation using LLM."""
        try:
            # Try LLM-based parsing first
            return self._llm_parse_feedback(feedback)
        except Exception as e:
            print(f"⚠️  LLM feedback parsing failed: {e}")
            # Fallback to heuristic-based parsing
            return self._heuristic_parse_feedback(feedback)

    def _llm_parse_feedback(self, feedback: str) -> Evaluation:
        """Use LLM to intelligently parse user feedback."""
        import json
        from dana.core.resource.builtins.llm_resource_type import LLMResourceType
        from dana.common.types import BaseRequest

        llm_resource = LLMResourceType.create_instance_from_values(
            {
                "name": "feedback_parser",
                "model": "auto",
                "temperature": 0.1,  # Very low temperature for consistent parsing
                "max_tokens": 300,
            }
        )
        llm_resource.initialize()

        parsing_prompt = f"""You are an expert at analyzing user feedback for AI responses. Parse the following user feedback and provide a structured evaluation.

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

        request = BaseRequest(
            arguments={
                "messages": [{"role": "user", "content": parsing_prompt}],
                "temperature": 0.1,
                "max_tokens": 300,
            }
        )

        response = llm_resource.query_sync(request)

        if response.success and response.content:
            try:
                content = self._extract_template_from_response(response.content)
                if content and content.strip():
                    parsed_data = json.loads(content)

                    return Evaluation(
                        prompt_id="",  # Will be set by caller
                        response="",  # Will be set by caller
                        criteria_scores=parsed_data.get("criteria_scores", {}),
                        overall_score=parsed_data.get("overall_score", 0.5),
                        improvement_suggestions=parsed_data.get("improvement_suggestions", []),
                        confidence=parsed_data.get("confidence", 0.7),
                    )
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️  Failed to parse LLM feedback response: {e}")
                return self._heuristic_parse_feedback(feedback)

        return self._heuristic_parse_feedback(feedback)

    def _heuristic_parse_feedback(self, feedback: str) -> Evaluation:
        """Fallback heuristic-based feedback parsing."""
        # Look for positive/negative indicators
        positive_words = ["good", "great", "excellent", "perfect", "helpful", "clear", "accurate"]
        negative_words = ["bad", "wrong", "unclear", "confusing", "incomplete", "verbose", "too long"]

        feedback_lower = feedback.lower()
        positive_count = sum(1 for word in positive_words if word in feedback_lower)
        negative_count = sum(1 for word in negative_words if word in feedback_lower)

        # Calculate overall score
        if positive_count > negative_count:
            overall_score = min(0.9, 0.6 + (positive_count * 0.1))
        elif negative_count > positive_count:
            overall_score = max(0.1, 0.4 - (negative_count * 0.1))
        else:
            overall_score = 0.5

        # Extract improvement suggestions
        suggestions = []
        if "verbose" in feedback_lower or "too long" in feedback_lower or "concise" in feedback_lower:
            suggestions.append("Make response more concise")
        if "unclear" in feedback_lower or "confusing" in feedback_lower:
            suggestions.append("Improve clarity and structure")
        if "incomplete" in feedback_lower:
            suggestions.append("Provide more comprehensive coverage")
        if "examples" in feedback_lower or "relatable" in feedback_lower:
            suggestions.append("Provide more relatable examples")
        if "structure" in feedback_lower or "organize" in feedback_lower:
            suggestions.append("Improve structure and organization")
        if "detailed" in feedback_lower or "more detail" in feedback_lower:
            suggestions.append("Provide more detailed explanations")

        return Evaluation(
            prompt_id="",  # Will be set by caller
            response="",  # Will be set by caller
            criteria_scores={
                "clarity": 0.8 if "clear" in feedback_lower else 0.5,
                "completeness": 0.8 if "complete" in feedback_lower else 0.5,
                "style": 0.8 if "good" in feedback_lower else 0.5,
                "length": 0.8 if "concise" in feedback_lower else 0.5,
            },
            overall_score=overall_score,
            improvement_suggestions=suggestions,
            confidence=0.3,  # Low confidence to distinguish from LLM evaluation
        )

    def _self_evaluate(self, response: str, prompt: Prompt) -> Evaluation:
        """Self-evaluate response using built-in criteria."""
        # Simple heuristic-based self-evaluation
        # In a real implementation, this could use LLM-based evaluation

        criteria_scores = {}

        # Length evaluation
        word_count = len(response.split())
        if 50 <= word_count <= 500:
            criteria_scores["length"] = 0.8
        elif word_count < 50:
            criteria_scores["length"] = 0.4
        else:
            criteria_scores["length"] = 0.6

        # Structure evaluation (look for paragraphs, lists, etc.)
        if "\n\n" in response or "\n- " in response or "\n1. " in response:
            criteria_scores["structure"] = 0.8
        else:
            criteria_scores["structure"] = 0.5

        # Completeness evaluation (simple keyword matching)
        prompt_words = set(prompt.text.lower().split())
        response_words = set(response.lower().split())
        overlap = len(prompt_words.intersection(response_words))
        criteria_scores["completeness"] = min(0.9, overlap / max(len(prompt_words), 1) * 2)

        # Clarity evaluation (sentence length, complexity)
        sentences = response.split(".")
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        if 10 <= avg_sentence_length <= 25:
            criteria_scores["clarity"] = 0.8
        else:
            criteria_scores["clarity"] = 0.6

        overall_score = sum(criteria_scores.values()) / len(criteria_scores)

        # Generate improvement suggestions
        suggestions = []
        if criteria_scores.get("length", 0.5) < 0.6:
            suggestions.append("Adjust response length")
        if criteria_scores.get("structure", 0.5) < 0.6:
            suggestions.append("Improve response structure")
        if criteria_scores.get("clarity", 0.5) < 0.6:
            suggestions.append("Enhance clarity and readability")

        return Evaluation(
            prompt_id=prompt.id,
            response=response,
            criteria_scores=criteria_scores,
            overall_score=overall_score,
            improvement_suggestions=suggestions,
            confidence=0.2,  # Low confidence to distinguish from LLM evaluation
        )

    def _evolve_template(self, prompt_id: str, evaluation: Evaluation) -> None:
        """Evolve template based on evaluation feedback using LLM."""
        # Get current template
        current_template = self.persistence.get_latest_template(prompt_id)
        if not current_template:
            return

        # Get version history
        versions = self.persistence.load_template_versions(prompt_id)
        next_version = len(versions) + 1

        # Use LLM to evolve the template intelligently
        evolved_template = self._llm_evolve_template(current_template, evaluation, versions, prompt_id)

        # Save evolved template if it changed
        if evolved_template and evolved_template != current_template:
            self.persistence.save_template_version(prompt_id, evolved_template, next_version)
            print(f"Template evolved to version {next_version} for prompt {prompt_id}")
            print(f"New template: {evolved_template}")

    def _llm_evolve_template(self, current_template: str, evaluation: Evaluation, versions: list, prompt_id: str) -> str:
        """Use LLM to intelligently evolve the template based on feedback."""
        try:
            # Get LLM resource from the system
            from dana.core.resource.builtins.llm_resource_type import LLMResourceType
            from dana.common.types import BaseRequest

            llm_resource = LLMResourceType.create_instance_from_values(
                {
                    "name": "template_evolver",
                    "model": "auto",
                    "temperature": 0.3,  # Lower temperature for more consistent evolution
                    "max_tokens": 2000,  # Increased for full response history
                }
            )
            llm_resource.initialize()

            # Build context about the template evolution history
            version_context = ""
            if len(versions) > 1:
                version_context = "\nPrevious template versions:\n"
                for version in versions[-3:]:  # Show last 3 versions
                    version_context += f"Version {version.version}: {version.template}\n"

            # Build interaction history context
            interaction_history = self._build_interaction_history(prompt_id)

            # Get the latest interaction for user feedback
            history = self.persistence.load_prompt_history(prompt_id)
            latest_interaction = history[-1] if history else None

            # Create the evolution prompt
            evolution_prompt = f"""You are a prompt engineering expert. Your task is to evolve a prompt template based on user feedback and evaluation results.

CURRENT TEMPLATE:
{current_template}

{interaction_history}

LATEST USER FEEDBACK:
{latest_interaction.feedback if latest_interaction and latest_interaction.feedback else 'No specific feedback provided'}

LATEST EVALUATION:
{evaluation.overall_score:.2f}/1.0 (confidence: {evaluation.confidence:.1f}) - {'LLM evaluation' if evaluation.confidence > 0.8 else 'Heuristic fallback'}

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

            # Debug: Show the evolution prompt being sent to LLM
            print("\n🔧 Evolving template with LLM...")

            # Make the LLM call
            request = BaseRequest(
                arguments={
                    "messages": [{"role": "user", "content": evolution_prompt}],
                    "temperature": 0.3,
                    "max_tokens": 2000,  # Increased for full response history
                }
            )

            response = llm_resource.query_sync(request)

            # Debug: Show the LLM response
            if response.success:
                print("✅ LLM evolution successful")
            else:
                print("❌ LLM evolution failed")

            if response.success and response.content:
                # Extract the evolved template
                evolved_template = self._extract_template_from_response(response.content)
                if evolved_template:
                    return evolved_template.strip()

            # Fallback to heuristic-based evolution if LLM fails
            return self._heuristic_evolve_template(current_template, evaluation)

        except Exception as e:
            print(f"⚠️  LLM template evolution failed: {e}")
            # Fallback to heuristic-based evolution
            return self._heuristic_evolve_template(current_template, evaluation)

    def _extract_template_from_response(self, response_content: Any) -> str:
        """Extract template text from LLM response."""
        if isinstance(response_content, str):
            return response_content
        elif isinstance(response_content, dict):
            # Handle different response formats
            if "choices" in response_content and response_content["choices"]:
                content = response_content["choices"][0].get("message", {}).get("content", "")
                return content
            elif "text" in response_content:
                return response_content["text"]
            elif "content" in response_content:
                return response_content["content"]
        return ""

    def _heuristic_evolve_template(self, current_template: str, evaluation: Evaluation) -> str:
        """Fallback heuristic-based template evolution."""
        evolved_template = current_template

        for suggestion in evaluation.improvement_suggestions:
            if "concise" in suggestion.lower():
                if "be concise" not in evolved_template.lower():
                    evolved_template = f"Be concise and direct. {evolved_template}"
            elif "clarity" in suggestion.lower():
                if "be clear" not in evolved_template.lower():
                    evolved_template = f"Be clear and well-structured. {evolved_template}"
            elif "comprehensive" in suggestion.lower():
                if "comprehensive" not in evolved_template.lower():
                    evolved_template = f"Provide a comprehensive response. {evolved_template}"
            elif "examples" in suggestion.lower() or "relatable" in suggestion.lower():
                if "examples" not in evolved_template.lower():
                    evolved_template = f"Provide relatable examples and practical illustrations. {evolved_template}"
            elif "structure" in suggestion.lower():
                if "structure" not in evolved_template.lower():
                    evolved_template = f"Use clear structure with headings and bullet points. {evolved_template}"

        return evolved_template

    def _build_interaction_history(self, prompt_id: str) -> str:
        """Build a detailed interaction history for the LLM evolution prompt."""
        history = self.persistence.load_prompt_history(prompt_id)

        if not history:
            return "No previous interactions available."

        history_text = "INTERACTION HISTORY:\n"

        for i, interaction in enumerate(history, 1):
            history_text += f"\n--- Interaction {i} ---\n"

            # Structure: LLM Response → User Feedback → Evaluation (if from LLM)

            # 1. Show the LLM response first
            if interaction.response:
                history_text += f"LLM Response: {interaction.response}\n"

            # 2. Show user feedback
            if interaction.feedback:
                history_text += f"User Feedback: {interaction.feedback}\n"

            # 3. Only include evaluation data if it came from LLM (high confidence)
            if interaction.evaluation and interaction.evaluation.confidence > 0.8:
                history_text += f"LLM Evaluation: {interaction.evaluation.overall_score:.2f}/1.0\n"
                if interaction.evaluation.improvement_suggestions:
                    history_text += f"LLM Suggestions: {', '.join(interaction.evaluation.improvement_suggestions)}\n"

        return history_text

    def get_history(self, prompt_id: str | None = None) -> list[Interaction]:
        """Get interaction history for specific prompt_id or all prompts."""
        if prompt_id:
            return self.persistence.load_prompt_history(prompt_id)
        else:
            all_interactions = []
            for pid in self.persistence.list_prompt_ids():
                all_interactions.extend(self.persistence.load_prompt_history(pid))
            return sorted(all_interactions, key=lambda x: x.timestamp)
