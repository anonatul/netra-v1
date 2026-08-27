"""NETRA ORM models — mirrors docs/SCHEMA.md (KB file 10).

Data class tagging (RAW / DERIVED / SYSTEM / HUMAN) is enforced at the
schema/column level so the classes are never conflated.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex[:12]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Disaster(Base):
    __tablename__ = "disasters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    disaster_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(32))  # FLOOD | EARTHQUAKE | CYCLONE | OTHER
    affected_geography: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    activation_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    severity_context: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    operating_mode: Mapped[str] = mapped_column(String(32), default="NORMAL")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    incidents: Mapped[list["Incident"]] = relationship(back_populates="disaster")


class Event(Base):
    """RAW — an individual incoming observation. Immutable; never deleted."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, default=_uuid)
    disaster_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    source_type: Mapped[str] = mapped_column(String(32), index=True)  # SMS|ERSS|ELS|WHATSAPP|FIELD|MANUAL|SIMULATED
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_identifier: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    processing_status: Mapped[str] = mapped_column(
        String(32), default="RECEIVED", index=True
    )  # RECEIVED|PROCESSED|FAILED|UNRESOLVED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Evidence(Base):
    """DERIVED + provenance — source-linked interpretation of an event."""

    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(32), ForeignKey("events.event_id"), index=True)
    incident_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("incidents.incident_id"), index=True, nullable=True)
    source_type: Mapped[str] = mapped_column(String(32))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    content_reference: Mapped[str] = mapped_column(String(32))
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    extraction: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {attr: {value, confidence, model}}
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    relationship: Mapped[str] = mapped_column(String(32), default="PRIMARY")  # PRIMARY|CORROBORATING|FIELD_VERIFIED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Incident(Base):
    """SYSTEM+RAW — consolidated representation of a real-world emergency."""

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, default=_uuid)
    disaster_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("disasters.disaster_id"), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="NEW", index=True)
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), default="UNKNOWN")  # LOW|MEDIUM|HIGH|CRITICAL|UNKNOWN
    victim_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vulnerability: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    priority: Mapped[str] = mapped_column(String(16), default="UNRATED", index=True)  # P1..P4|UNRATED
    zone_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("operational_zones.zone_id"), nullable=True, index=True)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    independent_source_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    last_evidence_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    disaster: Mapped["Disaster | None"] = relationship(back_populates="incidents")


class OperationalZone(Base):
    __tablename__ = "operational_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    zone_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, default=_uuid)
    disaster_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    center_lat: Mapped[float] = mapped_column(Float)
    center_lon: Mapped[float] = mapped_column(Float)
    radius_m: Mapped[float] = mapped_column(Float, default=200.0)
    incident_ids: Mapped[list] = mapped_column(JSON, default=list)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    independent_source_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority: Mapped[str] = mapped_column(String(16), default="UNRATED", index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class PriorityScore(Base):
    """SYSTEM — versioned history of priority decisions."""

    __tablename__ = "priority_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(32), ForeignKey("incidents.incident_id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    level: Mapped[str] = mapped_column(String(16))
    reasons: Mapped[dict] = mapped_column(JSON, default=dict)
    rule_version: Mapped[str] = mapped_column(String(64))
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Recommendation(Base):
    """SYSTEM — explainable resource suggestions."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(32), ForeignKey("incidents.incident_id"), index=True)
    resources: Mapped[list] = mapped_column(JSON, default=list)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    rule_version: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="SUGGESTED")  # SUGGESTED|ACCEPTED|REJECTED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FieldUpdate(Base):
    """HUMAN — responder verification/status updates."""

    __tablename__ = "field_updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(32), ForeignKey("incidents.incident_id"), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    update_type: Mapped[str] = mapped_column(String(32))  # VERIFY|VICTIM_COUNT|ACCESS|MEDICAL|RESCUED|FALSE|NOTE
    values: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    sync_state: Mapped[str] = mapped_column(String(32), default="SYNCED")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(32), default="OPERATOR")  # ADMIN|OPERATOR|COMMANDER|FIELD_RESPONDER|AUDITOR
    display_name: Mapped[str] = mapped_column(String(100), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    target_type: Mapped[str] = mapped_column(String(32))
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    previous_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class JobQueue(Base):
    """DB-backed async job queue (AD-003 — no Kafka/RabbitMQ)."""

    __tablename__ = "job_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)  # LLM_ENRICH
    payload_id: Mapped[str] = mapped_column(String(64), index=True)  # event_id
    status: Mapped[str] = mapped_column(String(32), default="QUEUED", index=True)  # QUEUED|RUNNING|DONE|FAILED
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)