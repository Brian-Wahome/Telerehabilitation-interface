import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, UUID4
from src.backend.dependencies.services import get_session_service
from src.backend.service.sessions_service import SessionService


class SessionCreate(BaseModel):
    id: UUID4 | None = None
    patient_id: UUID4
    therapist_id: UUID4
    scheduled_time: datetime

    class Config:
        from_attributes = True


router = APIRouter(
    prefix="/sessions",
    tags=["sessions"]
)


@router.post("/", status_code=201)
def create_session(
        session_data: SessionCreate,
        session_service: SessionService = Depends(get_session_service)
):
    try:
        session_id = uuid.uuid4()
        session_data.id = session_id
        session_data = session_data.model_dump()
        session_service.create_session(session_data)
        return {"message": "Session successfully created."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
