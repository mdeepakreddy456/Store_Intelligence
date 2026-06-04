import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


INPUT_FILE = Path("pipeline/output/events.jsonl")
OUTPUT_FILE = Path("event_log.jsonl")


def parse_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.fromisoformat(value)


def format_timestamp(value: str) -> str:
    dt = parse_timestamp(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")


def track_id_from_visitor(visitor_id: str):
    if not visitor_id:
        return None
    suffix = visitor_id.split("_")[-1]
    return int(suffix) if suffix.isdigit() else None


def infer_zone_type(zone_id: str) -> str:
    if not zone_id:
        return "UNKNOWN"
    if "BILLING" in zone_id:
        return "BILLING"
    if "DISPLAY" in zone_id:
        return "DISPLAY"
    return "SHELF"


def infer_revenue_zone(zone_id: str) -> str:
    return "No" if not zone_id or "ENTRY" in zone_id else "Yes"


def export_entry_like(event: dict, event_type: str) -> dict:
    return {
        "event_type": event_type,
        "id_token": event["visitor_id"],
        "store_code": event["store_id"],
        "camera_id": event["camera_id"],
        "event_timestamp": format_timestamp(event["timestamp"]),
        "is_staff": event.get("is_staff", False),
        "gender_pred": None,
        "age_pred": None,
        "age_bucket": None,
        "is_face_hidden": None,
        "group_id": None,
        "group_size": None,
    }


def export_zone_like(event: dict, event_type: str) -> dict:
    zone_id = event.get("zone_id")
    payload = {
        "event_type": event_type,
        "track_id": track_id_from_visitor(event["visitor_id"]),
        "store_id": event["store_id"],
        "camera_id": event["camera_id"],
        "zone_id": zone_id,
        "zone_name": zone_id,
        "zone_type": infer_zone_type(zone_id),
        "is_revenue_zone": infer_revenue_zone(zone_id),
        "event_time": format_timestamp(event["timestamp"]),
        "zone_hotspot_x": None,
        "zone_hotspot_y": None,
        "gender": None,
        "age": None,
        "age_bucket": None,
    }
    if event_type == "zone_dwell":
        payload["dwell_ms"] = event.get("dwell_ms", 0)
    return payload


def export_queue_like(event: dict) -> dict:
    metadata = event.get("metadata") or {}
    zone_id = event.get("zone_id") or "BILLING_QUEUE"
    return {
        "queue_event_id": event["event_id"],
        "event_type": "queue_joined",
        "track_id": track_id_from_visitor(event["visitor_id"]),
        "store_id": event["store_id"],
        "camera_id": event["camera_id"],
        "zone_id": zone_id,
        "zone_name": "Billing Counter Queue",
        "zone_type": "BILLING",
        "is_revenue_zone": "Yes",
        "queue_join_ts": format_timestamp(event["timestamp"]),
        "queue_served_ts": None,
        "queue_exit_ts": None,
        "wait_seconds": None,
        "queue_position_at_join": metadata.get("queue_depth"),
        "abandoned": False,
        "zone_hotspot_x": None,
        "zone_hotspot_y": None,
        "gender": None,
        "age": None,
        "age_bucket": None,
    }


def to_submission_event(event: dict) -> dict:
    event_type = event["event_type"]

    if event_type == "ENTRY":
        return export_entry_like(event, "entry")
    if event_type == "EXIT":
        return export_entry_like(event, "exit")
    if event_type == "REENTRY":
        return export_entry_like(event, "reentry")
    if event_type == "ZONE_ENTER":
        return export_zone_like(event, "zone_entered")
    if event_type == "ZONE_DWELL":
        return export_zone_like(event, "zone_dwell")
    if event_type == "ZONE_EXIT":
        return export_zone_like(event, "zone_exited")
    if event_type == "BILLING_QUEUE_JOIN":
        return export_queue_like(event)

    raise ValueError(f"Unsupported internal event type: {event_type}")


def export_events(input_file: Path, output_file: Path) -> int:
    count = 0
    with input_file.open("r", encoding="utf-8") as source, output_file.open(
        "w", encoding="utf-8"
    ) as target:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                exported = to_submission_event(event)
            except Exception as exc:
                raise ValueError(
                    f"Failed to export line {line_number}: {exc}"
                ) from exc
            target.write(json.dumps(exported) + "\n")
            count += 1
    return count


def validate_jsonl(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {exc}"
                ) from exc
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    if args.validate_only:
        count = validate_jsonl(OUTPUT_FILE)
        print(f"Validated {count} JSONL events in {OUTPUT_FILE}")
        return

    count = export_events(INPUT_FILE, OUTPUT_FILE)
    validated = validate_jsonl(OUTPUT_FILE)
    print(f"Exported {count} events to {OUTPUT_FILE}")
    print(f"Validated {validated} JSONL events in {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
