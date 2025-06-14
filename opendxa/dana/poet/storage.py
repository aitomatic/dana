"""POET Storage System - File-based storage for Alpha implementation"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from opendxa.common.utils.logging import DXA_LOGGER


class POETStorage:
    """File-based storage system for POET functions and metadata"""

    def __init__(self, base_path: str = ".poet"):
        self.base_path = Path(base_path)
        self._ensure_directories()
        DXA_LOGGER.info(f"POET storage initialized at {self.base_path}")

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        self.base_path.mkdir(exist_ok=True)
        (self.base_path / "executions").mkdir(exist_ok=True)
        (self.base_path / "feedback").mkdir(exist_ok=True)
        (self.base_path / "cache").mkdir(exist_ok=True)

    def store_enhanced_function(
        self, function_name: str, version: str, enhanced_code: str, metadata: Dict[str, Any], train_code: Optional[str] = None
    ) -> Path:
        """
        Store enhanced function code and metadata

        Creates directory structure:
        .poet/{function_name}/v{version}/
        ├── enhanced.py      # Enhanced function code
        ├── train.py         # Train method (if optimize_for specified)
        └── metadata.json    # Function metadata
        """

        function_dir = self.base_path / function_name
        version_dir = function_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # Store enhanced function code
        enhanced_file = version_dir / "enhanced.py"
        with open(enhanced_file, "w") as f:
            f.write(enhanced_code)

        # Store train code if provided (when optimize_for is specified)
        if train_code:
            train_file = version_dir / "train.py"
            with open(train_file, "w") as f:
                f.write(train_code)

        # Store metadata
        metadata_with_storage = {
            **metadata,
            "storage_info": {
                "stored_at": datetime.now().isoformat(),
                "version": version,
                "has_train_phase": train_code is not None,
                "enhanced_file": str(enhanced_file),
                "train_file": str(version_dir / "train.py") if train_code else None,
            },
        }

        metadata_file = version_dir / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata_with_storage, f, indent=2)

        # Update current symlink
        current_link = function_dir / "current"
        if current_link.exists() or current_link.is_symlink():
            current_link.unlink()
        current_link.symlink_to(version)

        DXA_LOGGER.info(f"Stored enhanced function {function_name} version {version}")
        return version_dir

    def load_enhanced_function(self, function_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Load enhanced function code and metadata"""

        function_dir = self.base_path / function_name
        if not function_dir.exists():
            raise FileNotFoundError(f"Function {function_name} not found")

        # Use specified version or current
        if version is None:
            current_link = function_dir / "current"
            if not current_link.exists():
                raise FileNotFoundError(f"No current version for {function_name}")
            version_dir = function_dir / current_link.readlink()
        else:
            version_dir = function_dir / version

        if not version_dir.exists():
            raise FileNotFoundError(f"Version {version} not found for {function_name}")

        # Load components
        enhanced_file = version_dir / "enhanced.py"
        metadata_file = version_dir / "metadata.json"
        train_file = version_dir / "train.py"

        if not enhanced_file.exists() or not metadata_file.exists():
            raise FileNotFoundError(f"Incomplete function data for {function_name}")

        # Read files
        with open(enhanced_file, "r") as f:
            enhanced_code = f.read()

        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        train_code = None
        if train_file.exists():
            with open(train_file, "r") as f:
                train_code = f.read()

        return {
            "function_name": function_name,
            "version": version_dir.name,
            "enhanced_code": enhanced_code,
            "train_code": train_code,
            "metadata": metadata,
            "version_dir": version_dir,
        }

    def list_function_versions(self, function_name: str) -> List[str]:
        """List all versions for a function"""
        function_dir = self.base_path / function_name
        if not function_dir.exists():
            return []

        versions = []
        for item in function_dir.iterdir():
            if item.is_dir() and item.name != "current":
                versions.append(item.name)

        # Sort versions (v1, v2, etc.)
        versions.sort(key=lambda x: int(x[1:]) if x.startswith("v") and x[1:].isdigit() else 0)
        return versions

    def get_current_version(self, function_name: str) -> Optional[str]:
        """Get current version for a function"""
        function_dir = self.base_path / function_name
        current_link = function_dir / "current"

        if current_link.exists() and current_link.is_symlink():
            return current_link.readlink().name
        return None

    def function_exists(self, function_name: str) -> bool:
        """Check if function exists in storage"""
        function_dir = self.base_path / function_name
        return function_dir.exists() and (function_dir / "current").exists()

    def store_execution_context(self, execution_id: str, context: Dict[str, Any]) -> Path:
        """Store execution context for feedback correlation"""
        executions_dir = self.base_path / "executions"
        execution_file = executions_dir / f"{execution_id}.json"

        context_with_metadata = {**context, "stored_at": datetime.now().isoformat(), "execution_id": execution_id}

        with open(execution_file, "w") as f:
            json.dump(context_with_metadata, f, indent=2)

        DXA_LOGGER.debug(f"Stored execution context for {execution_id}")
        return execution_file

    def load_execution_context(self, execution_id: str) -> Dict[str, Any]:
        """Load execution context"""
        executions_dir = self.base_path / "executions"
        execution_file = executions_dir / f"{execution_id}.json"

        if not execution_file.exists():
            raise FileNotFoundError(f"Execution context {execution_id} not found")

        with open(execution_file, "r") as f:
            return json.load(f)

    def store_feedback(self, execution_id: str, feedback_data: Dict[str, Any]) -> Path:
        """Store feedback data"""
        feedback_dir = self.base_path / "feedback"
        feedback_file = feedback_dir / f"{execution_id}_feedback.json"

        # Load existing feedback or create new
        if feedback_file.exists():
            with open(feedback_file, "r") as f:
                existing_feedback = json.load(f)
            if not isinstance(existing_feedback, list):
                existing_feedback = [existing_feedback]
        else:
            existing_feedback = []

        # Add new feedback
        feedback_entry = {**feedback_data, "stored_at": datetime.now().isoformat()}
        existing_feedback.append(feedback_entry)

        # Save updated feedback
        with open(feedback_file, "w") as f:
            json.dump(existing_feedback, f, indent=2)

        DXA_LOGGER.debug(f"Stored feedback for execution {execution_id}")
        return feedback_file

    def load_feedback(self, execution_id: str) -> List[Dict[str, Any]]:
        """Load feedback data for an execution"""
        feedback_dir = self.base_path / "feedback"
        feedback_file = feedback_dir / f"{execution_id}_feedback.json"

        if not feedback_file.exists():
            return []

        with open(feedback_file, "r") as f:
            feedback_data = json.load(f)

        # Ensure it's a list
        if not isinstance(feedback_data, list):
            feedback_data = [feedback_data]

        return feedback_data

    def get_function_feedback_summary(self, function_name: str) -> Dict[str, Any]:
        """Get aggregated feedback summary for a function"""
        # Find all executions for this function
        executions_dir = self.base_path / "executions"
        feedback_dir = self.base_path / "feedback"

        all_feedback = []
        execution_count = 0

        for execution_file in executions_dir.glob("*.json"):
            try:
                with open(execution_file, "r") as f:
                    context = json.load(f)

                if context.get("function_name") == function_name:
                    execution_count += 1
                    execution_id = context["execution_id"]

                    # Load feedback for this execution
                    feedback = self.load_feedback(execution_id)
                    all_feedback.extend(feedback)

            except Exception as e:
                DXA_LOGGER.warning(f"Failed to process execution file {execution_file}: {e}")

        # Aggregate statistics
        if not all_feedback:
            return {
                "function_name": function_name,
                "execution_count": execution_count,
                "feedback_count": 0,
                "summary": "No feedback available",
            }

        sentiments = [f.get("sentiment", "unknown") for f in all_feedback]
        feedback_types = [f.get("feedback_type", "unknown") for f in all_feedback]

        return {
            "function_name": function_name,
            "execution_count": execution_count,
            "feedback_count": len(all_feedback),
            "sentiment_distribution": {sentiment: sentiments.count(sentiment) for sentiment in set(sentiments)},
            "feedback_type_distribution": {ftype: feedback_types.count(ftype) for ftype in set(feedback_types)},
            "recent_feedback": all_feedback[-5:] if len(all_feedback) >= 5 else all_feedback,
        }

    def cleanup_old_versions(self, function_name: str, keep_versions: int = 5):
        """Clean up old versions, keeping only the most recent ones"""
        versions = self.list_function_versions(function_name)

        if len(versions) <= keep_versions:
            return

        # Remove oldest versions
        versions_to_remove = versions[:-keep_versions]
        function_dir = self.base_path / function_name

        for version in versions_to_remove:
            version_dir = function_dir / version
            if version_dir.exists():
                shutil.rmtree(version_dir)
                DXA_LOGGER.info(f"Cleaned up old version {function_name}/{version}")

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            "base_path": str(self.base_path),
            "total_functions": 0,
            "total_versions": 0,
            "total_executions": 0,
            "total_feedback_files": 0,
            "disk_usage_mb": 0,
        }

        try:
            # Count functions and versions
            for function_dir in self.base_path.iterdir():
                if function_dir.is_dir() and function_dir.name not in ["executions", "feedback", "cache"]:
                    stats["total_functions"] += 1
                    versions = self.list_function_versions(function_dir.name)
                    stats["total_versions"] += len(versions)

            # Count executions
            executions_dir = self.base_path / "executions"
            if executions_dir.exists():
                stats["total_executions"] = len(list(executions_dir.glob("*.json")))

            # Count feedback files
            feedback_dir = self.base_path / "feedback"
            if feedback_dir.exists():
                stats["total_feedback_files"] = len(list(feedback_dir.glob("*.json")))

            # Calculate disk usage (rough estimate)
            total_size = sum(f.stat().st_size for f in self.base_path.rglob("*") if f.is_file())
            stats["disk_usage_mb"] = round(total_size / (1024 * 1024), 2)

        except Exception as e:
            DXA_LOGGER.warning(f"Failed to calculate storage stats: {e}")

        return stats


# Global storage instance
_default_storage: Optional[POETStorage] = None


def get_default_storage() -> POETStorage:
    """Get or create the default storage instance"""
    global _default_storage
    if _default_storage is None:
        _default_storage = POETStorage()
    return _default_storage


def set_storage_path(path: str):
    """Set the storage path and reinitialize default storage"""
    global _default_storage
    _default_storage = POETStorage(path)
