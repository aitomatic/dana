from .domain_knowledge_repo import SQLDomainKnowledgeRepo, AbstractDomainKnowledgeRepo
from .conversation_repo import SQLConversationRepo, AbstractConversationRepo
from .background_task_repo import SQLBackgroundTaskRepo, AbstractBackgroundTaskRepo
from .document_repo import SQLDocumentRepo, AbstractDocumentRepo
from .interview_template_repo import SQLInterviewTemplateRepo, AbstractInterviewTemplateRepo


def get_domain_knowledge_repo() -> type(AbstractDomainKnowledgeRepo):
    return SQLDomainKnowledgeRepo


def get_conversation_repo() -> type(AbstractConversationRepo):
    return SQLConversationRepo


def get_background_task_repo() -> type(AbstractBackgroundTaskRepo):
    return SQLBackgroundTaskRepo


def get_document_repo() -> type(AbstractDocumentRepo):
    return SQLDocumentRepo


def get_interview_template_repo() -> type(AbstractInterviewTemplateRepo):
    return SQLInterviewTemplateRepo
