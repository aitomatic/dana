from enum import Enum


class KPConversationType(Enum):
    STRUCTURING = "structuring"
    QUESTION_GENERATION = "question_generation"
    KNOWLEDGE_GENERATION = "knowledge_generation"
    SMART_CHAT = "smart_chat"
    TEMPLATE_FINETUNING = "template_finetuning"
    INTERVIEW_SESSION = "interview_session"
