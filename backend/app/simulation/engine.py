"""Simulation engine — deterministic replay (NFR-097) + adversarial injection.

Reuses the real pipeline (process_event) — the simulator never shortcuts
extraction/clustering/priority. A sim run wipes operational data for a clean,
reproducible demo state.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.fusion.service import process_event
from app.models import (
    Disaster,
    Event,
    Evidence,
    FieldUpdate,
    Incident,
    JobQueue,
    OperationalZone,
    PriorityScore,
    Recommendation,
)
from app.simulation.scenarios import SIM_DISTRICT, build_adversarial_packs, build_killer_scenario

logger = logging.getLogger("netra.sim")

SIM_STATE = {"scenario_id": None, "seed": None, "next_batch": 0, "batches": 0, "disaster_id": None, "t0": None}


def _live_t0() -> str:
    """Scenario events replay as 'live' (recent) instead of a fixed stale epoch,
    so the freshness component of the Rescue Priority Score behaves in demos."""
    return (datetime.now(timezone.utc) - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _wipe_operational(db: Session) -> None:
    for model in (JobQueue, FieldUpdate, Recommendation, PriorityScore, Evidence, Incident, OperationalZone, Event):
        db.query(model).delete()
    db.query(Disaster).delete()
    db.commit()


def _make_event(db: Session, disaster_id: str, ev: dict) -> None:
    event = Event(
        disaster_id=disaster_id,
        source_type=ev["source_type"],
        source_timestamp=datetime.fromisoformat(ev["source_timestamp"]),
        text=ev["text"],
        source_identifier=ev["source_identifier"],
        location_lat=ev["lat"],
        location_lon=ev["lon"],
        location_accuracy_m=ev["accuracy_m"],
        processing_status="RECEIVED",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    process_event(db, event)
    from app.queue.service import enqueue
    enqueue(db, "LLM_ENRICH", event.event_id)


def start_scenario(db: Session, scenario_id: str, seed: int | None = None) -> dict:
    seed = seed or settings.simulation_seed
    _wipe_operational(db)

    disaster = Disaster(
        name=SIM_DISTRICT["name"],
        type=SIM_DISTRICT["type"],
        affected_geography=SIM_DISTRICT.get("center"),
        operating_mode=SIM_DISTRICT["mode"],
    )
    db.add(disaster)
    db.commit()
    db.refresh(disaster)

    if scenario_id == "killer":
        t0 = _live_t0()
        batches = build_killer_scenario(seed=seed, t0=t0)
    else:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    SIM_STATE.update({
        "scenario_id": scenario_id, "seed": seed, "next_batch": 0,
        "batches": len(batches), "disaster_id": disaster.disaster_id, "t0": t0,
    })

    first = batches[0]
    for ev in first.events:
        _make_event(db, disaster.disaster_id, ev)
    SIM_STATE["next_batch"] = 1
    return _state()

def step(db: Session) -> dict:
    idx = SIM_STATE["next_batch"]
    if idx >= SIM_STATE["batches"]:
        return {"done": True, **_state()}
    batches = build_killer_scenario(seed=SIM_STATE["seed"], t0=SIM_STATE.get("t0") or _live_t0())
    batch = batches[idx]
    for ev in batch.events:
        _make_event(db, SIM_STATE["disaster_id"], ev)
    SIM_STATE["next_batch"] = idx + 1
    return {"done": False, "batch": batch.label, "events": len(batch.events), **_state()}


def inject_pack(db: Session, pack: str) -> dict:
    packs = build_adversarial_packs(seed=SIM_STATE["seed"] or settings.simulation_seed,
                                    t0=SIM_STATE.get("t0") or _live_t0())
    if pack not in packs:
        raise ValueError(f"Unknown pack: {pack} (choose from {list(packs)})")
    batch = packs[pack]
    for ev in batch.events:
        _make_event(db, SIM_STATE["disaster_id"], ev)
    return {"pack": pack, "events": len(batch.events)}


def _state() -> dict:
    return {
        "scenario_id": SIM_STATE["scenario_id"],
        "seed": SIM_STATE["seed"],
        "next_batch": SIM_STATE["next_batch"],
        "batches": SIM_STATE["batches"],
        "disaster_id": SIM_STATE["disaster_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }