"""
Dana Language Server implementation using pygls.

This module provides a Language Server Protocol (LSP) implementation for Dana,
offering real-time diagnostics, hover information, and other editor features.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from lsprotocol import types as lsp
    from pygls.server import LanguageServer

    LSP_AVAILABLE = True
except ImportError:
    LSP_AVAILABLE = False
    logger.warning("LSP dependencies not installed. Install with: pip install lsprotocol pygls")

from dana.core.lang.parser.utils.parsing_utils import ParserCache


def main():
    """Main entry point for the Dana Language Server."""
    if not LSP_AVAILABLE:
        logger.error("Cannot start Dana Language Server: LSP dependencies not installed")
        logger.error("Install with: pip install lsprotocol pygls")
        sys.exit(1)

    logger.info("Starting Dana Language Server...")

    # Import LSP-specific code only when dependencies are available
    from dana.core.lang.lsp.analyzer import DanaAnalyzer

    class DanaLanguageServer(LanguageServer):
        """Language Server for Dana providing diagnostics, hover, and other features."""

        def __init__(self):
            """Initialize the Dana Language Server."""
            super().__init__("dana-ls", "0.1.0")
            self.analyzer = DanaAnalyzer()
            self.parser = ParserCache.get_parser("dana")

        async def _validate_document(self, uri: str, text: str):
            """Validate a Dana document and publish diagnostics."""
            try:
                # Parse the document with the existing Dana parser
                diagnostics = await self.analyzer.analyze(text)

                # Publish diagnostics
                self.publish_diagnostics(uri, diagnostics)

            except Exception as e:
                logger.error(f"Error validating document {uri}: {e}")
                # Publish a diagnostic about the validation error
                error_diagnostic = lsp.Diagnostic(
                    range=lsp.Range(start=lsp.Position(line=0, character=0), end=lsp.Position(line=0, character=0)),
                    message=f"Language server error: {str(e)}",
                    severity=lsp.DiagnosticSeverity.Error,
                    source="dana-ls",
                )
                self.publish_diagnostics(uri, [error_diagnostic])

        def _get_document_text(self, uri: str) -> str | None:
            """Safely get document text from workspace."""
            try:
                document = self.workspace.get_document(uri)
                return document.source
            except Exception as e:
                logger.warning(f"Could not retrieve document text for {uri}: {e}")
                return None

    # Create the server instance
    server = DanaLanguageServer()

    @server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
    async def did_open(ls: DanaLanguageServer, params: lsp.DidOpenTextDocumentParams):
        """Handle document open events."""
        logger.info(f"Document opened: {params.text_document.uri}")
        await ls._validate_document(params.text_document.uri, params.text_document.text)

    @server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
    async def did_change(ls: DanaLanguageServer, params: lsp.DidChangeTextDocumentParams):
        """Handle document change events."""
        # Get the full text from the first change (assuming full document sync)
        if params.content_changes:
            text = params.content_changes[0].text
            await ls._validate_document(params.text_document.uri, text)

    @server.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
    async def did_save(ls: DanaLanguageServer, params: lsp.DidSaveTextDocumentParams):
        """Handle document save events."""
        # Re-validate on save
        try:
            text = None

            # Check if text is provided in params (when includeText is true)
            if hasattr(params, "text") and params.text is not None:
                text = params.text
            else:
                # Fall back to reading from workspace if text not provided
                text = ls._get_document_text(params.text_document.uri)

            if text is not None:
                await ls._validate_document(params.text_document.uri, text)
            else:
                logger.warning(f"Could not get document text for validation on save: {params.text_document.uri}")

        except Exception as e:
            logger.warning(f"Error re-validating document on save: {e}")

    @server.feature(lsp.TEXT_DOCUMENT_HOVER)
    async def hover(ls: DanaLanguageServer, params: lsp.HoverParams) -> lsp.Hover | None:
        """Provide hover information for symbols."""
        try:
            # Get document text
            document = ls.workspace.get_document(params.text_document.uri)

            # Get hover information from analyzer
            hover_info = await ls.analyzer.get_hover(document.source, params.position.line, params.position.character)

            if hover_info:
                return lsp.Hover(contents=lsp.MarkupContent(kind=lsp.MarkupKind.Markdown, value=hover_info))
        except Exception as e:
            logger.warning(f"Error providing hover: {e}")

        return None

    @server.feature(lsp.TEXT_DOCUMENT_COMPLETION)
    async def completion(ls: DanaLanguageServer, params: lsp.CompletionParams) -> lsp.CompletionList:
        """Provide completion suggestions."""
        try:
            document = ls.workspace.get_document(params.text_document.uri)

            # Get completions from analyzer
            completions = await ls.analyzer.get_completions(document.source, params.position.line, params.position.character)

            completion_items = []
            for completion in completions:
                item = lsp.CompletionItem(
                    label=completion["label"],
                    kind=completion.get("kind", lsp.CompletionItemKind.Text),
                    detail=completion.get("detail"),
                    documentation=completion.get("documentation"),
                    insert_text=completion.get("insert_text", completion["label"]),
                )
                completion_items.append(item)

            return lsp.CompletionList(is_incomplete=False, items=completion_items)

        except Exception as e:
            logger.warning(f"Error providing completions: {e}")
            return lsp.CompletionList(is_incomplete=False, items=[])

    # Start the server
    server.start_io()


if __name__ == "__main__":
    main()
