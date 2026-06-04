# Engineering Choices

## 1. Detection Model Choice

### Options Considered

- YOLOv8n
- RT-DETR
- MediaPipe person detection
- Traditional OpenCV background and contour methods

### What AI Suggested

AI recommendations consistently pointed toward YOLOv8 or RT-DETR as the most practical modern object detectors for a take-home system. RT-DETR was described as a stronger accuracy candidate, while YOLOv8 was suggested as the easier path for rapid integration, better ecosystem support, and simpler local experimentation.

### What I Chose and Why

I chose `YOLOv8n` for the current implementation. The main reason was not “best absolute accuracy”; it was the combination of speed, low setup friction, and an implementation path that let the detection layer, event stream, API, and tests all land in one repository quickly. This submission is evaluated end to end, so a detector that is slightly less accurate but easy to integrate can be the right choice if it enables a complete system.

I paired it with tracker state and line/zone rules rather than a more expensive appearance-based Re-ID model. That keeps inference lightweight and easier to explain during follow-up questions.

### Trade-Offs

- Pros: fast local inference, easy integration, small model, familiar tooling
- Cons: weaker under partial occlusion, limited cross-camera identity quality, more false negatives than heavier models

## 2. Event Schema Design

### Options Considered

- Write detections directly to the database
- Use one internal canonical event schema only
- Emit organizer-style JSONL records directly from the detector
- Keep an internal schema and export a submission schema separately

### What AI Suggested

AI strongly favored an event-driven design with replayable JSONL because it decouples vision inference from analytics, improves debuggability, and supports idempotent ingestion. AI also suggested that keeping the event stream as the contract boundary would make testing and production reasoning easier.

### What I Chose and Why

I chose a canonical internal JSONL schema for the application and a second export step for the submission event log. The internal schema is the one used by the API and includes `event_id`, `store_id`, `camera_id`, `visitor_id`, `event_type`, `timestamp`, `zone_id`, `dwell_ms`, `is_staff`, `confidence`, and metadata. That shape fits the API code naturally and keeps ingestion clean.

However, the challenge resources include a sample JSONL file whose field names differ from the internal schema. Instead of rewriting the whole API around the flatter sample format, I added a submission export that converts the internal event stream into `event_log.jsonl`. This keeps the app coherent while still satisfying the deliverable requirement.

### Trade-Offs

- Pros: replayable, debuggable, idempotent, API-friendly, easier testing
- Cons: two schemas must be maintained, export step adds one more artifact to validate

## 3. API Architecture Choice

### Options Considered

- Flask + SQLAlchemy
- FastAPI + PostgreSQL
- FastAPI + SQLite
- Node/Express + PostgreSQL

### What AI Suggested

AI recommended FastAPI because it provides request validation, automatic OpenAPI docs, and a strong fit for a JSON event ingestion API. It also suggested PostgreSQL for a more production-oriented storage layer and better future support for analytics queries.

### What I Chose and Why

I chose FastAPI with PostgreSQL for the main application. FastAPI helped reduce boilerplate and made it straightforward to define schemas, expose `GET` and `POST` routes, and keep the contract explicit. PostgreSQL is heavier than SQLite for a take-home, but it better matches the “production-aware” requirement in the challenge and works cleanly with Docker Compose.

I also kept the ingestion endpoint idempotent by checking `event_id` before insert, because that behavior is explicitly called out in the challenge scoring rubric. The health endpoint includes feed freshness context so the service is useful operationally rather than just technically alive.

### Trade-Offs

- Pros: strong validation, generated docs, familiar SQL model, production-friendly deployment
- Cons: more setup overhead than SQLite, slightly more complexity in local testing

## Reflection on AI Guidance

The most useful AI suggestions were architectural rather than line-by-line code generation. AI helped compare detector families, reinforced the value of a replayable event stream, and suggested more ambitious staff and Re-ID approaches. I agreed with the event-driven architecture recommendation, partially agreed with the model-selection guidance, and intentionally overrode the heavier suggestions when they would have added complexity without improving the end-to-end submission enough. That balance is important here: the goal was not to accept every AI suggestion, but to use the advice selectively and document why.

