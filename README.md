# Store Intelligence

End-to-end retail analytics pipeline that turns CCTV detections into structured events, real-time API metrics, and a live dashboard.

## Submission Deliverables

This repository now includes the required submission artifacts at the repo root:

- `README.md`
- `DESIGN.md`
- `CHOICES.md`
- `event_log.jsonl`

The internal pipeline writes canonical API events to `pipeline/output/events.jsonl`. The root `event_log.jsonl` is the submission-ready JSONL export aligned to the provided sample event schema.

## Repository Layout

```text
app/            FastAPI app, schemas, analytics, persistence
pipeline/       Detection, tracking, event emission, submission export
dashboard/      Live dashboard
resources/      Challenge assets and sample files
tests/          API and edge-case coverage
event_log.jsonl Submission-ready event log
```

## Quick Start

Run the project in the acceptance-gate flow:

```bash
docker compose up --build
python pipeline/detect.py
python pipeline/export_submission_events.py
python pipeline/replay_events.py
pytest --cov=app
```

What each step does:

1. `docker compose up --build` starts PostgreSQL and the FastAPI service.
2. `python pipeline/detect.py` processes local video clips and emits internal events to `pipeline/output/events.jsonl`.
3. `python pipeline/export_submission_events.py` converts the internal event stream into the submission artifact `event_log.jsonl`.
4. `python pipeline/replay_events.py` replays internal events into `POST /events/ingest`.
5. `pytest --cov=app` runs the API and edge-case tests.

## API Endpoints

- `GET /health`
- `POST /events/ingest`
- `GET /stores/{store_id}/metrics`
- `GET /stores/{store_id}/funnel`
- `GET /stores/{store_id}/heatmap`
- `GET /stores/{store_id}/anomalies`

Interactive API docs are available at `http://localhost:8000/docs`.

## Event Files

- `pipeline/output/events.jsonl`: internal analytics event stream used by the API.
- `event_log.jsonl`: submission-ready JSONL export in the organizer sample style.
- `resources/sample_eventsbe42122.jsonl`: organizer-provided sample schema reference.

To regenerate the submission file:

```bash
python pipeline/export_submission_events.py
```

To validate that the export is valid JSONL:

```bash
python pipeline/export_submission_events.py --validate-only
```

## Dashboard

Run the live dashboard with:

```bash
python dashboard/live_dashboard.py
```

This demonstrates that the event pipeline and API are connected by showing metrics that refresh as events are ingested.

## Notes on the Current Build

- Staff exclusion is handled via rule-based heuristics in `pipeline/staff_classifier.py`.
- Re-entry is supported through the tracker state in `pipeline/tracker.py`.
- The submission export preserves all internal detections and writes missing sample-only fields as `null` when the current pipeline does not infer them.

## Documentation

- `DESIGN.md` explains the architecture and includes the required `AI-Assisted Decisions` section.
- `CHOICES.md` documents model, schema, and API decisions with AI suggestions and final trade-offs.

