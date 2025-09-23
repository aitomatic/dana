from .domain_knowledge_repo import SQLDomainKnowledgeRepo, AbstractDomainKnowledgeRepo
from .conversation_repo import SQLConversationRepo, AbstractConversationRepo


def get_domain_knowledge_repo() -> type(AbstractDomainKnowledgeRepo):
    return SQLDomainKnowledgeRepo


def get_conversation_repo() -> type(AbstractConversationRepo):
    return SQLConversationRepo
