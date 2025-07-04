"""
Meta knowledge extractor for Dana KNOWS system.

This module handles extracting high-level meta knowledge points from documents using LLM.
"""

import json
import uuid
from typing import Any

from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.types import BaseRequest
from dana.common.utils.logging import DANA_LOGGER
from dana.frameworks.knows.core.base import Document, KnowledgePoint, ProcessorBase


class MetaKnowledgeExtractor(ProcessorBase):
    """Extract meta-level knowledge points from documents using LLM."""
    
    DEFAULT_CONFIDENCE_THRESHOLD = 0.7
    MAX_RETRIES = 3
    
    def __init__(self, 
                 llm_resource: LLMResource | None = None,
                 confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
                 max_knowledge_points: int = 10):
        """Initialize meta knowledge extractor.
        
        Args:
            llm_resource: LLM resource for knowledge extraction
            confidence_threshold: Minimum confidence for knowledge points
            max_knowledge_points: Maximum number of knowledge points to extract
        """
        self.llm_resource = llm_resource or LLMResource()
        self.confidence_threshold = confidence_threshold
        self.max_knowledge_points = max_knowledge_points
        DANA_LOGGER.info(f"Initialized MetaKnowledgeExtractor with threshold: {confidence_threshold}")
    
    def process(self, document: Document) -> list[KnowledgePoint]:
        """Extract meta knowledge points from document.
        
        Args:
            document: Document to extract knowledge from
            
        Returns:
            List of extracted knowledge points
            
        Raises:
            ValueError: If document is invalid or extraction fails
        """
        if not self.validate_input(document):
            raise ValueError("Invalid document provided for meta knowledge extraction")
        
        try:
            # Extract meta knowledge using LLM
            knowledge_points = self._extract_with_llm(document)
            
            # Filter by confidence threshold
            filtered_points = [
                kp for kp in knowledge_points 
                if kp.confidence >= self.confidence_threshold
            ]
            
            # Limit number of points
            if len(filtered_points) > self.max_knowledge_points:
                # Sort by confidence and take top points
                filtered_points.sort(key=lambda x: x.confidence, reverse=True)
                filtered_points = filtered_points[:self.max_knowledge_points]
            
            DANA_LOGGER.info(f"Extracted {len(filtered_points)} meta knowledge points from document {document.id}")
            return filtered_points
            
        except Exception as e:
            DANA_LOGGER.error(f"Failed to extract meta knowledge from document {document.id}: {str(e)}")
            # Apply fallback mechanism
            return self._fallback_extraction(document)
    
    def validate_input(self, document: Document) -> bool:
        """Validate document before processing.
        
        Args:
            document: Document to validate
            
        Returns:
            True if document is valid
        """
        if not isinstance(document, Document):
            DANA_LOGGER.error("Input must be a Document object")
            return False
        
        if not document.content or len(document.content.strip()) == 0:
            DANA_LOGGER.error("Document content is empty")
            return False
        
        if len(document.content) > 50000:  # 50KB limit for LLM processing
            DANA_LOGGER.warning(f"Document {document.id} is large ({len(document.content)} chars), may impact performance")
        
        return True
    
    def _extract_with_llm(self, document: Document) -> list[KnowledgePoint]:
        """Extract knowledge points using LLM.
        
        Args:
            document: Document to process
            
        Returns:
            List of knowledge points
        """
        prompt = self._build_extraction_prompt(document)
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Query LLM for meta knowledge extraction
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant that extracts knowledge points from documents."},
                    {"role": "user", "content": prompt}
                ]
                
                request_params = {
                    "messages": messages,
                    "temperature": 0.3,  # Lower temperature for more consistent extraction
                    "max_tokens": 2000
                }
                
                request = BaseRequest(arguments=request_params)
                response = self.llm_resource.query_sync(request)
                
                if not response.success:
                    raise Exception(f"LLM query failed: {response.error}")
                
                # Extract response text
                response_text = self._extract_response_text(response.content)
                knowledge_points = self._parse_llm_response(response_text, document)
                
                if knowledge_points:
                    return knowledge_points
                
                DANA_LOGGER.warning(f"LLM extraction attempt {attempt + 1} returned no valid knowledge points")
                
            except Exception as e:
                DANA_LOGGER.error(f"LLM extraction attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.MAX_RETRIES - 1:
                    raise
        
        return []
    
    def _build_extraction_prompt(self, document: Document) -> str:
        """Build prompt for LLM meta knowledge extraction.
        
        Args:
            document: Document to extract from
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""
Extract high-level meta knowledge points from the following document. Focus on:
1. Key concepts and their relationships
2. Main processes or workflows described
3. Important facts, metrics, or specifications
4. Problem statements and solutions
5. Best practices or recommendations

Document Type: {document.format}
Document Content:
{document.content[:4000]}  # Limit content to avoid token limits

Please provide your response as a JSON array of knowledge points, where each point has:
- "content": The knowledge point description (string)
- "type": The category (one of: concept, process, fact, metric, problem, solution, best_practice)
- "confidence": Confidence score from 0.0 to 1.0 (float)
- "context": Related context or supporting information (object)

Example format:
[
  {{
    "content": "The system uses OAuth 2.0 for authentication",
    "type": "fact",
    "confidence": 0.9,
    "context": {{
      "domain": "authentication",
      "technical_level": "intermediate",
      "keywords": ["OAuth", "security", "authentication"]
    }}
  }}
]

Extract up to {self.max_knowledge_points} knowledge points, prioritizing the most important and relevant information.
"""
        return prompt.strip()
    
    def _extract_response_text(self, response_content: Any) -> str:
        """Extract text from LLM response content.
        
        Args:
            response_content: LLM response content
            
        Returns:
            Extracted text string
        """
        try:
            # Handle different response formats
            if isinstance(response_content, str):
                # Check if it's a string representation of the response object
                if response_content.startswith("{'choices':") or response_content.startswith('{"choices":'):
                    # Extract the content from the string representation
                    # Look for the content pattern: ChatCompletionMessage(content='...')
                    
                    # Find the start of the content field
                    content_start = response_content.find("content='")
                    if content_start != -1:
                        content_start += len("content='")
                        
                        # Find the end of the content field by looking for the pattern ', refusal=
                        content_end = response_content.find("', refusal=", content_start)
                        if content_end != -1:
                            content = response_content[content_start:content_end]
                            # Handle escaped quotes and newlines
                            content = content.replace("\\'", "'").replace("\\n", "\n").replace("\\t", "\t")
                            return content
                
                return response_content
            
            if isinstance(response_content, dict):
                # Handle OpenAI/Anthropic style response
                if "choices" in response_content and response_content["choices"]:
                    first_choice = response_content["choices"][0]
                    
                    # Handle OpenAI response objects (not plain dicts)
                    if hasattr(first_choice, 'message') and hasattr(first_choice.message, 'content'):
                        return first_choice.message.content
                    
                    # Handle plain dict format
                    if isinstance(first_choice, dict):
                        if "message" in first_choice:
                            message = first_choice["message"]
                            if isinstance(message, dict) and "content" in message:
                                return message["content"]
                        elif "text" in first_choice:
                            return first_choice["text"]
                
                # Handle direct content format
                if "content" in response_content:
                    return response_content["content"]
            
            # For objects with attributes (like OpenAI response objects)
            if hasattr(response_content, 'choices') and response_content.choices:
                first_choice = response_content.choices[0]
                if hasattr(first_choice, 'message') and hasattr(first_choice.message, 'content'):
                    return first_choice.message.content
            
            # Fallback to string conversion
            return str(response_content)
            
        except Exception as e:
            DANA_LOGGER.error(f"Error extracting response text: {str(e)}")
            return str(response_content)
    
    def _parse_llm_response(self, response: str, document: Document) -> list[KnowledgePoint]:
        """Parse LLM response into knowledge points.
        
        Args:
            response: LLM response text
            document: Source document
            
        Returns:
            List of parsed knowledge points
        """
        try:
            # Try to extract JSON from response
            response_clean = response.strip()
            
            # Handle cases where LLM wraps JSON in markdown
            if response_clean.startswith('```json'):
                start = response_clean.find('[')
                end = response_clean.rfind(']') + 1
                if start != -1 and end > start:
                    response_clean = response_clean[start:end]
            elif response_clean.startswith('```'):
                start = response_clean.find('[')
                end = response_clean.rfind(']') + 1
                if start != -1 and end > start:
                    response_clean = response_clean[start:end]
            
            # Parse JSON
            parsed_data = json.loads(response_clean)
            
            if not isinstance(parsed_data, list):
                DANA_LOGGER.error("LLM response is not a JSON array")
                return []
            
            knowledge_points = []
            for item in parsed_data:
                try:
                    kp = self._create_knowledge_point(item, document)
                    if kp:
                        knowledge_points.append(kp)
                except Exception as e:
                    DANA_LOGGER.warning(f"Failed to parse knowledge point: {str(e)}")
                    continue
            
            return knowledge_points
            
        except json.JSONDecodeError as e:
            DANA_LOGGER.error(f"Failed to parse LLM response as JSON: {str(e)}")
            return []
        except Exception as e:
            DANA_LOGGER.error(f"Error parsing LLM response: {str(e)}")
            return []
    
    def _create_knowledge_point(self, data: dict[str, Any], document: Document) -> KnowledgePoint | None:
        """Create a KnowledgePoint from parsed data.
        
        Args:
            data: Parsed knowledge point data
            document: Source document
            
        Returns:
            KnowledgePoint instance or None if invalid
        """
        try:
            # Validate required fields
            if not isinstance(data.get('content'), str) or not data['content'].strip():
                return None
            
            if not isinstance(data.get('type'), str):
                return None
            
            confidence = data.get('confidence', 0.5)
            if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
                confidence = 0.5
            
            context = data.get('context', {})
            if not isinstance(context, dict):
                context = {}
            
            # Add source information to context
            context.update({
                'source_document_id': document.id,
                'source_format': document.format,
                'extraction_method': 'llm_meta_extraction'
            })
            
            # Create knowledge point
            kp = KnowledgePoint(
                id=self._generate_knowledge_point_id(),
                type=data['type'],
                content=data['content'].strip(),
                context=context,
                confidence=float(confidence),
                metadata={
                    'extracted_from': document.id,
                    'extraction_timestamp': self._get_timestamp(),
                    'extractor_version': '1.0'
                }
            )
            
            return kp
            
        except Exception as e:
            DANA_LOGGER.error(f"Error creating knowledge point: {str(e)}")
            return None
    
    def _fallback_extraction(self, document: Document) -> list[KnowledgePoint]:
        """Fallback extraction method when LLM fails.
        
        Args:
            document: Document to extract from
            
        Returns:
            List of basic knowledge points
        """
        DANA_LOGGER.info(f"Applying fallback extraction for document {document.id}")
        
        try:
            # Basic rule-based extraction as fallback
            content = document.content
            
            # Extract sentences that might contain important information
            sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20]
            
            knowledge_points = []
            for i, sentence in enumerate(sentences[:5]):  # Limit to first 5 sentences
                if self._is_potentially_important(sentence):
                    kp = KnowledgePoint(
                        id=self._generate_knowledge_point_id(),
                        type="fact",
                        content=sentence,
                        context={
                            'source_document_id': document.id,
                            'extraction_method': 'fallback_rule_based',
                            'sentence_index': i
                        },
                        confidence=0.5,  # Lower confidence for fallback
                        metadata={
                            'extracted_from': document.id,
                            'extraction_timestamp': self._get_timestamp(),
                            'extractor_version': '1.0',
                            'is_fallback': True
                        }
                    )
                    knowledge_points.append(kp)
            
            DANA_LOGGER.info(f"Fallback extraction produced {len(knowledge_points)} knowledge points")
            return knowledge_points
            
        except Exception as e:
            DANA_LOGGER.error(f"Fallback extraction failed: {str(e)}")
            return []
    
    def _is_potentially_important(self, sentence: str) -> bool:
        """Check if a sentence contains potentially important information.
        
        Args:
            sentence: Sentence to check
            
        Returns:
            True if sentence seems important
        """
        # Simple heuristics for identifying important sentences
        important_indicators = [
            'process', 'workflow', 'step', 'procedure',
            'requirement', 'specification', 'standard',
            'metric', 'performance', 'accuracy', 'efficiency',
            'problem', 'issue', 'challenge', 'solution',
            'best practice', 'recommendation', 'guideline',
            'key', 'important', 'critical', 'essential',
            'algorithm', 'method', 'approach', 'technique'
        ]
        
        sentence_lower = sentence.lower()
        return any(indicator in sentence_lower for indicator in important_indicators)
    
    def _generate_knowledge_point_id(self) -> str:
        """Generate unique ID for knowledge point.
        
        Returns:
            Unique knowledge point ID
        """
        return f"kp_{uuid.uuid4().hex[:8]}"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp.
        
        Returns:
            ISO format timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat() 