from sqlalchemy.orm import Session as db_session
from contextlib import contextmanager
from .orm import User, Session
from uuid import uuid4
import structlog


class BaseAbstraction:
    def __init__(self, db: db_session):
        self.db = db
        self.session_id = str(uuid4())
        self.logger = structlog.stdlib.get_logger(__name__).bind(
            session_id=self.session_id,
            layer="repository",
        )

    @contextmanager
    def transaction(self):
        try:
            yield
            self.db.commit()
            self.logger.debug("Database commit is successful")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error {e} raised when committing")
            raise


class UserAbstraction(BaseAbstraction):
    def create_user(self, user: dict) -> User:
        with self.transaction():
            user = User(**user)
            self.db.add(user)


class SessionAbstraction(BaseAbstraction):
    def create_session(self, session: dict) -> Session:
        with self.transaction():
            session = Session(**session)
            self.db.add(session)
