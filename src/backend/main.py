from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from src.config.logging_config import configure_logging
from src.backend.routers import router
from dependencies.services import mqtt_service, get_mqtt_abstraction

# Create database tables
Base.metadata.create_all(bind=engine)

message_handler = get_mqtt_abstraction()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    configure_logging()
    mqtt_service.setup_mqtt_client(message_handler=message_handler)

    yield  # The app runs during this time

    # Shutdown
    mqtt_service.disconnect_client(client_id="default")
    mqtt_service.remove_client(client_id="default")


app = FastAPI(title="Tele-rehabilitation Interface")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# add routers to app
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Tele-rehabilitation Interface API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
