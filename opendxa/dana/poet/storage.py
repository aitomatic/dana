"""POET Storage System - File-based storage for Alpha implementation"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from dana.common.mixins.loggable import Loggable


class POETStorage(Loggable):
    """File-based storage system for POET functions and metadata"""

    def __init__(self, module_file: str | None = None):
        super().__init__()
        # If module_file is provided, collocate .dana/poet with the module
        if module_file:
            module_dir = Path(module_file).parent.resolve()
            self.base_path = module_dir / ".dana/poet"
        else:
            self.base_path = Path(".dana/poet").resolve()
        self._ensure_directories()
        self.log_info(f"POET storage initialized at {self.base_path}")

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        (self.base_path / "executions").mkdir(exist_ok=True)
        (self.base_path / "feedback").mkdir(exist_ok=True)
        (self.base_path / "cache").mkdir(exist_ok=True)
        (self.base_path / "magic").mkdir(exist_ok=True)  # For future magic function caching

    def store_enhanced_function(
        self, function_name: str, version: str, enhanced_code: str, metadata: dict[str, Any], train_code: str | None = None
    ) -> Path:
        """
        Store enhanced function code and metadata

        Creates directory structure:
        .dana/poet/{function_name}/v{version}/
        ├── enhanced.na      # Enhanced function code (Dana)
        ├── train.na         # Train method (if optimize_for specified)
        └── metadata.json    # Function metadata
        """

        function_dir = self.base_path / function_name
        version_dir = function_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # Store enhanced function code
        enhanced_file = version_dir / "enhanced.na"  # Changed to .na for Dana
        with open(enhanced_file, "w") as f:
            f.write(enhanced_code)

        # Store train code if provided (when optimize_for is specified)
        if train_code:
            train_file = version_dir / "train.na"  # Changed to .na for Dana
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
                "train_file": str(version_dir / "train.na") if train_code else None,
                "language": "dana",  # Track that this is Dana code
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

        self.log_info(f"Stored enhanced function {function_name} version {version}")
        return version_dir

    def load_enhanced_function(self, function_name: str, version: str | None = None) -> dict[str, Any]:
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
        enhanced_file = version_dir / "enhanced.na"
        metadata_file = version_dir / "metadata.json"
        train_file = version_dir / "train.na"

        if not enhanced_file.exists() or not metadata_file.exists():
            raise FileNotFoundError(f"Incomplete function data for {function_name}")

        # Read files
        with open(enhanced_file) as f:
            enhanced_code = f.read()

        with open(metadata_file) as f:
            metadata = json.load(f)

        train_code = None
        if train_file.exists():
            with open(train_file) as f:
                train_code = f.read()

        return {
            "function_name": function_name,
            "version": version_dir.name,
            "enhanced_code": enhanced_code,
            "train_code": train_code,
            "metadata": metadata,
            "version_dir": version_dir,
        }

    def list_function_versions(self, function_name: str) -> list[str]:
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

    def get_current_version(self, function_name: str) -> str | None:
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

    def store_execution_context(self, execution_id: str, context: dict[str, Any]) -> Path:
        """Store execution context for feedback correlation"""
        executions_dir = self.base_path / "executions"
        execution_file = executions_dir / f"{execution_id}.json"

        context_with_metadata = {**context, "stored_at": datetime.now().isoformat(), "execution_id": execution_id}

        with open(execution_file, "w") as f:
            json.dump(context_with_metadata, f, indent=2)

        self.log_debug(f"Stored execution context for {execution_id}")
        return execution_file

    def load_execution_context(self, execution_id: str) -> dict[str, Any]:
        """Load execution context"""
        executions_dir = self.base_path / "executions"
        execution_file = executions_dir / f"{execution_id}.json"

        if not execution_file.exists():
            raise FileNotFoundError(f"Execution context {execution_id} not found")

        with open(execution_file) as f:
            return json.load(f)

    def store_feedback(self, execution_id: str, feedback_data: dict[str, Any]) -> Path:
        """Store feedback data"""
        feedback_dir = self.base_path / "feedback"
        feedback_file = feedback_dir / f"{execution_id}_feedback.json"

        # Load existing feedback or create new
        if feedback_file.exists():
            with open(feedback_file) as f:
                existing_feedback = json.load(f)
            if not isinstance(existing_feedback, list):
                existing_feedback = [existing_feedback]
        else:
            existing_feedback = []

        # Add new feedback
        feedback_entry = {**feedback_data, "stored_at": datetime.now().isoformat()}
        existing_feedback.append(feedback_entry)

        # Store updated feedback
        with open(feedback_file, "w") as f:
            json.dump(existing_feedback, f, indent=2)

        self.log_debug(f"Stored feedback for execution {execution_id}")
        return feedback_file

    def load_feedback(self, execution_id: str) -> list[dict[str, Any]]:
        """Load feedback data"""
        feedback_dir = self.base_path / "feedback"
        feedback_file = feedback_dir / f"{execution_id}_feedback.json"

        if not feedback_file.exists():
            return []

        with open(feedback_file) as f:
            feedback = json.load(f)
            if not isinstance(feedback, list):
                return [feedback]
            return feedback

    def get_function_feedback_summary(self, function_name: str) -> dict[str, Any]:
        """Get summary of feedback for a function"""
        feedback_dir = self.base_path / "feedback"
        if not feedback_dir.exists():
            return {"total_feedback": 0, "feedback_by_version": {}}

        # Collect all feedback files
        feedback_files = list(feedback_dir.glob("*_feedback.json"))
        total_feedback = 0
        feedback_by_version = {}

        for feedback_file in feedback_files:
            with open(feedback_file) as f:
                feedback_data = json.load(f)
                if not isinstance(feedback_data, list):
                    feedback_data = [feedback_data]

                for entry in feedback_data:
                    if entry.get("function_name") == function_name:
                        total_feedback += 1
                        version = entry.get("version", "unknown")
                        if version not in feedback_by_version:
                            feedback_by_version[version] = 0
                        feedback_by_version[version] += 1

        return {
            "total_feedback": total_feedback,
            "feedback_by_version": feedback_by_version,
        }

    def cleanup_old_versions(self, function_name: str, keep_versions: int = 5):
        """Clean up old versions of a function"""
        versions = self.list_function_versions(function_name)
        if len(versions) <= keep_versions:
            return

        # Keep the most recent versions
        versions_to_remove = versions[:-keep_versions]
        function_dir = self.base_path / function_name

        for version in versions_to_remove:
            version_dir = function_dir / version
            if version_dir.exists():
                shutil.rmtree(version_dir)
                self.log_debug(f"Removed old version {version} of {function_name}")

    def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics"""
        stats = {
            "total_functions": 0,
            "total_versions": 0,
            "total_executions": 0,
            "total_feedback": 0,
            "storage_size": 0,
        }

        # Count functions and versions
        for function_dir in self.base_path.iterdir():
            if function_dir.is_dir() and function_dir.name not in ["executions", "feedback", "cache", "magic"]:
                stats["total_functions"] += 1
                versions = self.list_function_versions(function_dir.name)
                stats["total_versions"] += len(versions)

        # Count executions
        executions_dir = self.base_path / "executions"
        if executions_dir.exists():
            stats["total_executions"] = len(list(executions_dir.glob("*.json")))

        # Count feedback
        feedback_dir = self.base_path / "feedback"
        if feedback_dir.exists():
            stats["total_feedback"] = len(list(feedback_dir.glob("*_feedback.json")))

        # Calculate storage size
        stats["storage_size"] = sum(f.stat().st_size for f in self.base_path.rglob("*") if f.is_file())

        return stats

    def get_cached_generated_code(self, function_name: str, source_hash: str) -> dict[str, Any] | None:
        """Get cached generated code for a function"""
        cache_dir = self.base_path / "cache"
        cache_file = cache_dir / f"{function_name}_{source_hash}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file) as f:
                cache_data = json.load(f)
                if cache_data.get("source_hash") != source_hash:
                    return None
                return cache_data
        except Exception as e:
            self.log_error(f"Error reading cache for {function_name}: {e}")
            return None

    def cache_generated_code(self, function_name: str, source_hash: str, generated_code: str, metadata: dict[str, Any]) -> None:
        """Cache generated code for a function"""
        cache_dir = self.base_path / "cache"
        cache_file = cache_dir / f"{function_name}_{source_hash}.json"

        cache_data = {
            "function_name": function_name,
            "source_hash": source_hash,
            "generated_code": generated_code,
            "metadata": metadata,
            "cached_at": datetime.now().isoformat(),
        }

        try:
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
            self.log_debug(f"Cached generated code for {function_name}")
        except Exception as e:
            self.log_error(f"Error caching generated code for {function_name}: {e}")

    def _get_current_poet_version(self) -> str:
        """Get current POET version"""
        # TODO: Implement version tracking
        return "1.0.0-alpha"


# Global storage instance
_default_storage: dict[str, POETStorage] = {}


def get_default_storage(module_file: str | None = None) -> POETStorage:
    """Get default storage instance for a given module file"""
    global _default_storage
    key = str(Path(module_file).parent.resolve()) if module_file else "__default__"
    if key not in _default_storage:
        _default_storage[key] = POETStorage(module_file)
    return _default_storage[key]


def set_storage_path(path: str):
    """Set storage path for default instance"""
    global _default_storage
    _default_storage = POETStorage(path)
