import uuid
from enum import Enum
from typing import Optional, List, Dict
import  structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, UUID4, constr
from src.backend.dependencies.services import get_user_service, get_current_user
from src.backend.exceptions import UserAlreadyExists
from src.backend.service.users_service import UserService

logger = structlog.get_logger(__name__)
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
    except UserAlreadyExists:
        raise HTTPException(
            status_code=409,
            detail=f"User with email {user_data['email']} already exists",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/{user_id}", response_model=dict)
def get_user_by_id(
        user_id: UUID4,
        user_service: UserService = Depends(get_user_service),
        current_user: dict = Depends(get_current_user)  # Protected route
):
    """
    Get user details by ID. Only accessible by therapists, admins,
    or the user themselves.
    """
    try:
        # Get user details
        user_data = user_service.get_user_by_id(str(user_id))

        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if current user has permission to view this user
        if current_user["role"] not in ["therapist", "admin"] and current_user["id"] != str(user_id):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to view this user's details"
            )

        return user_data

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Add this to your users.py router file

@router.get("/", response_model=List[Dict])
def get_users(
        role: Optional[str] = Query(None, description="Filter users by role"),
        user_service: UserService = Depends(get_user_service),
        current_user: dict = Depends(get_current_user)  # Protected route
):
    """
    Get all users, with optional filtering by role.
    Only accessible by therapists and admins.
    """
    try:
        # Only therapists and admins can list users
        if current_user["role"] not in ["therapist", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Only therapists and admins can list users"
            )

        # Convert role string to enum value if provided
        role_enum = None
        if role:
            try:
                role_enum = UserRoleEnum[role.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid role: {role}. Valid roles are: {', '.join([r.name for r in UserRoleEnum])}"
                )

        # Get users with optional role filter
        users = user_service.get_users(role_enum)

        return users

    except Exception as e:
        logger.error(
            "Error on retrieving patient data",
            exc_info=True,
        )
        raise HTTPException(status_code=400, detail=str(e))
