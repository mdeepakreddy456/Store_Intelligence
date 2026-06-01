import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

OUTPUT_FILE = "pipeline/output/events.jsonl"

# create folder if not exists
Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)


def clear_events_file():
    """
    Clears old events before new run
    """
    open(OUTPUT_FILE, "w").close()


def generate_timestamp():
    """
    UTC timestamp
    """
    return datetime.now(timezone.utc).isoformat()


def build_event(
    store_id,
    camera_id,
    visitor_id,
    event_type,
    confidence,
    zone_id=None,
    dwell_ms=0,
    is_staff=False,
    queue_depth=None,
    sku_zone=None,
    session_seq=1,
):
    """
    Creates event schema
    """

    return {
        "event_id": str(uuid.uuid4()),
        "store_id": store_id,
        "camera_id": camera_id,
        "visitor_id": visitor_id,
        "event_type": event_type,
        "timestamp": generate_timestamp(),
        "zone_id": zone_id,
        "dwell_ms": dwell_ms,
        "is_staff": is_staff,
        "confidence": round(float(confidence), 2),
        "metadata": {
            "queue_depth": queue_depth,
            "sku_zone": sku_zone,
            "session_seq": session_seq,
        },
    }


def emit_event(event):
    """
    Save event to jsonl
    """

    with open(OUTPUT_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

    print(
        f"{event['event_type']} | "
        f"{event['visitor_id']} | "
        f"{event['camera_id']}"
    )