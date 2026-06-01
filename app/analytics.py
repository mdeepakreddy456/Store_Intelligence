from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Event
from app.models import Session as VisitorSession
from app.models import Anomaly


# ---------------------------------
# Metrics
# ---------------------------------
def get_store_metrics(
    db: Session,
    store_id: str
):

    unique_visitors = (
        db.query(
            func.count(
                func.distinct(Event.visitor_id)
            )
        )
        .filter(
            Event.store_id == store_id,
            Event.is_staff == False
        )
        .scalar()
    ) or 0

    converted_sessions = (
        db.query(
            func.count(VisitorSession.id)
        )
        .filter(
            VisitorSession.store_id == store_id,
            VisitorSession.converted == True
        )
        .scalar()
    ) or 0

    total_sessions = (
        db.query(
            func.count(VisitorSession.id)
        )
        .filter(
            VisitorSession.store_id == store_id
        )
        .scalar()
    ) or 0

    conversion_rate = (
        converted_sessions / total_sessions
        if total_sessions > 0
        else 0
    )

    dwell_rows = (
        db.query(
            Event.zone_id,
            func.avg(Event.dwell_ms)
        )
        .filter(
            Event.store_id == store_id,
            Event.zone_id.isnot(None),
            Event.is_staff == False
        )
        .group_by(Event.zone_id)
        .all()
    )

    avg_dwell_per_zone = {
        zone: float(avg)
        for zone, avg in dwell_rows
    }

    queue_depth = (
        db.query(func.count(Event.id))
        .filter(
            Event.store_id == store_id,
            Event.event_type ==
            "BILLING_QUEUE_JOIN"
        )
        .scalar()
    ) or 0

    abandoned = (
        db.query(func.count(Event.id))
        .filter(
            Event.store_id == store_id,
            Event.event_type ==
            "BILLING_QUEUE_ABANDON"
        )
        .scalar()
    ) or 0

    abandonment_rate = (
        abandoned / queue_depth
        if queue_depth > 0
        else 0
    )

    return {
        "unique_visitors":
            unique_visitors,

        "conversion_rate":
            round(conversion_rate, 2),

        "avg_dwell_per_zone":
            avg_dwell_per_zone,

        "queue_depth":
            queue_depth,

        "abandonment_rate":
            round(abandonment_rate, 2)
    }


# ---------------------------------
# Funnel
# ---------------------------------
def get_store_funnel(
    db: Session,
    store_id: str
):

    entry_count = (
        db.query(
            func.count(
                func.distinct(
                    Event.visitor_id
                )
            )
        )
        .filter(
            Event.store_id == store_id,
            Event.event_type == "ENTRY",
            Event.is_staff == False
        )
        .scalar()
    ) or 0

    zone_visit_count = (
        db.query(
            func.count(
                func.distinct(
                    Event.visitor_id
                )
            )
        )
        .filter(
            Event.store_id == store_id,
            Event.event_type ==
            "ZONE_ENTER",
            Event.is_staff == False
        )
        .scalar()
    ) or 0

    billing_queue_count = (
        db.query(
            func.count(
                func.distinct(
                    Event.visitor_id
                )
            )
        )
        .filter(
            Event.store_id == store_id,
            Event.event_type ==
            "BILLING_QUEUE_JOIN",
            Event.is_staff == False
        )
        .scalar()
    ) or 0

    purchase_count = (
        db.query(
            func.count(VisitorSession.id)
        )
        .filter(
            VisitorSession.store_id ==
            store_id,
            VisitorSession.converted ==
            True
        )
        .scalar()
    ) or 0

    dropoff_percentage = {
        "entry_to_zone":
            round(
                (
                    (
                        entry_count -
                        zone_visit_count
                    ) / entry_count
                ) * 100,
                2
            )
            if entry_count > 0
            else 0,

        "zone_to_billing":
            round(
                (
                    (
                        zone_visit_count -
                        billing_queue_count
                    ) / zone_visit_count
                ) * 100,
                2
            )
            if zone_visit_count > 0
            else 0,

        "billing_to_purchase":
            round(
                (
                    (
                        billing_queue_count -
                        purchase_count
                    ) / billing_queue_count
                ) * 100,
                2
            )
            if billing_queue_count > 0
            else 0
    }

    return {
        "entry_count":
            entry_count,

        "zone_visit_count":
            zone_visit_count,

        "billing_queue_count":
            billing_queue_count,

        "purchase_count":
            purchase_count,

        "dropoff_percentage":
            dropoff_percentage
    }


# ---------------------------------
# Heatmap
# ---------------------------------
def get_heatmap(
    db: Session,
    store_id: str
):

    rows = (
        db.query(
            Event.zone_id,
            func.count(Event.id),
            func.avg(Event.dwell_ms)
        )
        .filter(
            Event.store_id == store_id,
            Event.zone_id.isnot(None),
            Event.is_staff == False
        )
        .group_by(Event.zone_id)
        .all()
    )

    max_visits = max(
        [row[1] for row in rows],
        default=1
    )

    zones = []

    for zone_id, visits, dwell in rows:

        normalized = (
            visits / max_visits
        ) * 100

        zones.append({
            "zone_id":
                zone_id,

            "visit_frequency":
                visits,

            "avg_dwell_ms":
                float(dwell or 0),

            "normalized_score":
                round(normalized, 2)
        })

    session_count = (
        db.query(
            func.count(
                VisitorSession.id
            )
        )
        .filter(
            VisitorSession.store_id ==
            store_id
        )
        .scalar()
    ) or 0

    confidence = (
        "LOW"
        if session_count < 20
        else "HIGH"
    )

    return {
        "data_confidence":
            confidence,

        "zones":
            zones
    }


# ---------------------------------
# Anomalies
# ---------------------------------
def get_anomalies(
    db: Session,
    store_id: str
):

    anomalies = (
        db.query(Anomaly)
        .filter(
            Anomaly.store_id ==
            store_id
        )
        .all()
    )

    return [
        {
            "anomaly_type":
                a.anomaly_type,

            "severity":
                a.severity,

            "message":
                a.message,

            "suggested_action":
                a.suggested_action
        }
        for a in anomalies
    ]