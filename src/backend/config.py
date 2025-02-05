from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/telerehabilitation_db"
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    MQTT_BROKER_URL: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_WEBSOCKET_PORT: int = 9001

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
