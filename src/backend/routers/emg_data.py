import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, UUID4
from typing import Optional, List
from src.backend.dependencies.services import get_emg_data_service
from src.backend.service.emg_data_service import EMGDataService

router = APIRouter(
    prefix="/emg-data",
    tags=["emg-data"]
)


@router.get("/sessions/{session_id}")
def get_session_emg_data(
        session_id: UUID4,
        start_time: Optional[str] = Query(None),
        end_time: Optional[str] = Query(None),
        sensor_position: Optional[str] = Query(None),
        include_exercise_info: bool = Query(True),
        emg_data_service: EMGDataService = Depends(get_emg_data_service)
):
    """
    Get all EMG data for a specific therapy session
    """
    try:
        emg_data = emg_data_service.get_emg_data_for_session(
            session_id=str(session_id),
            start_time=start_time,
            end_time=end_time,
            sensor_position=sensor_position,
            include_exercise_info=include_exercise_info
        )
        return emg_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/multiple")
def get_multiple_sessions_emg_data(
        session_ids: List[UUID4],
        start_time: Optional[str] = Query(None),
        end_time: Optional[str] = Query(None),
        sensor_position: Optional[str] = Query(None),
        include_exercise_info: bool = Query(True),
        emg_data_service: EMGDataService = Depends(get_emg_data_service)
):
    """
    Get EMG data for multiple sessions
    """
    try:
        # Convert UUID objects to strings
        session_id_strings = [str(session_id) for session_id in session_ids]

        emg_data = emg_data_service.get_emg_data_for_multiple_sessions(
            session_ids=session_id_strings,
            start_time=start_time,
            end_time=end_time,
            sensor_position=sensor_position,
            include_exercise_info=include_exercise_info
        )
        return emg_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patients/{patient_id}/progress")
def get_patient_progress(
        patient_id: UUID4,
        time_range: int = Query(30, description="Number of days to look back"),
        exercise_name: Optional[str] = Query(None),
        sensor_position: Optional[str] = Query(None),
        emg_data_service: EMGDataService = Depends(get_emg_data_service)
):
    """
    Get a patient's progress over time
    """
    try:
        progress_data = emg_data_service.get_patient_progress(
            patient_id=str(patient_id),
            time_range=time_range,
            exercise_name=exercise_name,
            sensor_position=sensor_position
        )
        return progress_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/download")
def download_session_emg_data(
        session_id: UUID4,
        format: str = Query("csv", description="Format of the download: csv or json"),
        include_exercise_info: bool = Query(True),
        emg_data_service: EMGDataService = Depends(get_emg_data_service)
):
    """
    Download EMG data for a specific session
    """
    try:
        result = emg_data_service.download_emg_data_for_session(
            session_id=str(session_id),
            format=format,
            include_exercise_info=include_exercise_info
        )

        if format.lower() == "csv" and result["format"] == "csv":
            return StreamingResponse(
                result["data"],
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=emg_data_session_{session_id}.csv"}
            )
        elif format.lower() == "json" and result["format"] == "json":
            return JSONResponse(content=result["data"])
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'json'")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/multiple/download")
def download_multiple_sessions_emg_data(
        session_ids: List[UUID4],
        format: str = Query("csv", description="Format of the download: csv or json"),
        include_exercise_info: bool = Query(True),
        emg_data_service: EMGDataService = Depends(get_emg_data_service)
):
    """
    Download EMG data for multiple sessions
    """
    try:
        # Convert UUID objects to strings
        session_id_strings = [str(session_id) for session_id in session_ids]

        result = emg_data_service.download_emg_data_for_multiple_sessions(
            session_ids=session_id_strings,
            format=format,
            include_exercise_info=include_exercise_info
        )

        if format.lower() == "csv" and result["format"] == "csv":
            return StreamingResponse(
                result["data"],
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=emg_data_multiple_sessions.csv"}
            )
        elif format.lower() == "json" and result["format"] == "json":
            return JSONResponse(content=result["data"])
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'json'")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))