from fastapi import APIRouter, Depends, Query, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import logging
from pathlib import Path
from datetime import datetime
from collections import deque
import time
import asyncio
import re
from io import BytesIO
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
from dana.studio.api.services.knowledge_pack.interview_handler.converter import InterviewNoteProcessor, QuestionStatus
import json

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

        llm = LLMResource()

        prompt = f"""You are an expert interview coordinator. Based on the provided interview template, create a structured interview note that will guide the knowledge-capture session.

CRITICAL FILTERING RULES (MUST FOLLOW):
1. ONLY include topics that have explicit numbered questions (e.g., "1. Question text", "2. Another question")
2. EXCLUDE any topic that:
   - Has "[No specific opening questions provided...]" or similar placeholder text
   - Has only background information without numbered questions
   - Has empty or missing "Opening Questions" sections
   - Contains text like "[No specific opening questions provided in the template—prepare to probe based on background and relationship prompts.]"
3. You MUST verify each topic has at least ONE numbered question before including it
4. If a topic section has "Opening Questions:" followed by placeholder text or no actual numbered questions, EXCLUDE that topic entirely

INTERVIEW TEMPLATE:
{template_content}

STEP 1: First, identify which topics have explicit numbered questions.
For each topic in the template, check if it has numbered questions (format: "1. Question", "2. Question", etc.).
List your findings here:
- [Topic name 1]: [Number of questions found] - [INCLUDE/EXCLUDE with reason]
- [Topic name 2]: [Number of questions found] - [INCLUDE/EXCLUDE with reason]
...

STEP 2: Create the structured interview note for ONLY the topics you identified as having explicit numbered questions in STEP 1.

Create a markdown interview note with the following structure:

```markdown
# Interview Notes - {domain}
**Date**: {datetime.now().strftime('%Y-%m-%d')}

## Interview Goal
[Extract and summarize the goal from the template]

## Topics to Cover
[ONLY include topics that have explicit numbered questions. DO NOT include topics with placeholder text or no questions.]

### [Topic Name that contains questions]
**Background**: [Topic background from template]
**Status**: Not started
**Key Questions**: 
1. [First opening question from template]
2. [Second opening question from template]
3. [Third opening question from template]
[Continue with numbered list format for all questions from the template]

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
1. For **Key Questions** sections, ALWAYS use numbered list format: "1. Question text"
2. Each question must be on its own line starting with a number and period
3. Preserve the interview approach and style from the template
4. Create a comprehensive but organized note structure
5. Use the exact wording from the template where appropriate
6. DO NOT create placeholder questions - only use actual questions from the template

FINAL VERIFICATION:
Before returning your answer, confirm:
- Every topic under "## Topics to Cover" has at least one numbered question
- No topics with placeholder text like "[No specific opening questions provided...]" are included
- No topics with empty or missing questions are included
- If unsure about a topic, EXCLUDE it (better to have fewer topics than topics without questions)
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


@router.websocket("/ws/{session_id}")
async def interview_session_websocket(session_id: int, websocket: WebSocket):
    """WebSocket for real-time interview session updates"""
    from dana.studio.api.routers.v2.ws.domain_knowledge_ws import kp_interview_session_ws_notifier

    await kp_interview_session_ws_notifier.run_ws_loop_forever(websocket, str(session_id))


def _read_note_file(session_dir: str) -> str:
    """Read current interview note content"""
    note_path = Path(session_dir) / "interview_notes.md"
    if note_path.exists():
        try:
            with open(note_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to read note file: {e}")
            return ""
    return ""


async def _classify_user_intent(
    user_message: str,
    conversation_history: list,
    llm,
) -> dict:
    """
    Use LLM to classify user message intent.
    Returns: {
        "is_meta_question": bool,
        "is_information_sharing": bool,
        "intent": str,  # "meta_question" | "information_sharing" | "clarification"
        "confidence": float
    }
    """
    from dana.lang.common.types import BaseRequest
    from dana.lang.common.utils.misc import Misc

    # Build conversation context (last 5 messages)
    recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
    history_text = "\n".join([f"{msg.role}: {msg.content}" for msg in recent_history])

    prompt = f"""Classify the user's message intent in an interview context.

CONVERSATION HISTORY:
{history_text}

USER MESSAGE: {user_message}

Classify the user's intent into one of these categories:
1. **information_sharing**: User is sharing expertise, knowledge, experience, or answering questions about their domain
2. **meta_question**: User is asking about the interview process, progress, or how things work (e.g., "where are we?", "what's our progress?", "how does this work?")
3. **clarification**: User is asking for clarification about something previously discussed (e.g., "what do you mean by X?", "can you explain Y?")

Respond in JSON format:
{{
    "intent": "information_sharing" | "meta_question" | "clarification",
    "is_meta_question": boolean,
    "is_information_sharing": boolean,
    "confidence": float (0.0-1.0),
    "reasoning": "brief explanation"
}}"""

    llm_request = BaseRequest(
        arguments={
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at classifying user intent in interview conversations. Respond only with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 200,
        }
    )

    try:
        response = await llm.query(llm_request)
        content = Misc.get_response_content(response).strip()

        # Parse JSON response (remove markdown code blocks if present)
        if content.startswith("```"):
            parts = content.split("```")
            if len(parts) > 1:
                content = parts[1]
                if content.startswith("json"):
                    content = content[4:]
        content = content.strip()

        result = json.loads(content)
        return {
            "is_meta_question": result.get("is_meta_question", False),
            "is_information_sharing": result.get("is_information_sharing", False),
            "intent": result.get("intent", "information_sharing"),
            "confidence": result.get("confidence", 0.5),
            "reasoning": result.get("reasoning", ""),
        }
    except Exception as e:
        logger.warning(f"LLM intent classification failed: {e}, defaulting to information_sharing")
        # Default to information_sharing if classification fails
        return {
            "is_meta_question": False,
            "is_information_sharing": True,
            "intent": "information_sharing",
            "confidence": 0.5,
            "reasoning": "Classification failed, defaulting to information_sharing",
        }


async def _capture_notes_background(
    note_handler,
    request,
    current_note_content: str,
    session_id: int,
    session_dir: str,
):
    """Background task for note capture with WebSocket notification"""
    from dana.studio.api.routers.v2.ws.domain_knowledge_ws import kp_interview_session_ws_notifier

    try:
        result = await note_handler.handle(request, current_note_content=current_note_content)

        # Notify FE via WebSocket
        await kp_interview_session_ws_notifier.send_update_msg(
            websocket_id=str(session_id),
            message=json.dumps(
                {
                    "type": KPConversationType.INTERVIEW_SESSION.value,
                    "message": {
                        "tool_name": "note_capture",
                        "status": "finish",
                        "note_updated": result.get("note_updated", False),
                        "content": "Interview notes updated successfully",
                    },
                    "timestamp": datetime.now().timestamp(),
                }
            ),
        )
    except Exception as e:
        logger.error(f"Background note capture failed: {e}")
        # Notify FE of error
        await kp_interview_session_ws_notifier.send_update_msg(
            websocket_id=str(session_id),
            message=json.dumps(
                {
                    "type": KPConversationType.INTERVIEW_SESSION.value,
                    "message": {"tool_name": "note_capture", "status": "error", "error": str(e)},
                    "timestamp": datetime.now().timestamp(),
                }
            ),
        )


def _extract_question_info(message_content: str) -> dict[str, str] | None:
    """
    Extract question text and category from ask_question tool result.

    Returns:
        dict with 'question' and 'category' keys, or None if not an ask_question
    """
    import re

    # Check if this is an ask_question result
    if "<question>" not in message_content.lower() and "category:" not in message_content.lower():
        return None

    result = {}

    # Extract question (between <strong> tags or after "question" text)
    question_match = re.search(r"<strong>(.*?)</strong>", message_content, re.DOTALL)
    if not question_match:
        # Try alternative format
        question_match = re.search(r"<question>(.*?)</question>", message_content, re.DOTALL)
    if question_match:
        result["question"] = question_match.group(1).strip()

    # Extract category
    category_match = re.search(r"category:\s*(\w+)", message_content, re.IGNORECASE)
    if category_match:
        result["category"] = category_match.group(1).strip().lower()

    return result if result else None


def _find_last_interview_note_question_index(conversation_messages: list) -> int | None:
    """
    Find the index of the last interview_note question in conversation.

    Args:
        conversation_messages: List of conversation message objects

    Returns:
        Index of the last interview_note question message, or None if not found
    """
    for i in range(len(conversation_messages) - 1, -1, -1):
        msg = conversation_messages[i]
        if msg.sender == "assistant" and msg.require_user:
            question_info = _extract_question_info(msg.content)
            if question_info and question_info.get("category") == "interview_note":
                return i
    return None


def _find_relevant_messages(conversation_messages: list):
    index = _find_last_interview_note_question_index(conversation_messages)
    if index is not None:
        return conversation_messages[index:]
    return conversation_messages


def _find_last_interview_note_question_message(conversation_messages: list):
    """
    Find the last interview_note question message in conversation.

    Args:
        conversation_messages: List of conversation message objects

    Returns:
        The last interview_note question message object, or None if not found
    """
    for msg in reversed(conversation_messages):
        if msg.sender == "assistant" and msg.require_user:
            question_info = _extract_question_info(msg.content)
            if question_info and question_info.get("category") == "interview_note":
                return msg
    return None


def _has_more_questions(note_path: str) -> bool:
    """
    Check if there are more questions with not_asked status remaining.

    Args:
        note_path: Path to the interview_notes.md file

    Returns:
        True if there are more questions with not_asked status, False otherwise
    """
    try:
        processor = InterviewNoteProcessor()
        json_data = processor.from_file(note_path)

        # Check all topics for questions with not_asked status
        for topic in json_data.get("topics", []):
            questions = topic.get("key_questions", [])
            for question in questions:
                if isinstance(question, dict):
                    status = question.get("status", QuestionStatus.NOT_ASKED.value)
                    if status == QuestionStatus.NOT_ASKED.value:
                        return True
                else:
                    # String format question (backward compatibility) - treat as not_asked
                    if question.strip():
                        return True

        return False
    except Exception as e:
        logger.warning(f"Failed to check remaining questions: {e}")
        # On error, assume there might be more questions to be safe
        return True


def _enhance_progress_data_with_converter_statuses(progress_data: InterviewProgressData, note_path: str) -> InterviewProgressData:
    """
    Enhance InterviewProgressData with question statuses from InterviewNoteProcessor.

    Priority logic:
    - Prefer new status EXCEPT when it's 'not_asked' and old status is different
    - Convert new statuses to old format: asking/clarifying → being_asked, completed → answered

    Args:
        progress_data: InterviewProgressData from get_interview_progress (old approach)
        note_path: Path to the interview_notes.md file

    Returns:
        Enhanced InterviewProgressData with updated question statuses
    """
    try:
        processor = InterviewNoteProcessor()

        # Safeguard: Recalculate topic progress for all topics before reading progress data
        # This ensures topic status and completeness are up-to-date based on current question statuses
        for topic_progress in progress_data.topics:
            topic_name = topic_progress.topic_name
            try:
                processor.recalculate_topic_progress(topic_name, note_path)
                logger.debug(f"✅ Recalculated topic progress for '{topic_name}' as safeguard")
            except Exception as e:
                logger.warning(f"⚠️ Failed to recalculate topic progress for '{topic_name}' as safeguard: {e}")
                # Continue with other topics even if one fails

        new_json_data = processor.from_file(note_path)

        # Build question corpus for fuzzy matching
        from dana.studio.api.services.search.bm25 import BM25SearchEngine
        from dana.studio.api.services.knowledge_pack.interview_handler.utils import similarity_ratio

        topics_progresses = []

        # Process each topic in progress_data
        for topic_progress in progress_data.topics:
            topic_name = topic_progress.topic_name

            # Find matching topic in new structure
            matching_topic = None
            for new_topic in new_json_data.get("topics", []):
                if new_topic.get("topic_name") == topic_name:
                    matching_topic = new_topic
                    break

            if not matching_topic:
                continue

            topic_progress.completeness = matching_topic.get("current_understanding_level", {}).get(
                "completeness", topic_progress.completeness
            )

            topics_progresses.append(topic_progress.completeness)

            new_questions = matching_topic.get("key_questions", [])
            if not new_questions:
                continue

            # Build corpus of new question texts for matching
            new_question_texts = []
            new_question_map = {}  # text -> status

            for new_q in new_questions:
                if isinstance(new_q, dict):
                    q_text = new_q.get("text", new_q.get("question_text", ""))
                    q_status = new_q.get("status", QuestionStatus.NOT_ASKED.value)
                else:
                    q_text = str(new_q)
                    q_status = QuestionStatus.NOT_ASKED.value

                if q_text.strip():
                    new_question_texts.append(q_text)
                    new_question_map[q_text] = q_status

            if not new_question_texts:
                continue

            # Use BM25 for efficient matching
            search_engine = BM25SearchEngine(new_question_texts)

            # Match and update question statuses in progress_data
            for question_progress in topic_progress.questions:
                old_q_text = question_progress.question_text
                old_status = question_progress.status

                if not old_q_text or not old_q_text.strip():
                    continue

                # Try exact match first
                matched_new_status = None

                if old_q_text in new_question_map:
                    matched_new_status = new_question_map[old_q_text]
                else:
                    # Use BM25 + similarity for fuzzy matching
                    top_candidates = search_engine.get_top_n_indices(old_q_text, n=3)
                    best_similarity = 0.0

                    for idx in top_candidates:
                        candidate_text = new_question_texts[idx]
                        similarity = similarity_ratio(old_q_text, candidate_text)
                        if similarity > best_similarity and similarity > 0.7:  # Threshold for matching
                            best_similarity = similarity
                            matched_new_status = new_question_map[candidate_text]

                if matched_new_status:
                    # Apply priority logic
                    # Prefer new status EXCEPT when it's 'not_asked' and old status is different
                    if matched_new_status == QuestionStatus.NOT_ASKED.value and old_status != QuestionStatus.NOT_ASKED.value:
                        # Keep old status (trust conversation analysis over default)
                        continue

                    # Convert new statuses to old format
                    if matched_new_status in [QuestionStatus.ASKING.value, QuestionStatus.CLARIFYING.value]:
                        question_progress.status = QuestionStatus.BEING_ASKED.value
                    elif matched_new_status == QuestionStatus.COMPLETED.value:
                        question_progress.status = QuestionStatus.ANSWERED.value
                    else:
                        # For not_asked or other statuses, use as-is (already in old format)
                        question_progress.status = matched_new_status

                    logger.debug(f"✅ Updated question status: '{old_q_text[:50]}...' from '{old_status}' to '{question_progress.status}'")

        progress_data.overall_completeness = int(sum(topics_progresses) / len(topics_progresses))
        logger.debug("✅ Enhanced progress data with converter statuses")
        return progress_data

    except Exception as e:
        logger.warning(f"⚠️ Failed to enhance progress data with converter statuses: {e}")
        # Return original progress_data on error
        return progress_data


async def _precompute_document_answer_background(
    question_text: str,
    kp_id: int,
    rag_docs: RAGResourceV2,
    conversation_id: int,
    message_id: int,
):
    """
    Background task to precompute answer from documents.

    Steps:
    1. Query documents using ReadDocumentsTool
    2. Use LLM to generate answer from document results
    3. Store answer in message metadata

    Note: Creates its own database session since this runs in background.
    """
    from dana.studio.api.services.knowledge_pack.interview_question_handler.tools.read_documents_tool import ReadDocumentsTool
    from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
    from dana.lang.common.types import BaseRequest
    from dana.lang.common.utils.misc import Misc
    from dana.studio.api.core.database import get_db
    from dana.studio.api.core.models import Message

    try:
        logger.info(f"🔄 Starting document answer precomputation for question: {question_text[:100]}...")

        # Create new database session for background task
        db_gen = get_db()
        db = next(db_gen)

        try:
            # Create ReadDocumentsTool instance
            read_tool = ReadDocumentsTool(kp_id=kp_id, rag_docs=rag_docs)

            # Query documents
            tool_result = await read_tool.execute(query=question_text, db=db)
            document_results = tool_result.result

            if not document_results or "❌" in str(document_results):
                logger.warning(f"⚠️ No document results found for question: {question_text[:100]}")
                return

            # Use LLM to synthesize answer from document results
            llm = LLMResource()
            synthesis_prompt = f"""Based on the following document search results, provide a clear and concise answer to this question:

Question: {question_text}

Document Results:
{document_results}

Provide a synthesized answer based solely on the document content. Be concise and factual."""

            llm_request = BaseRequest(
                arguments={
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that synthesizes information from documents."},
                        {"role": "user", "content": synthesis_prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000,
                }
            )

            response = await llm.query(llm_request)
            document_answer = Misc.get_response_content(response).strip()

            logger.info(f"✅ Document answer precomputed: {document_answer[:100]}...")

            # Store answer in message metadata
            message_obj = db.query(Message).filter_by(id=message_id).first()
            if message_obj:
                # Get current metadata or initialize empty dict
                current_metadata = message_obj.msg_metadata or {}
                # Create new dict with document answer (SQLAlchemy JSON columns need new dict assignment)
                updated_metadata = {
                    **current_metadata,
                    "document_answer": document_answer,
                    "document_answer_computed_at": datetime.now().isoformat(),
                }
                # Assign back to msg_metadata
                message_obj.msg_metadata = updated_metadata
                db.commit()
                logger.info(f"✅ Stored document answer in message {message_id} metadata")
            else:
                logger.warning(f"⚠️ Message {message_id} not found for storing document answer")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ Error precomputing document answer: {e}", exc_info=True)


async def _update_expert_insights_background(
    topic_name: str,
    note_path: str,
    existing_insights: str,
    conversation_messages: list,
    domain: str,
    role: str,
) -> None:
    """
    Background task to update expert insights for a completed question.

    Steps:
    1. Read current markdown content
    2. Extract existing expert insights for the topic
    3. Use LLM to analyze conversation_messages and extract new insights
    4. Merge existing insights with new insights (preserve existing, add new)
    5. Update markdown file with updated insights

    Args:
        topic_name: Name of the topic to update
        note_path: Path to interview_notes.md
        existing_insights: Current expert insights text from markdown
        conversation_messages: List of Message objects from conversation
        domain: Domain name for context
        role: Role name for context
    """
    from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
    from dana.lang.common.types import BaseRequest
    from dana.lang.common.utils.misc import Misc

    try:
        logger.info(f"🔄 Starting expert insights update for topic: {topic_name}")

        # Format conversation messages for LLM
        conversation_text = ""
        for msg in conversation_messages:
            sender = "Assistant" if msg.sender in ["assistant", "agent"] else "User"
            content = msg.content if hasattr(msg, "content") else str(msg)
            conversation_text += f"{sender}: {content}\n\n"

        # Prepare existing insights text
        if existing_insights.strip() == "*No insights captured yet*" or not existing_insights.strip():
            existing_insights_text = "No existing insights."
        else:
            existing_insights_text = f"Existing insights:\n{existing_insights}"

        # Create LLM prompt for insight extraction
        prompt = f"""You are analyzing an expert interview conversation to extract and consolidate expert insights.

Domain: {domain}
Role: {role}
Topic: {topic_name}

{existing_insights_text}

Conversation:
{conversation_text}

Your task:
1. Analyze the conversation to extract key insights shared by the expert
2. Identify technical details, practices, process-specific information, and lessons learned
3. Merge with existing insights, avoiding duplicates
4. Preserve all existing insights unless they are contradicted by new information
5. Format as bullet points (use - for each insight)
6. Keep insights concise and actionable

Return ONLY the consolidated expert insights in bullet point format. Do not include any explanation or additional text."""

        # Use LLM to extract and merge insights
        llm = LLMResource()
        llm_request = BaseRequest(
            arguments={
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert at extracting and consolidating knowledge from interview conversations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 2000,
            }
        )

        response = await llm.query(llm_request)
        merged_insights = Misc.get_response_content(response).strip()

        if not merged_insights:
            logger.warning(f"⚠️ LLM returned empty insights for topic '{topic_name}'")
            return

        logger.info(f"✅ Extracted insights for topic '{topic_name}': {merged_insights[:100]}...")

        # Update markdown with merged insights
        processor = InterviewNoteProcessor()
        processor.update_topic_expert_insights(topic_name, merged_insights, note_path)

        logger.info(f"✅ Successfully updated expert insights for topic '{topic_name}'")

    except Exception as e:
        logger.warning(f"⚠️ Failed to update expert insights for topic '{topic_name}': {e}", exc_info=True)


@router.post("/{session_id}/chat", response_model=InterviewChatResponse)
async def session_chat(
    session_id: int,
    request: BaseMessage,
    session_repo: type[AbstractInterviewSessionRepo] = Depends(get_interview_session_repo),
    template_repo: type[AbstractInterviewTemplateRepo] = Depends(get_interview_template_repo),
    conv_repo: type[AbstractConversationRepo] = Depends(get_conversation_repo),
    db: Session = Depends(get_db),
    processor: InterviewNoteProcessor = Depends(InterviewNoteProcessor),
):
    """
    Chat endpoint for interview sessions using InterviewHandler.
    Matches template_finetune_chat pattern for consistent conversation management.
    """
    # Benchmark: Start total API response time
    api_start_time = time.perf_counter()
    logger.info(f"🚀 Starting interview session chat for session {session_id}")

    # Benchmark: Track individual operation times
    benchmark_times = {}

    try:
        # Get session
        op_start = time.perf_counter()
        logger.debug(f"Fetching session {session_id}")
        session = await session_repo.get_session(session_id, db=db)
        benchmark_times["db_fetch_session"] = time.perf_counter() - op_start
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
        op_start = time.perf_counter()
        logger.debug(f"Fetching template {session.interview_template_id} for session {session_id}")
        template = await template_repo.get_template(session.interview_template_id, db=db)
        benchmark_times["db_fetch_template"] = time.perf_counter() - op_start
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
        op_start = time.perf_counter()
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
        benchmark_times["db_conversation_ops"] = time.perf_counter() - op_start

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
        op_start = time.perf_counter()
        logger.debug(f"Initializing RAG for knowledge pack {template.kp_id}")
        rag_resource = await _initialize_rag_from_kp(template.kp_id, db)
        benchmark_times["rag_initialization"] = time.perf_counter() - op_start
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
        # Start from the last interview_note question onwards to keep context relevant
        from dana.studio.api.core.schemas import MessageData

        # Find the last interview_note question index
        relevant_messages = _find_relevant_messages(conversation.messages)

        chat_history = [
            MessageData(
                role=message.sender,
                content=message.content,
                require_user=message.require_user,
                treat_as_tool=message.treat_as_tool,
            )
            for message in relevant_messages
            if message.require_user or not message.treat_as_tool
        ]
        logger.debug(f"Built chat history with {len(chat_history)} messages (from {len(relevant_messages)} relevant messages)")

        # Read current note
        op_start = time.perf_counter()
        # Update question statuses in interview notes
        note_path = Path(session_dir) / "interview_notes.md"
        if note_path.exists():
            current_note = note_path.read_text(encoding="utf-8")
        else:
            current_note = ""
        benchmark_times["read_note_file"] = time.perf_counter() - op_start

        # Initialize LLM for intent classification
        from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource

        llm = LLMResource()

        # Classify user intent using LLM (kept for future use/debugging)
        op_start = time.perf_counter()

        # Create IntentDetectionRequest for handlers
        from dana.studio.api.core.schemas import IntentDetectionRequest

        intent_request = IntentDetectionRequest(
            user_message=request.content,
            chat_history=chat_history,
            current_domain_tree=None,
            agent_id=template.kp_id,  # Use kp_id, not session_id
        )

        # Initialize handler
        op_start = time.perf_counter()
        logger.debug(f"Initializing question handler for session {session_id}")
        from dana.studio.api.services.knowledge_pack.interview_question_handler import InterviewQuestionHandler

        domain = template.template_metadata.get("domain", "General")
        role = template.template_metadata.get("role", "Expert")

        question_handler = InterviewQuestionHandler(
            kp_id=template.kp_id,
            template_path=str(template_path),
            rag_docs=rag_resource,
            llm=llm,
            domain=domain,
            role=role,
        )
        # Set database session for ReadDocumentsTool
        question_handler.db = db
        benchmark_times["handler_initialization"] = time.perf_counter() - op_start

        # Check for precomputed document answer from last interview_note question
        # This ensures followup questions have access to the document_answer from the original interview_note question
        document_answer = None
        if relevant_messages:
            # Find the last interview_note question (not just the last assistant message, which could be a followup)
            last_interview_note_msg = relevant_messages[0]

            if last_interview_note_msg and last_interview_note_msg.metadata:
                document_answer = last_interview_note_msg.metadata.get("document_answer")
                if document_answer:
                    logger.info("📚 Found precomputed document answer from last interview_note question")
                else:
                    logger.debug("Last interview_note question found but no document_answer in metadata yet (may still be computing)")
            else:
                logger.debug("No interview_note question found in conversation, proceeding without document_answer")

        # Generate question
        op_start = time.perf_counter()
        logger.info(f"🚀 Starting QuestionHandler for session {session_id}")
        if current_note:
            note_data = processor.markdown_to_json(current_note)
            # NOTE: The below logic is to prevent expert insights from being included to the question handler
            for topic in note_data.get("topics", []):
                if "expert_insights" in topic:
                    topic["expert_insights"] = "[Insight captured and shown on the right side of the screen]"
            current_note = processor.json_to_markdown(note_data)

        question_result = await question_handler.handle(intent_request, current_note_content=current_note, document_answer=document_answer)
        benchmark_times["question_handler_execution"] = time.perf_counter() - op_start
        logger.info(f"✅ QuestionHandler completed for session {session_id}: status={question_result.get('status')}")

        # Use question result for response
        result = question_result

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

        op_start = time.perf_counter()
        ask_question_message_id = None
        ask_question_content = None
        if new_messages:
            logger.info(f"📝 Adding {len(new_messages)} new messages to conversation {conversation.id}")
            updated_conversation = await conv_repo.add_messages_to_conversation(
                conversation_id=conversation.id, messages=new_messages, db=db
            )
            logger.info(f"✅ Successfully added messages to conversation {conversation.id}")

            if note_path.exists():
                # Extract domain and role from template metadata
                domain = template.template_metadata.get("domain", "General")
                role = template.template_metadata.get("role", "Expert")

                current_stack = []
                conversation_stack = []
                dq = deque(maxlen=10)

                for _, message in enumerate(updated_conversation.messages[::-1]):
                    # if i > len(new_messages) and not len(dq):
                    #     break
                    if message.sender == "assistant":
                        if message.require_user:
                            conversation_stack.append(message)
                            question_info = _extract_question_info(message.content)
                            if question_info and question_info.get("category") == "interview_note":
                                dq.appendleft((message, current_stack, conversation_stack))
                                current_stack = []
                                conversation_stack = []
                            elif question_info and question_info.get("category") == "followup":
                                current_stack.append(QuestionStatus.CLARIFYING)

                        elif "<attempt_completion>" in message.content:
                            current_stack.append(QuestionStatus.COMPLETED)
                    else:
                        conversation_stack.append(message)
                    if len(dq) == 2:
                        break

                if len(dq) == 2:  # Process previous question status
                    msg, stack, conversation_stack = dq[0]
                    question_info = _extract_question_info(msg.content)
                    # When we ask other questions, we mark the last question as completed
                    if question_info:
                        try:
                            existing_status = processor.get_question_status(question_info["question"], str(note_path))
                            if existing_status != QuestionStatus.COMPLETED:
                                processor.mark_question_as_completed(question_info["question"], str(note_path))

                                # Trigger background task to update expert insights
                                topic_name = processor._get_topic_name_for_question(question_info["question"], str(note_path))
                                if topic_name:
                                    try:
                                        # Get existing insights from markdown
                                        json_data = processor.from_file(str(note_path))
                                        existing_insights = "*No insights captured yet*"
                                        for topic in json_data.get("topics", []):
                                            if topic.get("topic_name") == topic_name:
                                                existing_insights = topic.get("expert_insights", "*No insights captured yet*")
                                                break

                                        # Create background task
                                        asyncio.create_task(
                                            _update_expert_insights_background(
                                                topic_name,
                                                str(note_path),
                                                existing_insights,
                                                list(reversed(conversation_stack)),
                                                domain,
                                                role,
                                            )
                                        )
                                        logger.debug(f"🔄 Created background task to update expert insights for topic '{topic_name}'")
                                    except Exception as e:
                                        logger.warning(f"⚠️ Failed to trigger expert insights update for '{topic_name}': {e}")

                                # Recalculate topic progress for the previous question
                                if topic_name:
                                    try:
                                        processor.recalculate_topic_progress(topic_name, str(note_path))
                                    except Exception as e:
                                        logger.warning(f"⚠️ Failed to recalculate topic progress for '{topic_name}': {e}")
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to mark previous question as completed: {e}")

                if len(dq):  # Process current question status
                    msg, stack, conversation_stack = dq[-1]
                    ask_question_message_id = msg.id
                    ask_question_content = msg.content
                    question_info = _extract_question_info(msg.content)
                    if question_info:
                        try:
                            existing_status = processor.get_question_status(question_info["question"], str(note_path))
                            if existing_status != QuestionStatus.COMPLETED:
                                # Get topic name once for all operations
                                topic_name = processor._get_topic_name_for_question(question_info["question"], str(note_path))

                                if any(status == QuestionStatus.COMPLETED for status in stack):
                                    processor.mark_question_as_completed(question_info["question"], str(note_path))

                                    # Trigger background task to update expert insights
                                    if topic_name:
                                        try:
                                            # Get existing insights from markdown
                                            json_data = processor.from_file(str(note_path))
                                            existing_insights = "*No insights captured yet*"
                                            for topic in json_data.get("topics", []):
                                                if topic.get("topic_name") == topic_name:
                                                    existing_insights = topic.get("expert_insights", "*No insights captured yet*")
                                                    break

                                            # Create background task
                                            # If this question is completed, do not process it in the background. User need to see the updated result immediately.
                                            await _update_expert_insights_background(
                                                topic_name,
                                                str(note_path),
                                                existing_insights,
                                                list(reversed(conversation_stack)),
                                                domain,
                                                role,
                                            )
                                            logger.debug(f"🔄 Created background task to update expert insights for topic '{topic_name}'")
                                        except Exception as e:
                                            logger.warning(f"⚠️ Failed to trigger expert insights update for '{topic_name}': {e}")

                                elif any(status == QuestionStatus.CLARIFYING for status in stack):
                                    processor.mark_question_as_clarifying(question_info["question"], str(note_path))
                                else:
                                    processor.mark_question_as_asking(question_info["question"], str(note_path))

                                # Recalculate topic progress after question status update
                                if topic_name:
                                    try:
                                        processor.recalculate_topic_progress(topic_name, str(note_path))
                                    except Exception as e:
                                        logger.warning(f"⚠️ Failed to recalculate topic progress for '{topic_name}': {e}")
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to update question status: {e}")

        else:
            logger.debug("No new messages to add to conversation")
        benchmark_times["db_add_messages"] = time.perf_counter() - op_start

        # Trigger background task for document answer precomputation if interview_note question
        if ask_question_message_id and rag_resource and ask_question_content:
            question_info = _extract_question_info(ask_question_content)
            if question_info and question_info.get("question"):
                logger.info(
                    f"🔄 Triggering background task to precompute document answer for question: {question_info['question'][:100]}..."
                )
                asyncio.create_task(
                    _precompute_document_answer_background(
                        question_text=question_info["question"],
                        kp_id=template.kp_id,
                        rag_docs=rag_resource,
                        conversation_id=conversation.id,
                        message_id=ask_question_message_id,
                    )
                )

        # Update session status if workflow completed
        op_start = time.perf_counter()
        interview_modified = result.get("workflow_completed", False)
        if interview_modified:
            logger.info(f"🎯 Interview workflow completed for session {session_id}")
            await session_repo.update_session(session_id, InterviewSessionUpdate(status="completed"), db=db)

        # Mark last question as completed if workflow completed or no more questions remain
        # note_path = Path(session_dir) / "interview_notes.md"
        # if note_path.exists():
        #     try:
        #         processor = InterviewNoteProcessor()

        #         # Check if workflow completed or no more questions remain
        #         should_mark_completed = interview_modified or not _has_more_questions(str(note_path))

        #         if should_mark_completed:
        #             # Find the last interview_note question with asking or clarifying status
        #             json_data = processor.from_file(str(note_path))
        #             last_question_text = None

        #             # Search for the last question with asking or clarifying status
        #             for topic in reversed(json_data.get("topics", [])):
        #                 questions = topic.get("key_questions", [])
        #                 for question in reversed(questions):
        #                     if isinstance(question, dict):
        #                         status = question.get("status", QuestionStatus.NOT_ASKED.value)
        #                         if status in [QuestionStatus.ASKING.value, QuestionStatus.CLARIFYING.value]:
        #                             last_question_text = question.get("text", "")
        #                             break
        #                     if last_question_text:
        #                         break
        #                 if last_question_text:
        #                     break

        #             if last_question_text:
        #                 processor.mark_question_as_completed(last_question_text, str(note_path))
        #                 logger.info(f"✅ Marked last question as completed: {last_question_text[:60]}...")
        #     except Exception as e:
        #         logger.warning(f"⚠️ Failed to mark last question as completed: {e}")

        benchmark_times["db_update_session"] = time.perf_counter() - op_start

        # Convert MessageData to HandlerMessage for response
        # Use the deduplicated messages for the response
        from dana.studio.api.core.schemas_v2._conversation import HandlerMessage

        internal_conversation_response = [
            HandlerMessage(sender=msg.role, content=msg.content, require_user=msg.require_user, treat_as_tool=msg.treat_as_tool)
            for msg in internal_conversation[-len(new_messages) :]
            if new_messages
        ]

        # Benchmark: Calculate total API response time
        total_api_time = time.perf_counter() - api_start_time
        benchmark_times["total_api_time"] = total_api_time

        # Log response details with benchmark summary
        agent_response = result.get("message", "Interview processed successfully")
        logger.info(f"🎯 Interview session chat completed: interview_modified={interview_modified}, response_length={len(agent_response)}")

        # Log benchmark summary
        logger.info(
            f"⏱️  BENCHMARK [session={session_id}]: Total={total_api_time:.3f}s | "
            f"DB_ops={benchmark_times.get('db_fetch_session', 0) + benchmark_times.get('db_fetch_template', 0) + benchmark_times.get('db_conversation_ops', 0) + benchmark_times.get('db_add_messages', 0) + benchmark_times.get('db_update_session', 0):.3f}s | "
            f"RAG_init={benchmark_times.get('rag_initialization', 0):.3f}s | "
            f"Intent={benchmark_times.get('intent_classification', 0):.3f}s | "
            f"QuestionHandler={benchmark_times.get('question_handler_execution', 0):.3f}s | "
            f"NoteHandler_setup={benchmark_times.get('note_handler_setup', 0):.3f}s"
        )

        # Detailed benchmark breakdown (debug level)
        logger.warning(
            f"📊 Detailed Benchmark [session={session_id}]: {json.dumps({k: f'{v:.3f}s' for k, v in benchmark_times.items()}, indent=2)}"
        )

        return InterviewChatResponse(
            success=True,
            interview_modified=interview_modified,
            agent_response=agent_response,
            internal_conversation=internal_conversation_response,
            error=result.get("error", None),
        )

    except Exception as e:
        # Log benchmark even on error
        total_api_time = time.perf_counter() - api_start_time
        logger.error(f"❌ Error in interview session chat for session {session_id} after {total_api_time:.3f}s: {e}")
        import traceback

        logger.error(f"📋 Full traceback: {traceback.format_exc()}")

        # Log partial benchmark if available
        if benchmark_times:
            logger.error(
                f"⏱️  Partial Benchmark [session={session_id}]: {json.dumps({k: f'{v:.3f}s' for k, v in benchmark_times.items()}, indent=2)}"
            )

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

        # Get progress data using old approach first
        progress_data = get_interview_progress(progress_dict.get("topics", []), conversation_messages)

        # Enhance with question statuses from new converter
        try:
            progress_data = _enhance_progress_data_with_converter_statuses(progress_data, str(note_path))
            logger.debug("✅ Enhanced progress data with converter statuses")
        except Exception as e:
            logger.warning(f"⚠️ Failed to enhance progress data with converter, using old approach only: {e}")
            # Continue with progress_data from old approach

        return InterviewProgressResponse(success=True, data=progress_data, error=None)

    except Exception as e:
        logger.error(f"❌ Error getting progress for session {session_id}: {e}")
        import traceback

        logger.error(f"📋 Full traceback: {traceback.format_exc()}")

        return InterviewProgressResponse(success=False, data=None, error=str(e))


@router.get("/{session_id}/download-interview-note")
async def download_interview_note(
    session_id: int,
    session_repo: type[AbstractInterviewSessionRepo] = Depends(get_interview_session_repo),
    db: Session = Depends(get_db),
):
    """
    Download interview session notes as markdown file.

    Removes content from "## Documents Found" section onwards.
    """
    try:
        # Get session from database
        session = await session_repo.get_session(session_id, db=db)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Check if session has folder_path
        if not session.folder_path:
            raise HTTPException(status_code=404, detail=f"Session {session_id} has no folder path")

        # Check if interview notes file exists
        note_path = Path(session.folder_path) / "interview_notes.md"
        if not note_path.exists():
            raise HTTPException(status_code=404, detail=f"Interview notes not found for session {session_id}")

        # Read interview notes using InterviewNoteProcessor to validate the file
        processor = InterviewNoteProcessor()
        try:
            # Validate file can be read and parsed by processor
            processor.from_file(str(note_path))
        except Exception as e:
            logger.warning(f"Interview notes file validation failed: {e}")
            # Continue anyway - file might still be readable

        # Read raw markdown content for processing
        markdown_content = note_path.read_text(encoding="utf-8")

        # Remove content from "## Documents Found" onwards
        # Use regex to find and remove everything from "## Documents Found" to end of file
        pattern = r"## Documents Found.*"
        processed_content = re.sub(pattern, "", markdown_content, flags=re.DOTALL)

        # Clean up any trailing whitespace
        processed_content = processed_content.rstrip() + "\n"

        # Create BytesIO stream for download
        file_stream = BytesIO(processed_content.encode("utf-8"))

        # Return streaming response
        filename = f"interview_notes_session_{session_id}.md"
        return StreamingResponse(
            iter([file_stream.getvalue()]),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading interview note for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download interview note: {str(e)}")
