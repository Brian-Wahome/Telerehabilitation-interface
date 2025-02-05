from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
import enum
from sqlalchemy import Column, String, UUID, DateTime, ForeignKey, Boolean, Enum, Text, JSON, TIMESTAMP
from sqlalchemy.sql import func
import uuid
import datetime

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/telerehabilitation_db"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserRoleEnum(enum.Enum):
    patient = 1
    therapist = 2
    admin = 3


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(
        Enum(
            UserRoleEnum,
            name="user_role_enum",
            native_enum=False,
            create_constraint=True
        ),
        nullable=False,
        comment="Allowed values: patient, therapist, admin"
    )
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())