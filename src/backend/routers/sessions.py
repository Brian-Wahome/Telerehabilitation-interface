import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, UUID4
from src.backend.dependencies.services import get_session_service, get_current_user
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


@router.post("/", status_code=201, response_model=SessionResponse)
def schedule_session(
        session_data: SessionCreate,
        session_service: SessionService = Depends(get_session_service),
        current_user: dict = Depends(get_current_user)  # Protected route
):
    """
    Schedule a new therapy session (only therapists and admins can do this)
    """
    try:
        user_role = current_user["role"]
        user_id = current_user["id"]

        # Only therapists and admins can schedule sessions
        if user_role not in ["therapist", "admin"]:
            raise HTTPException(status_code=403, detail="Only therapists and admins can schedule sessions")

        # If the user is a therapist, they can only schedule sessions where they are the therapist
        if user_role == "therapist" and str(session_data.therapist_id) != user_id:
            raise HTTPException(status_code=403, detail="Therapists can only schedule sessions for themselves")

        # Create the session
        session_id = session_data.id or UUID4()
        session_data_dict = session_data.model_dump()
        session_data_dict["id"] = str(session_id)

        session = session_service.create_session(session_data_dict)
        return session

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
        session_id: UUID4,
        session_service: SessionService = Depends(get_session_service),
        current_user: dict = Depends(get_current_user)  # Protected route
):
    """
    Get a specific session if the user has access to it
    """
    try:
        session = session_service.get_session_by_id(str(session_id))
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        user_id = current_user["id"]
        user_role = current_user["role"]

        # Check if user has access to this session
        is_authorised = (
                user_role == "admin" or
                (user_role == "therapist" and session["therapist_id"] == user_id) or
                (user_role == "patient" and session["patient_id"] == user_id)
        )

        if not is_authorised:
            raise HTTPException(status_code=403, detail="Not authorised to access this session")

        return session

    except HTTPException as he:
        raise he
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


@router.get("/", response_model=List[SessionResponse])
def get_all_sessions(
        session_service: SessionService = Depends(get_session_service),
        current_user: dict = Depends(get_current_user)  # Protected route
):
    """
    Get all sessions the user has access to based on their role
    """
    try:
        user_id = current_user["id"]
        user_role = current_user["role"]

        # Admins can see all sessions
        if user_role == "admin":
            # Implement get_all_sessions in session_service
            return session_service.get_all_sessions()

        # Therapists see their own sessions
        elif user_role == "therapist":
            return session_service.get_sessions_by_therapist(user_id)

        # Patients see their own sessions
        elif user_role == "patient":
            return session_service.get_sessions_by_patient(user_id)

        else:
            raise HTTPException(status_code=403, detail="Unauthorized role")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/complete")
def complete_session(
        session_id: UUID4,
        session_service: SessionService = Depends(get_session_service),
        current_user: dict = Depends(get_current_user)  # Protected route
):
    """
    Mark a session as completed (only the therapist or admin can do this)
    """
    try:
        # Get the session
        session = session_service.get_session_by_id(str(session_id))
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        user_id = current_user["id"]
        user_role = current_user["role"]

        # Only the assigned therapist or an admin can complete a session
        is_authorised = (
                user_role == "admin" or
                (user_role == "therapist" and session["therapist_id"] == user_id)
        )

        if not is_authorised:
            raise HTTPException(status_code=403, detail="Not authosized to complete this session")

        # Mark session as completed
        completed_session = session_service.complete_session(str(session_id))
        return completed_session

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
