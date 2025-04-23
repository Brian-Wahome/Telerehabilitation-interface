from fastapi import Depends
from sqlalchemy.orm import Session
from src.backend.database import get_db
from src.backend.abstraction import UserAbstraction, SessionAbstraction, ExerciseAbstraction, ExerciseSetAbstraction, \
    EMGDataAbstraction, MQTTAbstraction
from src.backend.service.users_service import UserService
from src.backend.service.sessions_service import SessionService
from src.backend.service.mqtt_service import MQTTService
from src.backend.service.excercise_service import ExerciseService
from src.backend.service.exercise_set_service import ExerciseSetService
from src.backend.service.emg_data_service import EMGDataService

mqtt_service = MQTTService()


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
    return ExerciseSetAbstraction(exercise_set_abstraction)


def get_emg_data_service(db: Session = Depends(get_db)) -> EMGDataService:
    emg_data_abstraction = EMGDataAbstraction(db)
    return EMGDataService(emg_data_abstraction)


def get_mqtt_abstraction(db: Session = Depends(get_db)) -> MQTTAbstraction:
    mqtt_abstraction = MQTTAbstraction(db)
    return mqtt_abstraction
