from fastapi import FastAPI
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from typing import List
from datetime import datetime

from app.db import Base
from app.db import engine
from app.db import get_db

from app.models import Event

from app.schemas import (
    EventCreate,
    MetricsResponse,
    FunnelResponse,
    HeatmapResponse,
    AnomalyResponse,
    HealthResponse
)

from app.analytics import (
    get_store_metrics,
    get_store_funnel,
    get_heatmap,
    get_anomalies
)


# -----------------------------
# Create DB tables
# -----------------------------
Base.metadata.create_all(bind=engine)


# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(
    title="Store Intelligence API",
    version="1.0.0"
)


# -----------------------------
# Root
# -----------------------------
@app.get("/")
def root():
    return {
        "message": "Store Intelligence API Running"
    }


# -----------------------------
# Health
# -----------------------------
@app.get(
    "/health",
    response_model=HealthResponse
)
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"
    }


# -----------------------------
# Event Ingest
# -----------------------------
@app.post("/events/ingest")
def ingest_events(
    events: List[EventCreate],
    db: Session = Depends(get_db)
):
    ingested = 0
    duplicates = 0
    failed = 0

    for event in events:
        try:
            existing = (
                db.query(Event)
                .filter(
                    Event.event_id == event.event_id
                )
                .first()
            )

            if existing:
                duplicates += 1
                continue

            db_event = Event(
                event_id=event.event_id,
                store_id=event.store_id,
                camera_id=event.camera_id,
                visitor_id=event.visitor_id,
                event_type=event.event_type,
                timestamp=event.timestamp,
                zone_id=event.zone_id,
                dwell_ms=event.dwell_ms,
                is_staff=event.is_staff,
                confidence=event.confidence,
                metadata_json=(
                    event.metadata.model_dump()
                    if event.metadata
                    else {}
                )
            )

            db.add(db_event)
            ingested += 1

        except Exception:
            failed += 1

    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=503,
            detail={
                "message":
                "Database unavailable"
            }
        )

    return {
        "ingested": ingested,
        "duplicates": duplicates,
        "failed": failed
    }


# -----------------------------
# Metrics
# -----------------------------
@app.get(
    "/stores/{store_id}/metrics",
    response_model=MetricsResponse
)
def metrics(
    store_id: str,
    db: Session = Depends(get_db)
):
    return get_store_metrics(
        db,
        store_id
    )


# -----------------------------
# Funnel
# -----------------------------
@app.get(
    "/stores/{store_id}/funnel",
    response_model=FunnelResponse
)
def funnel(
    store_id: str,
    db: Session = Depends(get_db)
):
    return get_store_funnel(
        db,
        store_id
    )


# -----------------------------
# Heatmap
# -----------------------------
@app.get(
    "/stores/{store_id}/heatmap",
    response_model=HeatmapResponse
)
def heatmap(
    store_id: str,
    db: Session = Depends(get_db)
):
    return get_heatmap(
        db,
        store_id
    )


# -----------------------------
# Anomalies
# -----------------------------
@app.get(
    "/stores/{store_id}/anomalies",
    response_model=List[AnomalyResponse]
)
def anomalies(
    store_id: str,
    db: Session = Depends(get_db)
):
    return get_anomalies(
        db,
        store_id
    )