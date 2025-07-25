"""
Knowledge categorizer for Dana KNOWS system.

This module handles hierarchical categorization and relationship mapping of knowledge points.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from dana.common.utils.logging import DANA_LOGGER
from dana.frameworks.knows.core.base import KnowledgePoint, ProcessorBase


@dataclass
class KnowledgeCategory:
    """Knowledge category definition."""
    
    id: str
    name: str
    description: str
    parent_id: str | None = None
    keywords: list[str] = None
    confidence_threshold: float = 0.5
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass  
class CategoryRelationship:
    """Relationship between knowledge points and categories."""
    
    knowledge_point_id: str
    category_id: str
    confidence: float
    relationship_type: str  # "exact", "partial", "related"
    metadata: dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class KnowledgeCategorizer(ProcessorBase):
    """Categorize knowledge points hierarchically and map relationships."""
    
    # Default knowledge categories
    DEFAULT_CATEGORIES = [
        KnowledgeCategory(
            id="concept",
            name="Concept",
            description="Abstract concepts, definitions, and theoretical knowledge",
            keywords=["concept", "definition", "theory", "principle", "idea", "notion"]
        ),
        KnowledgeCategory(
            id="process",
            name="Process",
            description="Workflows, procedures, and step-by-step processes",
            keywords=["process", "workflow", "procedure", "step", "method", "approach"]
        ),
        KnowledgeCategory(
            id="fact",
            name="Fact",
            description="Concrete facts, data points, and specific information",
            keywords=["fact", "data", "information", "specification", "detail", "value"]
        ),
        KnowledgeCategory(
            id="metric",
            name="Metric",
            description="Measurements, performance indicators, and quantitative data",
            keywords=["metric", "measurement", "performance", "kpi", "indicator", "score"]
        ),
        KnowledgeCategory(
            id="problem",
            name="Problem",
            description="Problems, issues, challenges, and error conditions",
            keywords=["problem", "issue", "challenge", "error", "bug", "failure"]
        ),
        KnowledgeCategory(
            id="solution",
            name="Solution",
            description="Solutions, fixes, workarounds, and resolution methods",
            keywords=["solution", "fix", "resolve", "workaround", "remedy", "answer"]
        ),
        KnowledgeCategory(
            id="best_practice",
            name="Best Practice",
            description="Recommendations, guidelines, and proven practices",
            keywords=["best practice", "recommendation", "guideline", "standard", "practice"]
        )
    ]
    
    def __init__(self, 
                 categories: list[KnowledgeCategory] | None = None,
                 similarity_threshold: float = 0.6):
        """Initialize knowledge categorizer.
        
        Args:
            categories: Custom categories to use (defaults to DEFAULT_CATEGORIES)
            similarity_threshold: Minimum similarity for category assignment
        """
        self.categories = categories or self.DEFAULT_CATEGORIES
        self.similarity_threshold = similarity_threshold
        self.category_index = {cat.id: cat for cat in self.categories}
        
        DANA_LOGGER.info(f"Initialized KnowledgeCategorizer with {len(self.categories)} categories")
    
    def process(self, knowledge_points: list[KnowledgePoint]) -> dict[str, Any]:
        """Categorize knowledge points and map relationships.
        
        Args:
            knowledge_points: List of knowledge points to categorize
            
        Returns:
            Dictionary containing categorization results
            
        Raises:
            ValueError: If input is invalid
        """
        if not self.validate_input(knowledge_points):
            raise ValueError("Invalid knowledge points provided for categorization")
        
        try:
            # Categorize individual knowledge points
            categorized_points = []
            relationships = []
            
            for kp in knowledge_points:
                category_assignments = self._categorize_knowledge_point(kp)
                categorized_points.append({
                    'knowledge_point': kp,
                    'categories': category_assignments
                })
                
                # Create relationships
                for assignment in category_assignments:
                    rel = CategoryRelationship(
                        knowledge_point_id=kp.id,
                        category_id=assignment['category_id'],
                        confidence=assignment['confidence'],
                        relationship_type=assignment['relationship_type'],
                        metadata={
                            'matching_keywords': assignment.get('matching_keywords', []),
                            'assignment_method': 'keyword_similarity'
                        }
                    )
                    relationships.append(rel)
            
            # Map inter-point relationships
            point_relationships = self._map_knowledge_point_relationships(knowledge_points)
            
            # Generate category hierarchy
            hierarchy = self._build_category_hierarchy()
            
            result = {
                'categorized_points': categorized_points,
                'category_relationships': relationships,
                'point_relationships': point_relationships,
                'category_hierarchy': hierarchy,
                'summary': self._generate_categorization_summary(categorized_points, relationships)
            }
            
            DANA_LOGGER.info(f"Categorized {len(knowledge_points)} knowledge points into {len(set(r.category_id for r in relationships))} categories")
            return result
            
        except Exception as e:
            DANA_LOGGER.error(f"Failed to categorize knowledge points: {str(e)}")
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
    
    def _categorize_knowledge_point(self, knowledge_point: KnowledgePoint) -> list[dict[str, Any]]:
        """Categorize a single knowledge point.
        
        Args:
            knowledge_point: Knowledge point to categorize
            
        Returns:
            List of category assignments with confidence scores
        """
        assignments = []
        
        # Check existing type assignment
        existing_type = knowledge_point.type
        if existing_type and existing_type in self.category_index:
            assignments.append({
                'category_id': existing_type,
                'confidence': 0.9,  # High confidence for existing assignments
                'relationship_type': 'exact',
                'assignment_method': 'existing_type'
            })
        
        # Keyword-based categorization
        content_text = knowledge_point.content.lower()
        context_text = str(knowledge_point.context).lower() if knowledge_point.context else ""
        combined_text = f"{content_text} {context_text}"
        
        for category in self.categories:
            if category.id == existing_type:
                continue  # Skip already assigned category
            
            similarity_score = self._calculate_keyword_similarity(combined_text, category.keywords)
            
            if similarity_score >= self.similarity_threshold:
                relationship_type = self._determine_relationship_type(similarity_score)
                
                matching_keywords = [
                    kw for kw in category.keywords 
                    if kw in combined_text
                ]
                
                assignments.append({
                    'category_id': category.id,
                    'confidence': similarity_score,
                    'relationship_type': relationship_type,
                    'matching_keywords': matching_keywords,
                    'assignment_method': 'keyword_similarity'
                })
        
        # Sort by confidence and return top assignments
        assignments.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Limit to top 3 assignments to avoid over-categorization
        return assignments[:3]
    
    def _calculate_keyword_similarity(self, text: str, keywords: list[str]) -> float:
        """Calculate similarity between text and category keywords.
        
        Args:
            text: Text to analyze
            keywords: Category keywords
            
        Returns:
            Similarity score between 0 and 1
        """
        if not keywords:
            return 0.0
        
        matches = 0
        for keyword in keywords:
            if keyword.lower() in text:
                matches += 1
        
        # Calculate basic keyword match ratio
        base_score = matches / len(keywords)
        
        # Boost score for multiple matches
        if matches > 1:
            base_score = min(1.0, base_score * 1.2)
        
        return base_score
    
    def _determine_relationship_type(self, similarity_score: float) -> str:
        """Determine relationship type based on similarity score.
        
        Args:
            similarity_score: Similarity score
            
        Returns:
            Relationship type string
        """
        if similarity_score >= 0.8:
            return "exact"
        elif similarity_score >= 0.6:
            return "partial"
        else:
            return "related"
    
    def _map_knowledge_point_relationships(self, knowledge_points: list[KnowledgePoint]) -> list[dict[str, Any]]:
        """Map relationships between knowledge points.
        
        Args:
            knowledge_points: List of knowledge points
            
        Returns:
            List of relationships between knowledge points
        """
        relationships = []
        
        for i, kp1 in enumerate(knowledge_points):
            for j, kp2 in enumerate(knowledge_points[i+1:], start=i+1):
                # Calculate content similarity
                similarity = self._calculate_content_similarity(kp1.content, kp2.content)
                
                if similarity >= 0.7:  # High similarity threshold for relationships
                    relationships.append({
                        'source_id': kp1.id,
                        'target_id': kp2.id,
                        'relationship_type': 'similar_content',
                        'strength': similarity,
                        'metadata': {
                            'method': 'content_similarity',
                            'threshold': 0.7
                        }
                    })
                
                # Check for contextual relationships
                if self._have_contextual_relationship(kp1, kp2):
                    relationships.append({
                        'source_id': kp1.id,
                        'target_id': kp2.id,
                        'relationship_type': 'contextual',
                        'strength': 0.8,
                        'metadata': {
                            'method': 'contextual_analysis',
                            'shared_context': self._find_shared_context(kp1, kp2)
                        }
                    })
        
        return relationships
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content strings.
        
        Args:
            content1: First content string
            content2: Second content string
            
        Returns:
            Similarity score between 0 and 1
        """
        # Simple word-based similarity calculation
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _have_contextual_relationship(self, kp1: KnowledgePoint, kp2: KnowledgePoint) -> bool:
        """Check if two knowledge points have contextual relationship.
        
        Args:
            kp1: First knowledge point
            kp2: Second knowledge point
            
        Returns:
            True if they have contextual relationship
        """
        # Check if they come from the same document
        kp1_doc = kp1.context.get('source_document_id') if kp1.context else None
        kp2_doc = kp2.context.get('source_document_id') if kp2.context else None
        
        if kp1_doc and kp2_doc and kp1_doc == kp2_doc:
            return True
        
        # Check for shared keywords in context
        kp1_keywords = kp1.context.get('keywords', []) if kp1.context else []
        kp2_keywords = kp2.context.get('keywords', []) if kp2.context else []
        
        if kp1_keywords and kp2_keywords:
            shared_keywords = set(kp1_keywords).intersection(set(kp2_keywords))
            return len(shared_keywords) >= 2
        
        return False
    
    def _find_shared_context(self, kp1: KnowledgePoint, kp2: KnowledgePoint) -> dict[str, Any]:
        """Find shared context between two knowledge points.
        
        Args:
            kp1: First knowledge point
            kp2: Second knowledge point
            
        Returns:
            Dictionary of shared context elements
        """
        shared = {}
        
        if kp1.context and kp2.context:
            # Find common keys and values
            for key in kp1.context:
                if key in kp2.context and kp1.context[key] == kp2.context[key]:
                    shared[key] = kp1.context[key]
        
        return shared
    
    def _build_category_hierarchy(self) -> dict[str, Any]:
        """Build hierarchical representation of categories.
        
        Returns:
            Category hierarchy structure
        """
        hierarchy = {
            'root_categories': [],
            'category_tree': {}
        }
        
        for category in self.categories:
            category_info = {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'keywords': category.keywords,
                'parent_id': category.parent_id
            }
            
            if category.parent_id is None:
                hierarchy['root_categories'].append(category_info)
            
            hierarchy['category_tree'][category.id] = category_info
        
        return hierarchy
    
    def _generate_categorization_summary(self, 
                                       categorized_points: list[dict[str, Any]], 
                                       relationships: list[CategoryRelationship]) -> dict[str, Any]:
        """Generate summary of categorization results.
        
        Args:
            categorized_points: Categorized knowledge points
            relationships: Category relationships
            
        Returns:
            Summary statistics
        """
        category_counts = defaultdict(int)
        confidence_scores = []
        
        for rel in relationships:
            category_counts[rel.category_id] += 1
            confidence_scores.append(rel.confidence)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            'total_knowledge_points': len(categorized_points),
            'total_categories_used': len(category_counts),
            'category_distribution': dict(category_counts),
            'average_confidence': avg_confidence,
            'high_confidence_assignments': len([c for c in confidence_scores if c >= 0.8]),
            'low_confidence_assignments': len([c for c in confidence_scores if c < 0.6])
        } 