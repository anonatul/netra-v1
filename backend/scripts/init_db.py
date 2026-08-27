"""Initialize schema + seed demo data. Run: python -m scripts.init_db"""
from app.auth.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import ModelVersion, RuleVersion, User


def init() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            demo = [
                ("admin", "admin123", "ADMIN", "Demo Admin"),
                ("operator", "operator123", "OPERATOR", "Demo Operator"),
                ("commander", "commander123", "COMMANDER", "Demo Commander"),
                ("field", "field123", "FIELD_RESPONDER", "Demo Field Responder"),
                ("auditor", "auditor123", "AUDITOR", "Demo Auditor"),
                ("citizen-sim", "citizen-sim123", "CITIZEN", "Citizen Simulator"),
            ]
            for username, password, role, display in demo:
                db.add(User(username=username, password_hash=hash_password(password), role=role, display_name=display))
        db.add_all([
            ModelVersion(name="llm-extraction", version="llm-extract-v1", description="LLM extraction prompt contract v1", active=True),
            ModelVersion(name="rules-extraction", version="rules-v1", description="Deterministic multilingual rules", active=True),
            RuleVersion(name="priority", version="priority-v1.0", description="Rescue Priority Score draft weights", active=True),
        ])
        db.commit()
        print("DB initialized + demo users seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    init()