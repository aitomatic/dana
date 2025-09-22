from .domain_knowledge_repo import SQLDomainKnowledgeRepo, AbstractDomainKnowledgeRepo


def get_domain_knowledge_repo() -> type(AbstractDomainKnowledgeRepo):
    return SQLDomainKnowledgeRepo
