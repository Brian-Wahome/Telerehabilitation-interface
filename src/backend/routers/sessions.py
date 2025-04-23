import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, UUID4
from src.backend.dependencies.services import get_session_service
from src.backend.service.sessions_service import SessionService
from ..exceptions import UserDoesNotExist, SessionDoesNotExist


class SessionCreate(BaseModel):
    id: UUID4 | None = None
    patient_id: UUID4
    therapist_id: UUID4
    scheduled_time: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: UUID4
    patient_id: UUID4
    therapist_id: UUID4
    scheduled_time: str
    completed: Optional[str] = None
    notes: Optional[str] = None
    duration: Optional[int] = None


class SessionJoinRequest(BaseModel):
    user_id: UUID4


class ParticipantInfo(BaseModel):
    user_id: str
    session_id: str
    name: str
    role: str
    joined_at: str
    is_patient: bool
    is_therapist: bool


class SessionParticipantsResponse(BaseModel):
    session_id: UUID4
    participants: List[ParticipantInfo]


router = APIRouter(
    prefix="/sessions",
    tags=["sessions"]
)


@router.post("/", status_code=201)
def schedule_session(
        session_data: SessionCreate,
        session_service: SessionService = Depends(get_session_service)
):
    try:
        session_id = uuid.uuid4()
        session_data.id = session_id
        session_data = session_data.model_dump()
        session = session_service.create_session(session_data)
        return session
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
        session_id: UUID4,
        session_service: SessionService = Depends(get_session_service)
):
    """Get a session by its ID"""
    try:
        session = session_service.get_session_by_id(str(session_id))
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patient/{patient_id}", response_model=List[SessionResponse])
def get_patient_sessions(
        patient_id: UUID4,
        session_service: SessionService = Depends(get_session_service)
):
    """Get all sessions for a specific patient"""
    try:
        sessions = session_service.get_sessions_by_patient(str(patient_id))
        return sessions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/therapist/{therapist_id}", response_model=List[SessionResponse])
def get_therapist_sessions(
        therapist_id: UUID4,
        session_service: SessionService = Depends(get_session_service)
):
    """Get all sessions for a specific therapist"""
    try:
        sessions = session_service.get_sessions_by_therapist(str(therapist_id))
        return sessions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/join", response_model=ParticipantInfo)
def join_session(
        session_id: UUID4,
        join_request: SessionJoinRequest,
        session_service: SessionService = Depends(get_session_service)
):
    """Join a therapy session"""
    try:
        participant_info = session_service.join_session(
            session_id=str(session_id),
            user_id=str(join_request.user_id)
        )
        return participant_info
    except (ValueError, UserDoesNotExist, SessionDoesNotExist) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/leave")
def leave_session(
        session_id: UUID4,
        join_request: SessionJoinRequest,
        session_service: SessionService = Depends(get_session_service)
):
    """Leave a therapy session"""
    try:
        leave_info = session_service.leave_session(
            session_id=str(session_id),
            user_id=str(join_request.user_id)
        )
        return leave_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}/participants", response_model=SessionParticipantsResponse)
def get_session_participants(
        session_id: UUID4,
        session_service: SessionService = Depends(get_session_service)
):
    """Get all active participants in a session"""
    try:
        participants = session_service.get_session_participants(str(session_id))
        return {
            "session_id": session_id,
            "participants": participants
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
