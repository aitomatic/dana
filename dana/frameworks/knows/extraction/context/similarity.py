"""
Similarity search component for Dana KNOWS system.

This module handles vector-based similarity search, semantic matching, and relevance scoring.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np

from dana.common.utils.logging import DANA_LOGGER
from dana.frameworks.knows.core.base import KnowledgePoint, ProcessorBase


@dataclass
class SimilarityResult:
    """Result of similarity search operation."""
    
    query_id: str
    similar_items: list[dict[str, Any]]
    search_metadata: dict[str, Any]
    confidence: float


@dataclass
class SemanticMatch:
    """Semantic match between knowledge points."""
    
    source_id: str
    target_id: str
    similarity_score: float
    match_type: str  # "semantic", "keyword", "contextual"
    matching_features: list[str]
    metadata: dict[str, Any]


class SimilaritySearcher(ProcessorBase):
    """Vector-based similarity search and semantic matching."""
    
    DEFAULT_SIMILARITY_THRESHOLD = 0.7
    DEFAULT_MAX_RESULTS = 10
    
    def __init__(self, 
                 similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
                 max_results: int = DEFAULT_MAX_RESULTS,
                 enable_semantic_search: bool = True):
        """Initialize similarity searcher.
        
        Args:
            similarity_threshold: Minimum similarity score for matches
            max_results: Maximum number of results to return
            enable_semantic_search: Whether to enable semantic matching
        """
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        self.enable_semantic_search = enable_semantic_search
        
        # Knowledge point storage for similarity comparison
        self.knowledge_index: dict[str, KnowledgePoint] = {}
        self.content_vectors: dict[str, np.ndarray] = {}
        
        DANA_LOGGER.info(f"Initialized SimilaritySearcher with threshold: {similarity_threshold}")
    
    def process(self, knowledge_points: list[KnowledgePoint]) -> dict[str, Any]:
        """Find similar content and create similarity mappings.
        
        Args:
            knowledge_points: List of knowledge points to process
            
        Returns:
            Dictionary containing similarity results and mappings
            
        Raises:
            ValueError: If input is invalid
        """
        if not self.validate_input(knowledge_points):
            raise ValueError("Invalid knowledge points provided for similarity search")
        
        try:
            # Index knowledge points
            self._build_knowledge_index(knowledge_points)
            
            # Generate content vectors
            self._generate_content_vectors(knowledge_points)
            
            # Find similarities
            similarity_mappings = self._find_similarities(knowledge_points)
            
            # Create semantic matches
            semantic_matches = self._create_semantic_matches(similarity_mappings)
            
            # Generate similarity clusters
            clusters = self._generate_similarity_clusters(semantic_matches)
            
            result = {
                'similarity_mappings': similarity_mappings,
                'semantic_matches': semantic_matches,
                'similarity_clusters': clusters,
                'index_metadata': {
                    'total_knowledge_points': len(knowledge_points),
                    'indexed_points': len(self.knowledge_index),
                    'vector_dimensions': self._get_vector_dimensions(),
                    'similarity_threshold': self.similarity_threshold
                }
            }
            
            DANA_LOGGER.info(f"Found {len(semantic_matches)} semantic matches across {len(knowledge_points)} knowledge points")
            return result
            
        except Exception as e:
            DANA_LOGGER.error(f"Failed to perform similarity search: {str(e)}")
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
    
    def search_similar(self, query_point: KnowledgePoint, 
                      candidate_points: list[KnowledgePoint] | None = None) -> SimilarityResult:
        """Search for similar knowledge points to a query.
        
        Args:
            query_point: Knowledge point to find similarities for
            candidate_points: Optional list of candidates (uses index if None)
            
        Returns:
            SimilarityResult with similar items
        """
        if candidate_points is None:
            candidate_points = list(self.knowledge_index.values())
        
        # Generate query vector
        query_vector = self._generate_content_vector(query_point.content)
        
        # Find similarities
        similarities = []
        for candidate in candidate_points:
            if candidate.id == query_point.id:
                continue  # Skip self
            
            candidate_vector = self.content_vectors.get(
                candidate.id, 
                self._generate_content_vector(candidate.content)
            )
            
            similarity_score = self._calculate_vector_similarity(query_vector, candidate_vector)
            
            if similarity_score >= self.similarity_threshold:
                similarities.append({
                    'knowledge_point': candidate,
                    'similarity_score': similarity_score,
                    'match_features': self._identify_matching_features(query_point, candidate)
                })
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Limit results
        similarities = similarities[:self.max_results]
        
        return SimilarityResult(
            query_id=query_point.id,
            similar_items=similarities,
            search_metadata={
                'query_content_length': len(query_point.content),
                'candidates_searched': len(candidate_points) - 1,  # Exclude self
                'matches_found': len(similarities),
                'search_method': 'vector_similarity'
            },
            confidence=self._calculate_search_confidence(similarities)
        )
    
    def _build_knowledge_index(self, knowledge_points: list[KnowledgePoint]) -> None:
        """Build searchable index of knowledge points.
        
        Args:
            knowledge_points: Knowledge points to index
        """
        self.knowledge_index = {kp.id: kp for kp in knowledge_points}
        DANA_LOGGER.info(f"Built knowledge index with {len(self.knowledge_index)} points")
    
    def _generate_content_vectors(self, knowledge_points: list[KnowledgePoint]) -> None:
        """Generate content vectors for knowledge points.
        
        Args:
            knowledge_points: Knowledge points to vectorize
        """
        self.content_vectors = {}
        for kp in knowledge_points:
            self.content_vectors[kp.id] = self._generate_content_vector(kp.content)
        
        DANA_LOGGER.info(f"Generated {len(self.content_vectors)} content vectors")
    
    def _generate_content_vector(self, content: str) -> np.ndarray:
        """Generate vector representation of content.
        
        Args:
            content: Text content to vectorize
            
        Returns:
            Vector representation
        """
        # Simple TF-IDF style vectorization for now
        # In production, this would use embeddings from models like sentence-transformers
        
        # Tokenize and create basic features
        words = content.lower().split()
        
        # Create feature vector based on word frequencies and basic features
        features = {}
        
        # Word frequency features
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1
        
        # Normalize by document length
        total_words = len(words)
        for word, count in word_counts.items():
            features[f"word_{word}"] = count / total_words
        
        # Length features
        features["length_short"] = 1.0 if total_words < 10 else 0.0
        features["length_medium"] = 1.0 if 10 <= total_words < 50 else 0.0
        features["length_long"] = 1.0 if total_words >= 50 else 0.0
        
        # Type indicators (simple keyword matching)
        content_lower = content.lower()
        features["has_process"] = 1.0 if any(word in content_lower for word in ["process", "step", "procedure"]) else 0.0
        features["has_metric"] = 1.0 if any(word in content_lower for word in ["metric", "measure", "score", "%"]) else 0.0
        features["has_problem"] = 1.0 if any(word in content_lower for word in ["problem", "issue", "error"]) else 0.0
        
        # Convert to fixed-size vector (using top 100 features, pad if needed)
        feature_names = sorted(features.keys())
        if len(feature_names) < 100:
            # Pad with zeros to ensure 100 features
            feature_names.extend([f"pad_{i}" for i in range(100 - len(feature_names))])
        else:
            feature_names = feature_names[:100]
        
        vector = np.array([features.get(name, 0.0) for name in feature_names])
        
        # Normalize vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    def _calculate_vector_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """Calculate cosine similarity between vectors.
        
        Args:
            vector1: First vector
            vector2: Second vector
            
        Returns:
            Similarity score between 0 and 1
        """
        # Ensure vectors are same length
        min_len = min(len(vector1), len(vector2))
        v1 = vector1[:min_len]
        v2 = vector2[:min_len]
        
        # Calculate cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cosine_sim = dot_product / (norm1 * norm2)
        
        # Convert to 0-1 range (cosine similarity is -1 to 1)
        return (cosine_sim + 1) / 2
    
    def _identify_matching_features(self, kp1: KnowledgePoint, kp2: KnowledgePoint) -> list[str]:
        """Identify features that match between knowledge points.
        
        Args:
            kp1: First knowledge point
            kp2: Second knowledge point
            
        Returns:
            List of matching feature names
        """
        matching_features = []
        
        # Content word overlap
        words1 = set(kp1.content.lower().split())
        words2 = set(kp2.content.lower().split())
        overlap = words1.intersection(words2)
        
        if len(overlap) > 0:
            matching_features.append(f"word_overlap_{len(overlap)}")
        
        # Type matching
        if kp1.type == kp2.type:
            matching_features.append(f"same_type_{kp1.type}")
        
        # Context matching
        if kp1.context and kp2.context:
            context1_keys = set(kp1.context.keys())
            context2_keys = set(kp2.context.keys())
            shared_keys = context1_keys.intersection(context2_keys)
            
            for key in shared_keys:
                if kp1.context[key] == kp2.context[key]:
                    matching_features.append(f"context_{key}")
        
        # Confidence similarity
        if abs(kp1.confidence - kp2.confidence) < 0.1:
            matching_features.append("similar_confidence")
        
        return matching_features
    
    def _find_similarities(self, knowledge_points: list[KnowledgePoint]) -> list[dict[str, Any]]:
        """Find all similarity relationships between knowledge points.
        
        Args:
            knowledge_points: Knowledge points to analyze
            
        Returns:
            List of similarity mappings
        """
        similarity_mappings = []
        
        for i, kp1 in enumerate(knowledge_points):
            for j, kp2 in enumerate(knowledge_points[i+1:], start=i+1):
                
                # Calculate similarity
                vector1 = self.content_vectors[kp1.id]
                vector2 = self.content_vectors[kp2.id]
                similarity_score = self._calculate_vector_similarity(vector1, vector2)
                
                if similarity_score >= self.similarity_threshold:
                    matching_features = self._identify_matching_features(kp1, kp2)
                    
                    similarity_mappings.append({
                        'source_id': kp1.id,
                        'target_id': kp2.id,
                        'similarity_score': similarity_score,
                        'matching_features': matching_features,
                        'metadata': {
                            'source_type': kp1.type,
                            'target_type': kp2.type,
                            'source_confidence': kp1.confidence,
                            'target_confidence': kp2.confidence
                        }
                    })
        
        return similarity_mappings
    
    def _create_semantic_matches(self, similarity_mappings: list[dict[str, Any]]) -> list[SemanticMatch]:
        """Create semantic match objects from similarity mappings.
        
        Args:
            similarity_mappings: Raw similarity mappings
            
        Returns:
            List of SemanticMatch objects
        """
        semantic_matches = []
        
        for mapping in similarity_mappings:
            # Determine match type based on features
            match_type = self._determine_match_type(mapping['matching_features'])
            
            semantic_match = SemanticMatch(
                source_id=mapping['source_id'],
                target_id=mapping['target_id'],
                similarity_score=mapping['similarity_score'],
                match_type=match_type,
                matching_features=mapping['matching_features'],
                metadata=mapping['metadata']
            )
            
            semantic_matches.append(semantic_match)
        
        return semantic_matches
    
    def _determine_match_type(self, matching_features: list[str]) -> str:
        """Determine the type of semantic match.
        
        Args:
            matching_features: List of matching feature names
            
        Returns:
            Match type string
        """
        # Analyze features to determine match type
        has_word_overlap = any(f.startswith("word_overlap") for f in matching_features)
        has_context_match = any(f.startswith("context_") for f in matching_features)
        has_type_match = any(f.startswith("same_type") for f in matching_features)
        
        if has_word_overlap and has_context_match:
            return "semantic"
        elif has_word_overlap:
            return "keyword"
        elif has_context_match:
            return "contextual"
        else:
            return "similarity"
    
    def _generate_similarity_clusters(self, semantic_matches: list[SemanticMatch]) -> list[dict[str, Any]]:
        """Generate clusters of similar knowledge points.
        
        Args:
            semantic_matches: List of semantic matches
            
        Returns:
            List of similarity clusters
        """
        # Simple clustering based on similarity connections
        clusters = []
        processed_ids = set()
        
        for match in semantic_matches:
            if match.source_id in processed_ids and match.target_id in processed_ids:
                continue
            
            # Find all connected points
            cluster_ids = self._find_connected_points(match.source_id, semantic_matches)
            
            if len(cluster_ids) >= 2:  # Only clusters with 2+ points
                cluster_ids_list = list(cluster_ids)
                clusters.append({
                    'cluster_id': f"cluster_{len(clusters)}",
                    'member_ids': cluster_ids_list,
                    'cluster_size': len(cluster_ids),
                    'average_similarity': self._calculate_cluster_similarity(cluster_ids_list, semantic_matches),
                    'dominant_match_type': self._get_dominant_match_type(cluster_ids_list, semantic_matches)
                })
                
                processed_ids.update(cluster_ids)
        
        return clusters
    
    def _find_connected_points(self, start_id: str, semantic_matches: list[SemanticMatch]) -> set:
        """Find all points connected to a starting point.
        
        Args:
            start_id: Starting knowledge point ID
            semantic_matches: List of semantic matches
            
        Returns:
            Set of connected point IDs
        """
        connected = {start_id}
        to_process = [start_id]
        
        while to_process:
            current_id = to_process.pop()
            
            for match in semantic_matches:
                if match.source_id == current_id and match.target_id not in connected:
                    connected.add(match.target_id)
                    to_process.append(match.target_id)
                elif match.target_id == current_id and match.source_id not in connected:
                    connected.add(match.source_id)
                    to_process.append(match.source_id)
        
        return connected
    
    def _calculate_cluster_similarity(self, cluster_ids: list[str], 
                                    semantic_matches: list[SemanticMatch]) -> float:
        """Calculate average similarity within a cluster.
        
        Args:
            cluster_ids: IDs of points in cluster
            semantic_matches: List of semantic matches
            
        Returns:
            Average similarity score
        """
        cluster_matches = [
            match for match in semantic_matches
            if match.source_id in cluster_ids and match.target_id in cluster_ids
        ]
        
        if not cluster_matches:
            return 0.0
        
        return sum(match.similarity_score for match in cluster_matches) / len(cluster_matches)
    
    def _get_dominant_match_type(self, cluster_ids: list[str], 
                                semantic_matches: list[SemanticMatch]) -> str:
        """Get the dominant match type in a cluster.
        
        Args:
            cluster_ids: IDs of points in cluster
            semantic_matches: List of semantic matches
            
        Returns:
            Dominant match type
        """
        cluster_matches = [
            match for match in semantic_matches
            if match.source_id in cluster_ids and match.target_id in cluster_ids
        ]
        
        if not cluster_matches:
            return "unknown"
        
        # Count match types
        type_counts = defaultdict(int)
        for match in cluster_matches:
            type_counts[match.match_type] += 1
        
        # Return most common type
        return max(type_counts.items(), key=lambda x: x[1])[0]
    
    def _calculate_search_confidence(self, similarities: list[dict[str, Any]]) -> float:
        """Calculate confidence in search results.
        
        Args:
            similarities: List of similarity results
            
        Returns:
            Confidence score between 0 and 1
        """
        if not similarities:
            return 0.0
        
        # Base confidence on number and quality of matches
        num_matches = len(similarities)
        avg_similarity = sum(s['similarity_score'] for s in similarities) / num_matches
        
        # Normalize based on expected number of matches
        match_factor = min(1.0, num_matches / 5.0)  # Expect ~5 good matches
        
        return (avg_similarity * 0.7) + (match_factor * 0.3)
    
    def _get_vector_dimensions(self) -> int:
        """Get the dimension of content vectors.
        
        Returns:
            Vector dimension count
        """
        if self.content_vectors:
            return len(next(iter(self.content_vectors.values())))
        return 0 