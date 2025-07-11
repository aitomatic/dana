from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import db, schemas, services
from ..schemas import RunNAFileRequest, RunNAFileResponse, AgentGenerationRequest, AgentGenerationResponse
from ..services import run_na_file_service
from ..agent_generator import generate_agent_code_from_messages

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("/", response_model=list[schemas.AgentRead])
def list_agents(skip: int = 0, limit: int = 10, db: Session = Depends(db.get_db)):
    return services.get_agents(db, skip=skip, limit=limit)


@router.get("/{agent_id}", response_model=schemas.AgentRead)
def get_agent(agent_id: int, db: Session = Depends(db.get_db)):
    agent = services.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/", response_model=schemas.AgentRead)
def create_agent(agent: schemas.AgentCreate, db: Session = Depends(db.get_db)):
    return services.create_agent(db, agent)


@router.post("/run-na-file", response_model=RunNAFileResponse)
def run_na_file(request: RunNAFileRequest):
    return run_na_file_service(request)


@router.post("/generate", response_model=AgentGenerationResponse)
async def generate_agent(request: AgentGenerationRequest):
    """
    Generate Dana agent code from user conversation messages.
    
    This endpoint takes a list of conversation messages and generates
    appropriate Dana code for creating an agent based on the user's requirements.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Received agent generation request with {len(request.messages)} messages")
        
        # Convert Pydantic models to dictionaries
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        logger.info(f"Converted messages: {messages}")
        
        # Generate Dana code
        logger.info("Calling generate_agent_code_from_messages...")
        dana_code = await generate_agent_code_from_messages(messages, request.current_code or "")
        logger.info(f"Generated Dana code length: {len(dana_code)}")
        logger.debug(f"Generated Dana code: {dana_code[:500]}...")
        
        # Extract agent name and description from the generated code
        agent_name = None
        agent_description = None
        
        lines = dana_code.split('\n')
        for i, line in enumerate(lines):
            # Look for agent keyword syntax: agent AgentName:
            if line.strip().startswith('agent ') and line.strip().endswith(':'):
                # Next few lines should contain name and description
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if 'name : str =' in next_line:
                        agent_name = next_line.split('=')[1].strip().strip('"')
                        logger.info(f"Extracted agent name: {agent_name}")
                    elif 'description : str =' in next_line:
                        agent_description = next_line.split('=')[1].strip().strip('"')
                        logger.info(f"Extracted agent description: {agent_description}")
                    elif next_line.startswith('#'):  # Skip comments
                        continue
                    elif next_line == '':  # Skip empty lines
                        continue
                    elif not next_line.startswith('    '):  # Stop at non-indented lines
                        break
                break
            # Fallback: also check for old system: syntax
            elif 'system:agent_name' in line:
                agent_name = line.split('=')[1].strip().strip('"')
                logger.info(f"Extracted agent name (old format): {agent_name}")
            elif 'system:agent_description' in line:
                agent_description = line.split('=')[1].strip().strip('"')
                logger.info(f"Extracted agent description (old format): {agent_description}")
        
        response = AgentGenerationResponse(
            success=True,
            dana_code=dana_code,
            agent_name=agent_name,
            agent_description=agent_description
        )
        
        logger.info(f"Returning response with success={response.success}, code_length={len(response.dana_code)}")
        return response
        
    except Exception as e:
        logger.error(f"Error in generate_agent endpoint: {e}", exc_info=True)
        return AgentGenerationResponse(
            success=False,
            dana_code="",
            error=f"Failed to generate agent code: {str(e)}"
        )
