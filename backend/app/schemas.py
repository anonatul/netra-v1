"""Pydantic contracts for NETRA APIs — mirrors docs/API.md."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

SourceType = Literal["SMS", "ERSS", "ELS", "WHATSAPP", "FIELD", "MANUAL", "SIMULATED"]
DisasterType = Literal["FLOOD", "EARTHQUAKE", "CYCLONE", "OTHER"]
PriorityLevel = Literal["P1", "P2", "P3", "P4", "UNRATED"]
ConnectivityMode = Literal["NORMAL", "DEGRADED", "SEVERELY_DEGRADED", "CELLULAR_UNAVAILABLE"]


# ---------- Auth ----------
class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    display_name: str

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Events ----------
class LocationIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    accuracy_m: float | None = Field(default=None, ge=0)


class EventIn(BaseModel):
    source_type: SourceType
    source_timestamp: datetime
    text: str | None = None
    location: LocationIn | None = None
    source_identifier: str | None = Field(default=None, max_length=128)
    idempotency_key: str | None = Field(default=None, max_length=128)
    metadata: dict | None = None

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            return None
        return v


class EventOut(BaseModel):
    event_id: str
    status: str
    incident_id: str | None = None


# ---------- Incidents ----------
class PriorityOverrideIn(BaseModel):
    priority: PriorityLevel
    reason: str = Field(min_length=1, max_length=500)


class FieldUpdateIn(BaseModel):
    update_type: Literal["VERIFY", "VICTIM_COUNT", "ACCESS", "MEDICAL", "RESCUED", "FALSE", "NOTE"]
    values: dict = Field(default_factory=dict)
    notes: str | None = None


class RecommendationDecisionIn(BaseModel):
    status: Literal["ACCEPTED", "REJECTED"]


# ---------- Simulation ----------
class DisasterIn(BaseModel):
    name: str
    type: DisasterType
    affected_geography: dict | None = None
    operating_mode: ConnectivityMode = "NORMAL"


class ScenarioStartIn(BaseModel):
    scenario_id: str
    seed: int = 42


class InjectIn(BaseModel):
    count: int = Field(gt=0, le=5000)
    kind: Literal["fake_sos", "duplicates", "stale", "medical"] = "medical"


class NetworkIn(BaseModel):
    mode: ConnectivityMode


class LlmToggleIn(BaseModel):
    enabled: bool