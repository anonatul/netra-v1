from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

_database_url = settings.database_url
for _old, _new in (("postgresql://", "postgresql+psycopg://"), ("postgres://", "postgresql+psycopg://")):
    if _database_url.startswith(_old):
        _database_url = _new + _database_url[len(_old):]
        break

engine = create_engine(_database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False