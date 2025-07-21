"""
Context expansion component for Dana KNOWS system.

This module handles LLM-based context analysis, validation, and refinement.
"""

import json
from dataclasses import dataclass
from typing import Any

from dana.common.resource.llm.llm_resource import BaseRequest, BaseResponse, LLMResource
from dana.common.utils.logging import DANA_LOGGER
from dana.frameworks.knows.core.base import KnowledgePoint, ProcessorBase


@dataclass
class ContextExpansion:
    """Result of context expansion operation."""

    source_id: str
    expanded_context: dict[str, Any]
    expansion_type: str  # "semantic", "logical", "temporal", "causal"
    confidence: float
    reasoning: str
    metadata: dict[str, Any]


@dataclass
class ContextValidation:
    """Result of context validation."""

    context_id: str
    is_valid: bool
    validation_score: float
    issues_found: list[str]
    recommendations: list[str]
    metadata: dict[str, Any]


class ContextExpander(ProcessorBase):
    """LLM-based context expansion and validation."""

    DEFAULT_CONFIDENCE_THRESHOLD = 0.7
    DEFAULT_MAX_EXPANSIONS = 3

    EXPANSION_PROMPT_TEMPLATE = """
Analyze the following knowledge point and expand its context with additional relevant information.

Knowledge Point:
- ID: {knowledge_id}
- Type: {knowledge_type}
- Content: {content}
- Current Context: {current_context}
- Confidence: {confidence}

Please provide expanded context in the following areas:
1. **Semantic Context**: Related concepts, terminology, domain knowledge
2. **Logical Context**: Prerequisites, dependencies, logical connections
3. **Temporal Context**: Timeline, sequence, historical context
4. **Causal Context**: Cause-and-effect relationships, implications

For each expansion, provide:
- The expansion type (semantic/logical/temporal/causal)
- Additional context information
- Confidence level (0.0-1.0)
- Reasoning for the expansion

Return your response as JSON in this exact format:
```json
{{
    "expansions": [
        {{
            "expansion_type": "semantic",
            "expanded_context": {{
                "key1": "value1",
                "key2": "value2"
            }},
            "confidence": 0.85,
            "reasoning": "Explanation of why this expansion is relevant"
        }}
    ],
    "validation": {{
        "original_context_valid": true,
        "expansion_quality": 0.9,
        "recommendations": ["suggestion1", "suggestion2"]
    }}
}}
```
"""

    VALIDATION_PROMPT_TEMPLATE = """
Validate the context of the following knowledge point for accuracy, completeness, and relevance.

Knowledge Point:
- ID: {knowledge_id}
- Type: {knowledge_type}
- Content: {content}
- Context: {context}
- Confidence: {confidence}

Please evaluate:
1. **Accuracy**: Is the context information factually correct?
2. **Completeness**: Is important context missing?
3. **Relevance**: Is all context information relevant to the knowledge point?
4. **Consistency**: Is the context internally consistent?

Return your validation as JSON in this exact format:
```json
{{
    "validation_result": {{
        "is_valid": true,
        "validation_score": 0.85,
        "accuracy_score": 0.9,
        "completeness_score": 0.8,
        "relevance_score": 0.9,
        "consistency_score": 0.85
    }},
    "issues_found": [
        "Issue 1 description",
        "Issue 2 description"
    ],
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ],
    "reasoning": "Overall assessment explanation"
}}
```
"""

    def __init__(
        self,
        llm_resource: LLMResource | None = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        max_expansions: int = DEFAULT_MAX_EXPANSIONS,
    ):
        """Initialize context expander.

        Args:
            llm_resource: LLM resource for context expansion
            confidence_threshold: Minimum confidence for context expansions
            max_expansions: Maximum number of expansions per knowledge point
        """
        self.llm_resource = llm_resource
        self.confidence_threshold = confidence_threshold
        self.max_expansions = max_expansions

        DANA_LOGGER.info(f"Initialized ContextExpander with threshold: {confidence_threshold}")

    def process(self, knowledge_points: list[KnowledgePoint]) -> dict[str, Any]:
        """Expand context for knowledge points.

        Args:
            knowledge_points: List of knowledge points to process

        Returns:
            Dictionary containing context expansions and validations

        Raises:
            ValueError: If input is invalid
        """
        if not self.validate_input(knowledge_points):
            raise ValueError("Invalid knowledge points provided for context expansion")

        try:
            # Expand context for each knowledge point
            expansions = []
            for kp in knowledge_points:
                kp_expansions = self.expand_context(kp)
                expansions.extend(kp_expansions)

            # Validate expanded contexts
            validations = []
            for kp in knowledge_points:
                validation = self.validate_context(kp)
                validations.append(validation)

            # Create context relationships
            relationships = self._create_context_relationships(knowledge_points, expansions)

            # Generate context summary
            summary = self._generate_context_summary(expansions, validations)

            result = {
                "context_expansions": expansions,
                "context_validations": validations,
                "context_relationships": relationships,
                "expansion_summary": summary,
                "processing_metadata": {
                    "total_knowledge_points": len(knowledge_points),
                    "total_expansions": len(expansions),
                    "average_expansion_confidence": self._calculate_average_confidence(expansions),
                    "validation_pass_rate": self._calculate_validation_pass_rate(validations),
                },
            }

            DANA_LOGGER.info(f"Generated {len(expansions)} context expansions for {len(knowledge_points)} knowledge points")
            return result

        except Exception as e:
            DANA_LOGGER.error(f"Failed to expand context: {str(e)}")
            raise

    def validate_input(self, knowledge_points: list[KnowledgePoint]) -> bool:
        """Validate input knowledge points.

        Args:
            knowledge_points: Knowledge points to validate

        Returns:
            True if input is valid
        """
        if not isinstance(knowledge_points, list):
            DANA_LOGGER.error("Input must be a list of KnowledgePoint objects")
            return False

        if len(knowledge_points) == 0:
            DANA_LOGGER.error("Knowledge points list is empty")
            return False

        for kp in knowledge_points:
            if not isinstance(kp, KnowledgePoint):
                DANA_LOGGER.error(f"Invalid knowledge point type: {type(kp)}")
                return False

        return True

    def expand_context(self, knowledge_point: KnowledgePoint) -> list[ContextExpansion]:
        """Expand context for a single knowledge point.

        Args:
            knowledge_point: Knowledge point to expand context for

        Returns:
            List of context expansions
        """
        if self.llm_resource is None:
            DANA_LOGGER.warning("No LLM resource available, using rule-based expansion")
            return self._rule_based_expansion(knowledge_point)

        try:
            # Prepare LLM request
            prompt = self.EXPANSION_PROMPT_TEMPLATE.format(
                knowledge_id=knowledge_point.id,
                knowledge_type=knowledge_point.type,
                content=knowledge_point.content,
                current_context=json.dumps(knowledge_point.context or {}, indent=2),
                confidence=knowledge_point.confidence,
            )

            request = BaseRequest(
                arguments={"messages": [{"role": "user", "content": prompt}], "model": "gpt-4", "temperature": 0.3, "max_tokens": 1500}
            )

            # Get LLM response
            response = self.llm_resource.call(request)

            # Parse response
            expansions = self._parse_expansion_response(response, knowledge_point.id)

            # Filter by confidence threshold
            high_confidence_expansions = [exp for exp in expansions if exp.confidence >= self.confidence_threshold]

            # Limit number of expansions
            return high_confidence_expansions[: self.max_expansions]

        except Exception as e:
            DANA_LOGGER.error(f"LLM context expansion failed for {knowledge_point.id}: {str(e)}")
            return self._rule_based_expansion(knowledge_point)

    def validate_context(self, knowledge_point: KnowledgePoint) -> ContextValidation:
        """Validate context for a knowledge point.

        Args:
            knowledge_point: Knowledge point to validate

        Returns:
            Context validation result
        """
        if self.llm_resource is None:
            DANA_LOGGER.warning("No LLM resource available, using rule-based validation")
            return self._rule_based_validation(knowledge_point)

        try:
            # Prepare LLM request
            prompt = self.VALIDATION_PROMPT_TEMPLATE.format(
                knowledge_id=knowledge_point.id,
                knowledge_type=knowledge_point.type,
                content=knowledge_point.content,
                context=json.dumps(knowledge_point.context or {}, indent=2),
                confidence=knowledge_point.confidence,
            )

            request = BaseRequest(
                arguments={"messages": [{"role": "user", "content": prompt}], "model": "gpt-4", "temperature": 0.2, "max_tokens": 1000}
            )

            # Get LLM response
            response = self.llm_resource.call(request)

            # Parse response
            validation = self._parse_validation_response(response, knowledge_point.id)

            return validation

        except Exception as e:
            DANA_LOGGER.error(f"LLM context validation failed for {knowledge_point.id}: {str(e)}")
            return self._rule_based_validation(knowledge_point)

    def _parse_expansion_response(self, response: BaseResponse, source_id: str) -> list[ContextExpansion]:
        """Parse LLM response for context expansions.
        
        Args:
            response: LLM response
            source_id: Source knowledge point ID
            
        Returns:
            List of parsed context expansions
        """
        try:
            # Extract JSON content
            content = response.content
            if content is None:
                return []
            
            # Handle markdown-wrapped JSON
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            
            # Parse JSON
            parsed_data = json.loads(content)

            expansions = []
            for exp_data in parsed_data.get("expansions", []):
                expansion = ContextExpansion(
                    source_id=source_id,
                    expanded_context=exp_data.get("expanded_context", {}),
                    expansion_type=exp_data.get("expansion_type", "semantic"),
                    confidence=float(exp_data.get("confidence", 0.5)),
                    reasoning=exp_data.get("reasoning", ""),
                    metadata={
                        "llm_generated": True,
                        "validation_info": parsed_data.get("validation", {}),
                        "response_quality": self._assess_response_quality(exp_data),
                    },
                )
                expansions.append(expansion)

            return expansions

        except Exception as e:
            DANA_LOGGER.error(f"Failed to parse expansion response: {str(e)}")
            return []

    def _parse_validation_response(self, response: BaseResponse, context_id: str) -> ContextValidation:
        """Parse LLM response for context validation.
        
        Args:
            response: LLM response
            context_id: Context ID being validated
            
        Returns:
            Parsed context validation
        """
        try:
            # Extract JSON content
            content = response.content
            if content is None:
                return ContextValidation(
                    context_id=context_id,
                    is_valid=False,
                    validation_score=0.0,
                    issues_found=["Empty response content"],
                    recommendations=["Review context manually"],
                    metadata={"llm_generated": False, "parse_error": True}
                )
            
            # Handle markdown-wrapped JSON
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            
            # Parse JSON
            parsed_data = json.loads(content)

            validation_result = parsed_data.get("validation_result", {})

            validation = ContextValidation(
                context_id=context_id,
                is_valid=validation_result.get("is_valid", False),
                validation_score=float(validation_result.get("validation_score", 0.5)),
                issues_found=parsed_data.get("issues_found", []),
                recommendations=parsed_data.get("recommendations", []),
                metadata={
                    "llm_generated": True,
                    "detailed_scores": {
                        "accuracy": validation_result.get("accuracy_score", 0.5),
                        "completeness": validation_result.get("completeness_score", 0.5),
                        "relevance": validation_result.get("relevance_score", 0.5),
                        "consistency": validation_result.get("consistency_score", 0.5),
                    },
                    "reasoning": parsed_data.get("reasoning", ""),
                },
            )

            return validation

        except Exception as e:
            DANA_LOGGER.error(f"Failed to parse validation response: {str(e)}")
            return ContextValidation(
                context_id=context_id,
                is_valid=False,
                validation_score=0.0,
                issues_found=[f"Parse error: {str(e)}"],
                recommendations=["Review context manually"],
                metadata={"llm_generated": False, "parse_error": True},
            )

    def _rule_based_expansion(self, knowledge_point: KnowledgePoint) -> list[ContextExpansion]:
        """Fallback rule-based context expansion.

        Args:
            knowledge_point: Knowledge point to expand

        Returns:
            List of rule-based expansions
        """
        expansions = []

        # Semantic expansion based on content analysis
        content_lower = knowledge_point.content.lower()

        # Add semantic context based on keywords
        semantic_context = {}
        if "process" in content_lower or "procedure" in content_lower:
            semantic_context.update({"domain": "process_management", "category": "operational", "requires_sequence": True})

        if "error" in content_lower or "problem" in content_lower:
            semantic_context.update({"domain": "troubleshooting", "category": "issue_resolution", "urgency": "medium"})

        if semantic_context:
            expansions.append(
                ContextExpansion(
                    source_id=knowledge_point.id,
                    expanded_context=semantic_context,
                    expansion_type="semantic",
                    confidence=0.6,
                    reasoning="Rule-based semantic analysis of content keywords",
                    metadata={"rule_based": True, "method": "keyword_analysis"},
                )
            )

        # Logical expansion based on knowledge type
        if knowledge_point.type in ["process", "procedure"]:
            logical_context = {"has_prerequisites": True, "sequential_execution": True, "validation_required": True}

            expansions.append(
                ContextExpansion(
                    source_id=knowledge_point.id,
                    expanded_context=logical_context,
                    expansion_type="logical",
                    confidence=0.7,
                    reasoning=f"Standard logical structure for {knowledge_point.type} type",
                    metadata={"rule_based": True, "method": "type_analysis"},
                )
            )

        # Temporal expansion for time-sensitive content
        time_keywords = ["daily", "weekly", "monthly", "schedule", "deadline", "timeline"]
        if any(keyword in content_lower for keyword in time_keywords):
            temporal_context = {"time_sensitive": True, "requires_scheduling": True, "temporal_dependency": True}

            expansions.append(
                ContextExpansion(
                    source_id=knowledge_point.id,
                    expanded_context=temporal_context,
                    expansion_type="temporal",
                    confidence=0.65,
                    reasoning="Detected temporal keywords indicating time-based dependencies",
                    metadata={"rule_based": True, "method": "temporal_keyword_analysis"},
                )
            )

        return expansions

    def _rule_based_validation(self, knowledge_point: KnowledgePoint) -> ContextValidation:
        """Fallback rule-based context validation.

        Args:
            knowledge_point: Knowledge point to validate

        Returns:
            Rule-based validation result
        """
        issues = []
        recommendations = []
        validation_score = 0.5  # Default neutral score

        # Check if context exists
        if not knowledge_point.context:
            issues.append("No context information provided")
            recommendations.append("Add relevant context information")
            validation_score = 0.3
        else:
            # Check context completeness
            if len(knowledge_point.context) < 2:
                issues.append("Context appears incomplete (fewer than 2 context fields)")
                recommendations.append("Add more contextual information")
                validation_score = 0.6
            else:
                validation_score = 0.8

        # Check content-context alignment
        if knowledge_point.context:
            content_words = set(knowledge_point.content.lower().split())
            context_words = set()

            for value in knowledge_point.context.values():
                if isinstance(value, str):
                    context_words.update(value.lower().split())

            # Check for some overlap
            overlap = content_words.intersection(context_words)
            if len(overlap) == 0:
                issues.append("No apparent relationship between content and context")
                recommendations.append("Ensure context is relevant to the content")
                validation_score *= 0.7

        # Check confidence alignment
        if knowledge_point.confidence < 0.5 and len(issues) == 0:
            issues.append("Low confidence despite no validation issues found")
            recommendations.append("Review and potentially increase confidence if content is accurate")

        return ContextValidation(
            context_id=knowledge_point.id,
            is_valid=len(issues) == 0,
            validation_score=validation_score,
            issues_found=issues,
            recommendations=recommendations,
            metadata={
                "rule_based": True,
                "validation_method": "basic_rule_checks",
                "context_field_count": len(knowledge_point.context or {}),
            },
        )

    def _assess_response_quality(self, expansion_data: dict[str, Any]) -> float:
        """Assess the quality of an expansion response.

        Args:
            expansion_data: Expansion data from LLM

        Returns:
            Quality score between 0 and 1
        """
        quality_score = 0.5  # Base score

        # Check for required fields
        if "expanded_context" in expansion_data and expansion_data["expanded_context"]:
            quality_score += 0.2

        if "reasoning" in expansion_data and len(expansion_data["reasoning"]) > 10:
            quality_score += 0.2

        if "expansion_type" in expansion_data:
            quality_score += 0.1

        # Check context richness
        expanded_context = expansion_data.get("expanded_context", {})
        if len(expanded_context) >= 3:
            quality_score += 0.1

        if len(expanded_context) >= 5:
            quality_score += 0.1

        return min(1.0, quality_score)

    def _create_context_relationships(
        self, knowledge_points: list[KnowledgePoint], expansions: list[ContextExpansion]
    ) -> list[dict[str, Any]]:
        """Create relationships between contexts.

        Args:
            knowledge_points: Original knowledge points
            expansions: Context expansions

        Returns:
            List of context relationships
        """
        relationships = []

        # Group expansions by type
        expansions_by_type = {}
        for exp in expansions:
            if exp.expansion_type not in expansions_by_type:
                expansions_by_type[exp.expansion_type] = []
            expansions_by_type[exp.expansion_type].append(exp)

        # Find relationships within expansion types
        for exp_type, type_expansions in expansions_by_type.items():
            for i, exp1 in enumerate(type_expansions):
                for exp2 in type_expansions[i + 1 :]:
                    # Check for context overlap
                    context1_keys = set(exp1.expanded_context.keys())
                    context2_keys = set(exp2.expanded_context.keys())

                    overlap = context1_keys.intersection(context2_keys)
                    if len(overlap) > 0:
                        relationships.append(
                            {
                                "source_expansion_id": exp1.source_id,
                                "target_expansion_id": exp2.source_id,
                                "relationship_type": f"{exp_type}_context_overlap",
                                "shared_context_keys": list(overlap),
                                "relationship_strength": len(overlap) / max(len(context1_keys), len(context2_keys)),
                                "metadata": {
                                    "expansion_type": exp_type,
                                    "source_confidence": exp1.confidence,
                                    "target_confidence": exp2.confidence,
                                },
                            }
                        )

        return relationships

    def _generate_context_summary(self, expansions: list[ContextExpansion], validations: list[ContextValidation]) -> dict[str, Any]:
        """Generate summary of context processing.

        Args:
            expansions: List of context expansions
            validations: List of context validations

        Returns:
            Context processing summary
        """
        summary = {
            "expansion_summary": {
                "total_expansions": len(expansions),
                "by_type": {},
                "average_confidence": self._calculate_average_confidence(expansions),
                "high_confidence_count": len([e for e in expansions if e.confidence >= 0.8]),
            },
            "validation_summary": {
                "total_validations": len(validations),
                "valid_count": len([v for v in validations if v.is_valid]),
                "average_validation_score": self._calculate_average_validation_score(validations),
                "common_issues": self._get_common_issues(validations),
            },
        }

        # Count expansions by type
        for exp in expansions:
            exp_type = exp.expansion_type
            if exp_type not in summary["expansion_summary"]["by_type"]:
                summary["expansion_summary"]["by_type"][exp_type] = 0
            summary["expansion_summary"]["by_type"][exp_type] += 1

        return summary

    def _calculate_average_confidence(self, expansions: list[ContextExpansion]) -> float:
        """Calculate average confidence of expansions.

        Args:
            expansions: List of expansions

        Returns:
            Average confidence score
        """
        if not expansions:
            return 0.0

        return sum(exp.confidence for exp in expansions) / len(expansions)

    def _calculate_average_validation_score(self, validations: list[ContextValidation]) -> float:
        """Calculate average validation score.

        Args:
            validations: List of validations

        Returns:
            Average validation score
        """
        if not validations:
            return 0.0

        return sum(val.validation_score for val in validations) / len(validations)

    def _calculate_validation_pass_rate(self, validations: list[ContextValidation]) -> float:
        """Calculate validation pass rate.

        Args:
            validations: List of validations

        Returns:
            Pass rate between 0 and 1
        """
        if not validations:
            return 0.0

        valid_count = len([v for v in validations if v.is_valid])
        return valid_count / len(validations)

    def _get_common_issues(self, validations: list[ContextValidation]) -> list[str]:
        """Get most common validation issues.

        Args:
            validations: List of validations

        Returns:
            List of common issues
        """
        issue_counts = {}

        for validation in validations:
            for issue in validation.issues_found:
                if issue not in issue_counts:
                    issue_counts[issue] = 0
                issue_counts[issue] += 1

        # Sort by frequency and return top 5
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        return [issue for issue, count in sorted_issues[:5]]
