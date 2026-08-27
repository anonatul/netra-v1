"""Shared test setup: dedicated netra_test database.

Other test files drop_all/create_all per test on the same DB, so this
conftest restores schema + demo users after any wipe (autouse, per-test).
"""
import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://netra:netra@localhost:5433/netra_test"
)

import pytest  # noqa: E402
from sqlalchemy import inspect  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.auth.security import hash_password  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.models import User  # noqa: E402

DEMO_USERS = [
    ("admin", "admin123", "ADMIN", "Admin"),
    ("operator", "operator123", "OPERATOR", "Operator"),
    ("commander", "commander123", "COMMANDER", "Commander"),
    ("field", "field123", "FIELD", "Field Unit"),
    ("auditor", "auditor123", "AUDITOR", "Auditor"),
]


@pytest.fixture(autouse=True)
def _ensure_schema_users():
    if "users" not in inspect(engine).get_table_names():
        Base.metadata.create_all(engine)
    with Session(engine) as db:
        for username, password, role, display in DEMO_USERS:
            if db.query(User).filter(User.username == username).first() is None:
                db.add(User(
                    username=username, password_hash=hash_password(password),
                    role=role, display_name=display,
                ))
        db.commit()
    yield