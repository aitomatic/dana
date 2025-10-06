from aisuite.provider import Provider
import os
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from aisuite.framework import ChatCompletionResponse


class WatsonxProvider(Provider):
    def __init__(self, **config):
        self.service_url = config.get("service_url") or os.getenv("WATSONX_SERVICE_URL")
        self.api_key = config.get("api_key") or os.getenv("WATSONX_API_KEY")
        self.project_id = config.get("project_id") or os.getenv("WATSONX_PROJECT_ID")

        if not self.service_url or not self.api_key or not self.project_id:
            raise OSError(
                "Missing one or more required WatsonX environment variables: "
                "WATSONX_SERVICE_URL, WATSONX_API_KEY, WATSONX_PROJECT_ID. "
                "Please refer to the setup guide: /guides/watsonx.md."
            )

    def chat_completions_create(self, model, messages, **kwargs):
        model = ModelInference(
            model_id=model,
            credentials=Credentials(
                api_key=self.api_key,
                url=self.service_url,
            ),
            project_id=self.project_id,
        )

        res = model.chat(messages=messages, params=kwargs)
        return self.normalize_response(res)

    # def _extract_thinking_content(self, response):
    #     """
    #     Extract content between <think> tags if present and store it in reasoning_content.

    #     Args:
    #         response: The response object from the provider

    #     Returns:
    #         Modified response object
    #     """
    #     if hasattr(response, "choices") and response.choices:
    #         message = response.choices[0].message
    #         if hasattr(message, "content") and message.content:
    #             content = message.content.strip()
    #             if content.startswith("<think>") and "</think>" in content:
    #                 # Extract content between think tags
    #                 start_idx = len("<think>")
    #                 end_idx = content.find("</think>")
    #                 thinking_content = content[start_idx:end_idx].strip()

    #                 # Store the thinking content
    #                 message.reasoning_content = thinking_content

    #                 # Remove the think tags from the original content
    #                 message.content = content[end_idx + len("</think>") :].strip()

    #     return response

    def normalize_response(self, response):
        """
        Normalize WatsonX response to ChatCompletionResponse format.

        WatsonX response structure:
        {
            'id': 'chatcmpl-...',
            'object': 'chat.completion',
            'model_id': 'ibm/granite-3-8b-instruct',
            'model': 'ibm/granite-3-8b-instruct',
            'choices': [...],
            'created': 1759462546,
            'model_version': '1.1.0',
            'created_at': '2025-10-03T03:35:46.715Z',
            'usage': {'completion_tokens': 37, 'prompt_tokens': 172, 'total_tokens': 209},
            'system': {'warnings': [...]}
        }
        """
        # Create the normalized response
        openai_response = ChatCompletionResponse()

        # Map basic response fields
        openai_response.id = response.get("id")
        openai_response.object = response.get("object", "chat.completion")
        openai_response.created = response.get("created")
        openai_response.model = response.get("model")

        # Map usage statistics
        if "usage" in response:
            openai_response.usage = response["usage"]

        # Map system information if present
        if "system" in response:
            openai_response.system = response["system"]

        # Map additional WatsonX-specific fields
        if "model_id" in response:
            openai_response.model_id = response["model_id"]
        if "model_version" in response:
            openai_response.model_version = response["model_version"]
        if "created_at" in response:
            openai_response.created_at = response["created_at"]

        # Process choices - convert WatsonX choice format to framework format
        if "choices" in response:
            normalized_choices = []
            for choice in response["choices"]:
                normalized_choice = self._normalize_choice(choice)
                normalized_choices.append(normalized_choice)
            openai_response.choices = normalized_choices
        else:
            # Ensure we have at least one choice
            openai_response.choices = [self._create_empty_choice()]

        return openai_response

    def _normalize_choice(self, choice):
        """Normalize a single choice from WatsonX format to framework format."""
        from aisuite.framework.choice import Choice
        from aisuite.framework.message import Message

        normalized_choice = Choice()

        # Map finish_reason
        if "finish_reason" in choice:
            normalized_choice.finish_reason = choice["finish_reason"]

        # Map message
        if "message" in choice:
            message = choice["message"]
            normalized_message = Message(
                content=message.get("content"),
                role=message.get("role", "assistant"),
                tool_calls=message.get("tool_calls"),
                refusal=message.get("refusal"),
                reasoning_content=message.get("reasoning_content"),
            )
            normalized_choice.message = normalized_message

        # Map intermediate_messages if present
        if "intermediate_messages" in choice:
            intermediate_messages = []
            for msg in choice["intermediate_messages"]:
                intermediate_message = Message(
                    content=msg.get("content"),
                    role=msg.get("role", "assistant"),
                    tool_calls=msg.get("tool_calls"),
                    refusal=msg.get("refusal"),
                    reasoning_content=msg.get("reasoning_content"),
                )
                intermediate_messages.append(intermediate_message)
            normalized_choice.intermediate_messages = intermediate_messages

        return normalized_choice

    def _create_empty_choice(self):
        """Create an empty choice when no choices are provided."""
        from aisuite.framework.choice import Choice
        from aisuite.framework.message import Message

        choice = Choice()
        choice.message = Message(content="", role="assistant", tool_calls=None, refusal=None, reasoning_content=None)
        choice.finish_reason = "stop"
        return choice
