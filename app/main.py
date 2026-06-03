from fastapi import FastAPI
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from typing import List, Optional
from datetime import datetime, timedelta
import time

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

from app.logging import logger


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
def health(db: Session = Depends(get_db)):
    """Health check with database connectivity and stale feed detection."""
    
    try:
        # Check database connectivity
        db.query(Event).limit(1).all()
        db_status = "connected"
    except Exception as e:
        logger.log_database_error(endpoint="/health")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "disconnected",
            "error": str(e)
        }

    # Get last event timestamp to detect stale feed
    last_event = (
        db.query(Event.timestamp)
        .order_by(Event.timestamp.desc())
        .first()
    )

    last_event_timestamp = None
    stale_threshold_seconds = 300  # 5 minutes

    if last_event and last_event[0]:
        last_event_timestamp = last_event[0].isoformat()
        time_since_last_event = (
            datetime.utcnow() - last_event[0].replace(tzinfo=None)
        ).total_seconds()

        if time_since_last_event > stale_threshold_seconds:
            logger.log_stale_feed(
                store_id="STORE_BLR_002",
                last_event_timestamp=last_event_timestamp,
                stale_threshold_seconds=stale_threshold_seconds
            )

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "last_event_timestamp": last_event_timestamp,
        "stale_threshold_seconds": stale_threshold_seconds
    }


# -----------------------------
# Event Ingest
# -----------------------------
@app.post("/events/ingest")
def ingest_events(
    events: List[EventCreate],
    db: Session = Depends(get_db)
):
    """Ingest behavioral events with deduplication and structured logging."""
    
    start_time = time.time()
    ingested = 0
    duplicates = 0
    failed = 0
    store_id = "UNKNOWN"

    if events and len(events) > 0:
        store_id = events[0].store_id

    for event in events:
        try:
            # Check for duplicates (idempotent ingestion)
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

        except Exception as e:
            failed += 1

    try:
        db.commit()

    except SQLAlchemyError as e:
        db.rollback()
        
        logger.log_database_error(
            store_id=store_id,
            endpoint="/events/ingest"
        )

        raise HTTPException(
            status_code=503,
            detail={
                "message":
                "Database unavailable"
            }
        )

    # Log successful ingestion with structured logging
    latency_ms = (time.time() - start_time) * 1000
    logger.log_event_ingest(
        event_count=len(events),
        ingested=ingested,
        duplicates=duplicates,
        failed=failed,
        latency_ms=latency_ms,
        status="success",
        store_id=store_id
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