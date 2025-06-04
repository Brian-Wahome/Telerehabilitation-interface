from typing import Dict, List, Optional
import structlog
from src.backend.abstraction import ExerciseAbstraction


class ExerciseService:
    def __init__(self, exercise_abstraction: ExerciseAbstraction):
        self.exercise_abstraction = exercise_abstraction
        self.logger = structlog.get_logger(__name__)

    def create_exercise(self, exercise_data: Dict) -> Dict:
        """
        Function to create an exercise for a session
        :param exercise_data:
        :return:
        """
        self.logger.info(
            "Creating exercise",
            exercise_id=exercise_data.get('id'),
            name=exercise_data.get('name'),
            session_id=exercise_data.get('session_id')
        )
        exercise_orm = self.exercise_abstraction.create_exercise(exercise_data)

        # Convert ORM object to dictionary
        return {
            "id": str(exercise_orm.id),
            "session_id": str(exercise_orm.session_id),
            "name": exercise_orm.name,
            "description": exercise_orm.description,
            "notes": exercise_orm.notes,
            "created_at": exercise_orm.created_at.isoformat() if exercise_orm.created_at else None
        }

    def get_exercises_by_session(self, session_id: str) -> List[Dict]:
        """
        Function to retrieve exercises in a session
        :param session_id:
        :return:
        """
        self.logger.info(
            "Retrieving exercises for session",
            session_id=session_id
        )
        exercises_orm = self.exercise_abstraction.get_exercises_by_session(session_id)

        # Convert list of ORM objects to list of dictionaries
        return [
            {
                "id": str(exercise.id),
                "session_id": str(exercise.session_id),
                "name": exercise.name,
                "description": exercise.description,
                "notes": exercise.notes,
                "created_at": exercise.created_at.isoformat() if exercise.created_at else None
            }
            for exercise in exercises_orm
        ]

    def get_exercise_by_id(self, exercise_id: str) -> Optional[Dict]:
        """
        Function to retrieve an exercise by its id
        :param exercise_id:
        :return:
        """
        self.logger.info(
            "Retrieving exercise by ID",
            exercise_id=exercise_id
        )
        exercise_orm = self.exercise_abstraction.get_exercise_by_id(exercise_id)

        if not exercise_orm:
            return None

        # Convert ORM object to dictionary
        return {
            "id": str(exercise_orm.id),
            "session_id": str(exercise_orm.session_id),
            "name": exercise_orm.name,
            "description": exercise_orm.description,
            "notes": exercise_orm.notes,
            "created_at": exercise_orm.created_at.isoformat() if exercise_orm.created_at else None
        }
