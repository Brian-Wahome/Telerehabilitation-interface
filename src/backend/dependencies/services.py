from fastapi import Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..abstraction import UserAbstraction, SessionAbstraction
from ..service.users_service import UserService
from ..service.sessions_service import SessionService


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    user_abstraction = UserAbstraction(db)
    return UserService(user_abstraction)


def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    session_abstraction = SessionAbstraction(db)
    return SessionService(session_abstraction)
