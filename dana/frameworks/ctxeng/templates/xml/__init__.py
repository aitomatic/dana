"""
XML format templates for the Context Engineering Framework.
"""

from .analysis import XMLAnalysisTemplate
from .conversation import XMLConversationTemplate
from .general import XMLGeneralTemplate
from .problem_solving import XMLProblemSolvingTemplate

__all__ = ["XMLProblemSolvingTemplate", "XMLConversationTemplate", "XMLAnalysisTemplate", "XMLGeneralTemplate"]
