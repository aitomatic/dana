import os
import sys

from dana.common.base_war import BaseWAR


class BasePromptEngineer:
    def __init__(self, component: BaseWAR):
        self._component = component

    def _get_user_prompt_file(self, class_name: str) -> str:
        """Get user-specific prompt file path."""
        home_dir = os.path.expanduser("~")
        return os.path.join(home_dir, ".dana", "prompts", f"{class_name}.xml")

    def _get_lib_prompt_file(self, class_name: str) -> str:
        """Get lib/prompts file path."""
        project_root = self._find_library_root()
        return os.path.join(project_root, "lib", "prompts", f"{class_name}.xml")

    def _get_core_prompt_file(self, class_name: str) -> str:
        """Get core/prompts file path."""
        project_root = self._find_library_root()
        return os.path.join(project_root, "core", "prompts", f"{class_name}.xml")

    def get_prompt(self) -> str:
        return self._component.get_prompt()

    def _find_library_root(self) -> str:
        """Find dana library root (not agent project root) by looking for pyproject.toml or setup.py."""
        module_name = self._component.__class__.__module__
        depth = module_name.count(".")

        module = sys.modules[module_name]
        module_file = module.__file__
        if module_file is None:
            return os.getcwd()
        current_dir = os.path.dirname(module_file)

        for _ in range(depth - 1):
            current_dir = os.path.dirname(current_dir)

        return current_dir

    def _load_file_content(self, file_path: str) -> str:
        """Load raw text content from a single .xml file."""
        if not file_path or not os.path.exists(file_path):
            return ""

        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""

    def _get_co_located_prompt_file(self, class_name: str) -> str:
        """Get co-located prompt file path - searches multiple locations relative to agent file."""
        module_name = self._component.__class__.__module__
        module = sys.modules[module_name]
        module_file = module.__file__
        if module_file is None:
            return ""

        module_dir = os.path.dirname(module_file)

        # Try multiple extensions
        extensions = [".xml", ".prt"]

        # Priority 1: Same directory as agent .py
        for ext in extensions:
            path = os.path.join(module_dir, f"{class_name}{ext}")
            if os.path.exists(path):
                return path

        # Priority 2: Under prompts/ subdirectory
        for ext in extensions:
            path = os.path.join(module_dir, "prompts", f"{class_name}{ext}")
            if os.path.exists(path):
                return path

        # Priority 3+: Walk up directories looking for prompts/ folder
        # Stop at project root (look for pyproject.toml, setup.py, or git root)
        current_dir = module_dir
        for _ in range(10):  # Max 10 levels up
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Reached filesystem root
                break

            # Check for prompts/ in parent
            for ext in extensions:
                path = os.path.join(parent_dir, "prompts", f"{class_name}{ext}")
                if os.path.exists(path):
                    return path

            # Stop if we hit a project root marker
            if (
                os.path.exists(os.path.join(parent_dir, "pyproject.toml"))
                or os.path.exists(os.path.join(parent_dir, "setup.py"))
                or os.path.exists(os.path.join(parent_dir, ".git"))
            ):
                break

            current_dir = parent_dir

        return ""

    def _load_inherited_prompt_content(self) -> str:
        """Load and concatenate prompt files from inheritance chain (parent to child)."""
        # Get the Method Resolution Order (MRO) for inheritance support
        class_names = [cls.__name__ for cls in self._component.__class__.__mro__ if issubclass(cls, BaseWAR)]
        content_parts = []

        # Process classes in REVERSE MRO order (parent -> child)
        # Child sections will appear later in text, so searches find child version first
        for class_name in reversed(class_names):
            # Try to find a prompt file for this class (in priority order)
            user_prompt_file = self._get_user_prompt_file(class_name)
            if user_prompt_file and os.path.exists(user_prompt_file):
                content = self._load_file_content(user_prompt_file)
                if content:
                    content_parts.append(content)
                continue

            lib_prompt_file = self._get_lib_prompt_file(class_name)
            if lib_prompt_file and os.path.exists(lib_prompt_file):
                content = self._load_file_content(lib_prompt_file)
                if content:
                    content_parts.append(content)
                continue

            core_prompt_file = self._get_core_prompt_file(class_name)
            if core_prompt_file and os.path.exists(core_prompt_file):
                content = self._load_file_content(core_prompt_file)
                if content:
                    content_parts.append(content)
                continue

            co_located_file = self._get_co_located_prompt_file(class_name)
            if co_located_file and os.path.exists(co_located_file):
                content = self._load_file_content(co_located_file)
                if content:
                    content_parts.append(content)

        # Join with newlines; when searching, later sections override earlier ones
        return "\n\n".join(content_parts)