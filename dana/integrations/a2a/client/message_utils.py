import json

from python_a2a.models import Message


def extract_text_from_response(response: Message) -> str:
    """Extract text from response"""
    if response and hasattr(response, "content"):
        content_type = getattr(response.content, "type", None)

        if content_type == "text":
            return response.content.text
        elif content_type == "error":
            return f"Error: {response.content.message}"
        elif content_type == "function_response":
            return f"Function '{response.content.name}' returned: {json.dumps(response.content.response, indent=2)}"
        elif content_type == "function_call":
            params = {p.name: p.value for p in response.content.parameters}
            return f"Function call '{response.content.name}' with parameters: {json.dumps(params, indent=2)}"
        elif response.content is not None:
            return str(response.content)

    # If text extraction from standard format failed, check for Google A2A format
    if response:
        try:
            # Try to access parts directly
            google_format = response.to_google_a2a()
            if "parts" in google_format:
                for part in google_format["parts"]:
                    if part.get("type") == "text" and "text" in part:
                        return part["text"]
        except Exception:
            pass

    raise ValueError(f"No text response from response: {response}")
