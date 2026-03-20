"""Convert canonical multimodal content blocks to provider-specific wire formats.

Internal canonical format (Anthropic-style):
  Image:    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "..."}}
  Audio:    {"type": "audio", "source": {"type": "base64", "media_type": "audio/wav", "data": "..."}}
  Video:    {"type": "video", "source": {"type": "base64", "media_type": "video/mp4", "data": "..."}}
  Document: {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": "..."}}
  Text:     {"type": "text", "text": "..."}
"""

from __future__ import annotations

import base64
from typing import Any


# Block types that carry binary media
MULTIMODAL_TYPES = {"image", "audio", "video", "document"}


def is_multimodal_content(content: str | list[dict]) -> bool:
    """Check if content contains multimodal (non-text) blocks."""
    if isinstance(content, str):
        return False
    return any(block.get("type") in MULTIMODAL_TYPES for block in content)


def _unsupported_placeholder(block: dict) -> dict:
    """Create a text placeholder for an unsupported media block."""
    block_type = block.get("type", "unknown")
    media_type = block.get("source", {}).get("media_type", "")
    return {"type": "text", "text": f"[{block_type} content ({media_type}) not supported by this model]"}


def _extract_audio_format(media_type: str) -> str:
    """Extract audio format from media_type (e.g. 'audio/wav' -> 'wav')."""
    if "/" in media_type:
        fmt = media_type.split("/", 1)[1]
        # Normalize common variants
        if fmt in ("mpeg", "mp3"):
            return "mp3"
        return fmt
    return "wav"


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------


def convert_for_anthropic(
    blocks: list[dict],
    supports_vision: bool = True,
    supports_audio: bool = False,
    supports_video: bool = False,
) -> list[dict]:
    """Convert canonical blocks to Anthropic wire format.

    Image/document are already in Anthropic format (pass-through).
    Audio/video -> text placeholder (Anthropic doesn't support them as of 2026-03).
    """
    result: list[dict] = []
    for block in blocks:
        btype = block.get("type", "text")
        if btype == "text":
            result.append(block)
        elif btype == "image":
            result.append(block if supports_vision else _unsupported_placeholder(block))
        elif btype == "document":
            result.append(block if supports_vision else _unsupported_placeholder(block))
        elif btype == "audio":
            result.append(block if supports_audio else _unsupported_placeholder(block))
        elif btype == "video":
            result.append(block if supports_video else _unsupported_placeholder(block))
        else:
            result.append(block)
    return result


# ---------------------------------------------------------------------------
# OpenAI Chat Completions
# ---------------------------------------------------------------------------


def _canonical_image_to_openai(block: dict) -> dict:
    """Convert canonical image block to OpenAI image_url format."""
    source = block.get("source", {})
    if source.get("type") == "url":
        url = source["url"]
    else:
        # base64
        media_type = source.get("media_type", "image/png")
        data = source.get("data", "")
        url = f"data:{media_type};base64,{data}"
    return {"type": "image_url", "image_url": {"url": url, "detail": "auto"}}


def _canonical_audio_to_openai(block: dict) -> dict:
    """Convert canonical audio block to OpenAI input_audio format."""
    source = block.get("source", {})
    media_type = source.get("media_type", "audio/wav")
    data = source.get("data", "")
    return {
        "type": "input_audio",
        "input_audio": {"data": data, "format": _extract_audio_format(media_type)},
    }


def convert_for_openai(
    blocks: list[dict],
    supports_vision: bool = True,
    supports_audio: bool = False,
    supports_video: bool = False,
) -> list[dict]:
    """Convert canonical blocks to OpenAI Chat Completions wire format."""
    result: list[dict] = []
    for block in blocks:
        btype = block.get("type", "text")
        if btype == "text":
            result.append(block)
        elif btype == "image":
            result.append(_canonical_image_to_openai(block) if supports_vision else _unsupported_placeholder(block))
        elif btype == "audio":
            result.append(_canonical_audio_to_openai(block) if supports_audio else _unsupported_placeholder(block))
        elif btype == "video":
            # OpenAI doesn't support video input
            result.append(_unsupported_placeholder(block))
        elif btype == "document":
            if supports_vision:
                # OpenAI accepts PDFs via file content part
                source = block.get("source", {})
                data = source.get("data", "")
                media_type = source.get("media_type", "application/pdf")
                result.append(
                    {
                        "type": "file",
                        "file": {"file_data": f"data:{media_type};base64,{data}"},
                    }
                )
            else:
                result.append(_unsupported_placeholder(block))
        else:
            result.append(block)
    return result


# ---------------------------------------------------------------------------
# OpenAI Responses API
# ---------------------------------------------------------------------------


def convert_for_openai_responses(
    blocks: list[dict],
    supports_vision: bool = True,
    supports_audio: bool = False,
    supports_video: bool = False,
) -> list[dict]:
    """Convert canonical blocks to OpenAI Responses API wire format."""
    result: list[dict] = []
    for block in blocks:
        btype = block.get("type", "text")
        if btype == "text":
            result.append({"type": "input_text", "text": block.get("text", "")})
        elif btype == "image":
            if supports_vision:
                source = block.get("source", {})
                if source.get("type") == "url":
                    url = source["url"]
                else:
                    media_type = source.get("media_type", "image/png")
                    data = source.get("data", "")
                    url = f"data:{media_type};base64,{data}"
                result.append({"type": "input_image", "image_url": url})
            else:
                result.append({"type": "input_text", "text": _unsupported_placeholder(block)["text"]})
        elif btype == "audio":
            result.append(
                _canonical_audio_to_openai(block)
                if supports_audio
                else {"type": "input_text", "text": _unsupported_placeholder(block)["text"]}
            )
        elif btype == "video":
            result.append({"type": "input_text", "text": _unsupported_placeholder(block)["text"]})
        elif btype == "document":
            if supports_vision:
                source = block.get("source", {})
                data = source.get("data", "")
                media_type = source.get("media_type", "application/pdf")
                result.append(
                    {
                        "type": "file",
                        "file": {"file_data": f"data:{media_type};base64,{data}"},
                    }
                )
            else:
                result.append({"type": "input_text", "text": _unsupported_placeholder(block)["text"]})
        else:
            result.append(block)
    return result


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------


def convert_for_gemini(
    blocks: list[dict],
    supports_vision: bool = True,
    supports_audio: bool = True,
    supports_video: bool = True,
) -> list[Any]:
    """Convert canonical blocks to Gemini types.Part objects.

    Returns a mixed list of str and types.Part objects, which Gemini accepts
    directly in the `contents` parameter.
    """
    from google.genai import types as genai_types

    parts: list[Any] = []
    for block in blocks:
        btype = block.get("type", "text")
        if btype == "text":
            parts.append(genai_types.Part(text=block.get("text", "")))
        elif btype in ("image", "document"):
            if supports_vision:
                parts.append(_canonical_to_gemini_part(block, genai_types))
            else:
                parts.append(genai_types.Part(text=_unsupported_placeholder(block)["text"]))
        elif btype == "audio":
            if supports_audio:
                parts.append(_canonical_to_gemini_part(block, genai_types))
            else:
                parts.append(genai_types.Part(text=_unsupported_placeholder(block)["text"]))
        elif btype == "video":
            if supports_video:
                parts.append(_canonical_to_gemini_part(block, genai_types))
            else:
                parts.append(genai_types.Part(text=_unsupported_placeholder(block)["text"]))
        else:
            parts.append(genai_types.Part(text=str(block)))
    return parts


def _canonical_to_gemini_part(block: dict, genai_types: Any) -> Any:
    """Convert a canonical media block to a Gemini Part."""
    source = block.get("source", {})
    if source.get("type") == "url":
        return genai_types.Part.from_uri(file_uri=source["url"], mime_type=source.get("media_type", ""))
    # base64 -> bytes
    data = source.get("data", "")
    raw_bytes = base64.b64decode(data)
    media_type = source.get("media_type", "application/octet-stream")
    return genai_types.Part.from_bytes(data=raw_bytes, mime_type=media_type)
