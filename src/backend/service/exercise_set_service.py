from typing import Dict, List, Optional
import structlog
from io import BytesIO
import pandas as pd
from src.backend.abstraction import ExerciseSetAbstraction


class ExerciseSetService:
    def __init__(self, exercise_set_abstraction: ExerciseSetAbstraction):
        self.exercise_set_abstraction = exercise_set_abstraction
        self.logger = structlog.get_logger(__name__)

    def create_set(self, set_data: Dict) -> Dict:
        self.logger.info(
            "Creating exercise set",
            exercise_id=set_data.get('exercise_id'),
            repetitions=set_data.get('repetitions'),
            weight=set_data.get('weight')
        )
        set_orm = self.exercise_set_abstraction.create_set(set_data)

        # Convert ORM object to dictionary
        return {
            "id": str(set_orm.id),
            "exercise_id": str(set_orm.exercise_id),
            "set_number": set_orm.set_number,
            "repetitions": set_orm.repetitions,
            "weight": set_orm.weight,
            "start_time": set_orm.start_time.isoformat() if set_orm.start_time else None,
            "end_time": set_orm.end_time.isoformat() if set_orm.end_time else None,
            "completed": set_orm.completed,
            "notes": set_orm.notes
        }

    def get_sets_by_exercise(self, exercise_id: str) -> List[Dict]:
        self.logger.info(
            "Retrieving sets for exercise",
            exercise_id=exercise_id
        )
        sets_orm = self.exercise_set_abstraction.get_sets_by_exercise(exercise_id)

        # Convert list of ORM objects to list of dictionaries
        return [
            {
                "id": str(exercise_set.id),
                "exercise_id": str(exercise_set.exercise_id),
                "set_number": exercise_set.set_number,
                "repetitions": exercise_set.repetitions,
                "weight": exercise_set.weight,
                "start_time": exercise_set.start_time.isoformat() if exercise_set.start_time else None,
                "end_time": exercise_set.end_time.isoformat() if exercise_set.end_time else None,
                "completed": exercise_set.completed,
                "notes": exercise_set.notes
            }
            for exercise_set in sets_orm
        ]

    def get_set_by_id(self, set_id: str) -> Optional[Dict]:
        self.logger.info(
            "Retrieving exercise set by ID",
            set_id=set_id
        )
        set_orm = self.exercise_set_abstraction.get_set_by_id(set_id)

        if not set_orm:
            return None

        # Get the exercise ID
        exercise_id = str(set_orm.exercise_id)

        # Convert ORM object to dictionary
        return {
            "id": str(set_orm.id),
            "exercise_id": exercise_id,
            "set_number": set_orm.set_number,
            "repetitions": set_orm.repetitions,
            "weight": set_orm.weight,
            "start_time": set_orm.start_time.isoformat() if set_orm.start_time else None,
            "end_time": set_orm.end_time.isoformat() if set_orm.end_time else None,
            "completed": set_orm.completed,
            "notes": set_orm.notes
        }

    def start_set(self, set_id: str) -> Optional[Dict]:
        self.logger.info(
            "Starting exercise set",
            set_id=set_id
        )
        set_orm = self.exercise_set_abstraction.start_set(set_id)

        if not set_orm:
            return None

        # Convert ORM object to dictionary
        return {
            "id": str(set_orm.id),
            "exercise_id": str(set_orm.exercise_id),
            "set_number": set_orm.set_number,
            "repetitions": set_orm.repetitions,
            "weight": set_orm.weight,
            "start_time": set_orm.start_time.isoformat() if set_orm.start_time else None,
            "end_time": set_orm.end_time.isoformat() if set_orm.end_time else None,
            "completed": set_orm.completed,
            "notes": set_orm.notes
        }

    def complete_set(self, set_id: str, notes: Optional[str] = None) -> Optional[Dict]:
        self.logger.info(
            "Completing exercise set",
            set_id=set_id,
            notes=notes is not None
        )
        set_orm = self.exercise_set_abstraction.complete_set(set_id, notes)

        if not set_orm:
            return None

        # Convert ORM object to dictionary
        return {
            "id": str(set_orm.id),
            "exercise_id": str(set_orm.exercise_id),
            "set_number": set_orm.set_number,
            "repetitions": set_orm.repetitions,
            "weight": set_orm.weight,
            "start_time": set_orm.start_time.isoformat() if set_orm.start_time else None,
            "end_time": set_orm.end_time.isoformat() if set_orm.end_time else None,
            "completed": set_orm.completed,
            "notes": set_orm.notes
        }

    def get_emg_data_for_set(self, set_id: str, sensor_position: Optional[str] = None) -> Dict:
        self.logger.info(
            "Retrieving EMG data for set",
            set_id=set_id,
            sensor_position=sensor_position
        )
        result = self.exercise_set_abstraction.get_emg_data_for_set(set_id, sensor_position)

        # Get the exercise set info
        set_orm = self.exercise_set_abstraction.get_set_by_id(set_id)
        if not set_orm:
            return {
                "set_id": set_id,
                "data": []
            }

        # Format the data appropriately
        formatted_data = []
        for emg_data in result.get("data", []):
            if hasattr(emg_data, "__dict__"):  # Check if it's an ORM object
                formatted_data.append({
                    "time": emg_data.time.isoformat(),
                    "sensor_position": emg_data.sensor_position.name,
                    "value": emg_data.value,
                    "sensor_id": str(emg_data.sensor_id)
                })
            else:
                # Assume it's already a dictionary
                formatted_data.append(emg_data)

        return {
            "set_id": set_id,
            "exercise_id": str(set_orm.exercise_id),
            "set_number": set_orm.set_number,
            "start_time": set_orm.start_time.isoformat() if set_orm.start_time else None,
            "end_time": set_orm.end_time.isoformat() if set_orm.end_time else None,
            "data": formatted_data
        }

    def download_emg_data_for_set(self, set_id: str, format: str = "csv") -> Dict:
        self.logger.info(
            "Downloading EMG data for set",
            set_id=set_id,
            format=format
        )

        # Get EMG data
        emg_data_result = self.get_emg_data_for_set(set_id)
        emg_data = emg_data_result.get("data", [])

        if format.lower() == "csv":
            # Convert to DataFrame for CSV export
            df = pd.DataFrame(emg_data)
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
                "data": emg_data
            }

        else:
            raise ValueError(f"Unsupported format: {format}. Use 'csv' or 'json'")