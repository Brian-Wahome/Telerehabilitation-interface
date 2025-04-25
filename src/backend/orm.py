import enum
from sqlalchemy import Column, String, UUID, DateTime, ForeignKey, Float, Enum, TIMESTAMP, Integer, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base


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

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
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
    exercises = relationship("Exercise", back_populates="session")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID, ForeignKey("sessions.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    notes = Column(String(500))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("Session", back_populates="exercises")
    sets = relationship("ExerciseSet", back_populates="exercise")


class ExerciseSet(Base):
    __tablename__ = "exercise_sets"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    exercise_id = Column(UUID, ForeignKey("exercises.id"), nullable=False)
    set_number = Column(Integer, nullable=False)
    repetitions = Column(Integer)
    weight = Column(Float)
    start_time = Column(TIMESTAMP(timezone=True), nullable=True)
    end_time = Column(TIMESTAMP(timezone=True))
    completed = Column(Boolean, default=False)
    notes = Column(String(500))

    # Relationships
    exercise = relationship("Exercise", back_populates="sets")
    emg_data = relationship("EMGData", back_populates="exercise_set")


class Sensors(Base):
    __tablename__ = "sensors"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
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
    exercise_set_id = Column(UUID, ForeignKey("exercise_sets.id"), nullable=True)
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
    # Relationships
    sensor = relationship("Sensors", back_populates="emg_data")
    exercise_set = relationship("ExerciseSet", back_populates="emg_data")