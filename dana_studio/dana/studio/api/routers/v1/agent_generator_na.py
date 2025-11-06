import logging

from fastapi import APIRouter
from pydantic import BaseModel

from ..agent_generator import analyze_agent_capabilities, analyze_conversation_completeness, generate_agent_code_na

router = APIRouter(prefix="/agent-generator-na", tags=["agent-generator-na"])


class Message(BaseModel):
    """Message model for conversation"""

    role: str
    content: str


class AgentGeneratorNARequest(BaseModel):
    """Request model for NA-based agent generation"""

    messages: list[Message]
    current_code: str | None = ""


class AgentCapabilities(BaseModel):
    """Agent capabilities extracted from analysis"""

    summary: str | None = None
    knowledge: list[str] | None = None
    workflow: list[str] | None = None
    tools: list[str] | None = None


class AgentGeneratorNAResponse(BaseModel):
    """Response model for NA-based agent generation"""

    success: bool
    dana_code: str
    agent_name: str | None = None
    agent_description: str | None = None
    capabilities: AgentCapabilities | None = None
    needs_more_info: bool = False
    follow_up_message: str | None = None
    suggested_questions: list[str] | None = None
    error: str | None = None


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

        # Generate Dana code using NA approach first
        logger.info("Calling generate_agent_code_na...")
        dana_code, error = await generate_agent_code_na(messages, request.current_code or "")
        logger.info(f"Generated Dana code length: {len(dana_code)}")
        logger.debug(f"Generated Dana code: {dana_code[:500]}...")

        if error:
            logger.error(f"Error in NA-based generation: {error}")
            return AgentGeneratorNAResponse(success=False, dana_code="", error=error)

        # Analyze if we need more information
        conversation_analysis = await analyze_conversation_completeness(messages)

        # Extract agent name and description from the generated code
        agent_name = None
        agent_description = None

        lines = dana_code.split("\n")
        for i, line in enumerate(lines):
            # Look for agent keyword syntax: agent AgentName:
            if line.strip().startswith("agent ") and line.strip().endswith(":"):
                # Next few lines should contain name and description
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if "name : str =" in next_line:
                        agent_name = next_line.split("=")[1].strip().strip('"')
                        logger.info(f"Extracted agent name: {agent_name}")
                    elif "description : str =" in next_line:
                        agent_description = next_line.split("=")[1].strip().strip('"')
                        logger.info(f"Extracted agent description: {agent_description}")
                    elif next_line.startswith("#"):  # Skip comments
                        continue
                    elif next_line == "":  # Skip empty lines
                        continue
                    elif not next_line.startswith("    "):  # Stop at non-indented lines
                        break
                break

        # Analyze agent capabilities
        capabilities_data = await analyze_agent_capabilities(dana_code, messages)
        capabilities = AgentCapabilities(
            summary=capabilities_data.get("summary"),
            knowledge=capabilities_data.get("knowledge", []),
            workflow=capabilities_data.get("workflow", []),
            tools=capabilities_data.get("tools", []),
        )

        # Check if we need more information and include follow-up questions
        needs_more_info = conversation_analysis.get("needs_more_info", False)
        follow_up_message = conversation_analysis.get("follow_up_message") if needs_more_info else None
        suggested_questions = conversation_analysis.get("suggested_questions", []) if needs_more_info else None

        return AgentGeneratorNAResponse(
            success=True,
            dana_code=dana_code,
            agent_name=agent_name,
            agent_description=agent_description,
            capabilities=capabilities,
            needs_more_info=needs_more_info,
            follow_up_message=follow_up_message,
            suggested_questions=suggested_questions,
            error=None,
        )

    except Exception as e:
        logger.error(f"Error in generate_agent_na endpoint: {e}", exc_info=True)
        return AgentGeneratorNAResponse(
            success=False,
            dana_code="",
            agent_name=None,
            agent_description=None,
            capabilities=None,
            error=f"Failed to generate agent code: {str(e)}",
        )


@router.get("/health")
def health():
    """Health check endpoint for NA-based agent generator"""
    return {"status": "healthy", "service": "NA-based Agent Generator"}
