"""DB-backed async job queue (AD-003) + background worker.

One worker thread polls QUEUED jobs; LLM enrichment is off the critical path.
Failures are recorded per job; nothing is silently lost.
"""
import logging
import threading
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import JobQueue

logger = logging.getLogger("netra.queue")

_worker: threading.Thread | None = None
_running = False
_paused = False
POLL_INTERVAL_SECONDS = 1.0


def set_paused(paused: bool) -> None:
    """Pause the worker so maintenance ops (e.g. TRUNCATE) can lock tables."""
    global _paused
    _paused = paused


def is_paused() -> bool:
    return _paused


def enqueue(db: Session, kind: str, payload_id: str) -> None:
    existing = (
        db.query(JobQueue)
        .filter(JobQueue.kind == kind, JobQueue.payload_id == payload_id, JobQueue.status == "QUEUED")
        .first()
    )
    if existing is None:
        db.add(JobQueue(kind=kind, payload_id=payload_id, status="QUEUED"))
        db.commit()


def _claim_next(db: Session) -> JobQueue | None:
    job = (
        db.query(JobQueue)
        .filter(JobQueue.status == "QUEUED")
        .order_by(JobQueue.id.asc())
        .first()
    )
    if job:
        job.status = "RUNNING"
        job.attempts += 1
        db.commit()
    return job


def _run_loop() -> None:
    from app.llm.enrich import enrich_event

    while _running:
        db: Session = SessionLocal()
        try:
            if is_paused():
                time.sleep(POLL_INTERVAL_SECONDS)
                continue
            job = _claim_next(db)
            if job is None:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue
            try:
                if job.kind == "LLM_ENRICH":
                    enrich_event(db, job.payload_id)
                job.status = "DONE"
                job.error = None
            except Exception as exc:  # never let the worker die
                logger.error("job %s failed: %s", job.id, exc)
                job.status = "FAILED"
                job.error = str(exc)[:500]
            job.processed_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as exc:
            logger.error("queue loop error: %s", exc)
            time.sleep(POLL_INTERVAL_SECONDS)
        finally:
            db.close()


def start_worker() -> None:
    global _worker, _running
    if _worker is not None and _worker.is_alive():
        return
    _running = True
    _worker = threading.Thread(target=_run_loop, name="netra-queue-worker", daemon=True)
    _worker.start()
    logger.info("queue worker started")


def stop_worker() -> None:
    global _running, _worker
    _running = False
    if _worker is not None:
        _worker.join(timeout=5)
        _worker = None