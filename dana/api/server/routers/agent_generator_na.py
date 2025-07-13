from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from ..agent_generator import generate_agent_code_na
import logging

router = APIRouter(prefix="/agent-generator-na", tags=["agent-generator-na"])

class Message(BaseModel):
    """Message model for conversation"""
    role: str
    content: str

class AgentGeneratorNARequest(BaseModel):
    """Request model for NA-based agent generation"""
    messages: List[Message]
    current_code: Optional[str] = ""

class AgentGeneratorNAResponse(BaseModel):
    """Response model for NA-based agent generation"""
    success: bool
    dana_code: str
    error: Optional[str] = None

@router.post("/generate", response_model=AgentGeneratorNAResponse)
async def generate_agent_na(request: AgentGeneratorNARequest):
    """
    Generate Dana agent code using NA-based approach.
    
    This endpoint uses a .na file executed with DanaSandbox.quick_run to generate
    Dana agent code based on conversation messages and optional current code.
    
    Args:
        request: AgentGeneratorNARequest containing messages and optional current_code
        
    Returns:
        AgentGeneratorNAResponse with generated Dana code or error
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Received NA-based agent generation request with {len(request.messages)} messages")
        
        # Convert Pydantic models to dictionaries
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        logger.info(f"Converted messages: {messages}")
        
        # Generate Dana code using NA approach
        logger.info("Calling generate_agent_code_na...")
        dana_code, error = await generate_agent_code_na(messages, request.current_code or "")
        logger.info(f"Generated Dana code length: {len(dana_code)}")
        logger.debug(f"Generated Dana code: {dana_code[:500]}...")
        
        if error:
            logger.error(f"Error in NA-based generation: {error}")
            return AgentGeneratorNAResponse(
                success=False,
                dana_code="",
                error=error
            )
        
        return AgentGeneratorNAResponse(
            success=True,
            dana_code=dana_code,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error in generate_agent_na endpoint: {e}", exc_info=True)
        return AgentGeneratorNAResponse(
            success=False,
            dana_code="",
            error=f"Failed to generate agent code: {str(e)}"
        )

@router.get("/health")
def health():
    """Health check endpoint for NA-based agent generator"""
    return {"status": "healthy", "service": "NA-based Agent Generator"} 