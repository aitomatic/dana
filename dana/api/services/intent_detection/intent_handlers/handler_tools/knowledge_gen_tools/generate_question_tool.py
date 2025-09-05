from dana.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseTool,
    BaseToolInformation,
    InputSchema,
    BaseArgument,
    ToolResult,
)
from dana.api.core.schemas import DomainKnowledgeTree
import logging
from dana.api.services.intent_detection.intent_handlers.handler_prompts.knowledge_gen_prompts import CHECK_EXISTING_KNOWLEDGE_PROMPT
from typing import override
from dana.common.sys_resource.rag import RAGResource
from dana.common.sys_resource.llm import LegacyLLMResource as LLMResource
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc

logger = logging.getLogger(__name__)


class CheckExistingKnowledgeTool(BaseTool):
    def __init__(self, 
                 rag_resource: RAGResource,
                 knowledge_path: str,
                 tree_structure: DomainKnowledgeTree | None = None, 
                 ):
        tool_info = BaseToolInformation(
            name="check_existing_knowledge",
            description="Check for existing knowledge",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="query",
                        type="string",
                        description="Specific knowledge areas that you want to check for",
                        example="How to install foreign body detection systems",
                    ),
                ],
                required=[],
            ),
        )
        super().__init__(tool_info)
        self.tree_structure = tree_structure
        self.knowledge_path = knowledge_path
        self.rag_resource = rag_resource or RAGResource(
            name="knowledge_rag",
            sources=[str(self.knowledge_path)],
        )
        self.llm_resource = LLMResource(
            name="knowledge_llm",
        )

    @override
    async def _execute(self, query: str = "") -> ToolResult:
        """
        Explore and discover knowledge areas in the domain tree.

        Returns: ToolResult with knowledge inventory and discovery results
        """
        result = await self.rag_resource.query(query)
        res = await self.llm_resource.query(
            BaseRequest(
                arguments={
                    "messages": [
                        {"role": "system", "content": "You are a domain-agnostic analyst. Answer only with information found in the provided context."},
                        {"role": "user", "content": CHECK_EXISTING_KNOWLEDGE_PROMPT.format(query=query, context=result)},
                    ],
                    "temperature": 0.1,
                }
            )
        )

        res_content = Misc.get_response_content(res)

        return ToolResult(
            name=self.tool_information.name,
            result=res_content,
            require_user=False,
        )
    

if __name__ == "__main__":
    import asyncio
    tool = CheckExistingKnowledgeTool(
        rag_resource=RAGResource(
            name="knowledge_rag",
            sources=["agents/agent_11_sofia/knows"],
            debug=True,
            reranking=True,
        ),
        knowledge_path="agents/agent_11_sofia/knows",
    )
    print(asyncio.run(tool._execute(query="What is the capital expenditure?")))