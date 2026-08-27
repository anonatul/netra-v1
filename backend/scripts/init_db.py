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
        def ensure_model(name, version, description):
            if not db.query(ModelVersion).filter_by(name=name, version=version).first():
                db.add(ModelVersion(name=name, version=version, description=description, active=True))

        def ensure_rule(name, version, description):
            if not db.query(RuleVersion).filter_by(name=name, version=version).first():
                db.add(RuleVersion(name=name, version=version, description=description, active=True))

        ensure_model("llm-extraction", "llm-extract-v1", "LLM extraction prompt contract v1")
        ensure_model("rules-extraction", "rules-v1", "Deterministic multilingual rules")
        ensure_rule("priority", "priority-v1.0", "Rescue Priority Score draft weights")
        db.commit()
        print("DB initialized + demo users seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    init()