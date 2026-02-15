# Multimodal Read Tool - Product Requirements Document

## Overview

Enhance DanaCodingAgent's Read tool to support images and PDFs, bringing it to parity with Claude Code's Read tool. The LLM will be able to visually analyze images, read PDF documents (including embedded charts and diagrams), and continue reading text files as before.

| Aspect | Description |
|--------|-------------|
| Nature | Multimodal file reading capability for DanaCodingAgent |
| Current State | Text-only (UTF-8 files with cat -n formatting) |
| Target State | Text + Images (PNG, JPG, etc.) + PDFs (with page selection) |
| Key Insight | Anthropic API natively processes images and PDFs — we just need to deliver base64-encoded content |

## Problem Statement

DanaCodingAgent's Read tool can only read text files. When the agent encounters an image or PDF, it returns `"Error: Cannot read file as text (binary file?)"`. This is a critical gap because:

- Users working with industrial/engineering data frequently share **screenshots of dashboards**, **trend charts**, and **PDF case reports**
- The Anthropic API natively supports multimodal content (images, PDFs) — the LLM *can* understand these files, but our pipeline doesn't deliver them
- Claude Code's Read tool handles all of these seamlessly, setting the user expectation

## Why This Matters

1. **Capability Gap**: The LLM can understand images and PDFs, but our agent can't feed them to it
2. **User Workflow**: Industrial users regularly share dashboard screenshots, vibration trend PNGs, and PDF case reports — all currently unreadable
3. **Parity with Claude Code**: Users expect the same Read tool capabilities they get in Claude Code
4. **Chart Understanding**: PDF reports often contain embedded charts that are invisible to text extraction (e.g., a PDF page with 9 trend charts returns only 179 chars of text via pymupdf)

## User Stories

### Story 1: Read Dashboard Screenshots
> As a user, I want to share a PNG screenshot of my monitoring dashboard with the agent, so it can analyze the KPI values and alert statuses visually.

### Story 2: Read PDF Case Reports
> As a user, I want the agent to read a PDF case report (including embedded charts and tables), so it can summarize findings and recommendations.

### Story 3: Read Specific PDF Pages
> As a user, I want to read specific pages from a large PDF (e.g., pages 3-5 of a 50-page report), so I don't overwhelm the context window.

### Story 4: Read Trend Chart Images
> As a user, I want to share vibration trend or temperature trend PNGs with the agent, so it can identify anomalies and step changes visually.

## Technical Investigation Summary

### What We Tested

1. **Claude Code Read tool on images**: Returns `<output_image>` blocks — actual visual content the LLM can see and describe (dashboard KPIs, chart trends, axis labels)
2. **Claude Code Read tool on PDFs**: Returns extracted text per page + visual page renders. The LLM sees both text content and embedded charts
3. **pymupdf text extraction on chart-heavy PDF page**: Returns only 179 chars (header/footer). Charts are completely invisible to text extraction
4. **pymupdf page render (`get_pixmap`)**: Renders full page as image including charts — works, but charts are small
5. **pymupdf embedded image extraction (`get_images`)**: Extracts individual chart images at full resolution — best quality

### Key Insight: Anthropic API Does the Heavy Lifting

The Anthropic API natively processes:
- **Images**: `{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "..."}}`
- **PDFs**: `{"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": "..."}}`

We don't need to extract text from PDFs or OCR images — we just need to deliver the raw bytes as base64 to the API.

### Current Pipeline Constraint

The tool result pipeline is **text-only** at every layer:

```
Tool returns value → json.dumps to string → TimelineEntry.content: str → LLMMessage.content: str → API call
```

Modifying the tool result pipeline would require changes to 4+ layers.

### Chosen Approach: `inject_as_user` Pattern

The codebase already has an `inject_as_user` mechanism (used by Skill resource):

```
Tool returns dict with "inject_as_user" key
    ↓
_act_async() extracts inject_as_user content
    ↓
Tool result text → RESOURCE_RESULT entry (role="tool")
Injected content → USER_MESSAGE entry (role="user")  ← multimodal goes here
    ↓
LLM sees: tool result text + user message with image/PDF content
```

This requires widening only the **user message injection path**, not the entire tool result pipeline.

## Proposed Solution

### Architecture

```
User: "Read this chart image: /path/to/chart.png"
     │
     ▼
LLM calls Read(file_path="/path/to/chart.png")
     │
     ▼
FileIOResource.read()
  ├── Detects file type (extension + magic bytes)
  ├── Routes to handler:
  │   ├── .png/.jpg/.gif/.webp → _read_image()
  │   ├── .pdf → _read_pdf()
  │   └── default → _read_text() (existing behavior)
  │
  ├── _read_image():
  │   ├── Read raw bytes
  │   ├── Base64 encode
  │   └── Return {"message": "Image: chart.png (512x384, PNG)",
  │               "inject_as_user": [content_blocks]}
  │
  ├── _read_pdf():
  │   ├── Read raw bytes (full PDF or specific pages)
  │   ├── Base64 encode
  │   └── Return {"message": "PDF: report.pdf (5 pages, 463KB)",
  │               "inject_as_user": [content_blocks]}
  │
  └── _read_text():
      └── Existing cat-n behavior (unchanged)
     │
     ▼
_act_async() processes inject_as_user
     │
     ▼
Timeline: RESOURCE_RESULT("Image: chart.png...") + USER_MESSAGE([content_blocks])
     │
     ▼
LLM sees the image/PDF visually + tool result text
```

### Content Block Formats

**Image content block:**
```python
[
    {"type": "text", "text": "Visual contents of chart.png:"},
    {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": "<base64-encoded-bytes>"
        }
    }
]
```

**PDF content block:**
```python
[
    {"type": "text", "text": "Contents of report.pdf (pages 1-5):"},
    {
        "type": "document",
        "source": {
            "type": "base64",
            "media_type": "application/pdf",
            "data": "<base64-encoded-bytes>"
        }
    }
]
```

### Changes Required

#### Layer 1: FileIOResource (Read tool) — `file_io_resource.py`

- Add file type detection (extension-based, with magic byte fallback)
- Add `_read_image()` handler: read bytes → base64 → return with `inject_as_user`
- Add `_read_pdf()` handler: read bytes → base64 → return with `inject_as_user`
- Add `pages` parameter to `read()` method for PDF page selection
- For PDFs with `pages` parameter: use pymupdf to extract specific pages, then base64 encode the subset PDF
- Existing `_read_text()` behavior unchanged

#### Layer 2: LLMMessage — `types.py`

- Widen `content: str` to `content: str | list[dict]`
- This allows user messages to carry multimodal content blocks

#### Layer 3: TimelineEntry — `timeline.py`

- Allow `content` field to hold `str | list[dict]`
- In `_format_entry_content()`: pass content blocks through without stringifying
- Only apply truncation/labeling to string content, not content blocks

#### Layer 4: Provider Formatting — `compressed_timeline.py`

- When building Anthropic API messages, handle user messages with content block lists
- Pass content blocks directly as the message content array

## Requirements

### Functional Requirements

#### FR-1: Image Reading
- **FR-1.1**: Detect image files by extension (.png, .jpg, .jpeg, .gif, .webp, .bmp, .svg)
- **FR-1.2**: Read image bytes and base64 encode
- **FR-1.3**: Inject as multimodal content block via `inject_as_user`
- **FR-1.4**: Return descriptive text as tool result (filename, dimensions if detectable, format)
- **FR-1.5**: Handle common image errors (file too large, corrupt file)

#### FR-2: PDF Reading
- **FR-2.1**: Detect PDF files by extension (.pdf) and/or magic bytes (%PDF)
- **FR-2.2**: Read full PDF when small (≤10 pages) and no `pages` parameter
- **FR-2.3**: Support `pages` parameter for page range selection (e.g., "1-5", "3", "10-20")
- **FR-2.4**: Require `pages` parameter for PDFs >10 pages
- **FR-2.5**: Cap at 20 pages per request
- **FR-2.6**: Use pymupdf to extract page subsets when `pages` parameter is provided
- **FR-2.7**: Inject PDF as document content block via `inject_as_user`

#### FR-3: Text Reading (Unchanged)
- **FR-3.1**: Existing cat-n format behavior preserved exactly
- **FR-3.2**: offset/limit parameters work as before
- **FR-3.3**: Line truncation at 2000 chars preserved

#### FR-4: Pipeline Support
- **FR-4.1**: `LLMMessage.content` accepts `str | list[dict]`
- **FR-4.2**: `TimelineEntry` preserves content block lists without stringifying
- **FR-4.3**: Provider formatting passes content blocks to Anthropic API
- **FR-4.4**: `inject_as_user` mechanism handles both string and list[dict] content

### Non-Functional Requirements

#### NFR-1: Size Limits
- **NFR-1.1**: Warn/error for images > 20MB (Anthropic API limit)
- **NFR-1.2**: Enforce 20-page limit per PDF read request
- **NFR-1.3**: Total base64 payload should not exceed API limits

#### NFR-2: Backward Compatibility
- **NFR-2.1**: Text file reading behavior is 100% unchanged
- **NFR-2.2**: Existing tools using string content continue to work
- **NFR-2.3**: Timeline serialization/deserialization handles both formats
- **NFR-2.4**: No changes to tool result pipeline (only user message injection path)

#### NFR-3: Dependencies
- **NFR-3.1**: pymupdf (fitz) only required for PDF page extraction (`pages` parameter)
- **NFR-3.2**: No new system-level dependencies (no poppler, no external binaries)
- **NFR-3.3**: Image reading uses only Python stdlib (pathlib, base64, mimetypes)

## Scope

### In MVP
- ✅ Image reading (PNG, JPG, GIF, WebP) via base64 injection
- ✅ PDF reading (full document) via base64 injection
- ✅ `pages` parameter for PDF page selection (requires pymupdf)
- ✅ `LLMMessage.content` type widening
- ✅ `TimelineEntry` content block support
- ✅ Provider formatting for multimodal user messages
- ✅ File type detection by extension
- ✅ Size limit enforcement

### Out of MVP (Future)
- ❌ Jupyter notebook structured parsing (.ipynb → cells + outputs)
- ❌ Magic byte detection (fallback when extension is wrong/missing)
- ❌ Image resizing/compression for large images
- ❌ PDF text extraction fallback (for when API document support is unavailable)
- ❌ Word document (.docx) support
- ❌ Excel spreadsheet (.xlsx) support
- ❌ Multimodal tool results (modifying the RESOURCE_RESULT path)

## Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Large images/PDFs blow up context window | High | Medium | Size limits, page caps, clear error messages |
| Content blocks break timeline serialization | Medium | Low | Backward-compatible type widening, test both formats |
| Anthropic API format changes | Low | Low | Isolate content block construction in helper functions |
| pymupdf not installed | Low | Medium | Graceful fallback: send full PDF, warn about page selection |
| inject_as_user ordering issues | Medium | Low | Existing test coverage for ordering (`test_inject_as_user_ordering.py`) |

## Files to Modify

| File | Change |
|------|--------|
| `dana_agent/dana/core/resource/file_io_resource.py` | Add image/PDF handlers, `pages` param, `inject_as_user` return |
| `dana_agent/dana/common/llm/types.py` | Widen `LLMMessage.content` to `str \| list[dict]` |
| `dana_agent/dana/core/agent/timeline.py` | Handle content blocks in `_format_entry_content()` |
| `dana_agent/dana/core/agent/compressed_timeline.py` | Pass content blocks through in provider formatting |
| `dana_agent/dana/core/agent/star_agent.py` | Ensure `inject_as_user` with list[dict] is not stringified |

## Testing Strategy

### Unit Tests
- Image detection and base64 encoding for each format
- PDF detection and base64 encoding
- PDF page extraction with pymupdf
- `pages` parameter parsing ("1-5", "3", "10-20")
- Size limit enforcement
- Text reading unchanged (regression tests)
- Content block preservation through timeline
- LLMMessage with content blocks

### Integration Tests
- End-to-end: Read image → inject_as_user → timeline → LLM message
- End-to-end: Read PDF → inject_as_user → timeline → LLM message
- Mixed tool calls: Read text + Read image in same turn
- Large PDF with pages parameter

### Regression Tests
- All existing FileIOResource tests pass unchanged
- All existing timeline tests pass unchanged
- inject_as_user ordering test still passes

## References

- Current Read tool: `dana_agent/dana/core/resource/file_io_resource.py`
- inject_as_user mechanism: `dana_agent/dana/core/agent/star_agent.py:869-917`
- Skill resource (inject_as_user example): `dana_agent/dana/core/skills/dana_skills/skills.py:112-140`
- LLMMessage type: `dana_agent/dana/common/llm/types.py`
- Timeline: `dana_agent/dana/core/agent/timeline.py`
- Compressed timeline: `dana_agent/dana/core/agent/compressed_timeline.py`
- Anthropic API docs: Content blocks for images and documents
- Existing ordering test: `dana_agent/tests/unit/core/skills/test_inject_as_user_ordering.py`
