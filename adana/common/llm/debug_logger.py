"""
Debug logging system for LLM requests and responses.

This module provides comprehensive logging of all LLM interactions for debugging purposes.
Logs are stored in ~/.dana/logs/ with separate files for different types of interactions.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any

import structlog

from .types import LLMMessage, LLMResponse


logger = structlog.get_logger()


class LLMDebugLogger:
    """Debug logger for LLM requests and responses."""

    def __init__(self):
        """Initialize the debug logger."""
        self.log_dir = Path.home() / ".dana" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create separate log files for different types
        self.request_log = self.log_dir / "llm_requests.jsonl"
        self.response_log = self.log_dir / "llm_responses.jsonl"
        self.agent_log = self.log_dir / "agent_interactions.jsonl"
        self.error_log = self.log_dir / "errors.jsonl"

    def log_request(
        self, provider: str, model: str, messages: list[LLMMessage], agent_id: str | None = None, agent_type: str | None = None, **kwargs
    ) -> str:
        """
        Log an LLM request.

        Args:
            provider: LLM provider name
            model: Model name
            messages: List of messages being sent
            agent_id: ID of the agent making the request
            agent_type: Type of the agent making the request
            **kwargs: Additional parameters

        Returns:
            Request ID for correlation with response
        """
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # Convert messages to serializable format
        serializable_messages = []
        for msg in messages:
            serializable_messages.append({"role": msg.role, "content": msg.content, "length": len(msg.content) if msg.content else 0})

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "type": "request",
            "provider": provider,
            "model": model,
            "agent_id": agent_id,
            "agent_type": agent_type,
            "message_count": len(messages),
            "messages": serializable_messages,
            "total_input_length": sum(len(msg.content) if msg.content else 0 for msg in messages),
            "kwargs": {k: str(v) for k, v in kwargs.items()},  # Convert to strings for JSON
        }

        self._write_log_entry(self.request_log, log_entry)
        logger.debug("LLM request logged", request_id=request_id, provider=provider, model=model)

        return request_id

    def log_response(
        self,
        request_id: str,
        response: LLMResponse,
        provider: str,
        model: str,
        agent_id: str | None = None,
        agent_type: str | None = None,
        duration_ms: float | None = None,
    ):
        """
        Log an LLM response.

        Args:
            request_id: Request ID from log_request
            response: LLM response object
            provider: LLM provider name
            model: Model name
            agent_id: ID of the agent that made the request
            agent_type: Type of the agent that made the request
            duration_ms: Request duration in milliseconds
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "type": "response",
            "provider": provider,
            "model": response.model if response.model else model,
            "agent_id": agent_id,
            "agent_type": agent_type,
            "duration_ms": duration_ms,
            "content_length": len(response.content) if response.content else 0,
            "content_preview": response.content[:200] + "..." if response.content and len(response.content) > 200 else response.content,
            "finish_reason": response.finish_reason,
            "usage": response.usage,
            "tool_calls_count": len(response.tool_calls) if response.tool_calls else 0,
            "has_tool_calls": bool(response.tool_calls),
        }

        self._write_log_entry(self.response_log, log_entry)
        logger.debug("LLM response logged", request_id=request_id, content_length=log_entry["content_length"])

    def log_full_response_content(self, request_id: str, content: str, provider: str, model: str):
        """
        Log the full response content in a separate file for detailed debugging.

        Args:
            request_id: Request ID for correlation
            content: Full response content
            provider: LLM provider name
            model: Model name
        """
        full_content_log = self.log_dir / f"full_responses_{datetime.now().strftime('%Y%m%d')}.jsonl"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "provider": provider,
            "model": model,
            "full_content": content,
            "content_length": len(content) if content else 0,
        }

        self._write_log_entry(full_content_log, log_entry)

    def log_agent_interaction(
        self,
        agent_id: str,
        agent_type: str,
        interaction_type: str,
        content: str,
        target_agent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Log agent-to-agent interactions.

        Args:
            agent_id: ID of the agent performing the interaction
            agent_type: Type of the agent
            interaction_type: Type of interaction (query, response, tool_call, etc.)
            content: Content of the interaction
            target_agent_id: ID of target agent (for agent-to-agent calls)
            metadata: Additional metadata
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "agent_type": agent_type,
            "interaction_type": interaction_type,
            "target_agent_id": target_agent_id,
            "content_length": len(content) if content else 0,
            "content_preview": content[:200] + "..." if content and len(content) > 200 else content,
            "metadata": metadata or {},
        }

        self._write_log_entry(self.agent_log, log_entry)
        logger.debug("Agent interaction logged", agent_id=agent_id, interaction_type=interaction_type)

    def log_error(
        self,
        error: Exception,
        context: str,
        request_id: str | None = None,
        agent_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ):
        """
        Log errors for debugging.

        Args:
            error: The exception that occurred
            context: Context where the error occurred
            request_id: Request ID if available
            agent_id: Agent ID if available
            provider: LLM provider if available
            model: Model name if available
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "agent_id": agent_id,
            "provider": provider,
            "model": model,
            "context": context,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_details": getattr(error, "args", []),
        }

        self._write_log_entry(self.error_log, log_entry)
        logger.error("Error logged", context=context, error_type=type(error).__name__)

    def _write_log_entry(self, log_file: Path, entry: dict[str, Any]):
        """
        Write a log entry to a JSONL file.

        Args:
            log_file: Path to the log file
            entry: Log entry dictionary
        """
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            # Fallback logging - don't let logging errors break the application
            logger.error("Failed to write debug log", error=str(e), log_file=str(log_file))

    def get_log_stats(self) -> dict[str, Any]:
        """
        Get statistics about the debug logs.

        Returns:
            Dictionary with log statistics
        """
        stats = {"log_directory": str(self.log_dir), "log_files": {}}

        for log_file in [self.request_log, self.response_log, self.agent_log, self.error_log]:
            if log_file.exists():
                stats["log_files"][log_file.name] = {
                    "size_bytes": log_file.stat().st_size,
                    "line_count": sum(1 for _ in open(log_file, encoding="utf-8")),
                }
            else:
                stats["log_files"][log_file.name] = {"size_bytes": 0, "line_count": 0}

        return stats

    def cleanup_old_logs(self, days_to_keep: int = 7):
        """
        Clean up old log files.

        Args:
            days_to_keep: Number of days of logs to keep
        """
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)

        for log_file in self.log_dir.glob("*.jsonl"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    logger.info("Cleaned up old log file", file=str(log_file))
                except Exception as e:
                    logger.error("Failed to cleanup log file", file=str(log_file), error=str(e))


# Global instance
_debug_logger = None


def get_debug_logger() -> LLMDebugLogger:
    """Get the global debug logger instance."""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = LLMDebugLogger()
    return _debug_logger


def enable_debug_logging():
    """Enable debug logging (creates the logger and log directory)."""
    get_debug_logger()
    logger.info("LLM debug logging enabled", log_dir=str(get_debug_logger().log_dir))


def disable_debug_logging():
    """Disable debug logging."""
    global _debug_logger
    _debug_logger = None
    logger.info("LLM debug logging disabled")
