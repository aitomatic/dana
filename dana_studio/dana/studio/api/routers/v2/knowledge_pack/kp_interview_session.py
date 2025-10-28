from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import logging
from pathlib import Path

from dana.studio.api.core.database import get_db
from dana.studio.api.core.schemas_v2 import (
    InterviewSessionCreate,
    InterviewSessionUpdate,
    InterviewSessionResponse,
    InterviewSessionListResponse,
    InterviewChatResponse,
    BaseMessage,
    InterviewProgressResponse,
    InterviewProgressData,
    TopicProgress,
    QuestionProgress,
)
from dana.studio.api.repositories import (
    get_interview_session_repo,
    get_conversation_repo,
    get_interview_template_repo,
    get_domain_knowledge_repo,
    AbstractInterviewSessionRepo,
    AbstractConversationRepo,
    AbstractInterviewTemplateRepo,
    get_document_repo,
)
from dana.studio.api.core.schemas import ConversationCreate
from dana.studio.api.services.extraction_service import get_extraction_service
from dana.lang.common.sys_resource.rag.rag_resource_v2 import RAGResourceV2
from dana.studio.api.repositories.config import KNOW_FOLDER_NAME
from dana.studio.api.core.schemas import ConversationWithMessages

from .common import KPConversationType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/session")


async def _initialize_rag_from_kp(kp_id: int, db: Session) -> RAGResourceV2 | None:
    """Initialize RAGResourceV2 from knowledge pack knows folder and associated documents."""
    kb_repo = get_domain_knowledge_repo()
    doc_repo = get_document_repo()
    extraction_service = get_extraction_service()

    # Collect all sources
    sources = []

    # 1. Add knows folder
    kp_folder = kb_repo.get_knowledge_pack_folder(kp_id)
    knows_dir = kp_folder / KNOW_FOLDER_NAME
    if knows_dir.exists():
        sources.append(str(knows_dir))

    # 2. Add associated document paths
    kp = await kb_repo.get_kp(kp_id=kp_id, db=db)
    metadata = kp.kp_metadata
    if not metadata:
        metadata = {}
    associated_documents = metadata.get("associated_documents", [])
    if associated_documents:
        documents = await doc_repo.get_document_by_ids(document_ids=associated_documents, db=db)
        for document in documents:
            # Get document file path
            doc_path = Path(extraction_service.base_upload_directory) / str(document.file_path)
            if doc_path.exists():
                sources.append(str(doc_path))

    if not sources:
        return None

    # Initialize RAG with all sources
    rag = RAGResourceV2(
        sources=sources,
        name=f"interview_rag_kp_{kp_id}",
        chunk_size=1024,
        chunk_overlap=256,
        num_results=15,
        reranking=True,
        debug=False,
    )
    await rag.initialize()
    return rag


async def _initialize_interview_session(session_id: int, template_path: str, session_dir: str, domain: str, role: str) -> tuple[str, str]:
    """
    Initialize interview session with note from template.

    Args:
        session_id: ID of the session
        template_path: Path to the template README.md file
        session_dir: Directory where session files will be stored
        domain: Domain for the interview
        role: Role for the interview

    Returns:
        Path to the initialized interview note
    """
    try:
        # Create session directory
        Path(session_dir).mkdir(parents=True, exist_ok=True)

        # Note: We're implementing the note initialization logic directly here
        note_path = f"{session_dir}/interview_notes.md"

        # Read template content
        with open(template_path, encoding="utf-8") as f:
            template_content = f.read()

        # Use LLM to generate intelligent note structure (similar to InterviewHandler logic)
        from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
        from dana.lang.common.types import BaseRequest
        from dana.lang.common.utils.misc import Misc
        from datetime import datetime

        llm = LLMResource()

        prompt = f"""You are an expert interview coordinator. Based on the provided interview template, create a structured interview note that will guide the knowledge-capture session.

INTERVIEW TEMPLATE:
{template_content}

Create a markdown interview note with the following structure:

```markdown
# Interview Notes - {domain}
**Date**: {datetime.now().strftime('%Y-%m-%d')}

## Interview Goal
[Extract and summarize the goal from the template]

## Topics to Cover
[For each topic in the template, create a section with:]

### [Topic Name]
**Background**: [Topic background from template]
**Status**: Not started
**Key Questions**: 
1. [First opening question from template]
2. [Second opening question from template]
3. [Third opening question from template]
[Continue with numbered list format for all questions]
**Listen for connections to**: [Connections from template]

**Expert Insights**  
*No insights captured yet*

**Current Understanding Level**  
- **Completeness**: 0 % – Interview just started  
- **Confidence**: Low  
- **Next Steps**: Begin with opening questions for this topic  

---

## Documents Found
*No documents searched yet*

## Relationship Exploration Prompts
[Include the relationship exploration prompts from template]

## Follow-up Framework
[Include the follow-up framework questions from template]

## Final Assessment
### Current Understanding Level
- **Overall Completeness**: [Aggregate completeness across topics]
- **Overall Confidence**: [Aggregate confidence]
- **Recommended Next Steps**: [Synthesize next actions]

### Expert Insight Summaries
[Concise roll-up of key insights gathered from each topic]  
```

CRITICAL FORMATTING REQUIREMENTS:
1. Extract all topics and their details from the template
2. For **Key Questions** sections, ALWAYS use numbered list format: "1. Question text"
3. Each question must be on its own line starting with a number and period
4. Preserve the interview approach and style from the template
5. Create a comprehensive but organized note structure
6. Use the exact wording from the template where appropriate
"""

        llm_request = BaseRequest(
            arguments={
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert interview coordinator who creates structured interview notes from templates.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": None,
            }
        )

        response = await llm.query(llm_request)
        note_content = Misc.get_response_content(response)

        # Clean up the response to ensure it's valid markdown
        if note_content.startswith("```markdown"):
            note_content = note_content[11:]
        if note_content.endswith("```"):
            note_content = note_content[:-3]

        note_content = note_content.strip()

        # Write note
        with open(note_path, "w") as f:
            f.write(note_content)

        logger.info(f"Initialized interview note at {note_path}")
        return note_path, note_content

    except Exception as e:
        logger.error(f"Failed to initialize interview session: {e}")
        # Create minimal note as fallback
        minimal_note = f"""# Interview Notes - {domain}
**Date**: {datetime.now().strftime('%Y-%m-%d')}

## Topics to Cover
*To be determined from conversation*

## Expert Insights
*No insights captured yet*

## Current Understanding Level
- **Completeness**: 0% - Interview just started
- **Confidence**: Low
- **Next Steps**: Begin with opening questions

## Documents Found
*No documents searched yet*
"""
        Path(session_dir).mkdir(parents=True, exist_ok=True)
        note_path = f"{session_dir}/interview_notes.md"
        with open(note_path, "w") as f:
            f.write(minimal_note)
        return note_path, minimal_note


@router.post("/create", response_model=InterviewSessionResponse)
async def create_interview_session(
    request: InterviewSessionCreate,
    session_repo: type[AbstractInterviewSessionRepo] = Depends(get_interview_session_repo),
    conv_repo: type[AbstractConversationRepo] = Depends(get_conversation_repo),
    template_repo: type[AbstractInterviewTemplateRepo] = Depends(get_interview_template_repo),
    db: Session = Depends(get_db),
):
    """
    Create a new interview session for a template.
    Automatically creates a conversation for the session and initializes the interview note.
    """
    try:
        # Create the session
        session = await session_repo.create_session(request, db=db)

        # Get template to access folder_path and metadata
        template = await template_repo.get_template(session.interview_template_id, db=db)
        if not template:
            return InterviewSessionResponse(success=False, message="Template not found", error="Template not found")

        # Create session directory path
        session_dir = f"{template.folder_path}/sessions/session_{session.id}"

        # Get template path (README.md)
        template_path = Path(template.folder_path) / "README.md"
        if not template_path.exists():
            return InterviewSessionResponse(success=False, message="Template file not found", error="Template README.md not found")

        # Initialize interview session with note
        domain = template.template_metadata.get("domain", "General")
        role = template.template_metadata.get("role", "Expert")

        note_path, note_content = await _initialize_interview_session(
            session_id=session.id, template_path=str(template_path), session_dir=session_dir, domain=domain, role=role
        )

        # Update session with folder_path
        await session_repo.update_session(session.id, InterviewSessionUpdate(folder_path=session_dir), db=db)

        # Create conversation for the session
        await conv_repo.create_conversation(
            conversation_data=ConversationCreate(
                title=f"Interview Session [{session.id}]",
                agent_id=None,
                kp_id=None,
                template_id=session.interview_template_id,
                session_id=session.id,
            ),
            messages=[],
            type=KPConversationType.INTERVIEW_SESSION.value,
            db=db,
        )

        logger.info(f"Created interview session {session.id} for template {request.interview_template_id} with note at {note_path}")

        # Get updated session with folder_path
        updated_session = await session_repo.get_session(session.id, db=db)
        if updated_session:
            updated_session.content = note_content

        return InterviewSessionResponse(success=True, message="Interview session created successfully", data=updated_session)
    except Exception as e:
        logger.error(f"Error creating interview session: {e}")
        return InterviewSessionResponse(success=False, message="Failed to create interview session", error=str(e))


@router.get("/{session_id}", response_model=InterviewSessionResponse)
async def get_interview_session(
    session_id: int,
    session_repo: type[AbstractInterviewSessionRepo] = Depends(get_interview_session_repo),
    db: Session = Depends(get_db),
):
    """
    Get a specific interview session by ID with interview note content.
    """
    try:
        session = await session_repo.get_session(session_id, db=db)
        if not session:
            return InterviewSessionResponse(success=False, message=f"Session {session_id} not found", error="Session not found")

        # Read interview note content if folder_path exists
        content = None
        if session.folder_path:
            note_path = Path(session.folder_path) / "interview_notes.md"
            if note_path.exists():
                try:
                    with open(note_path, encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read interview note at {note_path}: {e}")
                    content = f"Error reading interview note: {str(e)}"
            else:
                content = "Interview note not found"
        else:
            content = "Session folder not initialized"

        # Create session data with content
        session_dict = session.model_dump()
        session_dict["content"] = content

        # Create InterviewSessionRead object with the content field
        from dana.studio.api.core.schemas_v2 import InterviewSessionRead

        session_with_content = InterviewSessionRead(**session_dict)

        return InterviewSessionResponse(success=True, message="Session retrieved successfully", data=session_with_content)
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        return InterviewSessionResponse(success=False, message="Failed to retrieve session", error=str(e))


@router.get("/", response_model=InterviewSessionListResponse)
async def list_interview_sessions(
    template_id: int = Query(..., description="Template ID"),
    skip: int = Query(0, ge=0, description="Number of sessions to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of sessions to return"),
    session_repo: type[AbstractInterviewSessionRepo] = Depends(get_interview_session_repo),
    db: Session = Depends(get_db),
):
    """
    List interview sessions for a template.
    """
    try:
        return await session_repo.get_session_by_template_id(template_id, skip=skip, limit=limit, db=db)
    except Exception as e:
        logger.error(f"Error listing sessions for template {template_id}: {e}")
        return InterviewSessionListResponse(success=False, message="Failed to list sessions", data=[], total=0, error=str(e))


@router.put("/{session_id}", response_model=InterviewSessionResponse)
async def update_interview_session(
    session_id: int,
    request: InterviewSessionUpdate,
    session_repo: type[AbstractInterviewSessionRepo] = Depends(get_interview_session_repo),
    db: Session = Depends(get_db),
):
    """
    Update an interview session.
    """
    try:
        session = await session_repo.update_session(session_id, request, db=db)
        return InterviewSessionResponse(success=True, message="Session updated successfully", data=session)
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {e}")
        return InterviewSessionResponse(success=False, message="Failed to update session", error=str(e))


@router.delete("/{session_id}", response_model=InterviewSessionResponse)
async def delete_interview_session(
    session_id: int,
    session_repo: type[AbstractInterviewSessionRepo] = Depends(get_interview_session_repo),
    db: Session = Depends(get_db),
):
    """
    Delete an interview session.
    """
    try:
        await session_repo.delete_session(session_id, db=db)
        return InterviewSessionResponse(success=True, message="Session deleted successfully", data=None)
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        return InterviewSessionResponse(success=False, message="Failed to delete session", error=str(e))


@router.get("/{session_id}/conversation", response_model=ConversationWithMessages)
async def get_session_conversation(
    session_id: int,
    conv_repo: type[AbstractConversationRepo] = Depends(get_conversation_repo),
    db: Session = Depends(get_db),
):
    """
    Get the conversation for a specific interview session.
    """
    try:
        conversation = await conv_repo.get_conversation_by_session(session_id, db=db)

        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation for session {session_id} not found")

        # Filter out tool messages (treat_as_tool=True and require_user=False)
        filtered_messages = [message for message in conversation.messages if not (message.treat_as_tool and not message.require_user)]

        # Create a new conversation object with filtered messages

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

        return {"success": True, "message": "Conversation retrieved successfully", "data": conversation}
    except Exception as e:
        logger.error(f"Error getting conversation for session {session_id}: {e}")
        return {"success": False, "message": "Failed to retrieve conversation", "error": str(e)}


@router.post("/{session_id}/chat", response_model=InterviewChatResponse)
async def session_chat(
    session_id: int,
    request: BaseMessage,
    session_repo: type[AbstractInterviewSessionRepo] = Depends(get_interview_session_repo),
    template_repo: type[AbstractInterviewTemplateRepo] = Depends(get_interview_template_repo),
    conv_repo: type[AbstractConversationRepo] = Depends(get_conversation_repo),
    db: Session = Depends(get_db),
):
    """
    Chat endpoint for interview sessions using InterviewHandler.
    Matches template_finetune_chat pattern for consistent conversation management.
    """
    logger.info(f"🚀 Starting interview session chat for session {session_id}")
    try:
        # Get session
        logger.debug(f"Fetching session {session_id}")
        session = await session_repo.get_session(session_id, db=db)
        if not session:
            logger.error(f"❌ Session {session_id} not found")
            return InterviewChatResponse(
                success=False,
                interview_modified=False,
                agent_response=f"Session {session_id} not found",
                internal_conversation=[],
                error="Session not found",
            )

        # Get template
        logger.debug(f"Fetching template {session.interview_template_id} for session {session_id}")
        template = await template_repo.get_template(session.interview_template_id, db=db)
        if not template:
            logger.error(f"❌ Template {session.interview_template_id} not found for session {session_id}")
            return InterviewChatResponse(
                success=False,
                interview_modified=False,
                agent_response=f"Template {session.interview_template_id} not found",
                internal_conversation=[],
                error="Template not found",
            )

        logger.info(f"✅ Found session {session_id} (template_id: {session.interview_template_id})")

        # Get or create conversation with KPConversationType.INTERVIEW_SESSION
        logger.debug(f"Looking for existing conversation for session {session_id}")
        conversation = await conv_repo.get_conversation_by_session(session_id, db=db)
        if not conversation:
            logger.info(f"🆕 Creating new conversation for session {session_id}")
            from dana.studio.api.core.schemas import ConversationCreate

            conversation = await conv_repo.create_conversation(
                conversation_data=ConversationCreate(
                    title=f"Interview Session [{session_id}]",
                    agent_id=None,
                    kp_id=None,
                    template_id=session.interview_template_id,
                    session_id=session_id,
                ),
                messages=[request],
                type=KPConversationType.INTERVIEW_SESSION.value,
                db=db,
            )
            logger.info(f"✅ Created conversation {conversation.id} for session {session_id}")
        else:
            logger.info(f"📝 Continuing existing conversation {conversation.id} for session {session_id}")
            conversation = await conv_repo.add_messages_to_conversation(conversation_id=conversation.id, messages=[request], db=db)
            logger.info(f"✅ Added message to conversation {conversation.id}")

        # Get template path (README.md)
        template_path = Path(template.folder_path) / "README.md"
        logger.debug(f"Template file path: {template_path}")

        if not template_path.exists():
            logger.error(f"❌ Template file not found: {template_path}")
            return InterviewChatResponse(
                success=False,
                interview_modified=False,
                agent_response="Template file not found",
                internal_conversation=[],
                error="Template README.md not found",
            )

        # Initialize RAG from knowledge pack
        logger.debug(f"Initializing RAG for knowledge pack {template.kp_id}")
        rag_resource = await _initialize_rag_from_kp(template.kp_id, db)
        if not rag_resource:
            logger.error(f"❌ No knowledge documents found for KP {template.kp_id}")
            return InterviewChatResponse(
                success=False,
                interview_modified=False,
                agent_response="No knowledge documents found",
                internal_conversation=[],
                error="Knowledge pack has no documents",
            )

        # Create session directory
        session_dir = session.folder_path
        if not session_dir:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Build chat history for handler (convert from conversation messages to MessageData)
        from dana.studio.api.core.schemas import MessageData

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

        # Create IntentDetectionRequest for handler
        from dana.studio.api.core.schemas import IntentDetectionRequest

        intent_request = IntentDetectionRequest(
            user_message=request.content,
            chat_history=chat_history,
            current_domain_tree=None,
            agent_id=template.kp_id,  # Use kp_id, not session_id
        )

        # Initialize InterviewHandler
        logger.debug(f"Initializing InterviewHandler for session {session_id}")
        from dana.studio.api.services.knowledge_pack.interview_handler.interview_handler import InterviewHandler

        handler = InterviewHandler(
            session_dir=session_dir,
            template_path=str(template_path),
            response_generator=None,  # Not used in current implementation
            rag_resource=rag_resource,
            domain=template.template_metadata.get("domain", "General"),
            role=template.template_metadata.get("role", "Expert"),
        )

        logger.info(f"🚀 Starting InterviewHandler for session {session_id}")
        result = await handler.handle(intent_request)
        logger.info(f"✅ InterviewHandler completed for session {session_id}: status={result.get('status')}")

        # Extract new messages from result and add to conversation
        internal_conversation = result.get("conversation", [])
        logger.debug(f"Handler returned {len(internal_conversation)} messages")

        # Convert handler messages to MessageCreate format and add to conversation
        # Implement deduplication logic similar to template chat
        from dana.studio.api.core.schemas import MessageCreate

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

        # Update session status if workflow completed
        interview_modified = result.get("workflow_completed", False)
        if interview_modified:
            logger.info(f"🎯 Interview workflow completed for session {session_id}")
            await session_repo.update_session(session_id, InterviewSessionUpdate(status="completed"), db=db)

        # Convert MessageData to HandlerMessage for response
        # Use the deduplicated messages for the response
        from dana.studio.api.core.schemas_v2._conversation import HandlerMessage

        internal_conversation_response = [
            HandlerMessage(sender=msg.role, content=msg.content, require_user=msg.require_user, treat_as_tool=msg.treat_as_tool)
            for msg in internal_conversation[-len(new_messages) :]
            if new_messages
        ]

        # Log response details
        agent_response = result.get("message", "Interview processed successfully")
        logger.info(f"🎯 Interview session chat completed: interview_modified={interview_modified}, response_length={len(agent_response)}")

        return InterviewChatResponse(
            success=True,
            interview_modified=interview_modified,
            agent_response=agent_response,
            internal_conversation=internal_conversation_response,
            error=result.get("error", None),
        )

    except Exception as e:
        logger.error(f"❌ Error in interview session chat for session {session_id}: {e}")
        import traceback

        logger.error(f"📋 Full traceback: {traceback.format_exc()}")

        return InterviewChatResponse(
            success=False,
            interview_modified=False,
            agent_response="Failed to process interview chat request",
            internal_conversation=[],
            error=str(e),
        )


@router.get("/{session_id}/progress", response_model=InterviewProgressResponse)
async def get_session_progress(
    session_id: int,
    session_repo: type[AbstractInterviewSessionRepo] = Depends(get_interview_session_repo),
    db: Session = Depends(get_db),
):
    """
    Get interview progress by parsing interview_notes.md file.
    Returns topic-by-topic progress with status indicators.
    """
    logger.info(f"📊 Getting progress for session {session_id}")
    try:
        # Get session
        session = await session_repo.get_session(session_id, db=db)
        if not session:
            logger.error(f"❌ Session {session_id} not found")
            return InterviewProgressResponse(success=False, data=None, error="Session not found")

        if not session.folder_path:
            logger.error(f"❌ Session {session_id} has no folder_path")
            return InterviewProgressResponse(success=False, data=None, error="Session folder path not found")

        # Check if interview notes file exists
        note_path = Path(session.folder_path) / "interview_notes.md"
        if not note_path.exists():
            logger.warning(f"⚠️ Interview notes not found for session {session_id}")
            return InterviewProgressResponse(
                success=True, data=InterviewProgressData(topics=[], overall_completeness=0, current_topic=None), error=None
            )

        # Parse interview notes
        from dana.studio.api.services.knowledge_pack.interview_handler.utils import (
            parse_interview_note,
            analyze_question_status,
            infer_current_topic_from_conversation,
            get_interview_progress,
        )

        # Get conversation messages for question status analysis
        conversation_messages = []
        if session.conversation_id:
            try:
                from dana.studio.api.repositories import get_conversation_repo

                conv_repo = get_conversation_repo()
                conversation = await conv_repo.get_conversation(session.conversation_id, db=db)
                if conversation and conversation.messages:
                    conversation_messages = [
                        {
                            "role": msg.sender,
                            "content": msg.content,
                            "created_at": msg.created_at,
                            "sender": msg.sender,
                            "treat_as_tool": msg.treat_as_tool,
                            "require_user": msg.require_user,
                        }
                        for msg in conversation.messages
                    ]
            except Exception as e:
                logger.warning(f"⚠️ Could not load conversation for question analysis: {e}")

        logger.debug(f"📝 Parsing interview notes from: {note_path}")
        progress_dict = parse_interview_note(str(note_path))

        # Get current topic from notes (might be stale)
        note_current_topic = progress_dict.get("current_topic")

        # ALWAYS infer from conversation to get the most accurate current topic
        if conversation_messages:
            progress_data = get_interview_progress(progress_dict.get("topics", []), conversation_messages)
            return InterviewProgressResponse(success=True, data=progress_data, error=None)

            inferred_topic = infer_current_topic_from_conversation(progress_dict.get("topics", []), conversation_messages)

            # Prefer conversation inference over note status
            if inferred_topic:
                progress_dict["current_topic"] = inferred_topic
                logger.info(f"📍 Current topic from conversation: {inferred_topic}")
            elif note_current_topic:
                # Validate note's current topic is not completed
                topic_data = next((t for t in progress_dict.get("topics", []) if t["topic_name"] == note_current_topic), None)
                if topic_data and topic_data["status"] == "completed":
                    # Clear current topic if it's completed
                    progress_dict["current_topic"] = None
                    logger.info(f"⚠️ Cleared completed topic as current: {note_current_topic}")

        # Convert to Pydantic models with question status analysis
        topics = []
        for topic in progress_dict.get("topics", []):
            # Analyze question status
            if topic["topic_name"] == note_current_topic:
                print(topic)
            question_statuses = analyze_question_status(
                template_questions=topic.get("questions", []),
                conversation_messages=conversation_messages,
                current_topic_name=progress_dict.get("current_topic"),
            )

            # Convert to QuestionProgress objects
            questions = [
                QuestionProgress(question_text=q["question_text"], status=q["status"], asked_at=q["asked_at"]) for q in question_statuses
            ]

            topics.append(
                TopicProgress(
                    topic_name=topic["topic_name"],
                    status=topic["status"],
                    completeness=topic["completeness"],
                    insights_count=topic["insights_count"],
                    questions=questions,
                )
            )

        progress_data = InterviewProgressData(
            topics=topics,
            overall_completeness=progress_dict.get("overall_completeness", 0),
            current_topic=progress_dict.get("current_topic"),
        )

        logger.info(f"✅ Progress retrieved for session {session_id}: {len(topics)} topics, {progress_data.overall_completeness}% complete")

        return InterviewProgressResponse(success=True, data=progress_data, error=None)

    except Exception as e:
        logger.error(f"❌ Error getting progress for session {session_id}: {e}")
        import traceback

        logger.error(f"📋 Full traceback: {traceback.format_exc()}")

        return InterviewProgressResponse(success=False, data=None, error=str(e))
