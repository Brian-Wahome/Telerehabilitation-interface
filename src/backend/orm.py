import enum
from sqlalchemy import Column, String, UUID, DateTime, ForeignKey, Boolean, Enum, Text, JSON, TIMESTAMP, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .database import Base


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

    # Relationships
    sessions_as_patient = relationship("Session", back_populates="patient", foreign_keys="Session.patient_id")
    sessions_as_therapist = relationship("Session", back_populates="therapist", foreign_keys="Session.therapist_id")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4())
    patient_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    therapist_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    completed = Column(DateTime(timezone=True))
    notes = Column(String(500))
    duration = Column(Integer)

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], back_populates="sessions_as_patient")
    therapist = relationship("User", foreign_keys=[therapist_id], back_populates="sessions_as_therapist")

    # Add EMG relationship once TimeScaleDb extension is set up