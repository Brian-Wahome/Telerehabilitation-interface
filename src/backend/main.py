import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from src.config.logging_config import configure_logging
from src.backend.routers.users import router as user_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tele-rehabilitation Interface", on_startup=[configure_logging])

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# add routers to app
app.include_router(user_router)

@app.get("/")
async def root():
    return {"message": "Tele-rehabilitation Interface API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
