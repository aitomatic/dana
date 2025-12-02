from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dana.studio.api.repositories import AbstractDomainKnowledgeRepo, AbstractBackgroundTaskRepo, AbstractDocumentRepo
from dana.studio.api.repositories import get_domain_knowledge_repo, get_background_task_repo, get_document_repo
from dana.studio.api.core.database import get_db
from dana.studio.api.core.schemas_v2 import KnowledgeGenerationResponse, BackgroundTaskResponse
from dana.studio.api.background.task_manager import get_task_manager
from dana.studio.api.repositories.config import KNOW_FOLDER_NAME
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gen")


async def _check_questions_exist(knows_path: Path) -> tuple[bool, list[str]]:
    """
    Check if knowledge.json files with questions exist in the knows directory.
    Returns (has_questions, missing_topics)
    """
    if not knows_path.exists():
        return False, ["knows directory does not exist"]

    missing_topics = []
    has_questions = False

    # Walk through knows directory to find knowledge.json files
    for knowledge_file in knows_path.rglob("knowledge.json"):
        try:
            with open(knowledge_file, encoding="utf-8") as f:
                data = json.load(f)

            # Check if file has knowledges with questions
            knowledges = data.get("knowledges", [])
            if not knowledges:
                topic_path = str(knowledge_file.relative_to(knows_path).parent)
                missing_topics.append(f"{topic_path} (no knowledges)")
                continue

            topic_has_questions = False
            for knowledge in knowledges:
                question = knowledge.get("question", "").strip()
                if question and "*Question" in question:
                    topic_has_questions = True
                    has_questions = True
                    break

            if not topic_has_questions:
                topic_path = str(knowledge_file.relative_to(knows_path).parent)
                missing_topics.append(f"{topic_path} (no questions)")

        except (json.JSONDecodeError, KeyError, OSError) as e:
            topic_path = str(knowledge_file.relative_to(knows_path).parent)
            missing_topics.append(f"{topic_path} (invalid file: {str(e)})")

    return has_questions, missing_topics


@router.post("/{knowledge_id}/generate-knowledge", response_model=KnowledgeGenerationResponse)
async def generate_knowledge(
    knowledge_id: int,
    kb_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    doc_repo: type[AbstractDocumentRepo] = Depends(get_document_repo),
    db: Session = Depends(get_db),
):
    """
    Generate knowledge from pre-generated questions using background task processing.

    This endpoint:
    1. Validates that questions exist in knowledge.json files
    2. Creates a background task to generate knowledge from questions
    3. Returns task ID for status tracking

    Args:
        knowledge_id: The ID of the knowledge pack to generate knowledge for

    Returns:
        KnowledgeGenerationResponse containing:
            - success: Whether the operation succeeded
            - message: Status message
            - task_id: Background task ID for tracking progress
    """
    try:
        # Get knowledge pack
        kb = await kb_repo.get_kp(kp_id=knowledge_id, db=db)
        if kb is None:
            raise HTTPException(status_code=404, detail="Knowledge pack not found")

        spec = kb.get_specialization_info()

        # Get paths
        domain_knowledge_path = str(kb_repo.get_knowledge_tree_path(knowledge_id).absolute())
        base_path = Path(domain_knowledge_path).parent
        knows_path = base_path / KNOW_FOLDER_NAME

        # Get associated documents from kp_metadata
        kp_metadata = kb.kp_metadata or {}
        associated_document_ids = kp_metadata.get("associated_documents", [])

        # Query documents to get file paths
        document_paths = []
        if associated_document_ids:
            documents = await doc_repo.get_document_by_ids(document_ids=associated_document_ids, db=db)
            document_paths = [document.file_path for document in documents]

        logger.info(f"Found {len(document_paths)} associated documents for knowledge pack {knowledge_id}")

        # Check if questions exist
        has_questions, missing_topics = await _check_questions_exist(knows_path)

        if not has_questions:
            error_msg = f"Questions not found. Please generate questions first. Missing: {', '.join(missing_topics[:5])}"
            if len(missing_topics) > 5:
                error_msg += f" and {len(missing_topics) - 5} more topics"

            return KnowledgeGenerationResponse(
                success=False, message="Questions not found. Please generate questions first.", error=error_msg
            )

        # Get template generation prompt override from kp_metadata if exists
        prompt_overrides = kp_metadata.get("prompt_overrides", {})
        template_generation_prompt = None
        if "template_generation" in prompt_overrides and "prompt" in prompt_overrides["template_generation"]:
            template_generation_prompt = prompt_overrides["template_generation"]["prompt"]

        # Create background task data
        task_data = {
            "knowledge_id": knowledge_id,
            "storage_path": str(knows_path),
            "document_paths": document_paths,  # List of document file paths
            "domain_knowledge_path": domain_knowledge_path,
            "knowledge_status_path": str(base_path / "knowledge_status.json"),
            "domain": spec.domain,
            "role": spec.role,
            "tasks": [spec.task],
            "template_generation_prompt": template_generation_prompt,  # KP override (can be None)
        }

        # Create background task
        task_manager = get_task_manager()
        task_id = await task_manager.add_knowledge_gen_task(data=task_data)

        if task_id is None:
            return KnowledgeGenerationResponse(
                success=False, message="Failed to create background task. Task may already exist.", error="Background task creation failed"
            )

        logger.info(f"🚀 Started knowledge generation background task {task_id} for knowledge pack {knowledge_id}")

        return KnowledgeGenerationResponse(
            success=True, message=f"Knowledge generation started for {len(missing_topics)} topics", task_id=task_id
        )

    except Exception as e:
        logger.error(f"❌ Failed to start knowledge generation for knowledge pack {knowledge_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start knowledge generation: {str(e)}")


@router.get("/{knowledge_id}/generation-status/{task_id}", response_model=BackgroundTaskResponse)
async def get_generation_status(
    knowledge_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    bg_repo: AbstractBackgroundTaskRepo = Depends(get_background_task_repo),
):
    """Get the status of a knowledge generation task."""
    task = await bg_repo.get_task_by_id(task_id, db=db)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/{knowledge_id}/knowledge-status")
async def get_knowledge_status(
    knowledge_id: int,
    kb_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Get the knowledge generation status for all topics in the knowledge pack's domain knowledge tree.
    Returns status for ALL topics, including ones not yet generated (with status=null).

    This endpoint combines data from:
    1. knowledge_status.json (topics that have been processed)
    2. domain_knowledge.json tree (all topics, including unprocessed ones)

    Returns:
        Dictionary with "topics" array containing status for each leaf node:
        - path: Topic path (e.g., "Parent - Child - Leaf")
        - status: Generation status (null, "question_generated", "success", "failed", etc.)
        - last_generated: Timestamp of last generation
        - file: Relative path to knowledge.json file
        - error: Error message if generation failed
    """
    try:
        # Get knowledge pack
        kb = await kb_repo.get_kp(kp_id=knowledge_id, db=db)
        if kb is None:
            raise HTTPException(status_code=404, detail="Knowledge pack not found")

        # Get folder path
        folder_path = kb_repo.get_knowledge_pack_folder(knowledge_id)
        status_path = folder_path / "knowledge_status.json"

        # Load existing knowledge status
        existing_status = {}
        if status_path.exists():
            try:
                with open(status_path, encoding="utf-8") as f:
                    status_data = json.load(f)
                # Create a map of path -> status for quick lookup
                existing_status = {topic["path"]: topic for topic in status_data.get("topics", [])}
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load knowledge_status.json for KP {knowledge_id}: {e}")

        # Load domain knowledge tree to get ALL topics
        tree = await kb_repo.get_kp_tree(kp_id=knowledge_id, db=db)

        # Extract all topic paths from the tree
        all_topics = []

        def extract_paths(node, parent_path="", is_root=True):
            if not node:
                return

            # Build current path
            current_topic = node.topic if hasattr(node, "topic") else None
            if not current_topic:
                return

            # Skip root node in path (to match backend format)
            if is_root:
                current_path = ""
            else:
                current_path = f"{parent_path} - {current_topic}" if parent_path else current_topic

            # Check if this is a leaf node (no children or empty children)
            is_leaf = not hasattr(node, "children") or not node.children or len(node.children) == 0

            if is_leaf and current_path:  # Only add non-root leaf nodes
                # Add this topic with its status (or null if not in status file)
                if current_path in existing_status:
                    all_topics.append(existing_status[current_path])
                else:
                    # Topic exists in tree but hasn't been generated yet
                    all_topics.append(
                        {
                            "path": current_path,
                            "status": None,  # null = not generated yet
                            "last_generated": None,
                            "file": None,
                            "error": None,
                        }
                    )

            # Recurse for children
            if hasattr(node, "children") and node.children:
                for child in node.children:
                    extract_paths(child, current_path, is_root=False)

        if tree and hasattr(tree, "root"):
            extract_paths(tree.root, "", is_root=True)

        return {"topics": all_topics}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge status for knowledge pack {knowledge_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
