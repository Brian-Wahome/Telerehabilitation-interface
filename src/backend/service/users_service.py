from typing import Dict, Optional, List
import structlog
from src.backend.abstraction import UserAbstraction, UserRoleEnum
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from ..exceptions import UserAlreadyExists


class UserService:
    def __init__(self, user_abstraction: UserAbstraction):
        self.user_abstraction = user_abstraction
        self.logger = structlog.get_logger(__name__)

    def create_user(self, user_data: Dict):
        try:
            self.logger.info("Creating user", user_email=user_data.get('email'), user_id=user_data.get('id'))
            self.user_abstraction.create_user(user_data)
        except IntegrityError as e:
            if isinstance(e.orig, UniqueViolation):
                raise UserAlreadyExists


    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Function to retrieve a user by ID
        :param user_id: The ID of the user to retrieve
        :return: User data as dictionary, or None if not found
        """
        self.logger.info(
            "Retrieving user by ID",
            user_id=user_id
        )
        return self.user_abstraction.get_user_by_id(user_id)

    # Add to users_service.py
    def get_users(self, role: Optional[UserRoleEnum] = None) -> List[Dict]:
        """
        Function to retrieve all users with optional role filtering
        :param role: Optional role to filter users by
        :return: List of user data dictionaries
        """
        self.logger.info(
            "Retrieving users",
            role=role.name if role else None
        )
        return self.user_abstraction.get_users(role)
