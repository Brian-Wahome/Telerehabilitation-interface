from typing import Dict
import structlog
from src.backend.abstraction import UserAbstraction
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
