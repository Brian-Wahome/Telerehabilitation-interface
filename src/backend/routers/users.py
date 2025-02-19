import uuid
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, UUID4, constr
from src.backend.dependencies.services import get_user_service
from src.backend.service.users_service import UserService


class UserRoleEnum(str, Enum):
    PATIENT = "patient"
    THERAPIST = "therapist"
    ADMIN = "admin"


class UserCreate(BaseModel):
    id: UUID4 | None = None
    email: EmailStr
    role: UserRoleEnum
    first_name: constr(max_length=100)
    last_name: constr(max_length=100)

    class Config:
        from_attributes = True


router = APIRouter(
    prefix="/users",
    tags=["user"]
)


@router.post("/", status_code=201)
def create_user(
        user_data: UserCreate,
        user_service: UserService = Depends(get_user_service)
):
    try:
        user_id = uuid.uuid4()
        user_data.id = user_id
        user_data = user_data.model_dump()
        user_service.create_user(user_data)
        return {"message": "User successfully created."}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
