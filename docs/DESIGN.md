# DESIGN.md

# Store Intelligence System Design

## 1. Architecture Overview

This project implements an end-to-end Store Intelligence pipeline that converts raw CCTV footage into real-time retail analytics. The system processes video feeds, detects customer behaviour, generates structured behavioural events, ingests them into an analytics API, and exposes live metrics for operational visibility.

The architecture consists of four layers:

1. Detection Layer
2. Event Streaming Layer
3. Intelligence API Layer
4. Live Dashboard Layer

The detection layer uses computer vision to identify customers and infer movement patterns. These detections are transformed into structured JSON events and written into an event stream (`events.jsonl`). The Intelligence API consumes these events and computes business metrics such as conversion rate, queue depth, funnel drop-off, and visitor counts. Finally, a dashboard displays metrics updating in near real-time.

The overall system follows:

Raw CCTV → Detection → Event Stream → API → Analytics Dashboard

---

## 2. Detection Pipeline

The detection pipeline uses YOLOv8n for person detection and ByteTrack for tracking identities across frames.

### Why YOLOv8n

YOLOv8n was selected because it offers:

* Fast inference speed
* Lightweight model size
* Good CPU performance
* Reliable person detection quality
* Easy integration with tracking pipelines

Each frame is processed to detect persons (`class=0`) and assign a track ID. A visitor session token (`visitor_id`) is generated from tracking information.

The system supports:

* ENTRY detection
* EXIT detection
* REENTRY detection
* ZONE_ENTER
* ZONE_DWELL
* BILLING_QUEUE_JOIN

A virtual entry line is used to determine entry and exit direction. Zone logic is rule-based using bounding-box center coordinates.

---

## 3. Event Flow

Every behavioural observation is converted into a structured event.

Example:

```json
{
  "event_id": "uuid",
  "store_id": "STORE_BLR_002",
  "camera_id": "CAM_ENTRY_01",
  "visitor_id": "VIS_101",
  "event_type": "ENTRY",
  "timestamp": "UTC timestamp",
  "zone_id": null,
  "dwell_ms": 0,
  "is_staff": false,
  "confidence": 0.91,
  "metadata": {
    "queue_depth": null,
    "sku_zone": null,
    "session_seq": 1
  }
}
```

Events are written into a JSONL stream (`pipeline/output/events.jsonl`) so they can be replayed into the API.

This design supports real-time processing, idempotency, replayability, and debugging.

---

## 4. Intelligence API

The Intelligence API is implemented using FastAPI with PostgreSQL.

The API exposes:

* `/events/ingest`
* `/stores/{id}/metrics`
* `/stores/{id}/funnel`
* `/stores/{id}/heatmap`
* `/stores/{id}/anomalies`
* `/health`

Metrics are computed dynamically from ingested events.

The API supports:

* Event deduplication using `event_id`
* Partial validation
* Real-time metrics
* Structured responses
* Health monitoring

Docker Compose is used to containerize PostgreSQL and the API.

---

## 5. Live Dashboard

A terminal-based dashboard was implemented using Rich.

The dashboard periodically queries store metrics and displays:

* Unique visitors
* Conversion rate
* Queue depth
* Abandonment rate

The dashboard updates while events are replayed into the API, demonstrating real-time integration between detection and analytics.

---

## 6. AI-Assisted Decisions

AI tools including ChatGPT were used throughout development to accelerate implementation and explore alternatives.

### Decision 1: Detection Model

AI suggested multiple detection models including YOLOv8, RT-DETR, and MediaPipe. After comparison, YOLOv8n was selected due to better CPU speed and easier integration with ByteTrack.

### Decision 2: Event Schema

AI suggested multiple schema formats. A JSONL event stream was chosen because it supports replay, debugging, streaming, and idempotent ingestion.

### Decision 3: API Architecture

AI recommended FastAPI and PostgreSQL for rapid REST API development, validation, and Docker compatibility. FastAPI was selected because of automatic OpenAPI generation and easier production-readiness.

In several places, generated suggestions were modified manually after testing and debugging to improve compatibility and simplicity.

---

## 7. Limitations

This implementation is intentionally lightweight and optimized for challenge constraints.

Known limitations include:

* Staff detection uses a placeholder boolean and is not vision-based
* Zone boundaries are rule-based instead of learned
* Re-identification is simplified using tracking continuity
* Conversion correlation with POS is minimal
* Camera overlap deduplication is approximate

Despite these limitations, the system demonstrates a complete production-style pipeline from video to live analytics.
