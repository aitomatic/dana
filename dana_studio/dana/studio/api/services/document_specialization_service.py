"""
Document Specialization Service Module

Extracts specialization information from documents using LLM.
"""

import logging
import tempfile
from typing import Any

from dana.studio.api.core.schemas import Specialization
from dana.studio.api.services.llamaindex_extraction_service import LlamaIndexExtractionService
from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.lang.common.types import BaseRequest
from dana.lang.common.utils.misc import Misc

logger = logging.getLogger(__name__)

# Optimized prompt for extracting comprehensive specialization information
SPECIALIZATION_EXTRACTION_PROMPT = """
You are an expert in analyzing professional documents (CVs, résumés, job descriptions) to extract specialization information **without altering explicitly stated tasks**.

--------------------  INPUT  --------------------
{document_text}
-------------------------------------------------

**OUTPUT SPECIFICATION**

Return **only** the XML structure below—nothing else:

<specialization>
<domain>...</domain>
<role>...</role>
<task>
(list of tasks / responsibilities copied verbatim, each task is a line starting with bullet symbols –;  
internal line-breaks may be collapsed to spaces so each task reads as one logical line)
- Task 1
- Task 2
...
</task>
</specialization>

**EXTRACTION RULES**

1. **DOMAIN (Industry/Field)**
   • Identify the most prominent industry or field (e.g., “Software Engineering”, “Healthcare”).  
   • Base your choice on frequency, seniority, recency, and context.

2. **ROLE (Position/Title)**
   • Provide the specific job title, including seniority if present (“Senior Data Scientist”).  
   • When multiple roles appear, choose the most recent or primary one.

3. **TASK / RESPONSIBILITIES**
   • **If the document supplies an explicit task list:**  
     – Copy every clearly defined task **verbatim**.  
     – Keep original bullet symbols, punctuation, and capitalization.  
     – You **may** replace any newline characters **within a single bullet** with a single space (to avoid hard line breaks inside XML).  
     – Separate each bullet with either a newline or a semicolon—consistency within the list is sufficient.  
   • **If duties are vague or embedded in prose:**  
     – Infer **one** concise task description in your own words, beginning with an action verb.  
     – Clearly separate inferred wording from any direct quotes.
   • Do not remove technical jargon or abbreviations present in the original text.

**GENERAL GUIDELINES**

- Read the entire document to detect implicit vs. explicit information.  
- Favor recent experience / the described role itself over older history.  
- Use industry-standard terminology for DOMAIN and ROLE, but **never** modify explicit TASK wording beyond whitespace normalization.  
- If any element is truly unknown, output “N/A” for that element.

**STRICT FORMAT CHECK**

- Output must be valid XML.  
- No additional commentary, whitespace before the root tag, or code fences.
"""


class DocumentSpecializationService:
    """Service for extracting specialization information from documents."""

    def __init__(self):
        self.extraction_service = LlamaIndexExtractionService()
        self.llm_resource = LLMResource()

    async def parse_specialization_from_upload(self, file_content: bytes, filename: str) -> dict[str, Any]:
        """Parse specialization information from an uploaded file."""
        temp_file_path = None
        try:
            # Save file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            # Extract text
            extraction_result = await self.extraction_service.extract(temp_file_path)
            extracted_text = ""
            for page in extraction_result.file_object.pages:
                extracted_text += page.page_content + "\n"

            # Parse specialization using LLM
            specialization = await self._parse_specialization_with_llm(extracted_text)

            return {
                "success": bool(specialization),
                "specialization": specialization,
                "extracted_text": extracted_text,
                "error": None if specialization else "Failed to parse specialization",
            }

        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            return {"success": False, "specialization": None, "extracted_text": None, "error": str(e)}
        finally:
            # Clean up temporary file
            if temp_file_path:
                try:
                    import os

                    os.unlink(temp_file_path)
                except Exception:
                    pass

    async def _parse_specialization_with_llm(self, document_text: str) -> Specialization | None:
        """Parse specialization information using LLM."""
        try:
            # Truncate if too long
            if len(document_text) > 8000:
                document_text = document_text[:8000]

            # Use optimized prompt
            prompt = SPECIALIZATION_EXTRACTION_PROMPT.format(document_text=document_text)

            request = BaseRequest(arguments={"messages": [{"role": "user", "content": prompt}]})

            # Call LLM
            llm_response = await self.llm_resource.query(request)
            if not llm_response:
                return None

            content = Misc.get_response_content(llm_response)

            # Parse response
            return self._parse_llm_response(content)

        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return None

    def _parse_llm_response(self, llm_response: str) -> Specialization | None:
        """Parse the LLM response to extract specialization information using regex."""
        try:
            import re

            # Use regex to extract domain, role, and task from XML format
            domain_pattern = r"<domain>(.*?)</domain>"
            role_pattern = r"<role>(.*?)</role>"
            task_pattern = r"<task>(.*?)</task>"

            domain_match = re.search(domain_pattern, llm_response, re.DOTALL | re.IGNORECASE)
            role_match = re.search(role_pattern, llm_response, re.DOTALL | re.IGNORECASE)
            task_match = re.search(task_pattern, llm_response, re.DOTALL | re.IGNORECASE)

            if domain_match and role_match and task_match:
                domain_text = domain_match.group(1).strip()
                role_text = role_match.group(1).strip()
                task_text = task_match.group(1).strip()

                if domain_text and role_text and task_text:
                    return Specialization(domain=domain_text, role=role_text, task=task_text)

        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")

        return None
