"""Simulation API — deterministic replay + adversarial injection (docs/API.md)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.deps import require_role
from app.database import get_db
from app.llm.gateway import LLM_STATE, set_sim_outage
from app.schemas import DisasterIn, InjectIn, LlmToggleIn, NetworkIn, ScenarioStartIn
from app.simulation.engine import SIM_STATE, inject_pack, start_scenario, step
from app.models import AuditLog, Disaster, User
from app.simulation.scenarios import SIM_DISTRICT

router = APIRouter()


@router.post("/disaster")
def activate_disaster(
    body: DisasterIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "COMMANDER")),
) -> dict:
    disaster = Disaster(
        name=body.name,
        type=body.type,
        affected_geography=body.affected_geography,
        operating_mode=body.operating_mode,
    )
    db.add(disaster)
    db.commit()
    db.refresh(disaster)
    return {"disaster_id": disaster.disaster_id, "mode": disaster.operating_mode}


@router.post("/scenario/start")
def scenario_start(
    body: ScenarioStartIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "COMMANDER")),
) -> dict:
    try:
        return start_scenario(db, body.scenario_id, body.seed)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": str(exc)})


@router.post("/reset")
def sim_reset(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "COMMANDER"))) -> dict:
    """Fresh demo state: wipe operational tables, keep users + rule/model versions + disasters."""
    from app.queue.service import start_worker, stop_worker

    stop_worker()  # no concurrent worker connections → no lock conflict with TRUNCATE
    try:
        db.execute(text("TRUNCATE field_updates, recommendations, priority_scores, evidence, incidents, "
                        "operational_zones, events, job_queue RESTART IDENTITY CASCADE"))
        db.commit()
    finally:
        start_worker()
    SIM_STATE["scenario_id"] = None
    SIM_STATE["phase"] = None
    return {"message": "operational state reset — fresh demo ready"}


@router.post("/scenario/step")
def scenario_step(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN", "COMMANDER"))) -> dict:
    if SIM_STATE["scenario_id"] is None:
        raise HTTPException(status_code=409, detail={"code": "CONFLICT", "message": "No scenario started"})
    return step(db)


@router.post("/inject")
def inject(
    body: InjectIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "COMMANDER")),
) -> dict:
    if SIM_STATE["scenario_id"] is None:
        raise HTTPException(status_code=409, detail={"code": "CONFLICT", "message": "No scenario started"})
    try:
        return inject_pack(db, body.kind)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": str(exc)})


@router.post("/network")
def set_network(
    body: NetworkIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("ADMIN", "COMMANDER")),
) -> dict:
    disaster = db.query(Disaster).order_by(Disaster.id.desc()).first()
    if disaster is None:
        raise HTTPException(status_code=409, detail={"code": "CONFLICT", "message": "No disaster active"})
    disaster.operating_mode = body.mode
    db.add(AuditLog(
        user_id=user.id,
        action="NETWORK_MODE",
        target_type="DISASTER",
        target_id=disaster.disaster_id,
        previous_value=None,
        new_value={"mode": body.mode},
        reason=f"connectivity set to {body.mode}",
    ))
    db.commit()
    return {"connectivity_mode": disaster.operating_mode}


@router.post("/llm")
def toggle_llm(
    body: LlmToggleIn,
    _: User = Depends(require_role("ADMIN", "COMMANDER")),
) -> dict:
    """Adversarial demo: kill/restore the LLM layer. Rules keep working; status flips DEGRADED."""
    set_sim_outage(not body.enabled)
    state = {k: v for k, v in LLM_STATE.items() if k != "sim_outage"}
    return {"llm_enabled": body.enabled, "state": state}


@router.get("/state")
def sim_state(_: User = Depends(require_role("ADMIN", "COMMANDER"))) -> dict:
    return SIM_STATE