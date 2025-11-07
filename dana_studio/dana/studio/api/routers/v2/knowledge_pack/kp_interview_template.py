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
from dana.studio.api.services.knowledge_pack.template_handler.template_finetune_handler import TemplateFinetuneHandler
from dana.studio.api.services.knowledge_pack.document_handler.document_exploration_handler import DocumentExplorationHandler
from dana.studio.api.repositories import get_document_repo
from dana.studio.api.services.extraction_service import get_extraction_service
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
        chat_history = [
            MessageData(
                role=message.sender,
                content=message.content,
                require_user=message.require_user,
                treat_as_tool=message.treat_as_tool,
            )
            for message in conversation.messages
            if message.require_user or not message.treat_as_tool
        ]
        logger.debug(f"Built chat history with {len(chat_history)} messages")

        # Initialize old_content for template diff computation (only used in editor mode)
        old_content = None

        if request.metadata.get("mode", "editor") == "editor":
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

            # Initialize TemplateFinetuneHandler
            logger.debug(f"Initializing TemplateFinetuneHandler for template {template_id}")
            handler = TemplateFinetuneHandler(
                template_path=str(template_file_path),
                knowledge_pack_path=knowledge_pack_path,
                kp_id=template.kp_id,
                doc_paths=None,  # TODO: Get document paths if available
                domain=spec.domain,
                role=spec.role,
                notifier=None,  # TODO: Add WebSocket notifier if available
            )

            # Store db session for tools that need it
            handler.db = db

            logger.info(f"🚀 Starting TemplateFinetuneHandler for template {template_id}")
            result = await handler.handle(intent_request)
            logger.info(f"✅ TemplateFinetuneHandler completed for template {template_id}: status={result.get('status')}")

            # Extract new messages from result and add to conversation
            internal_conversation = result.get("conversation", [])
            logger.debug(f"Handler returned {len(internal_conversation)} messages")
        else:
            # Use DocumentExplorationHandler for document exploration and Q&A
            logger.debug(f"Initializing DocumentExplorationHandler for template {template_id}")

            # Get document paths from knowledge pack metadata
            doc_repo = get_document_repo()
            extraction_service = get_extraction_service()
            kp_metadata = kb.kp_metadata or {}
            associated_documents = kp_metadata.get("associated_documents", [])
            doc_paths = []
            if associated_documents:
                documents = await doc_repo.get_document_by_ids(document_ids=associated_documents, db=db)
                for document in documents:
                    # Get document file path
                    doc_path = Path(extraction_service.base_upload_directory) / str(document.file_path)
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
