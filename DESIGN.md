# Store Intelligence Design

## Architecture Overview

This system is organized as a practical four-stage pipeline: detection, event streaming, analytics ingestion, and operator visibility. Raw CCTV footage is processed by the detection layer, which identifies people, assigns track IDs, and emits structured behavior events. Those events are written to JSONL so they can be replayed, inspected, and validated outside the vision loop. A FastAPI service ingests the event stream, stores normalized records in PostgreSQL, and computes store-level metrics such as unique visitors, queue depth, abandonment rate, and funnel drop-off. A live dashboard reads from the API and provides an operator-facing view of those metrics as they update.

The design intentionally separates the vision pipeline from the analytics API. That gives us a simple boundary for debugging and submission validation: if the detector emits bad events, the problem is visible in `pipeline/output/events.jsonl`; if the API behaves incorrectly, the same event stream can be replayed repeatedly without rerunning video inference. That separation also helps with idempotency, because the API treats `event_id` as the deduplication key and can safely ingest the same payload more than once.

The detection layer is built around YOLOv8n plus ByteTrack-style tracking. Entry and exit events are derived from line crossing on the entry camera. Zone visits are inferred from bounding-box centers entering predefined regions on the main-floor cameras. Billing activity is derived from detections inside the billing region. Staff exclusion is currently handled with contextual heuristics rather than a dedicated classifier, which keeps the implementation lightweight while still making the `is_staff` decision explicit in every emitted event.

## Data Flow

The internal event schema is the API-facing canonical format. Each event includes a globally unique `event_id`, the `store_id`, the `camera_id`, a `visitor_id`, event type, timestamp, optional zone data, dwell duration, staff flag, confidence, and metadata such as queue depth and session sequence. This schema supports replay, ingestion deduplication, and metric computation without depending on the original video.

For submission packaging, the repository also exports `event_log.jsonl`, which reformats the internal event stream into the organizer’s sample JSONL style. That export exists because the challenge resources include a flatter example schema with different field names for entry, zone, and queue events. Rather than changing the API’s internal contract, the repository now preserves the internal schema for application logic and generates a submission-ready file at the edge.

## Production Readiness

The API is containerized with Docker Compose and exposes health, ingest, metrics, funnel, heatmap, and anomaly endpoints. Ingestion is idempotent by `event_id`. Tests cover both happy paths and challenge edge cases such as empty store periods, staff-only clips, zero conversion, batch ingest, dwell tracking, stale feeds, and re-entry handling. Structured logging is implemented to support operational visibility during ingestion and health checks. The health endpoint also reports feed freshness so operators can quickly tell whether the system is live or stale.

## AI-Assisted Decisions

AI tools shaped several important decisions, but not all suggestions were accepted as-is.

First, AI suggested heavier detector options such as RT-DETR and full Re-ID pipelines such as DeepSORT plus appearance embeddings. After comparing that advice against the take-home constraints, I chose YOLOv8n with a simpler tracker because it offered a better implementation-speed-to-runtime-performance ratio for a small end-to-end system. The trade-off is lower robustness under occlusion and cross-camera identity ambiguity, but it let the full stack ship in time.

Second, AI recommended making the event stream the central system boundary instead of trying to couple detection directly to database writes. I agreed with that suggestion. JSONL replay turned out to be one of the most useful engineering choices in the repository because it makes debugging, validation, and repeatable ingestion much easier.

Third, AI suggested a more ambitious learned staff classifier and a more complex cross-camera re-identification strategy. I overrode both for this submission. The current rule-based staff classifier is weaker than a dedicated model, but it is easy to explain, fast to run, and good enough to keep staff handling visible in the pipeline. I documented that limitation directly instead of hiding it behind vague claims.

## Known Gaps

The current pipeline still has clear limitations. Zone names are inferred from hard-coded regions rather than store-specific machine-readable layouts. Billing abandonment is only partially modeled in the internal stream. Cross-camera identity continuity is heuristic rather than appearance-based. The submission export maps internal events into the organizer sample format, but some sample-only fields such as demographics and group metadata are emitted as `null` because the current detector does not infer them. Even with those gaps, the repository now contains the complete set of deliverables and a reproducible path from video to event stream to analytics API.

