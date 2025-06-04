from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional, Dict, List
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session as db_session
from contextlib import contextmanager
from orm import User, Session, EMGData, Exercise, ExerciseSet, Sensors, SensorPositionEnum, UserRoleEnum
from uuid import uuid4
import structlog
from exceptions import UserDoesNotExist, SessionDoesNotExist

active_participants: Dict[str, List[Dict]] = {}


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

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get a user by their ID"""
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return None

        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.name,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }


    def get_users(self, role: Optional[UserRoleEnum] = None) -> List[Dict]:
        """Get all users with optional role filtering"""
        # Start with a base query
        query = self.db.query(User)

        # Apply role filter if specified
        if role is not None:
            query = query.filter(User.role == role)

        # Execute query and convert to list of dictionaries
        users = query.all()

        return [
            {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.name,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ]


class SessionAbstraction(BaseAbstraction):

    def create_session(self, session: dict) -> Session:
        """"
        Create a session
        """
        with self.transaction():
            session = Session(**session)
            self.db.add(session)
            self.db.flush()
            return session

    # In abstraction.py, modify the get_session_by_id method

    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """Get a session by its ID with user information"""
        session = self.db.query(Session).filter(Session.id == session_id).first()

        if not session:
            return None

        # Get patient and therapist info
        patient = self.db.query(User).filter(User.id == session.patient_id).first()
        therapist = self.db.query(User).filter(User.id == session.therapist_id).first()

        # Create response with user details
        return {
            "id": str(session.id),
            "patient_id": str(session.patient_id),
            "therapist_id": str(session.therapist_id),
            "patient": {
                "id": str(patient.id),
                "name": f"{patient.first_name} {patient.last_name}",
                "email": patient.email
            } if patient else None,
            "therapist": {
                "id": str(therapist.id),
                "name": f"{therapist.first_name} {therapist.last_name}",
                "email": therapist.email
            } if therapist else None,
            "scheduled_time": session.scheduled_time.isoformat() if session.scheduled_time else None,
            "completed": session.completed.isoformat() if session.completed else None,
            "notes": session.notes,
            "duration": session.duration
        }

    def get_sessions_by_patient(self, patient_id: str) -> List[Dict]:
        """Get all sessions for a specific patient with user info"""
        sessions = self.db.query(Session).filter(Session.patient_id == patient_id).all()

        result = []
        for session in sessions:
            therapist = self.db.query(User).filter(User.id == session.therapist_id).first()
            patient = self.db.query(User).filter(User.id == session.patient_id).first()

            result.append({
                "id": str(session.id),
                "patient_id": str(session.patient_id),
                "therapist_id": str(session.therapist_id),
                "patient": {
                    "id": str(patient.id),
                    "name": f"{patient.first_name} {patient.last_name}",
                    "email": patient.email
                } if patient else None,
                "therapist": {
                    "id": str(therapist.id),
                    "name": f"{therapist.first_name} {therapist.last_name}",
                    "email": therapist.email
                } if therapist else None,
                "scheduled_time": session.scheduled_time.isoformat() if session.scheduled_time else None,
                "completed": session.completed.isoformat() if session.completed else None,
                "notes": session.notes,
                "duration": session.duration
            })

        return result

    def get_sessions_by_therapist(self, therapist_id: str) -> List[Dict]:
        """Get all sessions for a specific therapist with user info"""
        sessions = self.db.query(Session).filter(Session.therapist_id == therapist_id).all()

        result = []
        for session in sessions:
            therapist = self.db.query(User).filter(User.id == session.therapist_id).first()
            patient = self.db.query(User).filter(User.id == session.patient_id).first()

            result.append({
                "id": str(session.id),
                "patient_id": str(session.patient_id),
                "therapist_id": str(session.therapist_id),
                "patient": {
                    "id": str(patient.id),
                    "name": f"{patient.first_name} {patient.last_name}",
                    "email": patient.email
                } if patient else None,
                "therapist": {
                    "id": str(therapist.id),
                    "name": f"{therapist.first_name} {therapist.last_name}",
                    "email": therapist.email
                } if therapist else None,
                "scheduled_time": session.scheduled_time.isoformat() if session.scheduled_time else None,
                "completed": session.completed.isoformat() if session.completed else None,
                "notes": session.notes,
                "duration": session.duration
            })

        return result

    def join_session(self, session_id: str, user_id: str) -> Dict:
        """
        Allow a user to join a session

        Args:
            session_id: The ID of the session to join
            user_id: The ID of the user joining the session

        Returns:
            Dictionary with session and user information
        """
        # Verify session exists
        session = self.get_session_by_id(session_id)
        if not session:
            self.logger.error(
                "Failed to retrieve non-existent session",
                session_id=session_id
            )
            raise SessionDoesNotExist(f"Session with ID {session_id} not found")

        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            self.logger.error(
                "User not found",
                user_id=user_id
            )
            raise UserDoesNotExist(f"User with ID {user_id} not found")

        # Verify user has permission to join the session
        # Only the assigned therapist, patient, or admin can join
        is_authorized = (
                str(session.patient_id) == user_id or
                str(session.therapist_id) == user_id or
                user.role == UserRoleEnum.admin
        )

        if not is_authorized:
            raise ValueError("User is not authorized to join this session")

        # Initialize the participants list for this session if it doesn't exist
        if session_id not in active_participants:
            active_participants[session_id] = []

        # Check if user is already in the session
        for participant in active_participants[session_id]:
            if participant["user_id"] == user_id:
                # User is already in the session, update their connection time
                participant["joined_at"] = datetime.now()
                self.logger.info(
                    "User reconnected to session",
                    user_id=user_id,
                    session_id=session_id
                )
                return participant

        # Add user to active participants
        participant_info = {
            "user_id": user_id,
            "session_id": session_id,
            "name": f"{user.first_name} {user.last_name}",
            "role": user.role.name,
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_patient": str(session.patient_id) == user_id,
            "is_therapist": str(session.therapist_id) == user_id
        }
        active_participants[session_id].append(participant_info)

        self.logger.info(
            "User joined session",
            user_id=user_id,
            session_id=session_id,
            role=user.role.name
        )

        return participant_info

    def leave_session(self, session_id: str, user_id: str) -> Dict:
        """
        Allow a user to leave a session

        Args:
            session_id: The ID of the session to leave
            user_id: The ID of the user leaving the session

        Returns:
            Dictionary with session and user information
        """
        # Verify session has active participants
        if session_id not in active_participants:
            raise ValueError(f"No active participants in session {session_id}")

        # Find and remove user from participants
        for i, participant in enumerate(active_participants[session_id]):
            if participant["user_id"] == user_id:
                # Remove user from the session
                removed_participant = active_participants[session_id].pop(i)

                # If no participants left, remove the session from the active sessions
                if not active_participants[session_id]:
                    del active_participants[session_id]

                self.logger.info(
                    "User left session",
                    user_id=user_id,
                    session_id=session_id
                )

                return {
                    "user_id": user_id,
                    "session_id": session_id,
                    "left_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "duration": str((datetime.now() - datetime.strptime(removed_participant["joined_at"], "%Y-%m-%d %H:%M:%S")).total_seconds())
                }

        # User was not in the session
        raise ValueError(f"User {user_id} is not an active participant in session {session_id}")

    def get_session_participants(self, session_id: str) -> List[Dict]:
        """
        Get all active participants in a session

        Args:
            session_id: The ID of the session

        Returns:
            List of participant information dictionaries
        """
        if session_id not in active_participants:
            return []

        return active_participants[session_id]

    def complete_session(self, session_id: str, completed_time: datetime, notes: Optional[str] = None) -> Session:
        """
        Mark a session as completed with the provided datetime

        Args:
            session_id: The ID of the session to complete
            completed_time: The datetime when the session was completed
            notes: Optional notes to add to the session

        Returns:
            Updated session model
        """
        with self.transaction():
            session = self.get_session_by_id(session_id)
            if not session:
                raise ValueError(f"Session with ID {session_id} not found")

            # Set the completed datetime
            session.completed = completed_time

            # Update notes if provided
            if notes is not None:
                session.notes = notes

            # Calculate duration in minutes if we have both start and end times
            if session.scheduled_time and session.completed:
                duration_delta = session.completed - session.scheduled_time
                session.duration = int(duration_delta.total_seconds() / 60)

            return session


active_exercise_sets = {}
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
                    if session_id in active_exercise_sets:
                        emg_data["exercise_set_id"] = active_exercise_sets[session_id]
            with self.transaction():
                emg_data = EMGData(**emg_data)
                self.db.add(emg_data)

        except Exception as e:
            self.logger.error(f"Error adding EMG data: {e}", exc_info=True)
            raise

    def set_active_exercise_set(self, session_id: str, exercise_set_id: str):
        """Set the active exercise set for a session"""
        active_exercise_sets[session_id] = exercise_set_id
        self.logger.info(f"Set active exercise set",
                         session_id=session_id,
                         exercise_set_id=exercise_set_id)
        return {"session_id": session_id, "active_exercise_set_id": exercise_set_id}

    def clear_active_exercise_set(self, session_id: str):
        """Clear the active exercise set for a session"""
        previous_set_id = None
        if session_id in active_exercise_sets:
            previous_set_id = active_exercise_sets[session_id]
            del active_exercise_sets[session_id]
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


class EMGDataAbstraction(BaseAbstraction):
    def get_emg_data_for_session(
            self,
            session_id: str,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            sensor_position: Optional[str] = None,
            include_exercise_info: bool = True
    ) -> Dict:
        """
        Get all EMG data for a specific therapy session

        Args:
            session_id: The ID of the therapy session
            start_time: Optional start time filter
            end_time: Optional end time filter
            sensor_position: Optional filter for specific sensor position
            include_exercise_info: Whether to include exercise and set information

        Returns:
            Dictionary containing the session info and EMG data
        """
        # Get the session
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session:
            return {"session_id": session_id, "data": []}

        # Get all sensors for this session
        sensors = self.db.query(Sensors).filter(Sensors.session_id == session_id).all()
        if not sensors:
            return {"session_id": session_id, "data": []}

        sensor_ids = [sensor.id for sensor in sensors]

        # Build the query for EMG data
        query = self.db.query(EMGData).filter(EMGData.sensor_id.in_(sensor_ids))

        # Apply filters
        if start_time:
            query = query.filter(EMGData.time >= start_time)
        elif session.scheduled_time:
            query = query.filter(EMGData.time >= session.scheduled_time)

        if end_time:
            query = query.filter(EMGData.time <= end_time)
        elif session.completed:
            query = query.filter(EMGData.time <= session.completed)

        if sensor_position:
            try:
                # Try to convert string position to enum
                position_enum = SensorPositionEnum[sensor_position]
                query = query.filter(EMGData.sensor_position == position_enum)
            except (KeyError, ValueError):
                self.logger.warning(f"Invalid sensor position: {sensor_position}")

        # Order by time
        query = query.order_by(EMGData.time)

        # Execute query
        emg_data = query.all()

        # Format the data for response
        formatted_data = []
        for data in emg_data:
            emg_record = {
                "time": data.time.isoformat(),
                "sensor_position": data.sensor_position.name,
                "value": data.value,
                "sensor_id": str(data.sensor_id)
            }

            # Add exercise set info if available and requested
            if include_exercise_info and data.exercise_set_id:
                exercise_set = self.db.query(ExerciseSet).filter(ExerciseSet.id == data.exercise_set_id).first()
                if exercise_set:
                    emg_record["exercise_set_id"] = str(data.exercise_set_id)
                    emg_record["set_number"] = exercise_set.set_number

                    exercise = self.db.query(Exercise).filter(Exercise.id == exercise_set.exercise_id).first()
                    if exercise:
                        emg_record["exercise_id"] = str(exercise_set.exercise_id)
                        emg_record["exercise_name"] = exercise.name

            formatted_data.append(emg_record)

        # Get patient and therapist info
        patient = self.db.query(User).filter(User.id == session.patient_id).first()
        therapist = self.db.query(User).filter(User.id == session.therapist_id).first()

        # Calculate statistics
        stats = self._calculate_emg_statistics(formatted_data)

        return {
            "session_id": str(session_id),
            "patient": {
                "id": str(session.patient_id),
                "name": f"{patient.first_name} {patient.last_name}" if patient else "Unknown"
            },
            "therapist": {
                "id": str(session.therapist_id),
                "name": f"{therapist.first_name} {therapist.last_name}" if therapist else "Unknown"
            },
            "scheduled_time": session.scheduled_time.isoformat() if session.scheduled_time else None,
            "completed": session.completed.isoformat() if session.completed else None,
            "statistics": stats,
            "data_points_count": len(formatted_data),
            "data": formatted_data
        }

    def get_emg_data_for_multiple_sessions(
            self,
            session_ids: List[str],
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            sensor_position: Optional[str] = None,
            include_exercise_info: bool = True
    ) -> Dict:
        """
        Get EMG data for multiple sessions, useful for comparing progress over time

        Args:
            session_ids: List of session IDs to include
            start_time: Optional start time filter
            end_time: Optional end time filter
            sensor_position: Optional filter for specific sensor position
            include_exercise_info: Whether to include exercise and set information

        Returns:
            Dictionary containing the sessions info and EMG data
        """
        # Validate the session IDs
        valid_sessions = self.db.query(Session).filter(
            Session.id.in_(session_ids)
        ).all()

        if not valid_sessions:
            return {"session_ids": session_ids, "sessions": [], "data": []}

        valid_session_ids = [str(session.id) for session in valid_sessions]

        # Process each session
        sessions_data = []
        all_emg_data = []

        for session_id in valid_session_ids:
            session_result = self.get_emg_data_for_session(
                session_id=session_id,
                start_time=start_time,
                end_time=end_time,
                sensor_position=sensor_position,
                include_exercise_info=include_exercise_info
            )

            # Add session summary to the list
            session_summary = {
                "session_id": session_id,
                "patient": session_result.get("patient"),
                "scheduled_time": session_result.get("scheduled_time"),
                "completed": session_result.get("completed"),
                "data_points_count": session_result.get("data_points_count", 0),
                "statistics": session_result.get("statistics", {})
            }
            sessions_data.append(session_summary)

            # Add EMG data to the combined list
            for data_point in session_result.get("data", []):
                # Add session ID to each data point for reference
                data_point["session_id"] = session_id
                all_emg_data.append(data_point)

        # Sort all data by time
        all_emg_data.sort(key=lambda x: x.get("time"))

        # Generate overall statistics
        overall_stats = self._calculate_emg_statistics(all_emg_data)

        return {
            "session_ids": valid_session_ids,
            "sessions": sessions_data,
            "overall_statistics": overall_stats,
            "data_points_count": len(all_emg_data),
            "data": all_emg_data
        }

    def get_patient_progress(
            self,
            patient_id: str,
            time_range: Optional[int] = 30,  # Default to last 30 days
            exercise_name: Optional[str] = None,
            sensor_position: Optional[str] = None
    ) -> Dict:
        """
        Get a patient's progress over time, suitable for trend analysis

        Args:
            patient_id: The ID of the patient
            time_range: Number of days to look back (default: 30)
            exercise_name: Optional filter for specific exercise
            sensor_position: Optional filter for specific sensor position

        Returns:
            Dictionary containing progress data and trends
        """
        # Calculate the start date
        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_range)

        # Get all sessions for this patient in the time range
        sessions = self.db.query(Session).filter(
            Session.patient_id == patient_id,
            Session.scheduled_time >= start_date,
            Session.scheduled_time <= end_date
        ).order_by(Session.scheduled_time).all()

        if not sessions:
            return {"patient_id": patient_id, "sessions": [], "progress_data": []}

        session_ids = [str(session.id) for session in sessions]

        # Get all exercises for these sessions if exercise_name filter is applied
        exercise_filter = None
        if exercise_name:
            exercises = self.db.query(Exercise).filter(
                Exercise.session_id.in_(session_ids),
                Exercise.name.ilike(f"%{exercise_name}%")
            ).all()

            if exercises:
                exercise_ids = [str(exercise.id) for exercise in exercises]

                # Get all sets for these exercises
                exercise_sets = self.db.query(ExerciseSet).filter(
                    ExerciseSet.exercise_id.in_(exercise_ids)
                ).all()

                if exercise_sets:
                    exercise_set_ids = [str(exercise_set.id) for exercise_set in exercise_sets]
                    exercise_filter = exercise_set_ids

        # Process each session to collect data
        progress_data = []
        session_summaries = []

        for session in sessions:
            session_id = str(session.id)

            # Build the EMG data query
            sensors = self.db.query(Sensors).filter(Sensors.session_id == session_id).all()
            if not sensors:
                continue

            sensor_ids = [sensor.id for sensor in sensors]
            query = self.db.query(EMGData).filter(EMGData.sensor_id.in_(sensor_ids))

            # Apply sensor position filter
            if sensor_position:
                try:
                    position_enum = SensorPositionEnum[sensor_position]
                    query = query.filter(EMGData.sensor_position == position_enum)
                except (KeyError, ValueError):
                    self.logger.warning(f"Invalid sensor position: {sensor_position}")

            # Apply exercise filter if available
            if exercise_filter:
                query = query.filter(EMGData.exercise_set_id.in_(exercise_filter))

            # Get session time boundaries
            if session.scheduled_time:
                query = query.filter(EMGData.time >= session.scheduled_time)

            if session.completed:
                query = query.filter(EMGData.time <= session.completed)

            # Get aggregated statistics
            max_value = query.with_entities(func.max(EMGData.value)).scalar() or 0
            avg_value = query.with_entities(func.avg(EMGData.value)).scalar() or 0
            count = query.count()

            # Add to progress data
            session_date = session.scheduled_time.date().isoformat() if session.scheduled_time else "Unknown"
            progress_point = {
                "date": session_date,
                "session_id": session_id,
                "max_value": max_value,
                "avg_value": avg_value,
                "data_points": count
            }
            progress_data.append(progress_point)

            # Add session summary
            therapist = self.db.query(User).filter(User.id == session.therapist_id).first()
            session_summary = {
                "session_id": session_id,
                "date": session_date,
                "therapist": {
                    "id": str(session.therapist_id),
                    "name": f"{therapist.first_name} {therapist.last_name}" if therapist else "Unknown"
                },
                "completed": session.completed is not None,
                "emg_stats": {
                    "max_value": max_value,
                    "avg_value": avg_value,
                    "data_points": count
                }
            }
            session_summaries.append(session_summary)

        # Calculate trends
        trends = self._calculate_progress_trends(progress_data)

        # Get patient info
        patient = self.db.query(User).filter(User.id == patient_id).first()
        patient_name = f"{patient.first_name} {patient.last_name}" if patient else "Unknown"

        return {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "sessions_count": len(sessions),
            "date_range": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat()
            },
            "filter": {
                "exercise_name": exercise_name,
                "sensor_position": sensor_position
            },
            "trends": trends,
            "sessions": session_summaries,
            "progress_data": progress_data
        }

    def download_emg_data_for_session(
            self,
            session_id: str,
            format: str = "csv",
            include_exercise_info: bool = True
    ) -> Dict:
        """
        Download EMG data for a specific session in CSV or JSON format

        Args:
            session_id: The ID of the therapy session
            format: The format to download ('csv' or 'json')
            include_exercise_info: Whether to include exercise and set information

        Returns:
            Dictionary with format and data
        """
        # Get the EMG data
        result = self.get_emg_data_for_session(session_id, include_exercise_info=include_exercise_info)
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

    def download_emg_data_for_multiple_sessions(
            self,
            session_ids: List[str],
            format: str = "csv",
            include_exercise_info: bool = True
    ) -> Dict:
        """
        Download EMG data for multiple sessions in CSV or JSON format

        Args:
            session_ids: List of session IDs to include
            format: The format to download ('csv' or 'json')
            include_exercise_info: Whether to include exercise and set information

        Returns:
            Dictionary with format and data
        """
        # Get the EMG data
        result = self.get_emg_data_for_multiple_sessions(
            session_ids,
            include_exercise_info=include_exercise_info
        )
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

    def _calculate_emg_statistics(self, emg_data: List[Dict]) -> Dict:
        """
        Calculate statistics for EMG data

        Args:
            emg_data: List of EMG data points

        Returns:
            Dictionary with statistics
        """
        if not emg_data:
            return {
                "min": 0,
                "max": 0,
                "avg": 0,
                "by_sensor_position": {}
            }

        # Overall statistics
        values = [point.get("value", 0) for point in emg_data]
        min_value = min(values) if values else 0
        max_value = max(values) if values else 0
        avg_value = sum(values) / len(values) if values else 0

        # Group by sensor position
        positions = {}
        for point in emg_data:
            position = point.get("sensor_position")
            if position not in positions:
                positions[position] = []
            positions[position].append(point.get("value", 0))

        # Calculate statistics by position
        position_stats = {}
        for position, pos_values in positions.items():
            position_stats[position] = {
                "min": min(pos_values) if pos_values else 0,
                "max": max(pos_values) if pos_values else 0,
                "avg": sum(pos_values) / len(pos_values) if pos_values else 0,
                "count": len(pos_values)
            }

        return {
            "min": min_value,
            "max": max_value,
            "avg": avg_value,
            "by_sensor_position": position_stats
        }

    def _calculate_progress_trends(self, progress_data: List[Dict]) -> Dict:
        """
        Calculate trend information from progress data

        Args:
            progress_data: List of progress data points

        Returns:
            Dictionary with trend information
        """
        if not progress_data or len(progress_data) < 2:
            return {
                "direction": "unchanged",
                "percent_change": 0,
                "is_improving": False
            }

        # Sort by date
        sorted_data = sorted(progress_data, key=lambda x: x.get("date", ""))

        # Get first and last values
        first_avg = sorted_data[0].get("avg_value", 0)
        last_avg = sorted_data[-1].get("avg_value", 0)

        # Calculate percent change
        if first_avg > 0:
            percent_change = ((last_avg - first_avg) / first_avg) * 100
        else:
            percent_change = 0 if last_avg == 0 else 100

        # Determine direction
        if percent_change > 5:
            direction = "increasing"
            is_improving = True  # Assuming higher EMG values are better
        elif percent_change < -5:
            direction = "decreasing"
            is_improving = False
        else:
            direction = "unchanged"
            is_improving = False

        return {
            "direction": direction,
            "percent_change": round(percent_change, 2),
            "is_improving": is_improving,
            "first_value": first_avg,
            "last_value": last_avg,
            "period_start": sorted_data[0].get("date"),
            "period_end": sorted_data[-1].get("date")
        }


active_sessions = {}


class AuthAbstraction(BaseAbstraction):

    def login_with_email(self, email: str) -> Dict:
        """
        Simple login function that checks if email exists in the database

        Args:
            email: The email address to check

        Returns:
            Dictionary with user info and auth token if successful

        Raises:
            ValueError: If the email doesn't exist in the database
        """
        # Check if the email exists
        user = self.db.query(User).filter(User.email == email).first()

        if not user:
            self.logger.warning(f"Login attempt with non-existent email: {email}")
            raise ValueError(f"No user found with email: {email}")

        # Generate a simple auth token
        auth_token = str(uuid4())

        # Create user data dictionary
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.name,
            "auth_token": auth_token
        }

        # Store in active sessions
        active_sessions[auth_token] = user_data

        self.logger.info(
            "User logged in successfully",
            user_id=str(user.id),
            email=user.email,
            role=user.role.name
        )

        return user_data

    def logout(self, auth_token: str) -> bool:
        """
        Logout a user by invalidating their auth token

        Args:
            auth_token: The authentication token to invalidate

        Returns:
            True if successful, False if token wasn't found
        """
        if auth_token in active_sessions:
            user_data = active_sessions[auth_token]
            del active_sessions[auth_token]

            self.logger.info(
                "User logged out successfully",
                user_id=user_data.get("id"),
                email=user_data.get("email")
            )

            return True

        return False

    def verify_token(self, auth_token: str) -> Optional[Dict]:
        """
        Verify if an auth token is valid

        Args:
            auth_token: The authentication token to check

        Returns:
            User data dictionary if valid, None otherwise
        """
        return active_sessions.get(auth_token)

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Get user info by email

        Args:
            email: The email to look up

        Returns:
            User data dictionary if found, None otherwise
        """
        user = self.db.query(User).filter(User.email == email).first()

        if not user:
            return None

        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.name
        }
