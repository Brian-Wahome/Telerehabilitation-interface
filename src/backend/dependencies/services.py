from fastapi import Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..abstraction import UserAbstraction, SessionAbstraction, ExerciseAbstraction, ExerciseSetAbstraction, EMGDataAbstraction
from ..service.users_service import UserService
from ..service.sessions_service import SessionService
from ..service.mqtt_service import MQTTService
from ..service.excercise_service import ExerciseService
from ..service.exercise_set_service import ExerciseSetService
from ..service.emg_data_service import EMGDataService

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
    exercise_set_abstraction = ExerciseSetService(db)
    return ExerciseSetAbstraction(exercise_set_abstraction)

def get_emg_data_service(db: Session = Depends(get_db)) -> EMGDataService:
    emg_data_abstraction = EMGDataAbstraction(db)
    return EMGDataService(emg_data_abstraction)
