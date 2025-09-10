"""
Text format templates for the Context Engineering Framework.
"""

from .analysis import TextAnalysisTemplate
from .conversation import TextConversationTemplate
from .general import TextGeneralTemplate
from .problem_solving import TextProblemSolvingTemplate

__all__ = ["TextProblemSolvingTemplate", "TextConversationTemplate", "TextAnalysisTemplate", "TextGeneralTemplate"]
