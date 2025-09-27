from pydantic import BaseModel, ConfigDict, Field, AliasChoices
from dana.api.core.schemas import SenderRole


class BaseModelUseEnum(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class BaseMessage(BaseModelUseEnum):
    sender: SenderRole = Field(default=SenderRole.USER, validation_alias=AliasChoices("role"))  # Allow both "sender" and "role" as aliases
    content: str


class HandlerMessage(BaseMessage):
    require_user: bool = False
    treat_as_tool: bool = False
    metadata: dict = {}


class BaseConversation(BaseModelUseEnum):
    messages: list[BaseMessage]


class HandlerConversation(BaseModelUseEnum):
    messages: list[HandlerMessage]


class KnowledgePackResponse(BaseModel):
    success: bool
    is_tree_modified: bool = False
    agent_response: str
    internal_conversation: list[HandlerMessage] = []
    error: str | None = None
