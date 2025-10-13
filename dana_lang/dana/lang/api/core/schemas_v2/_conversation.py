from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field, AliasChoices
from dana.lang.api.core.schemas import SenderRole


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
