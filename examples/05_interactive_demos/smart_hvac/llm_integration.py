"""
LLM Integration for Smart HVAC Demo

This module provides LLM resource setup and configuration for the HVAC demo,
enabling real POET functionality with LLM-based reasoning and learning.
"""

import os
from typing import Any

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseRequest


class HVACLLMManager:
    """
    Manages LLM resources for the HVAC demo.

    Provides LLM-based reasoning for comfort optimization, energy management,
    and learning from user feedback patterns.
    """

    def __init__(self):
        self.llm: LLMResource | None = None
        self.initialized = False
        self._preferred_models = [
            {"name": "openai:gpt-4o-mini", "required_api_keys": ["OPENAI_API_KEY"]},
            {"name": "openai:gpt-3.5-turbo", "required_api_keys": ["OPENAI_API_KEY"]},
            {"name": "anthropic:claude-3-haiku-20240307", "required_api_keys": ["ANTHROPIC_API_KEY"]},
            {"name": "groq:llama3-8b-8192", "required_api_keys": ["GROQ_API_KEY"]},
        ]

    async def initialize(self) -> bool:
        """
        Initialize the LLM resource with available API keys.

        Returns:
            bool: True if LLM was successfully initialized
        """
        if self.initialized:
            return True

        try:
            # Check for available API keys
            available_models = self._get_available_models()
            if not available_models:
                print("⚠️ No LLM API keys found. POET will run without LLM features.")
                print("Set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY")
                return False

            # Create LLM resource with automatic model selection
            self.llm = LLMResource(name="hvac_reasoning_llm", preferred_models=self._preferred_models, temperature=0.7, max_tokens=500)

            await self.llm.initialize()
            self.initialized = True

            print(f"✅ LLM initialized with model: {self.llm.model}")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize LLM: {e}")
            return False

    def _get_available_models(self) -> list:
        """Get list of models with available API keys."""
        available = []
        for model_config in self._preferred_models:
            required_keys = model_config.get("required_api_keys", [])
            if all(os.environ.get(key) for key in required_keys):
                available.append(model_config)
        return available

    async def reason_about_comfort(
        self, current_temp: float, target_temp: float, user_feedback: str | None = None, comfort_history: list | None = None
    ) -> dict[str, Any]:
        """
        Use LLM to reason about user comfort and suggest adjustments.

        Args:
            current_temp: Current room temperature
            target_temp: Current target temperature
            user_feedback: Recent user feedback ("too_hot", "too_cold", "comfortable")
            comfort_history: List of recent comfort feedback

        Returns:
            Dict with LLM reasoning and suggested adjustments
        """
        if not self.llm:
            return {"error": "LLM not available", "suggested_adjustment": 0.0}

        # Build context for LLM reasoning
        context = f"""
        Current HVAC situation:
        - Room temperature: {current_temp}°F
        - Target temperature: {target_temp}°F
        - Temperature difference: {current_temp - target_temp:.1f}°F
        """

        if user_feedback:
            context += f"\n- User feedback: {user_feedback}"

        if comfort_history and len(comfort_history) > 0:
            recent_feedback = comfort_history[-5:]  # Last 5 feedback items
            feedback_summary = ", ".join([f["feedback"] for f in recent_feedback])
            context += f"\n- Recent feedback pattern: {feedback_summary}"

        prompt = f"""
        You are an intelligent HVAC comfort optimization system. Analyze the current situation and provide recommendations:

        {context}

        Based on this information, please:
        1. Analyze the comfort situation
        2. Suggest a temperature adjustment (in degrees F, can be negative)
        3. Explain your reasoning
        4. Rate the urgency (1-10) of making this adjustment

        Respond in JSON format:
        {{
            "analysis": "your analysis of the comfort situation",
            "suggested_adjustment": 0.0,
            "reasoning": "explanation of your recommendation", 
            "urgency": 5,
            "confidence": 0.8
        }}
        """

        try:
            request = BaseRequest(
                arguments={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,  # Lower temperature for more consistent reasoning
                    "max_tokens": 300,
                }
            )

            response = await self.llm.query(request)

            if response.success:
                # Try to parse JSON response
                import json

                try:
                    if response.content is None:
                        raise KeyError("Response content is None")
                    result = json.loads(response.content["choices"][0]["message"]["content"])
                    return result
                except (json.JSONDecodeError, KeyError):
                    # Fallback if JSON parsing fails
                    return {
                        "analysis": "LLM provided non-JSON response",
                        "suggested_adjustment": 0.0,
                        "reasoning": "Could not parse LLM response",
                        "urgency": 5,
                        "confidence": 0.3,
                    }
            else:
                return {"error": response.error, "suggested_adjustment": 0.0}

        except Exception as e:
            return {"error": str(e), "suggested_adjustment": 0.0}

    async def reason_about_energy_optimization(
        self, current_temp: float, target_temp: float, outdoor_temp: float, occupancy: bool, time_of_day: str = "afternoon"
    ) -> dict[str, Any]:
        """
        Use LLM to reason about energy optimization strategies.

        Args:
            current_temp: Current room temperature
            target_temp: Target temperature
            outdoor_temp: Outdoor temperature
            occupancy: Whether space is occupied
            time_of_day: Current time period

        Returns:
            Dict with energy optimization recommendations
        """
        if not self.llm:
            return {"error": "LLM not available", "energy_strategy": "standard"}

        prompt = f"""
        You are an energy optimization expert for HVAC systems. Analyze this situation:

        - Indoor temperature: {current_temp}°F
        - Target temperature: {target_temp}°F  
        - Outdoor temperature: {outdoor_temp}°F
        - Space occupied: {occupancy}
        - Time: {time_of_day}
        - Temperature difference from outdoor: {abs(current_temp - outdoor_temp):.1f}°F

        Provide energy optimization recommendations in JSON format:
        {{
            "energy_strategy": "aggressive_savings|moderate_savings|comfort_priority",
            "setpoint_adjustment": 0.0,
            "reasoning": "explanation of strategy",
            "estimated_savings": "percentage estimate",
            "comfort_impact": "minimal|moderate|significant"
        }}
        """

        try:
            request = BaseRequest(arguments={"messages": [{"role": "user", "content": prompt}], "temperature": 0.4, "max_tokens": 250})

            response = await self.llm.query(request)

            if response.success:
                import json

                try:
                    if response.content is None:
                        raise KeyError("Response content is None")
                    result = json.loads(response.content["choices"][0]["message"]["content"])
                    return result
                except (json.JSONDecodeError, KeyError):
                    return {
                        "energy_strategy": "standard",
                        "setpoint_adjustment": 0.0,
                        "reasoning": "Could not parse LLM response",
                        "estimated_savings": "unknown",
                        "comfort_impact": "minimal",
                    }
            else:
                return {"error": response.error, "energy_strategy": "standard"}

        except Exception as e:
            return {"error": str(e), "energy_strategy": "standard"}

    async def analyze_feedback_patterns(self, feedback_history: list) -> dict[str, Any]:
        """
        Use LLM to analyze patterns in user comfort feedback.

        Args:
            feedback_history: List of feedback entries with timestamps

        Returns:
            Dict with pattern analysis and recommendations
        """
        if not self.llm or not feedback_history:
            return {"patterns": [], "recommendations": []}

        # Summarize recent feedback for LLM analysis
        recent_feedback = feedback_history[-20:]  # Last 20 entries
        feedback_summary = []

        for entry in recent_feedback:
            feedback_summary.append(f"{entry.get('feedback', 'unknown')} at {entry.get('temp', '?')}°F")

        summary_text = "; ".join(feedback_summary)

        prompt = f"""
        Analyze this user comfort feedback history to identify patterns:

        Recent feedback: {summary_text}

        Identify patterns and provide recommendations in JSON format:
        {{
            "patterns": ["list of identified patterns"],
            "recommendations": ["list of actionable recommendations"], 
            "confidence": 0.8,
            "user_preference_temp_range": "estimated comfortable range"
        }}
        """

        try:
            request = BaseRequest(arguments={"messages": [{"role": "user", "content": prompt}], "temperature": 0.5, "max_tokens": 300})

            response = await self.llm.query(request)

            if response.success:
                import json

                try:
                    if response.content is None:
                        raise KeyError("Response content is None")
                    result = json.loads(response.content["choices"][0]["message"]["content"])
                    return result
                except (json.JSONDecodeError, KeyError):
                    return {
                        "patterns": ["Could not analyze patterns"],
                        "recommendations": ["Continue collecting feedback"],
                        "confidence": 0.3,
                        "user_preference_temp_range": "unknown",
                    }
            else:
                return {"patterns": [], "recommendations": []}

        except Exception:
            return {"patterns": [], "recommendations": []}


# Global LLM manager instance
llm_manager = HVACLLMManager()


async def initialize_llm_for_demo():
    """Initialize LLM for the demo. Call this at startup."""
    return await llm_manager.initialize()


def get_llm_manager() -> HVACLLMManager:
    """Get the global LLM manager instance."""
    return llm_manager
