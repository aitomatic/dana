from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field, AliasChoices
from datetime import datetime
from enum import StrEnum
from dana.api.core.schemas import SenderRole
from dana.api.core.schemas import DomainKnowledgeTree, DomainNode


class BaseModelUseEnum(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class BaseMessage(BaseModelUseEnum):
    sender: SenderRole = Field(default=SenderRole.USER, validation_alias=AliasChoices("role"))  # Allow both "sender" and "role" as aliases
    content: str


class HandlerMessage(BaseMessage):
    require_user: bool = False
    treat_as_tool: bool = False
    metadata: dict = {}


class BaseConversation(BaseModelUseEnum):
    messages: list[BaseMessage]


class HandlerConversation(BaseModelUseEnum):
    messages: list[HandlerMessage]


class KnowledgePackResponse(BaseModel):
    success: bool
    is_tree_modified: bool = False
    agent_response: str
    internal_conversation: list[HandlerMessage] = []
    error: str | None = None


class AddChildNodeRequest(BaseModel):
    child_topics: list[str]


class DomainNodeV2(DomainNode):
    children: list[DomainNodeV2] = []

    def _resolve_path(self, tree_node_path: str | list[str]) -> list[str]:
        if isinstance(tree_node_path, str):
            tree_node_path = tree_node_path.split("/")
        return tree_node_path

    def _is_empty_path(self, tree_node_path: list[str]) -> bool:
        if not tree_node_path:
            return True
        if len(tree_node_path) == 1 and not tree_node_path[0]:
            return True
        return False

    def find_node_by_path(self, tree_node_path: list[str]) -> tuple[DomainNodeV2 | None, int, DomainNodeV2 | None]:
        for idx, child in enumerate(self.children):
            if child.topic == tree_node_path[0]:
                if len(tree_node_path) == 1:
                    return self, idx, child
                else:
                    return child.find_node_by_path(tree_node_path[1:])
        return None, -1, None

    def get_str(self, indent_level: int = 0, indent: int = 2, is_last: bool | None = None, parent_prefix: str = "") -> str:
        prefix_str = "└── " if is_last is True else "├── " if is_last is False else ""
        _str = f"{parent_prefix}{prefix_str}{self.topic}\n"

        for i, child in enumerate(self.children):
            is_child_last = i == len(self.children) - 1
            # Build the prefix for children: parent prefix + current connection + spacing
            child_prefix = parent_prefix + ("    " if is_last is True else "│   " if is_last is False else "")
            child_str = child.get_str(indent_level + 1, indent, is_child_last, child_prefix)
            _str += child_str
        return _str


class DomainKnowledgeTreeV2(DomainKnowledgeTree):
    root: DomainNodeV2

    def _resolve_path(self, tree_node_path: str | list[str]) -> list[str]:
        if isinstance(tree_node_path, str):
            tree_node_path = tree_node_path.split("/")
        return tree_node_path

    def _check_empty_path(self, tree_node_path: list[str]) -> bool:
        if not tree_node_path:
            return True
        if len(tree_node_path) == 1 and not tree_node_path[0]:
            return True
        return False

    def _check_path_has_valid_root(self, tree_node_path: list[str]) -> bool:
        if len(tree_node_path) >= 1 and tree_node_path[0] == self.root.topic:
            return True
        return False

    def delete_node(self, tree_node_path: str | list[str]) -> None:
        tree_node_path = self._resolve_path(tree_node_path)
        # Handle delete root node
        if len(tree_node_path) == 1 and tree_node_path[0] == self.root.topic:
            raise ValueError("Cannot delete root node. Try modifying the node name instead.")

        # Handle empty paths - if path is empty or contains only empty strings, do nothing
        if self._check_empty_path(tree_node_path):
            return

        if not self._check_path_has_valid_root(tree_node_path):
            raise ValueError(f"Root node '{self.root.topic}' doesn't match path '{tree_node_path[0]}'")

        target_parent, target_index, target_node = self.root.find_node_by_path(tree_node_path[1:])
        if target_node and target_parent:
            target_parent.children.pop(target_index)

    def update_node_name(self, tree_node_path: str | list[str], node_name: str) -> None:
        tree_node_path = self._resolve_path(tree_node_path)
        # Handle empty paths - if path is empty or contains only empty strings, do nothing
        if self._check_empty_path(tree_node_path):
            return
        if not self._check_path_has_valid_root(tree_node_path):
            raise ValueError(f"Root node '{self.root.topic}' doesn't match path '{tree_node_path[0]}'")
        target_parent, _, target_node = self.root.find_node_by_path(tree_node_path[1:])
        if target_node and target_parent:
            target_node.topic = node_name

    def add_children_to_node(self, tree_node_path: str | list[str], child_topics: list[str]) -> None:
        """
        Add child nodes to the specified path in the tree.
        tree_node_path: should be a list of strings or a single string starting from root.
        child_topics: the topic name(s) for the new child node(s). Can be a single string or list of strings.
        """
        tree_node_path = self._resolve_path(tree_node_path)

        # Handle empty paths - if path is empty or contains only empty strings, add to root
        if self._check_empty_path(tree_node_path):
            return

        # Handle adding to root node
        if not self._check_path_has_valid_root(tree_node_path):
            raise ValueError(f"Root node '{self.root.topic}' doesn't match path '{tree_node_path[0]}'")

        target_parent, _, target_node = self.root.find_node_by_path(tree_node_path[1:])
        if target_node and target_parent:
            current_child_topics = set([child.topic for child in target_node.children])
            for child_topic in child_topics:
                if child_topic not in current_child_topics:
                    new_child = DomainNodeV2(topic=child_topic, children=[])
                    target_node.children.append(new_child)

    def get_str(self, indent_level: int = 0, indent: int = 2) -> str:
        return self.root.get_str(indent_level, indent, is_last=None, parent_prefix="")


class BackgroundTaskStatus(StrEnum):
    """Status values for background tasks."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BackgroundTaskType(StrEnum):
    """Task type values for background tasks."""

    KNOWLEDGE_GEN = "knowledge_gen"
    DEEP_EXTRACT = "deep_extract"


class BackgroundTaskResponse(BaseModel):
    id: int
    type: str
    status: BackgroundTaskStatus
    data: dict = {}
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(use_enum_values=True)


class PageContent(BaseModel):
    text: str
    page_number: int


class ExtractionOutput(BaseModel):
    original_filename: str
    source_document_id: int
    extraction_date: str
    total_pages: int
    documents: list[PageContent] = []


if __name__ == "__main__":
    with open("dana/api/server/assets/jordan_financial_analyst/domain_knowledge.json") as f:
        tree = DomainKnowledgeTreeV2.model_validate_json(f.read())
        print(tree.get_str())
