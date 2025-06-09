def visit_ExportStatement(self, node: ExportStatement) -> None:
    """Execute an export statement.

    Args:
        node: Export statement AST node
    """
    # Add name to module's exports
    if not hasattr(self.module, "__exports__"):
        self.module.__exports__ = set()
    self.module.__exports__.add(node.name)
