from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import services, schemas, db
from ..schemas import RunNAFileRequest, RunNAFileResponse
from ..services import run_na_file_service

router = APIRouter(prefix="/agents", tags=["agents"])

def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


@router.get("/", response_model=list[schemas.AgentRead])
def list_agents(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return services.get_agents(db, skip=skip, limit=limit)


@router.get("/{agent_id}", response_model=schemas.AgentRead)
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = services.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/", response_model=schemas.AgentRead)
def create_agent(agent: schemas.AgentCreate, db: Session = Depends(get_db)):
    return services.create_agent(db, agent)


@router.post("/run-na-file", response_model=RunNAFileResponse)
def run_na_file(request: RunNAFileRequest):
    return run_na_file_service(request)
