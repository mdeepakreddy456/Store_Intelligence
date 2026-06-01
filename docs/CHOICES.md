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
