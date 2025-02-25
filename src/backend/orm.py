import enum
from sqlalchemy import Column, String, UUID, DateTime, ForeignKey, Float, Enum, Text, JSON, TIMESTAMP, Integer
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
    sensors = relationship("Sensors", back_populates="session")


class Sensors(Base):
    __tablename__ = "sensors"
    id = Column(UUID, primary_key=True, default=uuid.uuid4())
    session_id = Column(UUID, ForeignKey("sessions.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("Session", back_populates="sensors")
    emg_data = relationship("EMGData", back_populates="sensor")


class SensorPositionEnum(enum.Enum):
    left_bicep = 1
    left_forearm = 2
    right_bicep = 3
    right_forearm = 4


class EMGData(Base):
    __tablename__ = "emg_data"
    time = Column(TIMESTAMP(timezone=True), primary_key=True)
    sensor_id = Column(UUID, ForeignKey("sensors.id"), primary_key=True)
    value = Column(Float, nullable=False)
    sensor_position = Column(
        Enum(
            SensorPositionEnum,
            name="sensor_position_enum",
            native_enum=False,
            create_constraint=True
        ),
        nullable=False,
        comment="Allowed values: left_bicep, left_forearm, right_bicep, right_forearm"
    )
    # Relationship to sensor
    sensor = relationship("Sensors", back_populates="emg_data")
