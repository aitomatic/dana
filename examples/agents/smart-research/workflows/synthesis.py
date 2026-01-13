"""Synthesis workflow for SmartResearchAgent - combines findings and identifies gaps."""

import time

from dana.common.protocols import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output
from dana.lib.resources.conversation import ConversationResource


class SynthesisWorkflow(BaseWorkflow):
    """
    Synthesizes findings from multiple sources.

    - Extracts claims
    - Cross-references information
    - Identifies themes
    - Detects knowledge gaps
    - Calculates confidence scores
    - Generates narrative and follow-ups
    """

    def __init__(self, workflow_id: str | None = None, llm_provider: str = "anthropic", model: str | None = None, **kwargs):
        super().__init__(workflow_id=workflow_id or "synthesis", **kwargs)
        self.conversation = ConversationResource(llm_provider=llm_provider, model=model or "claude-3-5-sonnet-20241022")

    @validate_input(
        query={"required": True, "type": str},
        sources={"required": True, "type": list},
    )
    @validate_output(
        success={"required": True, "type": bool},
        summary={"required": True, "type": dict},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Synthesize findings from sources.

        Args:
            query: Original query
            sources: List of source dicts with content

        Returns:
            {
                "success": True,
                "summary": {
                    "overview": str,
                    "key_findings": [...],
                    "themes": [...],
                },
                "knowledge_gaps": [...],
                "confidence": {...},
                "follow_up_questions": [...]
            }
        """
        query = kwargs["query"]
        sources = kwargs["sources"]
        start_time = time.time()

        # Broadcast: Starting synthesis
        self.broadcast(
            {
                "workflow_progress": {
                    "workflow_id": self.workflow_id,
                    "phase": "start",
                    "message": f"Synthesizing findings from {len(sources)} sources...",
                }
            }
        )

        try:
            # Filter sources with content
            valid_sources = [s for s in sources if s.get("content")]

            if not valid_sources:
                return self._create_fallback_response(query, "No valid sources with content")

            # Step 1: Extract key information (simplified - in production use LLM)
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "extract",
                        "message": f"Extracting key findings from {len(valid_sources)} sources...",
                    }
                }
            )
            key_findings = self._extract_findings(valid_sources, query)

            # Step 2: Identify themes
            self.broadcast(
                {"workflow_progress": {"workflow_id": self.workflow_id, "phase": "themes", "message": "Identifying common themes..."}}
            )
            themes = self._identify_themes(key_findings)

            # Step 3: Generate overview
            self.broadcast(
                {"workflow_progress": {"workflow_id": self.workflow_id, "phase": "overview", "message": "Generating synthesis overview..."}}
            )
            overview = self._generate_overview(query, key_findings, themes)

            # Step 4: Detect knowledge gaps
            self.broadcast(
                {"workflow_progress": {"workflow_id": self.workflow_id, "phase": "gaps", "message": "Detecting knowledge gaps..."}}
            )
            knowledge_gaps = self._detect_gaps(query, themes, valid_sources)

            # Step 5: Calculate confidence
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "confidence",
                        "message": "Calculating confidence scores...",
                    }
                }
            )
            confidence = self._calculate_confidence(valid_sources, knowledge_gaps)

            # Step 6: Generate follow-up questions
            follow_ups = self._generate_follow_ups(query, knowledge_gaps)

            processing_time = time.time() - start_time

            # Broadcast: Synthesis complete
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "complete",
                        "message": f"Synthesis complete (confidence: {confidence['overall']:.2f}, {len(key_findings)} findings)",
                    }
                }
            )

            return {
                "success": True,
                "summary": {
                    "overview": overview,
                    "key_findings": key_findings,
                    "themes": themes,
                },
                "knowledge_gaps": knowledge_gaps,
                "confidence": confidence,
                "follow_up_questions": follow_ups,
                "sources_used": [s["url"] for s in valid_sources],
                "metadata": {"sources_count": len(valid_sources), "processing_time": round(processing_time, 3), "timestamp": time.time()},
            }

        except Exception as e:
            return self._create_fallback_response(query, str(e))

    def _extract_findings(self, sources: list, query: str) -> list:
        """Extract key findings from sources."""
        findings = []

        for i, source in enumerate(sources[:10]):  # Limit to top 10
            content = source.get("content", "")
            if not content:
                continue

            # Simple extraction: use first paragraph or snippet
            snippet = source.get("snippet", "")
            title = source.get("title", "")

            # Create finding
            finding = {
                "finding": snippet[:200] if snippet else content[:200],
                "source_url": source.get("url", ""),
                "source_title": title,
                "significance": "medium",  # In production, use LLM to assess
                "confidence": source.get("scores", {}).get("overall", 0.7),
            }

            findings.append(finding)

        return findings[:5]  # Top 5 findings

    def _identify_themes(self, findings: list) -> list:
        """Identify common themes across findings."""
        # Simplified: return generic theme
        # In production, use LLM for theme extraction
        return [
            {
                "theme": "Main findings",
                "findings_count": len(findings),
                "description": f"Key information extracted from {len(findings)} sources",
            }
        ]

    def _generate_overview(self, query: str, findings: list, themes: list) -> str:
        """Generate overview paragraph."""
        # Simplified overview
        findings_summary = ". ".join([f["finding"][:100] for f in findings[:3]])
        overview = f"Research on '{query}' revealed {len(findings)} key findings. {findings_summary}..."

        return overview

    def _detect_gaps(self, query: str, themes: list, sources: list) -> list:
        """Detect knowledge gaps."""
        gaps = []

        # Simple heuristics for gap detection
        if len(sources) < 5:
            gaps.append(
                {
                    "gap": "Limited source coverage",
                    "severity": "medium",
                    "reason": f"Only {len(sources)} sources found",
                    "suggested_followup": f"Search for more comprehensive sources on '{query}'",
                }
            )

        # Check for date coverage
        dated_sources = [s for s in sources if s.get("date")]
        if len(dated_sources) < len(sources) * 0.5:
            gaps.append(
                {
                    "gap": "Publication dates unclear",
                    "severity": "low",
                    "reason": "Many sources lack clear publication dates",
                    "suggested_followup": "Focus on sources with clear dates for recency assessment",
                }
            )

        return gaps

    def _calculate_confidence(self, sources: list, gaps: list) -> dict:
        """Calculate multi-dimensional confidence scores."""
        # Verification score: based on source count
        verification = min(1.0, len(sources) / 10)

        # Recency score: based on sources with dates
        dated_sources = [s for s in sources if s.get("date")]
        recency = len(dated_sources) / max(1, len(sources))

        # Completeness: inverse of gaps
        completeness = max(0.3, 1.0 - (len(gaps) * 0.2))

        # Overall weighted score
        overall = (verification * 0.4) + (recency * 0.3) + (completeness * 0.3)

        explanation = []
        if verification > 0.7:
            explanation.append(f"Good source coverage ({len(sources)} sources)")
        if recency < 0.5:
            explanation.append("Some sources may lack clear dates")
        if len(gaps) > 2:
            explanation.append(f"Identified {len(gaps)} knowledge gaps")

        return {
            "overall": round(overall, 2),
            "dimensions": {"verification": round(verification, 2), "recency": round(recency, 2), "completeness": round(completeness, 2)},
            "explanation": explanation,
        }

    def _generate_follow_ups(self, query: str, gaps: list) -> list:
        """Generate follow-up questions based on gaps."""
        follow_ups = [gap["suggested_followup"] for gap in gaps if gap.get("suggested_followup")]

        # Add generic follow-ups
        if len(follow_ups) < 3:
            follow_ups.extend(
                [
                    f"What are the latest developments regarding '{query}'?",
                    f"How does '{query}' compare to related topics?",
                    f"What are the practical applications of '{query}'?",
                ]
            )

        return follow_ups[:5]  # Limit to 5

    def _create_fallback_response(self, query: str, error: str) -> DictParams:
        """Create fallback response when synthesis fails."""
        return {
            "success": False,
            "error": error,
            "summary": {"overview": f"Unable to fully synthesize information for '{query}'", "key_findings": [], "themes": []},
            "knowledge_gaps": [
                {
                    "gap": "Synthesis failure",
                    "severity": "high",
                    "reason": error,
                    "suggested_followup": f"Try rephrasing the query: '{query}'",
                }
            ],
            "confidence": {
                "overall": 0.0,
                "dimensions": {"verification": 0.0, "recency": 0.0, "completeness": 0.0},
                "explanation": [f"Error during synthesis: {error}"],
            },
            "follow_up_questions": [f"Rephrase: '{query}'"],
            "sources_used": [],
        }
