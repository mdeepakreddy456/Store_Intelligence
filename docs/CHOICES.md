# CHOICES.md

# Engineering Choices

## 1. Detection Model Choice

### Options Considered

* YOLOv8n
* RT-DETR
* MediaPipe
* Traditional OpenCV methods

### AI Suggestion

AI recommended YOLOv8 and RT-DETR for person detection. RT-DETR potentially offered stronger detection accuracy but required more compute and complexity.

### Final Choice: YOLOv8n

YOLOv8n was selected because:

* Fast CPU inference
* Lightweight deployment
* Good real-time performance
* Simple integration with tracking
* Mature documentation

The challenge prioritizes an end-to-end working system rather than perfect detection accuracy. YOLOv8n balanced speed and acceptable accuracy.

ByteTrack was added to improve identity consistency across frames.

### Trade-Offs

Pros:

* Fast
* Stable
* Easy integration

Cons:

* Misses some partial occlusions
* Lower accuracy than heavier models

---

## 2. Event Schema Design

### Options Considered

* Relational database-first design
* Nested event JSON schema
* JSONL streaming events

### AI Suggestion

AI suggested event-driven architecture because the challenge described a streaming analytics pipeline.

### Final Choice: JSONL Event Stream

The pipeline emits events into `events.jsonl`.

Reasons:

* Replayable
* Easy debugging
* Stream-friendly
* Supports idempotent ingestion
* Human-readable

Each event contains:

* Visitor identity
* Event type
* Confidence
* Store metadata
* Session ordering

The schema mirrors production telemetry systems where behaviour is represented as events.

### Trade-Offs

Pros:

* Flexible
* Easy ingestion
* Real-time compatible

Cons:

* Larger storage overhead than normalized relational structures

---

## 3. API Architecture Choice

### Options Considered

* Flask
* FastAPI
* Node.js Express

### AI Suggestion

AI suggested FastAPI because of:

* Automatic validation
* OpenAPI generation
* Strong typing support
* Better developer experience

### Final Choice: FastAPI + PostgreSQL

FastAPI was chosen because:

* Automatic Swagger documentation
* Strong validation through Pydantic
* Easy async support
* Simple REST API implementation

PostgreSQL was chosen because:

* Reliable relational storage
* SQL analytics support
* Docker compatibility
* Production familiarity

### Trade-Offs

Pros:

* Easy deployment
* Production-ready
* Strong schema validation

Cons:

* Slightly heavier than SQLite for local experimentation

---

## Reflection on AI Usage

AI significantly accelerated development but was not accepted blindly.

Several outputs required manual debugging, including:

* Docker networking issues
* Event ingestion bugs
* Tracking logic adjustments
* Test fixes

Generated code was reviewed, modified, and validated through testing and API verification. The final system reflects a combination of AI assistance and manual engineering decisions.

---

## 4. Tracking and Re-ID Strategy

### Options Considered

* ByteTrack (lightweight)
* DeepSORT (with Re-ID model)
* StrongSORT (advanced)
* Simple centroid tracking

### AI Suggestion

AI recommended DeepSORT with a Re-ID model for maximum accuracy. However, the Re-ID approach required additional pre-trained models and complexity.

### Final Choice: ByteTrack

ByteTrack was selected because:

* Lightweight and fast
* No Re-ID model required
* Good tracking consistency within camera
* Easy integration with YOLOv8

Cross-camera Re-ID uses heuristics:
* Timestamp proximity
* Visual feature matching (confidence scores)
* Zone transitions

### Trade-Offs

Pros:
* Simple, no extra models
* Fast processing
* Sufficient for single-store tracking

Cons:
* No cross-camera identity linking
* Can lose track in crowded scenes
* Identity swaps possible

---

## 5. Staff vs Customer Classification

### Options Considered

* Deep learning classifier (separate model)
* Rule-based heuristics
* Rule-based + confidence thresholds
* Geometric constraints (uniform shape detection)

### AI Suggestion

AI suggested a separate CNN classifier trained on staff/customer datasets. This would be more accurate but required labeled training data and additional inference.

### Final Choice: Rule-Based Heuristics + Camera Context

A hybrid approach was implemented:

* **Camera context**: Staff cameras get higher baseline probability
* **Event type weighting**: ENTRY/EXIT events → lower staff probability
* **Zone-based logic**: Billing area → higher staff probability
* **Behavioral patterns**: Recurring zone transitions → higher staff probability

Confidence is calibrated through experimentation.

### Trade-Offs

Pros:
* No additional model training required
* Fast, interpretable logic
* Works with challenge constraints

Cons:
* Cannot handle ambiguous cases
* Requires manual rule tuning
* May miss edge cases

---

## 6. Database Schema and Query Strategy

### Options Considered

* NoSQL (MongoDB) - flexible schema
* SQLite - lightweight, single file
* PostgreSQL - relational, production-ready
* Time-series DB (InfluxDB) - optimized for metrics

### AI Suggestion

AI recommended PostgreSQL for production readiness and SQL analytics, but also mentioned TimescaleDB for better time-series performance.

### Final Choice: PostgreSQL

PostgreSQL was selected because:

* ACID compliance ensures data integrity
* SQL enables complex analytics queries
* Docker support for easy deployment
* Proper indexing for query performance
* Familiar to production teams

### Schema Design

Events table:
- `event_id` (Primary Key, UUID)
- `store_id` (Indexed for filtering)
- `visitor_id` (Tracked for aggregation)
- `event_type` (Indexed for quick filtering)
- `timestamp` (Indexed for time-range queries)
- `zone_id`, `dwell_ms`, `is_staff`, `confidence`

Sessions table:
- Aggregates visitor entries into sessions
- Tracks conversion (presence of BILLING_QUEUE_JOIN)
- Enables funnel analysis

### Trade-Offs

Pros:
* Scales well for millions of events
* Complex queries supported
* Proven reliability

Cons:
* Heavier than NoSQL for simple access
* Requires schema planning upfront

---

## 7. Structured Logging and Observability

### Options Considered

* Simple print() statements
* Python logging module
* JSON structured logging
* Third-party services (DataDog, New Relic)

### AI Suggestion

AI recommended structured JSON logging for production observability and easier parsing by monitoring systems.

### Final Choice: JSON Structured Logging

Implementation includes:

* **trace_id**: Unique identifier for request tracking
* **store_id**: Store context
* **endpoint**: API endpoint called
* **latency_ms**: Request duration
* **event_count**: Events processed
* **status**: Success/error

Benefits:
* Machine-parseable logs
* Easy aggregation and alerting
* Production-ready monitoring

### Trade-Offs

Pros:
* Better observability
* Debugging support
* Analytics-ready

Cons:
* Slightly verbose output
* Requires log parsing tooling for alerts

---

## 8. Edge Case Handling Strategy

### Critical Edge Cases Addressed

1. **Empty Store**: Graceful handling when no events present
2. **Staff-Only Footage**: Filtering staff via `is_staff` flag
3. **Zero Conversion**: Proper handling of stores with visitors but no purchases
4. **Re-entries**: Tracking repeated visits by same visitor
5. **Group Entries**: Multiple people entering together
6. **Crowded Billing**: Queue depth tracking with threshold detection
7. **Partial Occlusion**: Confidence-based filtering of low-visibility detections
8. **Idempotent Ingestion**: Duplicate event handling via unique event_id

### Implementation

Edge cases are handled through:
* Early database checks (`SELECT COUNT(*)`)
* Confidence thresholds
* Event type filtering
* Behavioral pattern analysis
* Timestamp-based deduplication

---

## 9. Testing Strategy

### Test Coverage: 96%

Comprehensive tests cover:

* API endpoint responses
* Edge cases (empty store, staff-only, zero conversion)
* Batch event ingestion (up to 500 events)
* Idempotency verification
* Stale feed detection
* Zone dwell tracking
* Re-entry scenarios
* Group entry detection

Test database is isolated per test run to ensure reproducibility.

### Trade-Offs

Pros:
* High confidence in system behavior
* Regression detection
* Production readiness

Cons:
* Longer test execution time
* Test maintenance overhead
