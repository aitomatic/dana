from pydantic import BaseModel


class AgentInfo(BaseModel):
    name: str
    description: str
    topic: str
    role: str
    memory_enabled: bool = False
