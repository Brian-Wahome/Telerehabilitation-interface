from sqlalchemy.orm import Session
from contextlib import contextmanager


class BaseAbstraction:
    def __int__(self, db: Session):
        self.db = db

    @contextmanager
    def transaction(self):
        try:
            yield
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
