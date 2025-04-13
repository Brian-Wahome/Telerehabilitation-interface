from fastapi import APIRouter
from .users import router as users_router
from .sessions import router as sessions_router
from .mqtt import router as mqtt_router

router = APIRouter()
router.include_router(users_router)
router.include_router(sessions_router)
router.include_router(mqtt_router)
