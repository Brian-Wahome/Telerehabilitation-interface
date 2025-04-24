from typing import Dict, Optional, List
import structlog
from datetime import datetime
from src.backend.abstraction import SessionAbstraction


class SessionService:
    def __init__(self, session_abstraction: SessionAbstraction):
        self.session_abstraction = session_abstraction
        self.logger = structlog.get_logger(__name__)

    def create_session(self, session_data: Dict):
        """
        Function schedule a session with therapist.
        :param session_data:
        :return:
        """
        self.logger.info(
            "Creating session",
            rehabilitation_session_id=session_data.get('id'),
            patient_id=session_data.get('patient_id'),
            therapist_id=session_data.get('therapist_id')
        )
        session_orm = self.session_abstraction.create_session(session_data)
        return {
            "id": str(session_orm.id),
            "patient_id": str(session_orm.patient_id),
            "therapist_id": str(session_orm.therapist_id),
            "scheduled_time": session_orm.scheduled_time.isoformat() if session_orm.scheduled_time else None,
            "completed": session_orm.completed.isoformat() if session_orm.completed else None,
            "notes": session_orm.notes,
            "duration": session_orm.duration
        }

    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """Get a session by its ID"""
        self.logger.info(
            "Getting session by ID",
            session_id=session_id
        )

        session_orm = self.session_abstraction.get_session_by_id(session_id)

        if not session_orm:
            return None

        # Convert to dictionary
        return {
            "id": str(session_orm.id),
            "patient_id": str(session_orm.patient_id),
            "therapist_id": str(session_orm.therapist_id),
            "scheduled_time": session_orm.scheduled_time.isoformat() if session_orm.scheduled_time else None,
            "completed": session_orm.completed.isoformat() if session_orm.completed else None,
            "notes": session_orm.notes,
            "duration": session_orm.duration
        }

    def get_sessions_by_patient(self, patient_id: str) -> List[Dict]:
        """Get all sessions for a specific patient"""
        self.logger.info(
            "Getting sessions for patient",
            patient_id=patient_id
        )

        sessions_orm = self.session_abstraction.get_sessions_by_patient(patient_id)

        # Convert to list of dictionaries
        return [
            {
                "id": str(session.id),
                "patient_id": str(session.patient_id),
                "therapist_id": str(session.therapist_id),
                "scheduled_time": session.scheduled_time.isoformat() if session.scheduled_time else None,
                "completed": session.completed.isoformat() if session.completed else None,
                "notes": session.notes,
                "duration": session.duration
            }
            for session in sessions_orm
        ]

    def get_sessions_by_therapist(self, therapist_id: str) -> List[Dict]:
        """Get all sessions for a specific therapist"""
        self.logger.info(
            "Getting sessions for therapist",
            therapist_id=therapist_id
        )

        sessions_orm = self.session_abstraction.get_sessions_by_therapist(therapist_id)

        # Convert to list of dictionaries
        return [
            {
                "id": str(session.id),
                "patient_id": str(session.patient_id),
                "therapist_id": str(session.therapist_id),
                "scheduled_time": session.scheduled_time.isoformat() if session.scheduled_time else None,
                "completed": session.completed.isoformat() if session.completed else None,
                "notes": session.notes,
                "duration": session.duration
            }
            for session in sessions_orm
        ]

    def get_all_sessions(self) -> List[Dict]:
        """Get all sessions (for admins)"""
        self.logger.info("Getting all sessions")

        sessions_orm = self.session_abstraction.get_all_sessions()

        # Convert to list of dictionaries
        return [
            {
                "id": str(session.id),
                "patient_id": str(session.patient_id),
                "therapist_id": str(session.therapist_id),
                "scheduled_time": session.scheduled_time.isoformat() if session.scheduled_time else None,
                "completed": session.completed.isoformat() if session.completed else None,
                "notes": session.notes,
                "duration": session.duration
            }
            for session in sessions_orm
        ]

    def complete_session(self, session_id: str, notes: Optional[str] = None) -> Dict:
        """
        Mark a session as completed with current datetime

        Args:
            session_id: The ID of the session to complete
            notes: Optional notes to add to the session

        Returns:
            Updated session data
        """
        self.logger.info(
            "Completing session",
            session_id=session_id
        )

        # Complete the session with current datetime
        completed_session = self.session_abstraction.complete_session(
            session_id=session_id,
            completed_time=datetime.now(),
            notes=notes
        )

        # Convert to dictionary
        return {
            "id": str(completed_session.id),
            "patient_id": str(completed_session.patient_id),
            "therapist_id": str(completed_session.therapist_id),
            "scheduled_time": completed_session.scheduled_time.isoformat() if completed_session.scheduled_time else None,
            "completed": completed_session.completed.isoformat() if completed_session.completed else None,
            "notes": completed_session.notes,
            "duration": completed_session.duration
        }

    def join_session(self, session_id: str, user_id: str) -> Dict:
        """Allow a user to join a session"""
        self.logger.info(
            "User joining session",
            user_id=user_id,
            session_id=session_id
        )

        try:
            participant_info = self.session_abstraction.join_session(session_id, user_id)
            return participant_info
        except ValueError as e:
            self.logger.error(
                "Failed to join session",
                error=str(e),
                user_id=user_id,
                session_id=session_id
            )
            raise

    def leave_session(self, session_id: str, user_id: str) -> Dict:
        """Allow a user to leave a session"""
        self.logger.info(
            "User leaving session",
            user_id=user_id,
            session_id=session_id
        )

        try:
            leave_info = self.session_abstraction.leave_session(session_id, user_id)
            return leave_info
        except ValueError as e:
            self.logger.error(
                "Failed to leave session",
                error=str(e),
                user_id=user_id,
                session_id=session_id
            )
            raise

    def get_session_participants(self, session_id: str) -> List[Dict]:
        """Get all active participants in a session"""
        self.logger.info(
            "Getting session participants",
            session_id=session_id
        )

        participants = self.session_abstraction.get_session_participants(session_id)
        return participants
