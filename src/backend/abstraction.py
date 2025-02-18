from sqlalchemy.orm import Session
from contextlib import contextmanager
from .orm import User


class BaseAbstraction:
    def __init__(self, db: Session):
        self.db = db

    @contextmanager
    def transaction(self):
        try:
            yield
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise


class UserAbstraction(BaseAbstraction):
    def create_user(self, user: dict) -> User:
        with self.transaction():
            user = User(**user)
            self.db.add(user)
