import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, UUID4
from typing import Optional, List
from src.backend.dependencies.services import get_exercise_service
from src.backend.service.excercise_service import ExerciseService


class ExerciseCreate(BaseModel):
    session_id: UUID4
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None


class ExerciseResponse(BaseModel):
    id: UUID4
    session_id: UUID4
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None


router = APIRouter(
    prefix="/exercises",
    tags=["exercises"]
)


@router.post("/", status_code=201, response_model=ExerciseResponse)
def create_exercise(
        exercise_data: ExerciseCreate,
        exercise_service: ExerciseService = Depends(get_exercise_service)
):
    try:
        exercise_dict = exercise_data.model_dump()
        exercise_dict["id"] = str(uuid.uuid4())
        exercise = exercise_service.create_exercise(exercise_dict)
        return exercise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/session/{session_id}", response_model=List[ExerciseResponse])
def get_exercises_by_session(
        session_id: UUID4,
        exercise_service: ExerciseService = Depends(get_exercise_service)
):
    try:
        exercises = exercise_service.get_exercises_by_session(str(session_id))
        return exercises
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{exercise_id}", response_model=ExerciseResponse)
def get_exercise_by_id(
        exercise_id: UUID4,
        exercise_service: ExerciseService = Depends(get_exercise_service)
):
    try:
        exercise = exercise_service.get_exercise_by_id(str(exercise_id))
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        return exercise
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))