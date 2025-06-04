from typing import Dict, List, Optional
from datetime import datetime
import structlog
from src.backend.abstraction import EMGDataAbstraction


class EMGDataService:
    def __init__(self, emg_data_abstraction: EMGDataAbstraction):
        self.emg_data_abstraction = emg_data_abstraction
        self.logger = structlog.get_logger(__name__)

    def get_emg_data_for_session(
            self,
            session_id: str,
            start_time: Optional[str] = None,
            end_time: Optional[str] = None,
            sensor_position: Optional[str] = None,
            include_exercise_info: bool = True
    ) -> Dict:
        """
        Get all EMG data for a specific therapy session

        Args:
            session_id: The ID of the therapy session
            start_time: Optional start time filter (ISO format string)
            end_time: Optional end time filter (ISO format string)
            sensor_position: Optional filter for specific sensor position
            include_exercise_info: Whether to include exercise and set information

        Returns:
            Dictionary containing the session info and EMG data
        """
        # Convert string times to datetime if provided
        start_datetime = None
        end_datetime = None

        if start_time:
            try:
                start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                self.logger.warning(f"Invalid start_time format: {start_time}")

        if end_time:
            try:
                end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                self.logger.warning(f"Invalid end_time format: {end_time}")

        self.logger.info(
            "Retrieving EMG data for session",
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            sensor_position=sensor_position
        )

        return self.emg_data_abstraction.get_emg_data_for_session(
            session_id=session_id,
            start_time=start_datetime,
            end_time=end_datetime,
            sensor_position=sensor_position,
            include_exercise_info=include_exercise_info
        )

    def get_emg_data_for_multiple_sessions(
            self,
            session_ids: List[str],
            start_time: Optional[str] = None,
            end_time: Optional[str] = None,
            sensor_position: Optional[str] = None,
            include_exercise_info: bool = True
    ) -> Dict:
        """
        Get EMG data for multiple sessions, useful for comparing progress over time

        Args:
            session_ids: List of session IDs to include
            start_time: Optional start time filter (ISO format string)
            end_time: Optional end time filter (ISO format string)
            sensor_position: Optional filter for specific sensor position
            include_exercise_info: Whether to include exercise and set information

        Returns:
            Dictionary containing the sessions info and EMG data
        """
        # Convert string times to datetime if provided
        start_datetime = None
        end_datetime = None

        if start_time:
            try:
                start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                self.logger.warning(f"Invalid start_time format: {start_time}")

        if end_time:
            try:
                end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                self.logger.warning(f"Invalid end_time format: {end_time}")

        self.logger.info(
            "Retrieving EMG data for multiple sessions",
            session_ids=session_ids,
            start_time=start_time,
            end_time=end_time,
            sensor_position=sensor_position
        )

        return self.emg_data_abstraction.get_emg_data_for_multiple_sessions(
            session_ids=session_ids,
            start_time=start_datetime,
            end_time=end_datetime,
            sensor_position=sensor_position,
            include_exercise_info=include_exercise_info
        )

    def get_patient_progress(
            self,
            patient_id: str,
            time_range: Optional[int] = 30,
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
        self.logger.info(
            "Retrieving patient progress",
            patient_id=patient_id,
            time_range=time_range,
            exercise_name=exercise_name,
            sensor_position=sensor_position
        )

        return self.emg_data_abstraction.get_patient_progress(
            patient_id=patient_id,
            time_range=time_range,
            exercise_name=exercise_name,
            sensor_position=sensor_position
        )

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
        self.logger.info(
            "Downloading EMG data for session",
            session_id=session_id,
            format=format
        )

        return self.emg_data_abstraction.download_emg_data_for_session(
            session_id=session_id,
            format=format,
            include_exercise_info=include_exercise_info
        )

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
        self.logger.info(
            "Downloading EMG data for multiple sessions",
            session_ids=session_ids,
            format=format
        )

        return self.emg_data_abstraction.download_emg_data_for_multiple_sessions(
            session_ids=session_ids,
            format=format,
            include_exercise_info=include_exercise_info
        )