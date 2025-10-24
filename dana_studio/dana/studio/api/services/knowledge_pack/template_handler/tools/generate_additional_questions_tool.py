"""
GenerateAdditionalQuestionsTool for LLM-generated questions from knowledge summaries.
"""

from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.base_tool import (
    BaseArgument,
    BaseTool,
    BaseToolInformation,
    InputSchema,
    ToolResult,
)
from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.lang.common.types import BaseRequest
from dana.lang.common.utils.misc import Misc
from ..prompts import QUESTION_GENERATION_PROMPT
from dana.studio.api.repositories.config import KNOW_FOLDER_NAME
import json
import re
from pathlib import Path


class GenerateAdditionalQuestionsTool(BaseTool):
    """
    Tool for generating additional questions using knowledge summaries.
    """

    def __init__(
        self,
        template_path: str,
        knowledge_pack_path: str,
        domain: str = "General",
        role: str = "Domain Expert",
        llm: LLMResource = None,
        rag_knows=None,
        rag_docs=None,
    ):
        self.template_path = template_path
        self.knowledge_pack_path = knowledge_pack_path
        self.domain = domain
        self.role = role
        self.llm = llm or LLMResource()
        self.rag_knows = rag_knows
        self.rag_docs = rag_docs

        tool_info = BaseToolInformation(
            name="generate_additional_questions",
            description="Generate new questions for a topic based on knowledge summaries from the knowledge pack. Uses LLM to create contextually relevant questions.",
            input_schema=InputSchema(
                type="object",
                properties=[
                    BaseArgument(
                        name="topic_name",
                        type="string",
                        description="Name of the topic to generate questions for",
                        example="Data Collection and Performance Monitoring",
                    ),
                    BaseArgument(
                        name="focus_area",
                        type="string",
                        description="Specific area to focus the questions on (optional)",
                        example="Real-time analytics and predictive insights",
                    ),
                    BaseArgument(
                        name="num_questions",
                        type="integer",
                        description="Number of questions to generate (default: 3)",
                        example="5",
                    ),
                    BaseArgument(
                        name="document_ids",
                        type="array",
                        description="Optional: Specific document IDs to generate questions from (use list_documents to see available documents)",
                        example="[45, 67]",
                    ),
                ],
                required=["topic_name"],
            ),
        )
        super().__init__(tool_info)

    async def _execute(self, topic_name: str, focus_area: str = "", num_questions: int = 3, document_ids: list[int] = None, **kwargs) -> ToolResult:
        """
        Generate additional questions for a topic.
        """
        try:
            # Find knowledge summary for the topic (optional if documents provided)
            knowledge_summary = await self._find_knowledge_summary(topic_name, self.knowledge_pack_path)

            # If no summary and no documents, cannot proceed
            if not knowledge_summary and not document_ids:
                return ToolResult(
                    name="generate_additional_questions",
                    result=f"❌ No knowledge summary found for topic '{topic_name}' and no documents specified. Either provide document_ids or ensure knowledge generation has been completed for this topic.",
                    require_user=False,
                )

            # If no summary but documents provided, use placeholder (will rely on RAG from documents)
            if not knowledge_summary:
                knowledge_summary = "No knowledge summary available. Questions will be generated based on document content."

            # Retrieve relevant context from BOTH RAG resources IN PARALLEL
            import asyncio

            knows_context = ""
            docs_context = ""
            document_names = []

            # If document_ids provided, get document details for context
            if document_ids:
                try:
                    db = kwargs.get("db")
                    if db:
                        from dana.studio.api.repositories.document_repo import SQLDocumentRepo
                        documents = await SQLDocumentRepo.get_document_by_ids(
                            document_ids=document_ids, db=db
                        )
                        document_names = [doc.original_filename for doc in documents]
                except Exception as e:
                    print(f"Warning: Could not fetch document details: {e}")

            # Enhance query with document context if provided
            if document_ids:
                # If no knowledge summary, query needs to be more comprehensive
                if knowledge_summary == "No knowledge summary available. Questions will be generated based on document content.":
                    query = f"Extract key concepts, challenges, and best practices from the document about {topic_name}"
                    if focus_area:
                        query += f" specifically related to {focus_area}"
                    query += f". Provide detailed content suitable for generating interview questions."
                else:
                    # Normal query when knowledge summary exists
                    query = f"{topic_name} {focus_area} best practices interview questions"
                
                query += f" document_ids:{','.join(map(str, document_ids))}"
                if document_names:
                    query += f" from documents: {', '.join(document_names)}"
            else:
                query = f"{topic_name} {focus_area} best practices interview questions"

            # Query both RAG resources in parallel for better performance
            tasks = []
            if self.rag_knows:
                tasks.append(self.rag_knows.query(query))
            if self.rag_docs:
                tasks.append(self.rag_docs.query(query))

            # Execute queries in parallel
            if tasks:
                results = await asyncio.gather(*tasks)

                # Process results based on which RAGs are available
                result_idx = 0
                # Note: RAG query() returns formatted strings (not objects) since return_raw=False (default)
                
                if self.rag_knows:
                    knows_context = results[result_idx]  # Already a formatted string
                    result_idx += 1

                if self.rag_docs:
                    docs_context = results[result_idx]  # Already a formatted string

            # Generate questions using LLM with RAG context
            generated_questions = await self._generate_questions_from_summary(
                topic_name, knowledge_summary, focus_area, num_questions, self.domain, self.role, knows_context, docs_context, document_names
            )

            if not generated_questions:
                return ToolResult(
                    name="generate_additional_questions",
                    result="❌ Failed to generate questions from knowledge summary",
                    require_user=False,
                )

            # Format result
            content = self._format_generated_questions(topic_name, generated_questions, focus_area, document_names)

            return ToolResult(
                name="generate_additional_questions",
                result=content,
                require_user=True,  # Let user decide whether to use these questions
            )

        except Exception as e:
            return ToolResult(
                name="generate_additional_questions",
                result=f"❌ Error generating questions: {str(e)}",
                require_user=False,
            )

    async def _find_knowledge_summary(self, topic_name: str, knowledge_pack_path: str) -> str:
        """Find knowledge summary for the topic."""
        try:
            # Look for knowledge.json files in the knowledge pack
            knowledge_pack_dir = Path(knowledge_pack_path)
            knows_dir = knowledge_pack_dir / KNOW_FOLDER_NAME

            if not knows_dir.exists():
                return ""

            # Search for knowledge.json files
            knowledge_files = list(knowledge_pack_dir.rglob("knowledge.json"))

            for file_path in knowledge_files:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        knowledge_data = json.load(f)

                    # Check if this file has a summary and matches our topic
                    if "summary" in knowledge_data:
                        summary = knowledge_data["summary"]

                        # Try to match topic name (case-insensitive, flexible matching)
                        if self._topic_matches(topic_name, str(file_path), knowledge_data):
                            return summary

                except (json.JSONDecodeError, KeyError, OSError):
                    continue

            return ""

        except Exception as e:
            print(f"Error finding knowledge summary: {e}")
            return ""

    def _topic_matches(self, topic_name: str, file_path: str, knowledge_data: dict) -> bool:
        """Check if the knowledge file matches the topic."""
        # Simple matching based on file path and topic name
        topic_lower = topic_name.lower()
        path_lower = file_path.lower()

        # Check if topic name appears in the path
        if topic_lower in path_lower:
            return True

        # Check if we can match based on common patterns
        # This is a simple heuristic - could be improved
        return False

    async def _generate_questions_from_summary(
        self,
        topic_name: str,
        knowledge_summary: str,
        focus_area: str,
        num_questions: int,
        domain: str,
        role: str,
        knows_context: str = "",
        docs_context: str = "",
        document_names: list[str] = None,
    ) -> list[str]:
        """Generate questions using LLM based on knowledge summary."""
        try:
            # Build RAG context section
            rag_context_section = ""
            if knows_context or docs_context:
                rag_context_section = "Additional Context from Knowledge Sources:\n"
                if document_names:
                    rag_context_section += f"Focusing on specific documents: {', '.join(document_names)}\n\n"
                if knows_context:
                    rag_context_section += f"From Knowledge Pack:\n{knows_context}\n\n"
                if docs_context:
                    rag_context_section += f"From Documents:\n{docs_context}\n\n"
            else:
                rag_context_section = ""

            # Adjust prompt based on whether we have a real knowledge summary
            if knowledge_summary == "No knowledge summary available. Questions will be generated based on document content.":
                prompt_addition = "\n\nIMPORTANT: No knowledge summary is available. Generate questions based ENTIRELY on the document context provided above. Focus on extracting expert insights, best practices, challenges, and lessons learned from the document content."
            else:
                prompt_addition = ""

            # Create prompt
            prompt = QUESTION_GENERATION_PROMPT.format(
                role=role,
                domain=domain,
                topic_name=topic_name,
                focus_area=focus_area or "general aspects",
                knowledge_summary=knowledge_summary,
                rag_context_section=rag_context_section,
                num_questions=num_questions,
            ) + prompt_addition

            # Query LLM
            request = BaseRequest(
                arguments={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                }
            )

            response = await self.llm.query(request)
            content = Misc.get_response_content(response).strip()

            # Parse questions from response
            questions = self._parse_questions_from_response(content)
            return questions

        except Exception as e:
            print(f"Error generating questions: {e}")
            return []

    def _parse_questions_from_response(self, content: str) -> list[str]:
        """Parse questions from LLM response."""
        questions = []

        # Look for numbered questions
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            # Match patterns like "1. Question text" or "1) Question text"
            match = re.match(r"^\d+[.)]\s*(.+)$", line)
            if match:
                questions.append(match.group(1).strip())

        return questions

    def _format_generated_questions(self, topic_name: str, questions: list, focus_area: str, document_names: list[str] = None) -> str:
        """Format generated questions for display."""
        content_parts = []

        content_parts.append(f"## Generated Questions for: {topic_name}")
        content_parts.append("")

        if document_names:
            content_parts.append(f"**Based on Documents**: {', '.join(document_names)}")
            content_parts.append("")

        if focus_area:
            content_parts.append(f"**Focus Area**: {focus_area}")
            content_parts.append("")

        content_parts.append("**Generated Questions**:")
        for i, question in enumerate(questions, 1):
            content_parts.append(f"{i}. {question}")

        content_parts.append("")
        if document_names:
            content_parts.append("**These questions were generated based on the specified documents and knowledge summary.**")
        else:
            content_parts.append("**These questions were generated based on the knowledge summary for this topic.**")
        content_parts.append("**Would you like to add these to the template?**")

        return "\n".join(content_parts)
