from datetime import datetime

from sqlalchemy.orm import Session as db_session
from contextlib import contextmanager
from orm import User, Session, EMGData, Exercise, ExerciseSet
from uuid import uuid4
import structlog


class BaseAbstraction:
    def __init__(self, db: db_session):
        self.db = db
        self.session_id = str(uuid4())
        self.logger = structlog.stdlib.get_logger(__name__).bind(
            session_id=self.session_id,
            layer="repository",
        )

    @contextmanager
    def transaction(self):
        try:
            yield
            self.db.commit()
            self.logger.debug("Database commit is successful")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error {e} raised when committing")
            raise


class UserAbstraction(BaseAbstraction):
    def create_user(self, user: dict) -> User:
        with self.transaction():
            user = User(**user)
            self.db.add(user)


class SessionAbstraction(BaseAbstraction):
    def create_session(self, session: dict) -> Session:
        with self.transaction():
            session = Session(**session)
            self.db.add(session)


class MQTTAbstraction(BaseAbstraction):
    def add_emg_data(self, emg_data: dict):
        with self.transaction():
            emg_data = EMGData(**emg_data)
            self.db.add(emg_data)


class ExerciseAbstraction(BaseAbstraction):
    def create_exercise(self, exercise_data: dict) -> Exercise:
        with self.transaction():
            exercise = Exercise(**exercise_data)
            self.db.add(exercise)
            return exercise

    def get_exercises_by_session(self, session_id: str) -> list:
        return self.db.query(Exercise).filter(Exercise.session_id == session_id).all()

    def get_exercise_by_id(self, exercise_id: str) -> Exercise | None:
        return self.db.query(Exercise).filter(Exercise.id == exercise_id).first()


class ExerciseSetAbstraction(BaseAbstraction):
    def create_set(self, set_data: dict) -> ExerciseSet:
        with self.transaction():
            # Get the next set number for this exercise
            last_set = self.db.query(ExerciseSet).filter(
                ExerciseSet.exercise_id == set_data['exercise_id']
            ).order_by(ExerciseSet.set_number.desc()).first()

            next_set_number = 1
            if last_set:
                next_set_number = last_set.set_number + 1

            set_data['set_number'] = next_set_number
            exercise_set = ExerciseSet(**set_data)
            self.db.add(exercise_set)
            return exercise_set

    def get_sets_by_exercise(self, exercise_id: str) -> list:
        return self.db.query(ExerciseSet).filter(
            ExerciseSet.exercise_id == exercise_id
        ).order_by(ExerciseSet.set_number).all()

    def get_set_by_id(self, set_id: str) -> ExerciseSet:
        return self.db.query(ExerciseSet).filter(ExerciseSet.id == set_id).first()

    def start_set(self, set_id: str) -> ExerciseSet:
        with self.transaction():
            exercise_set = self.get_set_by_id(set_id)
            if exercise_set:
                exercise_set.start_time = datetime.now()
            return exercise_set

    def complete_set(self, set_id: str, notes: str = None) -> ExerciseSet:
        with self.transaction():
            exercise_set = self.get_set_by_id(set_id)
            if exercise_set:
                exercise_set.end_time = datetime.now()
                exercise_set.completed = True
                if notes:
                    exercise_set.notes = notes
            return exercise_set
