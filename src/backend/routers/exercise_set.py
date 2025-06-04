import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, UUID4
from typing import Optional, List, Any
from src.backend.dependencies.services import get_exercise_set_service, get_mqtt_service, get_exercise_service
from src.backend.service.exercise_set_service import ExerciseSetService
from src.backend.service.mqtt_service import MQTTService
from src.backend.service.excercise_service import ExerciseService
import structlog

logger = structlog.get_logger(__name__)


class ExerciseSetCreate(BaseModel):
    exercise_id: UUID4
    repetitions: Optional[int] = None
    weight: Optional[float] = None
    notes: Optional[str] = None


class ExerciseSetResponse(BaseModel):
    id: UUID4
    exercise_id: UUID4
    set_number: int
    repetitions: Optional[int] = None
    weight: Optional[float] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    completed: bool = False
    notes: Optional[str] = None


class ExerciseSetUpdateStatus(BaseModel):
    completed: bool = True
    notes: Optional[str] = None


router = APIRouter(
    prefix="/exercise-sets",
    tags=["exercise-sets"]
)


@router.post("/", status_code=201, response_model=ExerciseSetResponse)
def create_exercise_set(
        set_data: ExerciseSetCreate,
        exercise_set_service: ExerciseSetService = Depends(get_exercise_set_service)
):
    try:
        set_dict = set_data.model_dump()
        set_dict["id"] = str(uuid.uuid4())
        exercise_set = exercise_set_service.create_set(set_dict)
        return exercise_set
    except Exception as e:
        logger.error(
            f'Error whilst creating exercise-set{e}',
            exc_info=True,
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exercise/{exercise_id}", response_model=List[ExerciseSetResponse])
def get_sets_by_exercise(
        exercise_id: UUID4,
        exercise_set_service: ExerciseSetService = Depends(get_exercise_set_service)
):
    try:
        sets = exercise_set_service.get_sets_by_exercise(str(exercise_id))
        return sets
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{set_id}", response_model=ExerciseSetResponse)
def get_set_by_id(
        set_id: UUID4,
        exercise_set_service: ExerciseSetService = Depends(get_exercise_set_service)
):
    try:
        exercise_set = exercise_set_service.get_set_by_id(str(set_id))
        if not exercise_set:
            raise HTTPException(status_code=404, detail="Exercise set not found")
        return exercise_set
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{set_id}/start", response_model=ExerciseSetResponse)
def start_exercise_set(
        set_id: UUID4,
        exercise_set_service: ExerciseSetService = Depends(get_exercise_set_service),
        exercise_service: ExerciseService = Depends(get_exercise_service),
        mqtt_service: MQTTService = Depends(get_mqtt_service)
):
    try:
        # Start the set
        exercise_set = exercise_set_service.start_set(str(set_id))
        if not exercise_set:
            raise HTTPException(status_code=404, detail="Exercise set not found")

        # Get the exercise to find the session ID
        exercise_id = exercise_set["exercise_id"]
        exercise = exercise_service.get_exercise_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found for this set")

        # Set this as the active exercise set for the session
        # This will now also handle MQTT subscription
        session_id = exercise["session_id"]
        mqtt_service.set_active_exercise_set(session_id, str(set_id))

        return exercise_set
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{set_id}/complete", response_model=ExerciseSetResponse)
def complete_exercise_set(
        set_id: UUID4,
        update_data: ExerciseSetUpdateStatus,
        exercise_set_service: ExerciseSetService = Depends(get_exercise_set_service),
        exercise_service: ExerciseService = Depends(get_exercise_service),
        mqtt_service: MQTTService = Depends(get_mqtt_service)
):
    try:
        # Complete the set
        exercise_set = exercise_set_service.complete_set(str(set_id), update_data.notes)
        if not exercise_set:
            raise HTTPException(status_code=404, detail="Exercise set not found")

        # Get the exercise to find the session ID
        exercise_id = exercise_set["exercise_id"]
        exercise = exercise_service.get_exercise_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found for this set")

        # Clear this as the active exercise set for the session
        # This will now also handle MQTT unsubscription
        session_id = exercise["session_id"]
        mqtt_service.clear_active_exercise_set(session_id)

        return exercise_set
    except Exception as e:
        logger.error(
            "Error occurred whilst completing a set",
            exc_info=True,
        )

        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{set_id}/emg-data")
def get_set_emg_data(
        set_id: UUID4,
        sensor_position: Optional[str] = Query(None),
        exercise_set_service: ExerciseSetService = Depends(get_exercise_set_service)
):
    try:
        emg_data = exercise_set_service.get_emg_data_for_set(str(set_id), sensor_position)
        return emg_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{set_id}/download")
def download_set_emg_data(
        set_id: UUID4,
        format: str = Query("csv", description="Format of the download: csv or json"),
        exercise_set_service: ExerciseSetService = Depends(get_exercise_set_service)
):
    try:
        result = exercise_set_service.download_emg_data_for_set(str(set_id), format)

        if format.lower() == "csv" and result["format"] == "csv":
            return StreamingResponse(
                result["data"],
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=emg_data_set_{set_id}.csv"}
            )
        elif format.lower() == "json" and result["format"] == "json":
            return JSONResponse(content=result["data"])
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'json'")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))