from typing import Optional

from fastapi import Depends, Header, Cookie, HTTPException
from sqlalchemy.orm import Session
from src.backend.database import get_db, SessionLocal
from src.backend.abstraction import UserAbstraction, SessionAbstraction, ExerciseAbstraction, ExerciseSetAbstraction, \
    EMGDataAbstraction, MQTTAbstraction, AuthAbstraction
from src.backend.service.users_service import UserService
from src.backend.service.sessions_service import SessionService
from src.backend.service.mqtt_service import MQTTService
from src.backend.service.excercise_service import ExerciseService
from src.backend.service.exercise_set_service import ExerciseSetService
from src.backend.service.emg_data_service import EMGDataService
from src.backend.service.authentication_service import AuthService

db = SessionLocal()
mqtt_abstraction_singleton = MQTTAbstraction(db)
mqtt_service = MQTTService(mqtt_abstraction_singleton)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    user_abstraction = UserAbstraction(db)
    return UserService(user_abstraction)


def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    session_abstraction = SessionAbstraction(db)
    return SessionService(session_abstraction)


def get_mqtt_service() -> MQTTService:
    return mqtt_service


def get_exercise_service(db: Session = Depends(get_db)) -> ExerciseService:
    exercise_abstraction = ExerciseAbstraction(db)
    return ExerciseService(exercise_abstraction)


def get_exercise_set_service(db: Session = Depends(get_db)) -> ExerciseSetService:
    exercise_set_abstraction = ExerciseSetAbstraction(db)
    return ExerciseSetService(exercise_set_abstraction)


def get_emg_data_service(db: Session = Depends(get_db)) -> EMGDataService:
    emg_data_abstraction = EMGDataAbstraction(db)
    return EMGDataService(emg_data_abstraction)


def get_mqtt_abstraction(db: Session = Depends(get_db)) -> MQTTAbstraction:
    mqtt_abstraction = MQTTAbstraction(db)
    return mqtt_abstraction


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    auth_abstraction = AuthAbstraction(db)
    return AuthService(auth_abstraction)


# Authentication dependency for protected routes
def get_current_user(
        auth_token: Optional[str] = Cookie(None),
        authorisation: Optional[str] = Header(None),
        auth_service: AuthService = Depends(get_auth_service)
):
    # Try to get token from either cookie or authorisation header
    token = auth_token
    if not token and authorisation and authorisation.startswith("Bearer "):
        token = authorisation.replace("Bearer ", "")

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_data = auth_service.verify_token(token)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_data


