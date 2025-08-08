"""
Result standardization and formatting helpers for Dana Product Search PoC.

Provides clean separation between Dana orchestration and Python data processing.
"""

from typing import Any


def standardize_part_results(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Convert part search bridge results to standardized format.

    Args:
        raw: Output from part_search_bridge.part_search_smart()

    Returns:
        List of standardized result dictionaries
    """
    if not raw or not raw.get("results"):
        return []

    standardized = []
    for result in raw["results"]:
        standardized.append(
            {
                "product_name": result.get("product_name", ""),
                "mfr_part_num": result.get("mfr_part_num", ""),
                "mfr_brand": result.get("mfr_brand", ""),
                "source_category": result.get("source_category", ""),
                "data_source": result.get("data_source", ""),
                "other_attributes": f"ID: {result.get('id', '')}, Source: {result.get('data_source', '')}",
                "search_strategy": raw.get("strategy_used", ""),
                "confidence_level": raw.get("confidence", ""),
            }
        )

    return standardized


def standardize_vector_results(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convert tabular_index vector search results to standardized format.

    Args:
        items: Raw vector search results from tabular_index.retrieve()

    Returns:
        List of standardized result dictionaries
    """
    standardized = []
    for item in items:
        metadata = item.get("metadata", {})

        standardized.append(
            {
                "product_name": str(item.get("text", "")),
                "mfr_part_num": str(metadata.get("mfr_part_num", "")),
                "mfr_brand": str(metadata.get("mfr_brand", metadata.get("make", ""))),
                "source_category": str(metadata.get("source_category", "")),
                "data_source": "vector_search",
                "other_attributes": str(metadata),
                "search_strategy": "vector_similarity",
                "confidence_level": "medium",
            }
        )

    return standardized


def merge_and_dedupe_results(
    part_results: list[dict[str, Any]], vector_results: list[dict[str, Any]], max_results: int = 5
) -> list[dict[str, Any]]:
    """
    Merge part search and vector search results, removing duplicates.

    Args:
        part_results: Standardized part search results
        vector_results: Standardized vector search results
        max_results: Maximum number of results to return

    Returns:
        Merged and deduplicated results list
    """
    # Start with part results (higher priority)
    merged = list(part_results)

    # Add vector results, avoiding duplicates by part number
    seen_parts = {r["mfr_part_num"].lower() for r in part_results if r["mfr_part_num"]}

    for vector_result in vector_results:
        part_num = vector_result["mfr_part_num"].lower()

        # Add if not a duplicate and under max limit
        if part_num not in seen_parts and len(merged) < max_results:
            merged.append(vector_result)
            if part_num:  # Only track non-empty part numbers
                seen_parts.add(part_num)

    return merged[:max_results]


def format_results_for_ai(standardized: list[dict[str, Any]]) -> str:
    """
    Format standardized results for LLM ranking prompt.

    Args:
        standardized: List of standardized result dictionaries

    Returns:
        Formatted string for ranking prompt
    """
    if not standardized:
        return "No results found."

    formatted_lines = []
    for idx, result in enumerate(standardized, 1):
        lines = [
            f"Result #: {idx}",
            f"Product Name: {result['product_name']}",
            f"Supplier Part Number: {result['mfr_part_num']}",
            f"Supplier Name: {result['mfr_brand']}",
            f"Category: {result['source_category']}",
        ]

        # Add optional attributes if present
        if result.get("other_attributes") and result["other_attributes"] != "":
            lines.append(f"Other Attributes: {result['other_attributes']}")

        # Add search metadata for debugging
        if result.get("search_strategy"):
            lines.append(f"Search Method: {result['search_strategy']}")

        formatted_lines.append("\n".join(lines))

    return "\n\n".join(formatted_lines)


def to_best_match(standardized: list[dict[str, Any]], index: int, notes: str, confidence: float) -> dict[str, Any]:
    """
    Convert ranked result to BestMatch format as specified in plan.

    Args:
        standardized: List of standardized results
        index: 1-based index of selected result
        notes: Ranking explanation
        confidence: Confidence score (0.0-1.0)

    Returns:
        BestMatch dictionary
    """
    if not standardized or index < 1 or index > len(standardized):
        return {
            "product_name": "No results found",
            "supplier_part_number": "",
            "supplier_name": "",
            "quantity": "",
            "data_source": "",
            "category": "",
            "notes": notes or "No valid results available",
            "confidence_score": 0.0,
        }

    selected = standardized[index - 1]  # Convert to 0-based index

    return {
        "product_name": selected["product_name"],
        "supplier_part_number": selected["mfr_part_num"],
        "supplier_name": selected["mfr_brand"],
        "quantity": "",  # Not available in current data
        "data_source": selected.get("data_source", ""),
        "category": selected["source_category"],
        "notes": notes,
        "confidence_score": confidence,
    }


def build_search_response(
    query: str,
    results: list[dict[str, Any]],
    best_match: dict[str, Any],
    processing_time: float,
    enhanced_query: str = "",
    weighted_term: str = "",
    broad_search_count: int = 0,
) -> dict[str, Any]:
    """
    Build final SearchResponse structure as specified in plan.

    Args:
        query: Original user query
        results: List of all search results
        best_match: Selected best match result
        processing_time: Total processing time in seconds
        enhanced_query: LLM-enhanced query
        weighted_term: Most weighted keyword
        broad_search_count: Number of results from broad search

    Returns:
        Complete SearchResponse dictionary
    """
    return {
        "query": query,
        "results": results,
        "total_results": len(results),
        "processing_time": processing_time,
        "best_match": best_match,
        "web_search": None,  # Placeholder as per plan
        "internal": {"enhanced_query": enhanced_query, "weighted_term": weighted_term, "broad_search_count": broad_search_count},
    }
