from typing import Dict
import structlog
from src.backend.abstraction import ExerciseAbstraction


class ExerciseService:
    def __init__(self, exercise_abstraction: ExerciseAbstraction):
        self.exercise_abstraction = exercise_abstraction
        self.logger = structlog.get_logger(__name__)

    def create_exercise(self, exercise_data: Dict):
        self.logger.info(
            "Creating exercise",
            exercise_id=exercise_data.get('id'),
            name=exercise_data.get('name'),
            session_id=exercise_data.get('session_id')
        )
        return self.exercise_abstraction.create_exercise(exercise_data)

    def get_exercises_by_session(self, session_id: str):
        self.logger.info(
            "Successfully retrieved exercise sessions",
            session_id=session_id
        )
        return self.exercise_abstraction.get_exercises_by_session(session_id)

    def get_exercise_by_id(self, exercise_id: str):
        self.logger.info(
            "Successfully retrieved exercise_by_id",
            exercise_id=exercise_id
        )
        return self.exercise_abstraction.get_exercise_by_id(exercise_id)
