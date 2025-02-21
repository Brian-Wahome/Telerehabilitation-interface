from fastapi import Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..abstraction import UserAbstraction
from ..service.users_service import UserService


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    user_abstraction = UserAbstraction(db)
    return UserService(user_abstraction)
