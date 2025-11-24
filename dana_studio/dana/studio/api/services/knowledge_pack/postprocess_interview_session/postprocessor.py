"""
Postprocessor for aggregating and comparing expert insights across multiple interview sessions.
"""

import glob
import hashlib
import json
import logging
from pathlib import Path
from difflib import SequenceMatcher
from typing import Any
from datetime import datetime

from dana.studio.api.services.search.bm25 import BM25SearchEngine
from dana.studio.api.services.knowledge_pack.interview_handler.utils import parse_interview_note
from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.lang.common.types import BaseRequest
from dana.lang.common.utils import Misc

logger = logging.getLogger(__name__)


def find_all_interview_notes(template_path: str) -> list[str]:
    """
    Find all interview_notes.md files within the template's sessions.

    Args:
        template_path: Path to the template directory (e.g., knowledge_packs/1/templates/template_2)

    Returns:
        Sorted list of paths to interview_notes.md files
    """
    pattern = str(Path(template_path) / "sessions" / "*" / "interview_notes.md")
    notes_paths = sorted(glob.glob(pattern))
    logger.info(f"Found {len(notes_paths)} interview notes in {template_path}")
    return notes_paths


def parse_all_sessions(notes_paths: list[str]) -> list[dict[str, Any]]:
    """
    Parse all interview notes files and extract topics with insights.

    Args:
        notes_paths: List of paths to interview_notes.md files

    Returns:
        List of session data with structure:
        [{
            "session_name": "session_1",
            "session_path": "/path/to/session_1",
            "topics": [{
                "topic_name": "...",
                "expert_insight": "...",
                "insights_count": 3,
                "status": "completed"
            }]
        }]
    """
    sessions_data = []

    for note_path in notes_paths:
        # Extract session name from path (e.g., session_1, session_2)
        session_name = Path(note_path).parent.name

        # Parse the interview note
        parsed_data = parse_interview_note(note_path)

        if "error" in parsed_data:
            logger.warning(f"Error parsing {note_path}: {parsed_data['error']}")
            continue

        # Extract relevant topic information
        topics = []
        for topic in parsed_data.get("topics", []):
            topics.append(
                {
                    "topic_name": topic["topic_name"],
                    "expert_insight": topic.get("expert_insight", ""),
                    "insights_count": topic.get("insights_count", 0),
                    "status": topic.get("status", "not_started"),
                }
            )

        sessions_data.append({"session_name": session_name, "session_path": str(Path(note_path).parent), "topics": topics})

        logger.info(f"Parsed {session_name}: {len(topics)} topics")

    return sessions_data


def group_topics_by_similarity(all_sessions_data: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """
    Group topics from different sessions by similarity using BM25 and SequenceMatcher.

    Args:
        all_sessions_data: List of session data with topics

    Returns:
        Dictionary mapping topic names to list of expert insights from different sessions:
        {
            "Topic Name": [
                {"session": "session_1", "expert_insight": "...", "status": "completed", "insights_count": 5},
                {"session": "session_2", "expert_insight": "...", "status": "in_progress", "insights_count": 3}
            ]
        }
    """
    if not all_sessions_data:
        return {}

    # Collect all topics from all sessions with their metadata
    all_topics = []
    for session in all_sessions_data:
        for topic in session["topics"]:
            all_topics.append(
                {
                    "session": session["session_name"],
                    "topic_name": topic["topic_name"],
                    "expert_insight": topic["expert_insight"],
                    "status": topic["status"],
                    "insights_count": topic["insights_count"],
                }
            )

    if not all_topics:
        return {}

    # Build BM25 search engine with all topic names
    topic_names = [t["topic_name"] for t in all_topics]
    bm25_engine = BM25SearchEngine(topic_names)

    grouped_topics = {}
    processed_indices = set()

    # For each topic, find similar topics across all sessions
    for i, topic in enumerate(all_topics):
        if i in processed_indices:
            continue

        topic_name = topic["topic_name"]

        # Search for similar topics using BM25 (get top 10 candidates)
        top_n = min(10, len(all_topics))
        similar_indices = bm25_engine.get_top_n_indices(topic_name, n=top_n)

        # Filter by SequenceMatcher similarity >= 0.7
        matched_topics = [topic]  # Start with the current topic
        processed_indices.add(i)

        for idx in similar_indices:
            if idx == i or idx in processed_indices:
                continue

            candidate_name = all_topics[idx]["topic_name"]
            similarity = SequenceMatcher(None, topic_name.lower(), candidate_name.lower()).ratio()

            if similarity >= 0.7:
                matched_topics.append(all_topics[idx])
                processed_indices.add(idx)

        # Use the first (highest BM25 score) topic name as the canonical name
        canonical_name = topic_name
        grouped_topics[canonical_name] = matched_topics

        logger.debug(f"Grouped {len(matched_topics)} topics under '{canonical_name}'")

    logger.info(f"Grouped {len(all_topics)} topics into {len(grouped_topics)} unique topics")
    return grouped_topics


async def analyze_topic_with_llm(topic_name: str, sessions_data: list[dict[str, Any]], llm: LLMResource) -> str | None:
    """
    Analyze a single topic using LLM to generate markdown with consensus and contradictions.

    Args:
        topic_name: Name of the topic being analyzed
        sessions_data: List of session data for this topic
        llm: Initialized LLM resource

    Returns:
        Markdown-formatted analysis for this topic
    """
    # Build the prompt with expert insights
    prompt_parts = [
        "You are an expert knowledge analyst specializing in identifying consensus and contradictions across multiple expert interviews. Your task is to analyze expert insights for a specific topic and generate a structured markdown report.\n",
        "# Task",
        f"Analyze the following expert insights for the topic: **{topic_name}**\n",
        "# Expert Insights\n",
    ]

    session_parts = []

    # Add each session's insights
    for session_data in sorted(sessions_data, key=lambda x: x["session"]):
        session = session_data["session"]
        status = session_data["status"]
        insights_count = session_data["insights_count"]
        expert_insight = session_data["expert_insight"]

        if not expert_insight or "No insights captured yet" in expert_insight:
            continue
        else:
            session_parts.append(f"## {session.replace('_', ' ').title()}")
            session_parts.append(f"Status: {status}")
            session_parts.append(f"Insights Count: {insights_count}\n")
            session_parts.append(f"{expert_insight}\n")

    if not session_parts:
        return None

    prompt_parts.extend(session_parts)

    # Add instructions
    prompt_parts.extend(
        [
            "\n---\n",
            "# Instructions\n",
            "Generate a markdown report with the following structure:\n",
            "1. **Expert Consensus Section** (🤝 emoji):",
            "   - List items where ALL or MOST experts agree",
            "   - Use checkmark bullets (✅)",
            "   - Quote supporting evidence from multiple sessions",
            "   - Only include genuine consensus items\n",
            "2. **Areas of Disagreement Section** (⚠️ emoji):",
            "   - Identify contradictions and conflicting views",
            "   - Classify severity: 🔴 CRITICAL, 🟡 MEDIUM, 🟢 LOW",
            "   - For each contradiction:",
            "     * Clear subject/title",
            "     * List each expert's position with quotes",
            "     * Provide analysis of why it's contradictory",
            "     * Suggest resolution approach",
            "   - Focus on substantive disagreements, not stylistic differences\n",
            "3. **Topic Statistics Section** (📊 emoji):",
            "   - Count consensus items",
            "   - Count contradictions by severity",
            "   - Session completion status\n",
            "# Important Guidelines\n",
            "- Be specific and quote actual text from expert insights",
            "- Distinguish between genuine contradictions and acceptable variations",
            "- Classify severity appropriately (CRITICAL = safety/compliance or operational impact, MEDIUM = efficiency, LOW = preference)",
            "- Provide actionable recommendations for contradictions",
            "- Keep consensus items focused on true agreement (not just similar topics)",
            "- If insights are empty or placeholder, note this clearly",
            "- Start directly with: ## Topic: [topic name]",
            "- Do NOT include any preamble or explanation before the markdown\n",
            "Generate the markdown report now:",
        ]
    )

    prompt = "\n".join(prompt_parts)

    try:
        # Create LLM request
        request = BaseRequest(
            arguments={
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert knowledge analyst. Generate structured markdown reports analyzing consensus and contradictions in expert insights. Output only the markdown report with no additional commentary.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": None,
            }
        )

        # Query LLM
        logger.info(f"Analyzing topic with LLM: {topic_name}")
        response = await llm.query(request)

        if response and response.success:
            markdown = Misc.get_response_content(response)
            logger.info(f"Successfully generated analysis for: {topic_name}")
            return markdown
        else:
            logger.error(f"LLM query failed for topic: {topic_name}, using fallback")
            return None

    except Exception as e:
        logger.error(f"Error analyzing topic with LLM: {topic_name}, error: {e}")
        return None


def _generate_fallback_topic_report(topic_name: str, sessions_data: list[dict[str, Any]]) -> str:
    """
    Generate a simple fallback report when LLM is unavailable.

    Args:
        topic_name: Name of the topic
        sessions_data: List of session data for this topic

    Returns:
        Simple markdown report
    """
    lines = [f"## Topic: {topic_name}\n"]

    # Sort by session name for consistent ordering
    sessions_data_sorted = sorted(sessions_data, key=lambda x: x["session"])

    for session_topic in sessions_data_sorted:
        session = session_topic["session"]
        status = session_topic["status"]
        insights_count = session_topic["insights_count"]
        expert_insight = session_topic["expert_insight"]

        lines.append(f"### {session.replace('_', ' ').title()} (Status: {status}, Insights: {insights_count})\n")

        # Check if insights are empty or placeholder
        if not expert_insight or "*No insights captured yet*" in expert_insight or expert_insight.strip() == "":
            lines.append("*No insights captured yet*\n")
        else:
            lines.append(f"{expert_insight}\n")

    lines.append("---\n")
    return "\n".join(lines)


async def generate_enhanced_markdown_report(grouped_topics: dict[str, list[dict[str, Any]]], llm: LLMResource | None = None) -> str:
    """
    Generate an enhanced markdown report using LLM to analyze each topic individually.

    Args:
        grouped_topics: Dictionary of grouped topics with insights from multiple sessions
        llm: Optional initialized LLM resource (if None, uses fallback format)

    Returns:
        Markdown-formatted string report with consensus and contradictions
    """
    if not grouped_topics:
        return "# Multi-Session Expert Insights Comparison\n\nNo topics found to compare.\n"

    # Calculate summary statistics
    total_topics = len(grouped_topics)

    # Count unique sessions
    all_sessions = set()
    for topics_list in grouped_topics.values():
        for topic in topics_list:
            all_sessions.add(topic["session"])
    sessions_count = len(all_sessions)

    # Count topics with multiple expert inputs
    multi_expert_topics = sum(1 for topics_list in grouped_topics.values() if len(topics_list) > 1)

    # Build markdown report header
    lines = [
        "# Multi-Session Expert Insights Comparison\n",
        "## Summary\n",
        f"- Total Topics: {total_topics}",
        f"- Sessions Analyzed: {sessions_count}",
        f"- Topics with Multiple Expert Inputs: {multi_expert_topics}\n",
        "---\n",
    ]

    # Process each topic (with or without LLM)
    if llm:
        logger.info(f"Processing {total_topics} topics with LLM analysis")
        for i, (topic_name, sessions_data) in enumerate(grouped_topics.items(), 1):
            logger.info(f"Processing topic {i}/{total_topics}: {topic_name}")
            topic_markdown = await analyze_topic_with_llm(topic_name, sessions_data, llm)
            if not topic_markdown:
                continue
            lines.append(topic_markdown)
            lines.append("\n---\n")
    else:
        logger.info("Processing topics without LLM (fallback format)")
        for topic_name, sessions_data in grouped_topics.items():
            topic_markdown = _generate_fallback_topic_report(topic_name, sessions_data)
            lines.append(topic_markdown)

    return "\n".join(lines)


def generate_markdown_report(grouped_topics: dict[str, list[dict[str, Any]]]) -> str:
    """
    Generate a markdown report comparing expert insights across sessions.

    Args:
        grouped_topics: Dictionary of grouped topics with insights from multiple sessions

    Returns:
        Markdown-formatted string report
    """
    if not grouped_topics:
        return "# Multi-Session Expert Insights Comparison\n\nNo topics found to compare.\n"

    # Calculate summary statistics
    total_topics = len(grouped_topics)

    # Count unique sessions
    all_sessions = set()
    for topics_list in grouped_topics.values():
        for topic in topics_list:
            all_sessions.add(topic["session"])
    sessions_count = len(all_sessions)

    # Count topics with multiple expert inputs
    multi_expert_topics = sum(1 for topics_list in grouped_topics.values() if len(topics_list) > 1)

    # Build markdown report
    lines = [
        "# Multi-Session Expert Insights Comparison\n",
        "## Summary\n",
        f"- Total Topics: {total_topics}",
        f"- Sessions Analyzed: {sessions_count}",
        f"- Topics with Multiple Expert Inputs: {multi_expert_topics}\n",
        "---\n",
    ]

    # Add each topic section
    for topic_name, sessions_data in grouped_topics.items():
        lines.append(f"## Topic: {topic_name}\n")

        # Sort by session name for consistent ordering
        sessions_data_sorted = sorted(sessions_data, key=lambda x: x["session"])

        for session_topic in sessions_data_sorted:
            session = session_topic["session"]
            status = session_topic["status"]
            insights_count = session_topic["insights_count"]
            expert_insight = session_topic["expert_insight"]

            lines.append(f"### {session.replace('_', ' ').title()} (Status: {status}, Insights: {insights_count})\n")

            # Check if insights are empty or placeholder
            if not expert_insight or "*No insights captured yet*" in expert_insight or expert_insight.strip() == "":
                lines.append("*No insights captured yet*\n")
            else:
                lines.append(f"{expert_insight}\n")

        lines.append("---\n")

    return "\n".join(lines)


def _get_cache_dir(template_path: str) -> Path:
    """Get or create the cache directory for a template."""
    cache_dir = Path(template_path) / ".analysis_cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def _generate_topic_cache_key(topic_name: str, sessions_data: list[dict]) -> str:
    """
    Generate cache key by hashing concatenated expert insights.

    Cache key changes only when the actual expert insights change.

    Args:
        topic_name: The topic name
        sessions_data: List of session dicts with expert_insight fields

    Returns:
        Hash-based cache key like "topic_abc123def456"
    """
    # Concatenate all expert insights in a deterministic order
    content = "".join(s["expert_insight"] for s in sorted(sessions_data, key=lambda x: x["session"]))

    # Generate hash
    hash_topic_name = hashlib.sha256(topic_name.encode("utf-8")).hexdigest()[:6]
    hash_digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    return f"topic_{hash_topic_name}_{hash_digest}"


def load_topic_from_cache(template_path: str, topic_name: str, sessions_data: list[dict]) -> dict | None:
    """
    Load cached topic analysis if it exists and content hasn't changed.

    Args:
        template_path: Path to template folder
        topic_name: The topic name
        sessions_data: List of session data (used for key generation)

    Returns:
        Cached topic data with sessions and unified_report, or None if not cached
    """
    cache_dir = _get_cache_dir(template_path)
    cache_key = _generate_topic_cache_key(topic_name, sessions_data)
    cache_file = cache_dir / f"{cache_key}.json"

    if not cache_file.exists():
        return None

    try:
        cached_data = json.loads(cache_file.read_text())

        # Verify topic name matches (sanity check)
        if cached_data.get("topic_name") == topic_name:
            logger.debug(f"Cache HIT for topic: {topic_name} (key: {cache_key})")
            return cached_data.get("analysis")
        else:
            logger.warning(f"Topic name mismatch in cache for {topic_name}")
            return None

    except Exception as e:
        logger.error(f"Error loading cache for topic {topic_name}: {e}")
        return None


def save_topic_to_cache(template_path: str, topic_name: str, sessions_data: list[dict], topic_analysis: dict) -> None:
    """
    Save topic analysis to cache with content-based key.

    Args:
        template_path: Path to template folder
        topic_name: Name of the topic
        sessions_data: List of session data (used for key generation)
        topic_analysis: The analysis dict with 'sessions' and 'unified_report'
    """
    cache_dir = _get_cache_dir(template_path)
    cache_key = _generate_topic_cache_key(topic_name, sessions_data)
    cache_file = cache_dir / f"{cache_key}.json"

    cache_data = {"topic_name": topic_name, "cache_key": cache_key, "cached_at": datetime.now().isoformat(), "analysis": topic_analysis}

    cache_file.write_text(json.dumps(cache_data, indent=2, ensure_ascii=False))
    logger.debug(f"Cached topic: {topic_name} (key: {cache_key})")


def cleanup_old_topic_caches(template_path: str, active_keys: set[str]) -> None:
    """
    Remove old cache files for topics that no longer exist or have changed.

    Args:
        template_path: Path to template folder
        active_keys: Set of currently active cache keys
    """
    cache_dir = _get_cache_dir(template_path)

    if not cache_dir.exists():
        return

    for cache_file in cache_dir.glob("topic_*.json"):
        cache_key = cache_file.stem
        if cache_key not in active_keys:
            cache_file.unlink()
            logger.debug(f"Removed stale cache: {cache_key}")


async def generate_structured_analysis(
    template_path: str, template_id: int, use_llm: bool = True, llm_config: dict[str, Any] | None = None
) -> dict:
    """
    Generate structured JSON analysis for API consumption.

    Returns:
    {
        "topics": {
            "Topic Name": {
                "sessions": [...],
                "unified_report": "..."
            }
        },
        "template_id": int,
        "generated_at": str,
        "total_topics": int,
        "total_sessions": int
    }
    """
    # Step 1-3: Find, parse, and group topics
    notes_paths = find_all_interview_notes(template_path)
    if not notes_paths:
        return {
            "topics": {},
            "template_id": template_id,
            "generated_at": datetime.now().isoformat(),
            "total_topics": 0,
            "total_sessions": 0,
        }

    all_sessions_data = parse_all_sessions(notes_paths)
    grouped_topics = group_topics_by_similarity(all_sessions_data)

    # Step 4: Initialize LLM if requested
    llm = None
    if use_llm:
        try:
            llm = LLMResource(
                name="insight_analyzer",
                description="Analyzes expert insights for consensus and contradictions",
            )
            await llm.initialize()
            if not hasattr(llm, "_is_available") or not llm._is_available:
                llm = None
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            llm = None

    # Step 5: Build structured output
    result = {
        "topics": {},
        "template_id": template_id,
        "generated_at": datetime.now().isoformat(),
        "total_topics": len(grouped_topics),
        "total_sessions": len(all_sessions_data),
    }

    # Process each topic
    for i, (topic_name, sessions_data) in enumerate(grouped_topics.items(), 1):
        logger.info(f"Processing topic {i}/{len(grouped_topics)}: {topic_name}")

        # Format sessions data
        sessions_list = [
            {"session": s["session"], "expert_insight": s["expert_insight"], "status": s["status"], "insights_count": s["insights_count"]}
            for s in sorted(sessions_data, key=lambda x: x["session"])
        ]

        # Generate unified report with LLM (or fallback)
        if llm:
            unified_report = await analyze_topic_with_llm(topic_name, sessions_data, llm)
        else:
            unified_report = None

        result["topics"][topic_name] = {"sessions": sessions_list, "unified_report": unified_report}

    logger.info(f"Generated structured analysis: {result['total_topics']} topics, {result['total_sessions']} sessions")
    return result


async def generate_kp_analysis(kp_id: int, templates: list, use_llm: bool = True, llm_config: dict[str, Any] | None = None) -> dict:
    """
    Generate structured JSON analysis for all templates in a knowledge pack.
    Now with per-topic caching for efficiency.

    Args:
        kp_id: Knowledge pack ID
        templates: List of template objects with id, name, and folder_path
        use_llm: Whether to use LLM for analysis
        llm_config: Optional LLM configuration

    Returns:
    {
        "kp_id": int,
        "generated_at": str,
        "templates": [
            {
                "template_id": int,
                "template_name": str,
                "topics": {...},
                "total_topics": int,
                "total_sessions": int
            },
            ...
        ]
    }
    """
    logger.info(f"Generating analysis for knowledge pack {kp_id} with {len(templates)} templates")

    # Initialize LLM once for all templates if requested
    llm = None
    if use_llm:
        try:
            default_config = {"max_tokens": None}
            config = {**default_config, **(llm_config or {})}

            llm = LLMResource(
                name="insight_analyzer", description="Analyzes expert insights for consensus and contradictions", config=config
            )
            await llm.initialize()
            if not hasattr(llm, "_is_available") or not llm._is_available:
                logger.warning("LLM initialization failed, falling back to basic reporting")
                llm = None
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            llm = None

    template_analyses = []

    # Process each template
    for template in templates:
        logger.info(f"Processing template {template.id}: {template.name}")

        # Find interview notes in this template
        notes_paths = find_all_interview_notes(template.folder_path)

        if not notes_paths:
            logger.warning(f"No interview notes found for template {template.id}")
            template_analyses.append(
                {"template_id": template.id, "template_name": template.name, "topics": {}, "total_topics": 0, "total_sessions": 0}
            )
            continue

        # Parse and group topics
        all_sessions_data = parse_all_sessions(notes_paths)
        grouped_topics = group_topics_by_similarity(all_sessions_data)

        # Build topics analysis with caching
        topics_dict = {}
        active_cache_keys = set()
        cache_hits = 0
        cache_misses = 0

        for topic_name, sessions_data in grouped_topics.items():
            # Try to load from cache first
            cached_analysis = load_topic_from_cache(template.folder_path, topic_name, sessions_data)

            if cached_analysis:
                # Use cached analysis
                topics_dict[topic_name] = cached_analysis
                cache_hits += 1

                # Track active cache key
                cache_key = _generate_topic_cache_key(topic_name, sessions_data)
                active_cache_keys.add(cache_key)
            else:
                # Generate fresh analysis
                cache_misses += 1

                # Format sessions data
                sessions_list = [
                    {
                        "session": s["session"],
                        "expert_insight": s["expert_insight"],
                        "status": s["status"],
                        "insights_count": s["insights_count"],
                    }
                    for s in sorted(sessions_data, key=lambda x: x["session"])
                ]

                # Generate unified report with LLM (or fallback)
                if llm:
                    unified_report = await analyze_topic_with_llm(topic_name, sessions_data, llm)
                else:
                    unified_report = _generate_fallback_topic_report(topic_name, sessions_data)

                topic_analysis = {"sessions": sessions_list, "unified_report": unified_report}

                topics_dict[topic_name] = topic_analysis

                if unified_report:
                    # Save to cache if there's any generated report
                    save_topic_to_cache(template.folder_path, topic_name, sessions_data, topic_analysis)

                # Track active cache key
                cache_key = _generate_topic_cache_key(topic_name, sessions_data)
                active_cache_keys.add(cache_key)

        # Cleanup stale caches
        cleanup_old_topic_caches(template.folder_path, active_cache_keys)

        logger.info(
            f"Template {template.id} completed: {len(grouped_topics)} topics " f"(cache hits: {cache_hits}, misses: {cache_misses})"
        )

        template_analyses.append(
            {
                "template_id": template.id,
                "template_name": template.name,
                "topics": topics_dict,
                "total_topics": len(grouped_topics),
                "total_sessions": len(all_sessions_data),
            }
        )

    result = {"kp_id": kp_id, "generated_at": datetime.now().isoformat(), "templates": template_analyses}

    logger.info(f"Completed KP analysis: {len(template_analyses)} templates processed")
    return result


async def aggregate_interview_insights(template_path: str, use_llm: bool = True, llm_config: dict[str, Any] | None = None) -> str:
    """
    Main function to aggregate and compare expert insights across multiple interview sessions.

    Args:
        template_path: Path to the template directory containing session folders
                      (e.g., 'knowledge_packs/1/templates/template_2')
        use_llm: Whether to use LLM for enhanced analysis (default: True)
        llm_config: Optional LLM configuration dict (model, temperature, etc.)

    Returns:
        Markdown-formatted string report comparing insights across sessions

    Example:
        >>> import asyncio
        >>> report = await aggregate_interview_insights('knowledge_packs/1/templates/template_2')
        >>> print(report)
        # Multi-Session Expert Insights Comparison
        ...

        >>> # Without LLM (fallback format)
        >>> report = await aggregate_interview_insights(
        ...     'knowledge_packs/1/templates/template_2',
        ...     use_llm=False
        ... )
    """
    logger.info(f"Starting interview insights aggregation for: {template_path}")
    logger.info(f"LLM analysis: {'enabled' if use_llm else 'disabled'}")

    # Step 1: Find all interview notes
    notes_paths = find_all_interview_notes(template_path)

    if not notes_paths:
        logger.warning(f"No interview notes found in {template_path}")
        return "# Multi-Session Expert Insights Comparison\n\nNo interview notes found.\n"

    # Step 2: Parse all sessions
    all_sessions_data = parse_all_sessions(notes_paths)

    if not all_sessions_data:
        logger.warning("No valid session data found")
        return "# Multi-Session Expert Insights Comparison\n\nNo valid session data found.\n"

    # Step 3: Group topics by similarity
    grouped_topics = group_topics_by_similarity(all_sessions_data)

    # Step 4: Generate markdown report (with or without LLM)
    if use_llm:
        try:
            # Initialize LLM
            default_config = {"max_tokens": None}
            config = {**default_config, **(llm_config or {})}

            logger.info(f"Initializing LLM with config: {config}")
            llm = LLMResource(
                name="insight_analyzer", description="Analyzes expert insights for consensus and contradictions", config=config
            )

            await llm.initialize()

            if not hasattr(llm, "_is_available") or not llm._is_available:
                logger.warning("LLM resource is not available, falling back to basic format")
                report = generate_markdown_report(grouped_topics)
            else:
                # Generate enhanced report with LLM
                report = await generate_enhanced_markdown_report(grouped_topics, llm)

        except Exception as e:
            logger.error(f"Error using LLM: {e}, falling back to basic format")
            report = generate_markdown_report(grouped_topics)
    else:
        # Generate basic report without LLM
        report = generate_markdown_report(grouped_topics)

    logger.info(f"Successfully generated report with {len(grouped_topics)} topics")
    return report


if __name__ == "__main__":
    # Example usage for testing
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def main():
        template_path = "knowledge_packs/1/templates/template_3_test"

        # Test with LLM
        print("=" * 80)
        print("Testing with LLM analysis...")
        print("=" * 80)
        report = await aggregate_interview_insights(template_path, use_llm=True)
        # print(report[:2000])  # Print first 2000 chars
        # print("\n... (truncated)")

        print(report)

        # Optionally test without LLM
        # print("\n" + "=" * 80)
        # print("Testing without LLM (fallback)...")
        # print("=" * 80)
        # report_fallback = await aggregate_interview_insights(template_path, use_llm=False)
        # print(report_fallback[:1000])

    asyncio.run(main())
