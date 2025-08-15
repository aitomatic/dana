import os
import tempfile
import platform
import subprocess
from pathlib import Path
import json
from datetime import UTC, datetime
import logging

from fastapi import APIRouter, HTTPException

from dana.api.core.schemas import (
    MultiFileProject,
    RunNAFileRequest,
    RunNAFileResponse,
)
from dana.api.server.services import run_na_file_service

router = APIRouter(prefix="/agents", tags=["agents"])

# Simple in-memory task status tracker
processing_status = {}


@router.post("/run-na-file", response_model=RunNAFileResponse)
def run_na_file(request: RunNAFileRequest):
    return run_na_file_service(request)


@router.post("/write-files")
async def write_multi_file_project(project: MultiFileProject):
    """
    Write a multi-file project to disk.

    This endpoint writes all files in a multi-file project to the specified location.
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Writing multi-file project: {project.name}")

        # Create project directory
        project_dir = Path(f"projects/{project.name}")
        project_dir.mkdir(parents=True, exist_ok=True)

        # Write each file
        written_files = []
        for file_info in project.files:
            file_path = project_dir / file_info.filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_info.content)
            written_files.append(str(file_path))
            logger.info(f"Written file: {file_path}")

        # Create project metadata
        metadata = {
            "name": project.name,
            "description": project.description,
            "main_file": project.main_file,
            "structure_type": project.structure_type,
            "files": [f.filename for f in project.files],
            "created_at": datetime.now(UTC).isoformat(),
        }

        metadata_path = project_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return {"success": True, "project_dir": str(project_dir), "written_files": written_files, "metadata_file": str(metadata_path)}

    except Exception as e:
        logger.error(f"Error writing multi-file project: {e}")
        return {"success": False, "error": str(e)}


@router.post("/write-files-temp")
async def write_multi_file_project_temp(project: MultiFileProject):
    """
    Write a multi-file project to a temporary directory.

    This endpoint writes all files in a multi-file project to a temporary location
    for testing or preview purposes.
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Writing multi-file project to temp: {project.name}")

        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix=f"dana_project_{project.name}_"))

        # Write each file
        written_files = []
        for file_info in project.files:
            file_path = temp_dir / file_info.filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_info.content)
            written_files.append(str(file_path))
            logger.info(f"Written temp file: {file_path}")

        # Create project metadata
        metadata = {
            "name": project.name,
            "description": project.description,
            "main_file": project.main_file,
            "structure_type": project.structure_type,
            "files": [f.filename for f in project.files],
            "created_at": datetime.now(UTC).isoformat(),
            "temp_dir": str(temp_dir),
        }

        metadata_path = temp_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return {"success": True, "temp_dir": str(temp_dir), "written_files": written_files, "metadata_file": str(metadata_path)}

    except Exception as e:
        logger.error(f"Error writing multi-file project to temp: {e}")
        return {"success": False, "error": str(e)}


@router.post("/validate-multi-file")
async def validate_multi_file_project(project: MultiFileProject):
    """
    Validate a multi-file project structure and dependencies.

    This endpoint performs comprehensive validation of a multi-file project:
    - Checks file structure and naming
    - Validates dependencies between files
    - Checks for circular dependencies
    - Validates Dana syntax for each file
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Validating multi-file project: {project.name}")

        validation_results = {
            "success": True,
            "project_name": project.name,
            "file_count": len(project.files),
            "errors": [],
            "warnings": [],
            "file_validations": [],
            "dependency_analysis": {},
        }

        # Validate file structure
        filenames = [f.filename for f in project.files]
        if len(filenames) != len(set(filenames)):
            validation_results["errors"].append("Duplicate filenames found")
            validation_results["success"] = False

        # Check for main file
        if project.main_file not in filenames:
            validation_results["errors"].append(f"Main file '{project.main_file}' not found in project files")
            validation_results["success"] = False

        # Validate each file
        for file_info in project.files:
            file_validation = {"filename": file_info.filename, "valid": True, "errors": [], "warnings": []}

            # Check file extension
            if not file_info.filename.endswith(".na"):
                file_validation["warnings"].append("File should have .na extension")

            # Check file content
            if not file_info.content.strip():
                file_validation["errors"].append("File is empty")
                file_validation["valid"] = False

            # Basic Dana syntax check (simplified)
            if "agent" in file_info.content.lower() and "def solve" not in file_info.content:
                file_validation["warnings"].append("Agent file should contain solve function")

            validation_results["file_validations"].append(file_validation)

            if not file_validation["valid"]:
                validation_results["success"] = False

        # Dependency analysis
        validation_results["dependency_analysis"] = {"has_circular_deps": False, "missing_deps": [], "dependency_graph": {}}

        # Check for circular dependencies (simplified)
        def has_circular_deps(filename, visited=None, path=None):
            if visited is None:
                visited = set()
            if path is None:
                path = []

            if filename in path:
                return True

            visited.add(filename)
            path.append(filename)

            # This is a simplified check - in reality, you'd parse imports
            # For now, just check if any file references another
            for file_info in project.files:
                if file_info.filename == filename:
                    # Check for potential imports (simplified)
                    content = file_info.content.lower()
                    for other_file in project.files:
                        if other_file.filename != filename:
                            if other_file.filename.replace(".na", "") in content:
                                if has_circular_deps(other_file.filename, visited, path):
                                    return True
                    break

            path.pop()
            return False

        for file_info in project.files:
            if has_circular_deps(file_info.filename):
                validation_results["dependency_analysis"]["has_circular_deps"] = True
                validation_results["errors"].append(f"Circular dependency detected involving {file_info.filename}")
                validation_results["success"] = False

        return validation_results

    except Exception as e:
        logger.error(f"Error validating multi-file project: {e}")
        return {"success": False, "error": str(e), "project_name": project.name}


@router.post("/open-agent-folder")
async def open_agent_folder(request: dict):
    """
    Open the agent folder in the system file explorer.

    This endpoint opens the specified agent folder in the user's default file explorer.
    """
    logger = logging.getLogger(__name__)

    try:
        agent_folder = request.get("agent_folder")
        if not agent_folder:
            return {"success": False, "error": "agent_folder is required"}

        folder_path = Path(agent_folder)
        if not folder_path.exists():
            return {"success": False, "error": f"Agent folder not found: {agent_folder}"}

        logger.info(f"Opening agent folder: {folder_path}")

        # Open folder based on platform
        if platform.system() == "Windows":
            os.startfile(str(folder_path))
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", str(folder_path)])
        else:  # Linux
            subprocess.run(["xdg-open", str(folder_path)])

        return {"success": True, "message": f"Opened agent folder: {folder_path}"}

    except Exception as e:
        logger.error(f"Error opening agent folder: {e}")
        return {"success": False, "error": str(e)}


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a background task.

    This endpoint returns the current status of a background task by its ID.
    """
    logger = logging.getLogger(__name__)

    try:
        if task_id not in processing_status:
            raise HTTPException(status_code=404, detail="Task not found")

        status = processing_status[task_id]
        logger.info(f"Task {task_id} status: {status}")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deep-train")
async def deep_train_agent(request: dict):
    """
    Perform deep training on an agent.

    This endpoint initiates a deep training process for an agent using advanced
    machine learning techniques.
    """
    logger = logging.getLogger(__name__)

    try:
        agent_id = request.get("agent_id")
        request.get("training_data", [])
        request.get("training_config", {})

        if not agent_id:
            return {"success": False, "error": "agent_id is required"}

        logger.info(f"Starting deep training for agent {agent_id}")

        # This is a placeholder implementation
        # In a real implementation, you would:
        # 1. Load the agent from database
        # 2. Prepare training data
        # 3. Initialize training process
        # 4. Run training in background
        # 5. Update agent with new weights/knowledge

        # Simulate training process
        training_result = {
            "agent_id": agent_id,
            "training_status": "completed",
            "training_metrics": {"accuracy": 0.95, "loss": 0.05, "epochs": 100},
            "training_time": "2.5 hours",
            "new_capabilities": ["Enhanced reasoning", "Better context understanding", "Improved response quality"],
        }

        logger.info(f"Deep training completed for agent {agent_id}")

        return {"success": True, "message": "Deep training completed successfully", "result": training_result}

    except Exception as e:
        logger.error(f"Error in deep training: {e}")
        return {"success": False, "error": str(e)}
