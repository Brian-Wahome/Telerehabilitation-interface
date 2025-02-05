import enum
from sqlalchemy import Column, String, UUID, DateTime, ForeignKey, Boolean, Enum, Text, JSON, TIMESTAMP
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


