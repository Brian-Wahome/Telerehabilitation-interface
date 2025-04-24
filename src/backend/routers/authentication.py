from fastapi import APIRouter, Depends, HTTPException, Cookie, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional

from src.backend.dependencies.services import get_auth_service
from src.backend.service.authentication_service import AuthService


class LoginRequest(BaseModel):
    email: EmailStr


class LoginResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    auth_token: str


router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)


@router.post("/login", response_model=LoginResponse)
def login(
        login_data: LoginRequest,
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login a user with their email address only (no password required for initial iteration)
    """
    try:
        user_data = auth_service.login_with_email(login_data.email)

        # Create a response with auth token in both body and cookie
        response = JSONResponse(content=user_data)

        # Set a cookie with the auth token
        # secure=True should be used in production
        # httponly=True prevents JavaScript access to the cookie
        response.set_cookie(
            key="auth_token",
            value=user_data["auth_token"],
            httponly=True,
            max_age=3600,  # 1 hour
            path="/"
        )

        return response
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
def logout(
        auth_token: Optional[str] = Cookie(None),
        authorization: Optional[str] = Header(None),
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout a user by invalidating their auth token
    """
    # Try to get token from either cookie or authorization header
    token = auth_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")

    if not token:
        raise HTTPException(status_code=401, detail="No authentication token provided")

    success = auth_service.logout(token)

    # Clear the cookie even if the token wasn't found
    response = JSONResponse(content={"status": "success" if success else "token_not_found"})
    response.delete_cookie(key="auth_token")

    return response


@router.get("/verify")
def verify_token(
        auth_token: Optional[str] = Cookie(None),
        authorisation: Optional[str] = Header(None),
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify if an auth token is valid
    """
    # Try to get token from either cookie or authorization header
    token = auth_token
    if not token and authorisation and authorisation.startswith("Bearer "):
        token = authorisation.replace("Bearer ", "")

    if not token:
        raise HTTPException(status_code=401, detail="No authentication token provided")

    user_data = auth_service.verify_token(token)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {
        "id": user_data["id"],
        "email": user_data["email"],
        "first_name": user_data["first_name"],
        "last_name": user_data["last_name"],
        "role": user_data["role"]
    }


@router.get("/check-email/{email}")
def check_email_exists(
        email: str,
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Check if an email exists in the system
    """
    user_data = auth_service.get_user_by_email(email)

    if not user_data:
        return {"exists": False}

    return {"exists": True}
