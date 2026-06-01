# Store Intelligence

End-to-end Store Intelligence system for retail analytics using CCTV footage, FastAPI, PostgreSQL, and YOLOv8.

## Features

* CCTV person detection
* Entry/Exit tracking
* Zone dwell analytics
* Billing queue detection
* Real-time metrics API
* Live dashboard
* Dockerized deployment
* Event replay system

---

## Setup

### 1. Clone repository

```bash
git clone <repo-url>
cd store-intelligence
```

### 2. Start API + database

```bash
docker compose up --build
```

### 3. Run detection pipeline

```bash
python pipeline/detect.py
```

This generates:

```text
pipeline/output/events.jsonl
```

### 4. Replay events into API

```bash
python pipeline/replay_events.py
```

### 5. Open Swagger API docs

```text
http://localhost:8000/docs
```

---

## Live Dashboard

Run:

```bash
python dashboard/live_dashboard.py
```

The dashboard updates metrics in near real-time while events are replayed.

---

## Run Tests

```bash
pytest --cov=app
```

Expected:

* > 70% test coverage
* API tests passing

---

## API Endpoints

### Health

```text
GET /health
```

### Metrics

```text
GET /stores/{store_id}/metrics
```

### Funnel

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
