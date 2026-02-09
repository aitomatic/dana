from .base_resource import BaseResource
from .bash import BashResource
from .file_edit_resource import FileEditResource
from .file_io_resource import FileIOResource
from .search_resource import SearchResource
from .task_resource import TaskResource
from .todo_resource import ToDoResource


def __getattr__(name: str):
    """Lazy import DanaSkillResource to avoid circular import."""
    if name == "DanaSkillResource":
        from dana.core.skills import DanaSkillResource

        return DanaSkillResource
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseResource",
    "BashResource",
    "FileIOResource",
    "ToDoResource",
    "FileEditResource",
    "SearchResource",
    "TaskResource",
    "DanaSkillResource",
]
