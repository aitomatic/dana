from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.orm import Session
import shutil
import logging

from dana.studio.api.core.database import get_db
from dana.studio.api.core.schemas_v2 import (
    InterviewTemplateCreate,
    InterviewTemplateUpdate,
    InterviewTemplateResponse,
    InterviewTemplateListResponse,
    TemplateFinetuneChannelResponse,
    BaseMessage,
)
from dana.studio.api.core.schemas import MessageCreate, ConversationCreate, IntentDetectionRequest, MessageData
from dana.studio.api.repositories import (
    get_interview_template_repo,
    get_domain_knowledge_repo,
    get_conversation_repo,
    AbstractConversationRepo,
)
from dana.studio.api.repositories.interview_template_repo import AbstractInterviewTemplateRepo
from dana.studio.api.repositories.domain_knowledge_repo import AbstractDomainKnowledgeRepo
from dana.studio.api.services.knowledge_pack.template_handler.template_modification_handler import TemplateModificationHandler
from dana.studio.api.services.knowledge_pack.document_handler.document_exploration_handler import DocumentExplorationHandler
from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.lang.common.types import BaseRequest
from dana.lang.common.utils.misc import Misc
from dana.studio.api.repositories import get_document_repo
from enum import StrEnum


class ChatMode(StrEnum):
    EDITOR = "editor"
    CHAT = "chat"
    AUTO = "auto"


from .common import KPConversationType
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/template")


@router.post("/create", response_model=InterviewTemplateResponse)
async def create_interview_template(
    request: InterviewTemplateCreate,
    template_repo: type[AbstractInterviewTemplateRepo] = Depends(get_interview_template_repo),
    domain_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Create a new interview template for a knowledge pack.
    If source_template_id is provided, duplicates from that template.
    If source_template_id is None, duplicates from master template.
    """
    try:
        # Check if we should duplicate from existing template
        # Always duplicate when source_template_id is provided or None (use master)
        if True:  # Always use duplication logic for now
            # Use duplicate_template method
            template = await template_repo.duplicate_template(request, db=db)

            # Copy folder structure from source template
            if request.source_template_id is None:
                # Get master template to copy from
                source_template = await template_repo.get_template_by_kp_id(request.kp_id, is_master=True, db=db)
            else:
                # Get specific source template
                source_template = await template_repo.get_template(request.source_template_id, db=db)

            template_content = None
            if source_template:
                # Get source and destination folders
                source_folder = Path(source_template.folder_path)
                dest_folder = Path(template.folder_path)
                readme_file = dest_folder / "README.md"
                # Copy folder structure if source exists
                if source_folder.exists():
                    # Remove destination if it exists
                    if dest_folder.exists():
                        shutil.rmtree(dest_folder)
                    shutil.copytree(source_folder, dest_folder)

                    logger.info(f"Copied template folder from {source_folder} to {dest_folder}")
                else:
                    # Create basic folder structure if source doesn't exist
                    dest_folder.mkdir(parents=True, exist_ok=True)
                    readme_file = dest_folder / "README.md"
                    readme_file.write_text(
                        f"# {template.name}\n\n{template.description or 'Interview template'}\n\n*Template created on {template.created_at}*\n"
                    )
                if readme_file.exists():
                    template_content = readme_file.read_text()
                template.readme_content = template_content
        else:
            # Original behavior - create new template from scratch
            template = await template_repo.create_template(request, db=db)

            # Create folder structure
            template_folder = Path(request.folder_path)
            template_folder.mkdir(parents=True, exist_ok=True)

            # Create placeholder README.md
            readme_file = template_folder / "README.md"
            readme_file.write_text(
                f"# {request.name}\n\n{request.description or 'Interview template'}\n\n*Template created on {template.created_at}*\n"
            )

        logger.info(f"Created interview template {template.id} for KP {request.kp_id} at {template.folder_path}")

        return InterviewTemplateResponse(success=True, message="Interview template created successfully", data=template)
    except Exception as e:
        logger.error(f"Error creating interview template: {e}")
        return InterviewTemplateResponse(success=False, message="Failed to create interview template", error=str(e))


@router.get("/{template_id}", response_model=InterviewTemplateResponse)
async def get_interview_template(
    template_id: int,
    template_repo: type[AbstractInterviewTemplateRepo] = Depends(get_interview_template_repo),
    domain_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Get a specific interview template by ID.
    """
    try:
        template = await template_repo.get_template(template_id, db=db)
        if not template:
            return InterviewTemplateResponse(success=False, message=f"Template {template_id} not found", error="Template not found")

        # Read README.md content from template folder
        readme_content = None
        try:
            readme_file = Path(template.folder_path) / "README.md"

            if readme_file.exists():
                readme_content = readme_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not read README.md for template {template_id}: {e}")
            readme_content = None

        # Add readme_content to template data
        template_dict = template.__dict__.copy()
        template_dict["readme_content"] = readme_content

        # Create a new template object with readme_content
        from dana.studio.api.core.schemas_v2 import InterviewTemplateRead

        template_with_readme = InterviewTemplateRead(**template_dict)

        return InterviewTemplateResponse(success=True, message="Template retrieved successfully", data=template_with_readme)
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        return InterviewTemplateResponse(success=False, message="Failed to retrieve template", error=str(e))


@router.get("/", response_model=InterviewTemplateListResponse)
async def list_interview_templates(
    kp_id: int = Query(..., description="Knowledge pack ID"),
    skip: int = Query(0, ge=0, description="Number of templates to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of templates to return"),
    template_repo: type[AbstractInterviewTemplateRepo] = Depends(get_interview_template_repo),
    db: Session = Depends(get_db),
):
    """
    List interview templates for a knowledge pack.
    """
    try:
        return await template_repo.list_templates_by_kp(kp_id, skip=skip, limit=limit, db=db)
    except Exception as e:
        logger.error(f"Error listing templates for KP {kp_id}: {e}")
        return InterviewTemplateListResponse(success=False, message="Failed to list templates", data=[], total=0, error=str(e))


@router.get("/{template_id}/conversation")
async def get_template_conversation(
    template_id: int,
    conv_repo: type[AbstractConversationRepo] = Depends(get_conversation_repo),
    db: Session = Depends(get_db),
):
    """
    Get the template fine-tuning conversation for an interview template.
    Filters out messages where treat_as_tool=True and require_user=False.

    Args:
        template_id: Interview template ID
        conv_repo: Conversation repository
        db: Database session

    Returns:
        ConversationWithMessages or 404 if not found
    """
    try:
        conversation = await conv_repo.get_conversation_by_template_and_type(
            template_id=template_id, type=KPConversationType.TEMPLATE_FINETUNING.value, db=db
        )

        if not conversation:
            raise HTTPException(status_code=404, detail=f"Template fine-tuning conversation for template {template_id} not found")

        # Filter out tool messages (treat_as_tool=True and require_user=False)
        filtered_messages = [message for message in conversation.messages if not (message.treat_as_tool and not message.require_user)]

        # Create a new conversation object with filtered messages
        from dana.studio.api.core.schemas import ConversationWithMessages

        filtered_conversation = ConversationWithMessages(
            id=conversation.id,
            title=conversation.title,
            agent_id=conversation.agent_id,
            kp_id=conversation.kp_id,
            template_id=conversation.template_id,
            session_id=conversation.session_id,
            type=conversation.type,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=filtered_messages,
        )

        return filtered_conversation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template conversation for template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}", response_model=InterviewTemplateResponse)
async def update_interview_template(
    template_id: int,
    request: InterviewTemplateUpdate,
    template_repo: type[AbstractInterviewTemplateRepo] = Depends(get_interview_template_repo),
    domain_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Update an interview template.
    """
    try:
        # Get current template to check if name changed
        current_template = await template_repo.get_template(template_id, db=db)
        if not current_template:
            return InterviewTemplateResponse(success=False, message=f"Template {template_id} not found", error="Template not found")

        # Update database record
        updated_template = await template_repo.update_template(template_id, request, db=db)

        logger.info(f"Updated interview template {template_id}")

        return InterviewTemplateResponse(success=True, message="Interview template updated successfully", data=updated_template)
    except ValueError as e:
        logger.error(f"Bad request error updating template {template_id}: {e}")
        return InterviewTemplateResponse(success=False, message="Invalid request data", error=str(e))
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {e}")
        return InterviewTemplateResponse(success=False, message="Failed to update template", error=str(e))


@router.patch("/{template_id}/content", response_model=InterviewTemplateResponse)
async def update_template_content(
    template_id: int,
    readme_content: str = Body(..., embed=True),
    template_repo: type[AbstractInterviewTemplateRepo] = Depends(get_interview_template_repo),
    db: Session = Depends(get_db),
):
    """
    Update the README.md content of an interview template.

    Args:
        template_id: Template ID
        readme_content: New README markdown content

    Returns:
        Updated template with new readme_content
    """
    try:
        # Get template
        template = await template_repo.get_template(template_id, db=db)
        if not template:
            return InterviewTemplateResponse(success=False, message=f"Template {template_id} not found", error="Template not found")

        # Check if master template (cannot edit)
        if template.is_master:
            return InterviewTemplateResponse(
                success=False, message="Master template cannot be edited", error="Master templates are read-only"
            )

        # Write to README.md file
        readme_file = Path(template.folder_path) / "README.md"
        readme_file.parent.mkdir(parents=True, exist_ok=True)
        readme_file.write_text(readme_content, encoding="utf-8")

        # Return updated template with new content
        template_dict = template.__dict__.copy()
        template_dict["readme_content"] = readme_content

        from dana.studio.api.core.schemas_v2 import InterviewTemplateRead

        template_with_readme = InterviewTemplateRead(**template_dict)

        logger.info(f"Updated README for template {template_id}")

        return InterviewTemplateResponse(success=True, message="Template README updated successfully", data=template_with_readme)

    except Exception as e:
        logger.error(f"Error updating template {template_id} README: {e}")
        return InterviewTemplateResponse(success=False, message="Failed to update template README", error=str(e))


@router.get("/{template_id}/system-prompt")
async def get_template_system_prompt(
    template_id: int,
    template_repo: type[AbstractInterviewTemplateRepo] = Depends(get_interview_template_repo),
    db: Session = Depends(get_db),
):
    """
    Get the system prompt for an interview template.

    Args:
        template_id: Template ID
        template_repo: Template repository
        db: Database session

    Returns:
        System prompt content or empty string if not found
    """
    try:
        # Get template
        template = await template_repo.get_template(template_id, db=db)
        if not template:
            return {"success": False, "error": f"Template {template_id} not found", "system_prompt": ""}

        # Read system prompt file
        system_prompt_file = Path(template.folder_path) / "system_prompt.prompt"

        if system_prompt_file.exists():
            try:
                system_prompt = system_prompt_file.read_text(encoding="utf-8")
                return {"success": True, "system_prompt": system_prompt}
            except Exception as e:
                logger.warning(f"Could not read system prompt file for template {template_id}: {e}")
                return {"success": True, "system_prompt": ""}
        else:
            # Return empty string if file doesn't exist
            return {"success": True, "system_prompt": ""}

    except Exception as e:
        logger.error(f"Error getting system prompt for template {template_id}: {e}")
        return {"success": False, "error": str(e), "system_prompt": ""}


@router.patch("/{template_id}/system-prompt")
async def update_template_system_prompt(
    template_id: int,
    system_prompt: str = Body(..., embed=True),
    template_repo: type[AbstractInterviewTemplateRepo] = Depends(get_interview_template_repo),
    db: Session = Depends(get_db),
):
    """
    Update the system prompt for an interview template.

    Args:
        template_id: Template ID
        system_prompt: System prompt content
        template_repo: Template repository
        db: Database session

    Returns:
        Success response with updated system prompt
    """
    try:
        # Get template
        template = await template_repo.get_template(template_id, db=db)
        if not template:
            return {"success": False, "error": f"Template {template_id} not found", "system_prompt": ""}

        # Check if master template (cannot edit)
        if template.is_master:
            return {"success": False, "error": "Master template cannot be edited", "system_prompt": ""}

        # Write to system_prompt.prompt file
        system_prompt_file = Path(template.folder_path) / "system_prompt.prompt"
        system_prompt_file.parent.mkdir(parents=True, exist_ok=True)
        system_prompt_file.write_text(system_prompt, encoding="utf-8")

        logger.info(f"Updated system prompt for template {template_id}")

        return {"success": True, "system_prompt": system_prompt}

    except Exception as e:
        logger.error(f"Error updating system prompt for template {template_id}: {e}")
        return {"success": False, "error": str(e), "system_prompt": ""}


async def legacy_chat(chat_history: list[MessageData]):
    from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
    from dana.lang.common.types import BaseRequest
    from dana.lang.common.utils import Misc
    from dana.studio.api.core.schemas_v2 import SenderRole

    llm = LegacyLLMResource()

    messages = [{"role": message.role, "content": message.content} for message in chat_history]
    llm_request = BaseRequest(
        arguments={
            "messages": [
                {
                    "role": "system",
                    "content": """
                You are ChatGPT, a large language model based on the GPT-5 model and trained by OpenAI. Knowledge cutoff: 2024-06 Current date: 2025-08-08

                Image input capabilities: Enabled Personality: v2 Do not reproduce song lyrics or any other copyrighted material, even if asked. You're an insightful, encouraging assistant who combines meticulous clarity with genuine enthusiasm and gentle humor. Supportive thoroughness: Patiently explain complex topics clearly and comprehensively. Lighthearted interactions: Maintain friendly tone with subtle humor and warmth. Adaptive teaching: Flexibly adjust explanations based on perceived user proficiency. Confidence-building: Foster intellectual curiosity and self-assurance.

                Do not end with opt-in questions or hedging closers. Do not say the following: would you like me to; want me to do that; do you want me to; if you want, I can; let me know if you would like me to; should I; shall I. Ask at most one necessary clarifying question at the start, not the end. If the next step is obvious, do it. Example of bad: I can write playful examples. would you like me to? Example of good: Here are three playful examples:.. ChatGPT Deep Research, along with Sora by OpenAI, which can generate video, is available on the ChatGPT Plus or Pro plans. If the user asks about the GPT-4.5, o3, or o4-mini models, inform them that logged-in users can use GPT-4.5, o4-mini, and o3 with the ChatGPT Plus or Pro plans. GPT-4.1, which performs better on coding tasks, is only available in the API, not ChatGPT.
                Always respond in markdown format but inside <response> tags.
            """,
                }
            ]
            + messages,
            "temperature": 0.1,
        }
    )

    response = await llm.query(llm_request)
    content = Misc.get_response_content(response)
    internal_conversation = [MessageData(role=SenderRole.ASSISTANT, content=content)]
    result = {
        "status": "success",
        "message": content,
        "conversation": internal_conversation,
        "template_modified": False,
        "error": None,
    }
    return result


# Mode detection prompt with conversational continuity and content state awareness
MODE_DETECTION_PROMPT = """
You are part of a system that helps users create and modify interview templates.

CONTEXT:
- Chat box on the left for discussion and collaborative drafting
- Template on the right for viewing/editing (the actual file)
- Content in CHAT is DRAFT/WORK-IN-PROGRESS
- Content in TEMPLATE is COMMITTED/SAVED

MODES:
1. CHAT mode: Collaborative drafting, brainstorming, refining ideas
   - User is exploring, asking questions, working on drafts
   - Content is NOT yet applied to template (still in chat)
   - LLM provides suggestions, refinements, alternatives
   - Modifications to recent chat content stay in CHAT
   
2. EDITOR mode: Direct template file modification
   - User explicitly wants to apply/commit changes to the template FILE
   - Changes are immediately written to the actual template
   - Should only trigger when user clearly references the template itself

CRITICAL DECISION LOGIC:

**Decision Tree (Use First):**
1. Does it say "give me", "show me", "provide me", "generate for me"? → CHAT
2. Does it say "apply the steps", "follow the steps", "execute the process", "run the workflow", "apply a process"? → CHAT
3. Does it say "apply to template", "save to template", "update the template", "modify the template", "write to template"? → EDITOR
4. Does it say "apply changes", "apply these", "apply this"? → Check context:
   - If referring to template file ("apply these changes to the template") → EDITOR
   - If referring to process/steps ("apply these steps") → CHAT
5. If still unclear → Default to CHAT (safer)

**"Apply Steps" vs "Apply Changes" Distinction (CRITICAL):**
- "apply the steps" / "apply a process" / "follow the steps" / "execute the process" = CHAT
  → User wants to see generated content from following a process/workflow
  → Examples: "apply the steps to give me...", "follow the process and show me...", "execute the workflow to generate..."
- "apply changes to template" / "apply to template" / "apply these to template" = EDITOR
  → User wants to commit/write changes to the template file
  → Examples: "apply these changes to the template", "apply this to the template", "update the template with this"

**Content State Awareness:**
- If assistant just provided content in chat AND user wants to modify it → CHAT mode (refining draft)
- If content is already in template AND user wants to modify it → EDITOR mode (editing file)
- If unclear whether content is committed → Default to CHAT (safer)

**Workflow Context:**
- If previous messages show collaborative drafting → Default to CHAT
- If user says "yes/proceed" in response to a refinement offer → Stay in CHAT
- If user says "yes/proceed" in response to "should I apply to template?" → EDITOR
- If previous mode was CHAT and message is ambiguous → Stay in CHAT

**Modification Commands Context-Dependent:**
- "Remove section 5" AFTER assistant provided content in chat → CHAT (refining draft)
- "Remove section 5 from the template" → EDITOR (explicit template reference)
- "Change question 3" without template reference AND still drafting → CHAT
- "Change question 3 in the template" → EDITOR (explicit template reference)

Explicit EDITOR signals (must reference template OR show intent to commit):
- "add this to the template"
- "apply these changes to the template"
- "update the template with this"
- "commit these questions"
- "save to template"
- "replace the template content"
- "write this to the template"
- "modify the template"
- "update the actual template"
- Direct modification commands AFTER user confirmed "apply to template"

Explicit CHAT signals:
- "let's refine these"
- "give me a better version"
- "reassess these questions"
- "what do you think about..."
- "help me improve..."
- "show me alternatives"
- "give me the refined version"
- "review the template" (exploring, not modifying)
- Modification requests on content just provided in chat
- "apply the steps and give me..."
- "follow the steps to generate..."
- "execute the process and show me..."
- "review and apply [steps/process] to give me..."
- "apply the steps in [X] to give me..."
- "follow the process to create..."
- "run the workflow to generate..."
- "execute the workflow and provide..."
- Any request that says "give me", "show me", "provide me", "generate for me" (user wants to see content first)

AMBIGUOUS cases (default to CHAT to preserve continuity and prevent accidental template changes):
- Simple affirmations: "yes", "ok", "proceed", "continue", "sure"
- Follow-up questions: "what about...", "how can we..."
- Requests for more: "give me more", "show me alternatives"
- Vague references: "use that", "do it", "go ahead"
- Modification commands without explicit template reference: "remove section 5", "change this", "add more detail"

IMPORTANT: 
- **CHAT is the safe default** - prevents accidental template overwrites
- If the conversation shows ongoing collaborative work, prefer CHAT mode
- Only switch to EDITOR when user EXPLICITLY asks to modify the template FILE
- When in doubt about "yes/proceed" responses, stay in current mode (prefer CHAT)
- Conversational continuity is key - abrupt mode switches break workflow
- **If assistant just provided content, assume modifications are refining that content (CHAT)**

<examples>
Conversation:
User: "Help me create better safety questions"
Assistant: [provides draft questions in chat]
User: "Reassess those questions"
Assistant: [provides assessment, asks "Would you like me to proceed with rewriting?"]
User: "Yes"
→ Mode: CHAT
Reasoning: "Yes" is a continuation of drafting workflow, not an explicit template modification request. User is still collaborating.

Conversation:
User: "Give me the refined version"
Assistant: [provides refined questions in chat]
User: "Add these to the template"
→ Mode: EDITOR
Reasoning: "Add these to the template" is a clear signal to apply changes to the actual template.

Conversation:
User: "Review the template and apply the steps and give me the enhanced set of questions"
Assistant: [provides enhanced questions in chat]
User: "Remove section 5"
→ Mode: CHAT
Reasoning: Assistant just provided content in chat. User wants to refine the draft by removing section 5. No explicit "apply to template" signal. Still in collaborative drafting phase.

Conversation:
User: "Review the template and apply the steps and give me the enhanced set of questions"
Assistant: [provides enhanced questions in chat]
User: "Perfect! Remove section 5 and add this to the template"
→ Mode: EDITOR
Reasoning: User explicitly says "add this to the template", indicating they want to commit the changes.

Conversation:
User: "Change question 3 in the Safety topic to ask about PPE"
Previous mode: No previous chat context (first message)
→ Mode: EDITOR
Reasoning: User wants immediate template edit with specific location reference, not collaborative drafting.

Conversation:
User: "Change question 3 to ask about PPE"
Previous mode: CHAT (just provided draft questions)
→ Mode: CHAT
Reasoning: Still refining the draft that was just provided. No explicit template reference.

Conversation:
Previous mode: CHAT
User: "Proceed"
→ Mode: CHAT
Reasoning: Ambiguous affirmation with no explicit template modification signal. Maintain continuity with previous CHAT mode.

Conversation:
User: "What documents are available?"
→ Mode: CHAT
Reasoning: User wants to explore documents, not modify template.

Conversation:
User: "Update section 2 with the refined questions"
Assistant: [provides refined section 2 in chat]
User: "Good, now save it"
→ Mode: EDITOR
Reasoning: "Save it" after refinement indicates user wants to commit to template.

Conversation:
Assistant: "Here are the revised questions. Would you like me to apply these to the template?"
User: "Yes"
→ Mode: EDITOR
Reasoning: User affirming explicit question about applying to template.

Conversation:
User: "Review the questions in the template and follow and apply the steps in the system prompt to give me an advanced set of enhanced questions"
Previous mode: No previous chat context (first message)
→ Mode: CHAT
Reasoning: User says "apply the steps" (referring to a process) and "give me" (wants to see content). This is clearly a request to execute a process and show results, not to commit changes to template. The phrase "apply the steps" means "follow/execute the steps", not "apply changes to template".

Conversation:
User: "Review the template and apply the steps to generate enhanced questions"
Previous mode: No previous chat context (first message)
→ Mode: CHAT
Reasoning: "apply the steps" refers to executing a process/workflow, and "generate" indicates user wants to see the output. No explicit "apply to template" or "save to template" signal.

Conversation:
User: "Apply the steps in the system prompt and show me the results"
→ Mode: CHAT
Reasoning: "Apply the steps" = execute process, "show me" = wants to see content. This is process execution, not template modification.

Conversation:
User: "Follow the process outlined in the prompt to give me better questions"
→ Mode: CHAT
Reasoning: "Follow the process" = execute workflow, "give me" = wants to see content. No template modification intent.

Conversation:
User: "Execute the workflow and apply these changes to the template"
→ Mode: EDITOR
Reasoning: "Apply these changes to the template" is explicit template modification signal, even though it starts with "execute the workflow".
</examples>

Respond with JSON:
{
    "reasoning": "Brief explanation considering: 1) Was content just provided in chat? 2) Is this refining a draft or modifying the template file? 3) Are there explicit template references? 4) Workflow continuity",
    "mode": "editor" | "chat"
}
"""


async def detect_chat_mode(
    user_message: str,
    chat_history: list[MessageData] | None = None,
    llm: LLMResource | None = None,
    previous_mode: ChatMode | None = None,
) -> str:
    """
    Detect if user wants editor mode (template modification) or chat mode (document exploration).
    Uses conversational context and previous mode to maintain workflow continuity.

    Args:
        user_message: The current user message
        chat_history: Optional chat history for context
        llm: Optional LLM resource (creates new one if not provided)

    Returns:
        "editor" or "chat"
    """
    try:
        if llm is None:
            llm = LLMResource()

        # Build messages for mode detection
        messages = [{"role": "system", "content": MODE_DETECTION_PROMPT}]

        conversation_texts = []

        # Add recent chat history for context (last 6 messages for better workflow understanding)
        if chat_history:
            recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history
            for msg in recent_history:
                conversation_texts.append(f"{msg.role}: {msg.content}")

        # Add current user message
        conversation_texts.append(f"user: {user_message}")

        # Build prompt with previous mode context
        mode_context = f"Previous mode: {previous_mode}\n\n" if previous_mode else ""
        prompt_content = f"{mode_context}Choose the mode based on the following conversation:\n\n" + "\n---\n".join(conversation_texts)

        messages.append({"role": "user", "content": prompt_content})

        llm_request = BaseRequest(
            arguments={
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1000,  # Only need one word response
            }
        )

        response = await llm.query(llm_request)
        mode_response = Misc.get_response_content(response).strip().lower()
        print(f"🔍 Mode detection response: {mode_response}")

        try:
            mode = Misc.text_to_dict(mode_response).get("mode", ChatMode.CHAT)
        except Exception as _:
            mode = mode_response

        # Validate and normalize response
        if "editor" in mode:
            detected_mode = ChatMode.EDITOR
        elif "chat" in mode:
            detected_mode = ChatMode.CHAT
        else:
            # Default to CHAT if unclear (safer for continuity - prevents accidental template modifications)
            logger.warning(f"Unclear mode detection result: '{mode}', defaulting to 'chat'")
            detected_mode = ChatMode.CHAT

        logger.info(f"Mode detection: '{user_message[:50]}...' -> {detected_mode} (previous: {previous_mode})")
        return detected_mode

    except Exception as e:
        logger.error(f"Error detecting chat mode: {e}, defaulting to 'chat'")
        return ChatMode.CHAT  # Default to chat mode on error


@router.post("/{template_id}/chat", response_model=TemplateFinetuneChannelResponse)
async def template_finetune_chat(
    template_id: int,
    request: BaseMessage,
    template_repo: type[AbstractInterviewTemplateRepo] = Depends(get_interview_template_repo),
    conv_repo: type[AbstractConversationRepo] = Depends(get_conversation_repo),
    kb_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Chat endpoint for template fine-tuning.
    Allows conversational refinement of interview templates.
    """
    logger.info(f"🚀 Starting template fine-tune chat for template {template_id}")
    try:
        # Fetch template by template_id
        logger.debug(f"Fetching template {template_id}")
        template = await template_repo.get_template(template_id, db=db)
        if not template:
            logger.error(f"❌ Template {template_id} not found")
            return TemplateFinetuneChannelResponse(
                success=False,
                template_modified=False,
                agent_response=f"Template {template_id} not found",
                internal_conversation=[],
                error=f"Template {template_id} not found",
            )

        if template.is_master:
            logger.error(f"❌ Master template {template_id} cannot be fine-tuned")
            return TemplateFinetuneChannelResponse(
                success=False,
                template_modified=False,
                agent_response=f"Master template {template_id} cannot be fine-tuned",
                internal_conversation=[],
                error="Master template cannot be fine-tuned",
            )

        logger.info(f"✅ Found template {template_id} (kp_id: {template.kp_id})")

        # Fetch KP by template.kp_id
        logger.debug(f"Fetching knowledge pack {template.kp_id} for template {template_id}")
        kb = await kb_repo.get_kp(kp_id=template.kp_id, db=db)
        if kb is None:
            logger.error(f"❌ Knowledge pack {template.kp_id} not found for template {template_id}")
            return TemplateFinetuneChannelResponse(
                success=False,
                template_modified=False,
                agent_response=f"Knowledge pack {template.kp_id} not found",
                internal_conversation=[],
                error="Knowledge pack not found",
            )
        logger.info(f"✅ Found knowledge pack {template.kp_id}")

        # Get or create conversation with KPConversationType.TEMPLATE_FINETUNING
        logger.debug(f"Looking for existing conversation for template {template_id}")
        conversation = await conv_repo.get_conversation_by_template_and_type(
            template_id=template_id, type=KPConversationType.TEMPLATE_FINETUNING.value, db=db
        )
        if not conversation:
            logger.info(f"🆕 Creating new conversation for template {template_id}")
            conversation = await conv_repo.create_conversation(
                conversation_data=ConversationCreate(
                    title=f"Template fine-tuning [{template_id}]", agent_id=None, kp_id=template.kp_id, template_id=template_id
                ),
                messages=[request],
                type=KPConversationType.TEMPLATE_FINETUNING.value,
                db=db,
            )
            logger.info(f"✅ Created conversation {conversation.id} for template {template_id}")
        else:
            logger.info(f"📝 Continuing existing conversation {conversation.id} for template {template_id}")
            conversation = await conv_repo.add_messages_to_conversation(conversation_id=conversation.id, messages=[request], db=db)
            logger.info(f"✅ Added message to conversation {conversation.id}")

        # Build template path
        template_folder = Path(template.folder_path)
        template_file_path = template_folder / "README.md"
        logger.debug(f"Template file path: {template_file_path}")

        # Check if template file exists, if not create it
        if not template_file_path.exists():
            logger.info(f"📄 Creating placeholder template file at {template_file_path}")
            template_folder.mkdir(parents=True, exist_ok=True)
            template_file_path.write_text("# Interview Template\n\nThis is a placeholder template.\n")
            logger.info(f"✅ Created placeholder template file at {template_file_path}")
        else:
            logger.debug(f"📄 Using existing template file at {template_file_path}")

        # Build knowledge pack path
        knowledge_pack_path = str(kb_repo.get_knowledge_tree_path(template.kp_id).parent.absolute())
        logger.debug(f"Knowledge pack path: {knowledge_pack_path}")

        # Get specialization info
        spec = kb.get_specialization_info()
        logger.debug(f"Specialization: domain={spec.domain}, role={spec.role}")

        # Build chat history for handler (convert from conversation messages to MessageData)
        previous_mode = None
        chat_history = []
        for message in conversation.messages:
            if message.require_user or not message.treat_as_tool:
                chat_history.append(
                    MessageData(
                        role=message.sender,
                        content=message.content,
                        require_user=message.require_user,
                        treat_as_tool=message.treat_as_tool,
                        metadata=message.metadata if hasattr(message, "metadata") else {},
                    )
                )
            previous_mode = message.metadata.get("mode", ChatMode.CHAT)

        logger.debug(f"Built chat history with {len(chat_history)} messages")

        # Auto-detect mode from user message
        mode = request.metadata.get("mode", ChatMode.AUTO)
        if mode == ChatMode.AUTO:
            detected_mode = await detect_chat_mode(request.content, chat_history, previous_mode=previous_mode)
            print(f"🔍 Detected mode: {detected_mode} for template {template_id}")
        else:
            detected_mode = mode
            print(f"🔍 Using mode: {detected_mode} for template {template_id}")

        # Initialize old_content for template diff computation (only used in editor mode)
        old_content = None

        if detected_mode == ChatMode.EDITOR:
            # Create IntentDetectionRequest for handler
            intent_request = IntentDetectionRequest(
                user_message=request.content, chat_history=chat_history, current_domain_tree=None, agent_id=template.kp_id
            )

            # Read old content before modification
            try:
                old_content = template_file_path.read_text(encoding="utf-8")
                logger.debug(f"📄 Read old template content ({len(old_content)} chars)")
            except Exception as e:
                logger.warning(f"⚠️ Could not read old template content: {e}")
                old_content = ""

            # Initialize TemplateModificationHandler
            logger.debug(f"Initializing TemplateModificationHandler for template {template_id}")
            handler = TemplateModificationHandler(
                template_path=str(template_file_path),
                kp_id=template.kp_id,
                llm=None,  # Will use default LLMResource
                notifier=None,  # TODO: Add WebSocket notifier if available
            )

            # Store db session for tools that need it
            handler.db = db

            logger.info(f"🚀 Starting TemplateModificationHandler for template {template_id}")
            result = await handler.handle(intent_request)
            logger.info(f"✅ TemplateModificationHandler completed for template {template_id}: status={result.get('status')}")

            # Extract new messages from result and add to conversation
            internal_conversation = result.get("conversation", [])
            logger.debug(f"Handler returned {len(internal_conversation)} messages")
        else:
            # Use DocumentExplorationHandler for document exploration and Q&A
            logger.debug(f"Initializing DocumentExplorationHandler for template {template_id}")

            # Get document paths from knowledge pack metadata
            doc_repo = get_document_repo()
            kp_metadata = kb.kp_metadata or {}
            associated_documents = kp_metadata.get("associated_documents", [])
            doc_paths = []
            if associated_documents:
                documents = await doc_repo.get_document_by_ids(document_ids=associated_documents, db=db)
                for document in documents:
                    # Get document file path
                    doc_path = Path(str(document.file_path))
                    if doc_path.exists():
                        doc_paths.append(str(doc_path))

            logger.debug(f"Found {len(doc_paths)} document paths for knowledge pack {template.kp_id}")

            # Create IntentDetectionRequest for handler
            intent_request = IntentDetectionRequest(
                user_message=request.content, chat_history=chat_history, current_domain_tree=None, agent_id=template.kp_id
            )

            # Initialize DocumentExplorationHandler
            handler = DocumentExplorationHandler(
                kp_id=template.kp_id,
                doc_paths=doc_paths if doc_paths else None,
                template_path=str(template_file_path),
                domain=spec.domain,
                role=spec.role,
                notifier=None,  # TODO: Add WebSocket notifier if available
            )

            # Store db session for tools that need it
            handler.db = db

            logger.info(f"🚀 Starting DocumentExplorationHandler for template {template_id}")
            result = await handler.handle(intent_request)
            logger.info(f"✅ DocumentExplorationHandler completed for template {template_id}: status={result.get('status')}")

            # Extract new messages from result and add to conversation
            internal_conversation = result.get("conversation", [])
            logger.debug(f"DocumentExplorationHandler returned {len(internal_conversation)} messages")

        # Convert handler messages to MessageCreate format and add to conversation
        # Implement deduplication logic similar to knowledge_structuring_chat
        new_messages = []
        for message in reversed(internal_conversation):
            if (
                conversation.messages
                and message.role == conversation.messages[-1].sender
                and message.content == conversation.messages[-1].content
            ):
                break
            new_messages.append(
                MessageCreate(
                    sender=message.role,
                    content=message.content,
                    require_user=message.require_user,
                    treat_as_tool=message.treat_as_tool,
                    metadata={"mode": detected_mode},
                )
            )
        new_messages = new_messages[::-1]  # Reverse to get correct order

        if new_messages:
            logger.info(f"📝 Adding {len(new_messages)} new messages to conversation {conversation.id}")
            await conv_repo.add_messages_to_conversation(conversation_id=conversation.id, messages=new_messages, db=db)
            logger.info(f"✅ Successfully added messages to conversation {conversation.id}")
        else:
            logger.debug("No new messages to add to conversation")

        # Convert MessageData to HandlerMessage for response
        # Use the deduplicated messages for the response
        from dana.studio.api.core.schemas_v2._conversation import HandlerMessage

        internal_conversation_response = [
            HandlerMessage(
                sender=msg.role,
                content=msg.content,
                require_user=msg.require_user,
                treat_as_tool=msg.treat_as_tool,
            )
            for msg in internal_conversation[-len(new_messages) :]
            if new_messages
        ]

        # Log response details
        template_modified = result.get("template_modified", False)
        agent_response = result.get("message", "Template fine-tuning completed successfully.")
        logger.info(f"🎯 Template fine-tuning completed: modified={template_modified}, response_length={len(agent_response)}")

        # Compute diff if template was modified
        template_diff = None
        if template_modified:
            try:
                new_content = template_file_path.read_text(encoding="utf-8")
                logger.info(f"📄 Read new template content ({len(new_content)} chars)")
                logger.info(f"📊 Old content length: {len(old_content) if old_content else 0}")
                logger.info(f"📊 Contents are same: {old_content == new_content}")

                # Import diff computation utilities
                from dana.studio.api.core.schemas_v2._interview_template import TemplateDiff, TemplateDiffSection
                import difflib

                # Use difflib to compute line-based diff
                old_lines = old_content.splitlines(keepends=True) if old_content else []
                new_lines = new_content.splitlines(keepends=True)

                differ = difflib.Differ()
                diff_result = list(differ.compare(old_lines, new_lines))

                # Parse diff into sections
                sections = []
                current_section = None
                line_num = 0

                for line in diff_result:
                    if line.startswith("+ "):
                        # Addition
                        if current_section and current_section["type"] == "add":
                            current_section["content"] += line[2:]
                        else:
                            if current_section:
                                sections.append(TemplateDiffSection(**current_section))
                            current_section = {"type": "add", "content": line[2:], "line_start": line_num, "line_end": line_num}
                        line_num += 1
                    elif line.startswith("- "):
                        # Removal
                        if current_section and current_section["type"] == "remove":
                            current_section["content"] += line[2:]
                        else:
                            if current_section:
                                sections.append(TemplateDiffSection(**current_section))
                            current_section = {"type": "remove", "content": line[2:], "line_start": line_num, "line_end": line_num}
                    elif line.startswith("  "):
                        # Unchanged
                        if current_section and current_section["type"] == "unchanged":
                            current_section["content"] += line[2:]
                            current_section["line_end"] = line_num
                        else:
                            if current_section:
                                sections.append(TemplateDiffSection(**current_section))
                            current_section = {"type": "unchanged", "content": line[2:], "line_start": line_num, "line_end": line_num}
                        line_num += 1

                # Add last section
                if current_section:
                    sections.append(TemplateDiffSection(**current_section))

                template_diff = TemplateDiff(sections=sections, old_content=old_content, new_content=new_content)
                logger.info(f"✅ Computed template diff with {len(sections)} sections")

            except Exception as e:
                logger.error(f"❌ Error computing template diff: {e}")
                template_diff = None

        return TemplateFinetuneChannelResponse(
            success=True,
            template_modified=template_modified,
            agent_response=agent_response,
            internal_conversation=internal_conversation_response,
            template_diff=template_diff,
            error=result.get("error", None),
        )

    except Exception as e:
        logger.error(f"❌ Error in template fine-tune chat for template {template_id}: {e}")
        import traceback

        logger.error(f"📋 Full traceback: {traceback.format_exc()}")

        return TemplateFinetuneChannelResponse(
            success=False,
            template_modified=False,
            agent_response="Failed to process template fine-tuning request",
            internal_conversation=[],
            error=str(e),
        )


@router.get("/{template_id}/conversations")
async def list_template_conversations(
    template_id: int,
    template_repo: type[AbstractInterviewTemplateRepo] = Depends(get_interview_template_repo),
    conv_repo: type[AbstractConversationRepo] = Depends(get_conversation_repo),
    db: Session = Depends(get_db),
):
    """List all conversations for a template (multi-user support)."""
    try:
        # Verify template exists
        template = await template_repo.get_template(template_id, db=db)
        if not template:
            return {"success": False, "error": f"Template {template_id} not found", "conversations": []}

        # Get all conversations for this template
        conversations = await conv_repo.get_conversations_by_template(template_id=template_id, db=db)

        return {
            "success": True,
            "template_id": template_id,
            "conversations": [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "type": conv.type,
                    "message_count": len(conv.messages),
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                }
                for conv in conversations
            ],
        }
    except Exception as e:
        logger.error(f"Error listing conversations for template {template_id}: {e}")
        return {"success": False, "error": str(e), "conversations": []}


@router.delete("/{template_id}", response_model=InterviewTemplateResponse)
async def delete_interview_template(
    template_id: int,
    template_repo: type[AbstractInterviewTemplateRepo] = Depends(get_interview_template_repo),
    domain_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Delete an interview template and its folder.
    """
    try:
        # Get template info before deletion
        template = await template_repo.get_template(template_id, db=db)
        if not template:
            return InterviewTemplateResponse(success=False, message=f"Template {template_id} not found", error="Template not found")

        # Prevent deletion of master templates
        if template.is_master:
            return InterviewTemplateResponse(
                success=False, message="Master template cannot be deleted", error="Master templates are protected and cannot be deleted"
            )

        # Delete from database (cascades to sessions)
        await template_repo.delete_template(template_id, db=db)

        # Delete folder from filesystem
        template_folder = Path(template.folder_path)

        if template_folder.exists():
            shutil.rmtree(template_folder)
            logger.info(f"Deleted template folder: {template_folder}")

        logger.info(f"Deleted interview template {template_id} and its folder")

        return InterviewTemplateResponse(success=True, message=f"Interview template {template_id} deleted successfully")
    except ValueError as e:
        logger.error(f"Bad request error deleting template {template_id}: {e}")
        return InterviewTemplateResponse(success=False, message=str(e), error=str(e))
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {e}")
        return InterviewTemplateResponse(success=False, message="Failed to delete template", error=str(e))
