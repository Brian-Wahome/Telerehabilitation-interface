from typing import Dict
import structlog
from src.backend.abstraction import SessionAbstraction


class SessionService:
    def __init__(self, session_abstraction: SessionAbstraction):
        self.session_abstraction = session_abstraction
        self.logger = structlog.get_logger(__name__)

    def create_session(self, session_data: Dict):
        self.logger.info(
            "Creating session",
            rehabilitation_session_id=session_data.get('id'),
            patient_id=session_data.get('patient_id'),
            therapist_id=session_data.get('therapist_id')
        )
        self.session_abstraction.create_session(session_data)
