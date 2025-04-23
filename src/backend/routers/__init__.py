from fastapi import APIRouter
from .users import router as users_router
from .sessions import router as sessions_router
from .mqtt import router as mqtt_router
from .exercises import router as exercises_router
from .exercise_set import router as exercises_set_router
from .emg_data import router as emg_data_router

router = APIRouter()
router.include_router(users_router)
router.include_router(sessions_router)
router.include_router(mqtt_router)
router.include_router(exercises_router)
router.include_router(exercises_set_router)
router.include_router(emg_data_router)
