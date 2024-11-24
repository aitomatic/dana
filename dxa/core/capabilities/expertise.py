"""Domain expertise capability for DXA."""

from typing import Dict, Any, Optional, List
from dxa.core.capabilities.base import BaseCapability

class DomainExpertiseCapability(BaseCapability):
    """Capability to reason within a specific domain."""
    
    def __init__(
        self,
        domain: str,
        knowledge_base: Optional[Dict[str, Any]] = None,
        rules: Optional[List[Dict]] = None
    ):
        """Initialize domain expertise capability.
        
        Args:
            domain: The domain of expertise
            knowledge_base: Optional domain-specific knowledge
            rules: Optional domain-specific rules and constraints
        """
        super().__init__(
            name=f"{domain}_expertise",
            description=f"Domain expertise in {domain}"
        )
        self.domain = domain
        self.knowledge_base = knowledge_base or {}
        self.rules = rules or []

    async def use(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Apply domain expertise to a problem.
        
        Args:
            context: Current context including problem details
            **kwargs: Additional arguments
            
        Returns:
            Dict containing expert analysis and recommendations
        """
        if not self.is_enabled:
            return {
                "success": False,
                "error": "Domain expertise capability is disabled"
            }

        try:
            # Apply domain rules
            analysis = self._analyze_with_rules(context)
            
            # Apply domain knowledge
            insights = self._apply_knowledge(context)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                context,
                analysis,
                insights
            )
            
            return {
                "success": True,
                "domain": self.domain,
                "analysis": analysis,
                "insights": insights,
                "recommendations": recommendations
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def can_handle(self, context: Dict[str, Any]) -> bool:
        """Check if this expertise can handle the given context.
        
        Args:
            context: Context to check
            
        Returns:
            True if this expertise is relevant, False otherwise
        """
        # Check if context mentions domain
        if self.domain.lower() in str(context).lower():
            return True
            
        # Check if context matches any domain rules
        return any(
            self._matches_rule(context, rule)
            for rule in self.rules
        )

    def _analyze_with_rules(self, context: Dict[str, Any]) -> List[Dict]:
        """Analyze context using domain rules."""
        analyses = []
        for rule in self.rules:
            if self._matches_rule(context, rule):
                analyses.append({
                    "rule": rule["name"],
                    "analysis": rule["analyze"](context)
                })
        return analyses

    def _apply_knowledge(self, context: Dict[str, Any]) -> List[Dict]:
        """Apply domain knowledge to context."""
        insights = []
        for concept, knowledge in self.knowledge_base.items():
            if self._is_relevant(concept, context):
                insights.append({
                    "concept": concept,
                    "insight": knowledge["apply"](context)
                })
        return insights

    def _generate_recommendations(
        self,
        context: Dict[str, Any],
        analysis: List[Dict],
        insights: List[Dict]
    ) -> List[Dict]:
        """Generate recommendations based on analysis and insights."""
        recommendations = []
        
        # Add rule-based recommendations
        for item in analysis:
            if "recommendation" in item["rule"]:
                recommendations.append({
                    "source": f"rule:{item['rule']}",
                    "recommendation": item["rule"]["recommendation"]
                })
        
        # Add knowledge-based recommendations
        for item in insights:
            if "recommendation" in self.knowledge_base[item["concept"]]:
                recommendations.append({
                    "source": f"knowledge:{item['concept']}",
                    "recommendation": self.knowledge_base[item["concept"]]["recommendation"]
                })
        
        return recommendations

    def _matches_rule(self, context: Dict[str, Any], rule: Dict) -> bool:
        """Check if context matches a domain rule."""
        if "condition" in rule:
            return rule["condition"](context)
        return False

    def _is_relevant(self, concept: str, context: Dict[str, Any]) -> bool:
        """Check if a knowledge concept is relevant to context."""
        if concept in self.knowledge_base:
            if "is_relevant" in self.knowledge_base[concept]:
                return self.knowledge_base[concept]["is_relevant"](context)
        return False 