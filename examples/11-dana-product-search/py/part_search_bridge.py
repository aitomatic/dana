"""
Lightweight, optimized manufacturer part-number search for PoC.

No dependency on the legacy module; uses direct SQL via psycopg2.
Tries exact → wildcard (surrounded with %) → fuzzy (pg_trgm) and returns
compact, standardized structure compatible with the Dana pipeline.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import psycopg2
import psycopg2.extras


def _get_conn():
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        dbname=os.getenv("PG_DATABASE", "vector_db"),
        user=os.getenv("PG_USER", "admin"),
        password=os.getenv("PG_PASSWORD", "admin"),
    )


def _fetch_rows(query: str, params: tuple[Any, ...]) -> list[dict]:
    try:
        with _get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params)
                return list(cur.fetchall())
    except Exception:
        return []


def _rows_to_results(rows: list[dict]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for r in rows:
        results.append(
            {
                "id": r.get("id"),
                "mfr_part_num": r.get("mfr_part_num", ""),
                "mfr_brand": r.get("mfr_brand") or r.get("mfr", ""),
                "product_name": r.get("product_name", ""),
                "data_source": r.get("data_source", ""),
                "source_category": r.get("source_category", ""),
            }
        )
    return results


def _exact(part_number: str, limit: int) -> list[dict[str, Any]]:
    # Case-insensitive exact match by default
    q = (
        "SELECT id, mfr_part_num, mfr, mfr_brand, product_name, data_source, source_category "
        "FROM normalized_products WHERE UPPER(mfr_part_num) = UPPER(%s) ORDER BY id LIMIT %s"
    )
    rows = _fetch_rows(q, (part_number, limit))
    return _rows_to_results(rows)


def _wildcard(part_number: str, limit: int) -> list[dict[str, Any]]:
    pattern = f"%{part_number}%"
    q = (
        "SELECT id, mfr_part_num, mfr, mfr_brand, product_name, data_source, source_category "
        "FROM normalized_products WHERE UPPER(mfr_part_num) LIKE UPPER(%s) "
        "ORDER BY LENGTH(mfr_part_num), id LIMIT %s"
    )
    rows = _fetch_rows(q, (pattern, limit))
    return _rows_to_results(rows)


def _fuzzy(part_number: str, limit: int, min_sim: float = 0.5) -> list[dict[str, Any]]:
    # Requires pg_trgm extension; if unavailable, returns empty
    q = (
        "SELECT id, mfr_part_num, mfr, mfr_brand, product_name, data_source, source_category, "
        "       similarity(mfr_part_num, %s) AS sim "
        "FROM normalized_products "
        "WHERE mfr_part_num %% %s "
        "ORDER BY sim DESC, LENGTH(mfr_part_num), id LIMIT %s"
    )
    rows = _fetch_rows(q, (part_number, part_number, limit))
    filtered = [r for r in rows if float(r.get("sim", 0.0)) >= min_sim]
    return _rows_to_results(filtered)


def part_search_smart(part_number: str, limit_to_top: Optional[int] = None) -> dict[str, Any]:
    limit = limit_to_top or 3

    # 1) exact
    exact = _exact(part_number, limit)
    if exact:
        return {
            "strategy_used": "exact",
            "total_found": len(exact),
            "confidence": "high",
            "results": exact,
        }

    # 2) wildcard (contains)
    wildcard = _wildcard(part_number, limit)
    if wildcard:
        return {
            "strategy_used": "wildcard",
            "total_found": len(wildcard),
            "confidence": "medium",
            "results": wildcard,
        }

    # 3) fuzzy (pg_trgm)
    fuzzy = _fuzzy(part_number, limit, min_sim=0.5)
    if fuzzy:
        return {
            "strategy_used": "fuzzy",
            "total_found": len(fuzzy),
            "confidence": "high",
            "results": fuzzy,
        }

    return {"strategy_used": "none", "total_found": 0, "confidence": "none", "results": []}
