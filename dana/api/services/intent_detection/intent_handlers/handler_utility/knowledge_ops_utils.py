from dana.api.core.schemas import DomainKnowledgeTree
from pathlib import Path


def save_tree(tree: DomainKnowledgeTree, path: str):
    _path = Path(path)
    _path.write_text(tree.model_dump_json(indent=4))


def load_tree(path: str) -> DomainKnowledgeTree:
    _path = Path(path)
    return DomainKnowledgeTree.model_validate_json(_path.read_text())
