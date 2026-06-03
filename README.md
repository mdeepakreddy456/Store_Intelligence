# Retail Analytics Platform

Comprehensive retail insights platform leveraging CCTV analysis, FastAPI backend, PostgreSQL database, and YOLOv8 for customer behavior intelligence.

## Key Capabilities

* Person detection from video feeds
* Customer journey tracking (entry/exit events)
* Location-based visitor duration metrics
* Queue monitoring and analysis
* REST API for real-time intelligence
* Interactive metrics visualization
* Container-based deployment
* Event stream processing and replay

---

## Getting Started

### 1. Get the code

```bash
git clone <repo-url>
cd store-intelligence
```

### 2. Launch backend services

```bash
docker compose up --build
```

### 3. Process video feeds

```bash
python pipeline/detect.py
```

This produces:

```text
pipeline/output/events.jsonl
```

### 4. Load analytics data

```bash
python pipeline/replay_events.py
```

### 5. Access API documentation

```text
http://localhost:8000/docs
```

---

## Interactive Dashboard

Execute:

```bash
python dashboard/live_dashboard.py
```

Dashboard refreshes with updated metrics as events are processed and ingested.

---

## Testing

```bash
pytest --cov=app
```

Target metrics:

* Minimum 70% code coverage
* All API tests pass

---

## Available Endpoints

### Status Check

```text
GET /health
```

### Store Insights

```text
GET /stores/{store_id}/metrics
```

### User Journey Analysis

```text
GET /stores/{store_id}/funnel
```

### Heatmap

```text
GET /stores/{store_id}/heatmap
```

### Anomalies

```text
GET /stores/{store_id}/anomalies
```

### Ingest Events

```text
POST /events/ingest
```

---

## Tech Stack

* YOLOv8n
* ByteTrack
* FastAPI
* PostgreSQL
* Docker
* OpenCV
* Rich Dashboard
* Pytest

---

## Project Structure

```text
store-intelligence/
│
├── app/
├── pipeline/
├── dashboard/
├── tests/
├── docs/
├── docker-compose.yml
└── README.md
```

---

## System Design

Video Input → Detection & Tracking → Structured Events → Analytics Engine → Metrics API → Visualization

---

## Video Dataset

Video files should be placed in:

```
data/videos/
```

Expected file format:

```
data/videos/CAM 1.mp4
data/videos/CAM 2.mp4
data/videos/CAM 3.mp4
data/videos/CAM 4.mp4
data/videos/CAM 5.mp4
```

---

## Quick Demo Workflow

1. Initialize services

  ```bash
  docker compose up --build
  ```

2. Execute detection

  ```bash
  python pipeline/detect.py
  ```

3. Populate database

  ```bash
  python pipeline/replay_events.py
  ```

4. Explore API

  ```
  http://localhost:8000/docs
  ```

5. Launch visualization

  ```bash
  python dashboard/live_dashboard.py
  ```

---

## Implementation Notes

This project was built with assistance from AI tools for architectural planning, implementation acceleration, validation, and testing optimization.

All generated code has been thoroughly reviewed, adapted, and tested in practical scenarios.

Refer to `docs/DESIGN.md` and `docs/CHOICES.md` for architectural decisions and engineering trade-offs.

---

## License

Project-specific use only.

Video dataset ownership and licensing terms remain with the original provider and are not included in this distribution.
