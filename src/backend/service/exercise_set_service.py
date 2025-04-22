from typing import Dict, Optional
import structlog
from src.backend.abstraction import ExerciseSetAbstraction


class ExerciseSetService:
    def __init__(self, exercise_set_abstraction: ExerciseSetAbstraction):
        self.exercise_set_abstraction = exercise_set_abstraction
        self.logger = structlog.get_logger(__name__)

    def create_set(self, set_data: Dict):
        self.logger.info(
            "Creating exercise set",
            exercise_id=set_data.get('exercise_id'),
            repetitions=set_data.get('repetitions'),
            weight=set_data.get('weight')
        )
        return self.exercise_set_abstraction.create_set(set_data)

    def get_sets_by_exercise(self, exercise_id: str):
        self.logger.info(
            "Retrieving sets for exercise",
            exercise_id=exercise_id
        )
        return self.exercise_set_abstraction.get_sets_by_exercise(exercise_id)

    def get_set_by_id(self, set_id: str):
        self.logger.info(
            "Retrieving exercise set by ID",
            set_id=set_id
        )
        return self.exercise_set_abstraction.get_set_by_id(set_id)

    def start_set(self, set_id: str):
        self.logger.info(
            "Starting exercise set",
            set_id=set_id
        )
        return self.exercise_set_abstraction.start_set(set_id)

    def complete_set(self, set_id: str, notes: Optional[str] = None):
        self.logger.info(
            "Completing exercise set",
            set_id=set_id,
            notes=notes is not None
        )
        return self.exercise_set_abstraction.complete_set(set_id, notes)