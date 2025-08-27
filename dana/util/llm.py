"""LLM utilities."""


from datetime import datetime
from typing import Optional

from dana.common.types import BaseRequest, BaseResponse


__all__ = [
    "from_prompts_to_request",
    "from_response_to_content",
]


DEFAULT_MAX_TOKENS: int = 8000  # DeepSeek-Chat


def get_current_local_context_info() -> str:
    """Get user's current local context."""
    return f"CURRENT DATE & TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z (%z)')}"


def from_prompts_to_request(*user_prompts: str, system_prompts: Optional[list[str]] = None) -> BaseRequest:
    """Convert a prompt to a request."""
    system_prompts: list[str] = system_prompts or []

    system_prompts.append(get_current_local_context_info())

    system_prompts: list[str] = [f"*** [SYSTEM MESSAGE #{i}] ***\n\n{system_prompt}\n\n\n\n"
                                 for i, system_prompt in enumerate(system_prompts)]

    return BaseRequest(arguments=dict(system_messages=system_prompts,
                                      user_messages=user_prompts,
                                      temperature=0, max_tokens=DEFAULT_MAX_TOKENS))


def from_response_to_content(response: BaseResponse) -> str:
    """Convert a response to content."""
    if response.success:
        try:
            return response.content['choices'][0]['message']['content']
        except Exception as e:
            raise ValueError(f"Failed to extract content from response: {response}") from e

    raise ValueError(f"LLM query failed due to: {response.error}")
