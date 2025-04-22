from datetime import datetime
from io import BytesIO
from typing import Optional, Dict
import pandas as pd
from sqlalchemy.orm import Session as db_session
from contextlib import contextmanager
from orm import User, Session, EMGData, Exercise, ExerciseSet, Sensors, SensorPositionEnum
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
        try:
            sensor_id = emg_data.get("sensor_id")

            # retrieve session
            if sensor_id:
                sensor = self.db.query(Sensors).filter(Sensors.id == sensor_id).first()
                if sensor:
                    session_id = sensor.session_id
                    # Check if there's an active exercise set for this session
                    if session_id in self.active_exercise_sets:
                        emg_data["exercise_set_id"] = self.active_exercise_sets[session_id]
            with self.transaction():
                emg_data = EMGData(**emg_data)
                self.db.add(emg_data)

        except Exception as e:
            self.logger.error(f"Error adding EMG data: {e}", exc_info=True)
            raise

    def set_active_exercise_set(self, session_id: str, exercise_set_id: str):
        """Set the active exercise set for a session"""
        self.active_exercise_sets[session_id] = exercise_set_id
        self.logger.info(f"Set active exercise set",
                         session_id=session_id,
                         exercise_set_id=exercise_set_id)
        return {"session_id": session_id, "active_exercise_set_id": exercise_set_id}

    def clear_active_exercise_set(self, session_id: str):
        """Clear the active exercise set for a session"""
        previous_set_id = None
        if session_id in self.active_exercise_sets:
            previous_set_id = self.active_exercise_sets[session_id]
            del self.active_exercise_sets[session_id]
            self.logger.info(f"Cleared active exercise set",
                             session_id=session_id,
                             previous_set_id=previous_set_id)

        return {"session_id": session_id, "previous_exercise_set_id": previous_set_id}


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

    def get_emg_data_for_set(self, set_id: str, sensor_position: Optional[str] = None) -> Dict:
        """
        Get EMG data for a specific exercise set

        Args:
            set_id: The ID of the exercise set
            sensor_position: Optional filter for specific sensor position

        Returns:
            Dictionary containing the set info and EMG data
        """
        # Get the exercise set
        exercise_set = self.get_set_by_id(set_id)
        if not exercise_set:
            return {"set_id": set_id, "data": []}

        # Build the query for EMG data
        query = self.db.query(EMGData).filter(EMGData.exercise_set_id == set_id)

        # Apply sensor position filter if specified
        if sensor_position:
            try:
                # convert string position to enum
                position_enum = SensorPositionEnum[sensor_position]
                query = query.filter(EMGData.sensor_position == position_enum)
            except (KeyError, ValueError):
                self.logger.warning(f"Invalid sensor position: {sensor_position}")

        # Get start and end times
        if exercise_set.start_time:
            query = query.filter(EMGData.time >= exercise_set.start_time)

        if exercise_set.end_time:
            query = query.filter(EMGData.time <= exercise_set.end_time)

        # Order by time
        query = query.order_by(EMGData.time)

        # Execute query
        emg_data = query.all()

        # Format the data for response
        formatted_data = []
        for data in emg_data:
            formatted_data.append({
                "time": data.time.isoformat(),
                "sensor_position": data.sensor_position.name,
                "value": data.value,
                "sensor_id": str(data.sensor_id)
            })

        # Get exercise information
        exercise = self.db.query(Exercise).filter(Exercise.id == exercise_set.exercise_id).first()

        return {
            "set_id": str(set_id),
            "exercise_id": str(exercise_set.exercise_id),
            "exercise_name": exercise.name if exercise else None,
            "set_number": exercise_set.set_number,
            "start_time": exercise_set.start_time.isoformat() if exercise_set.start_time else None,
            "end_time": exercise_set.end_time.isoformat() if exercise_set.end_time else None,
            "data": formatted_data
        }

    def download_emg_data_for_set(self, set_id: str, format: str = "csv") -> Dict:
        """
        Download EMG data for a specific exercise set in CSV or JSON format

        Args:
            set_id: The ID of the exercise set
            format: The format to download ('csv' or 'json')

        Returns:
            Dictionary with format and data
        """
        # Get the EMG data
        result = self.get_emg_data_for_set(set_id)
        data = result.get("data", [])

        if not data:
            return {"format": format, "data": []}

        if format.lower() == "csv":
            # Create a DataFrame and convert to CSV
            df = pd.DataFrame(data)
            output = BytesIO()
            df.to_csv(output, index=False)
            output.seek(0)

            return {
                "format": "csv",
                "data": output
            }

        elif format.lower() == "json":
            return {
                "format": "json",
                "data": data
            }

        else:
            raise ValueError(f"Unsupported format: {format}. Use 'csv' or 'json'.")
