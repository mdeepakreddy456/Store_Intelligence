# PROMPT:
# Generate FastAPI tests for Store Intelligence API including health,
# metrics, funnel, heatmap, anomalies and event ingestion.
#
# CHANGES MADE:
# Added challenge-specific assertions and simplified setup.
import os

os.environ["POSTGRES_HOST"] = "localhost"
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200


def test_health():
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "database" in data


def test_ingest_event():
    payload = [
        {
            "event_id": "test-event-001",
            "store_id": "STORE_BLR_002",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": "VIS_TEST_001",
            "event_type": "ENTRY",
            "timestamp": "2026-05-31T18:16:39.131189Z",
            "zone_id": None,
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.95,
            "metadata": {
                "queue_depth": None,
                "sku_zone": None,
                "session_seq": 1
            }
        }
    ]

    response = client.post("/events/ingest", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert "ingested" in data
    assert "duplicates" in data
    assert "failed" in data


def test_metrics():
    response = client.get("/stores/STORE_BLR_002/metrics")

    assert response.status_code == 200

    data = response.json()

    assert "unique_visitors" in data
    assert "conversion_rate" in data


def test_funnel():
    response = client.get("/stores/STORE_BLR_002/funnel")

    assert response.status_code == 200

    data = response.json()

    assert "entry_count" in data
    assert "dropoff_percentage" in data


def test_heatmap():
    response = client.get("/stores/STORE_BLR_002/heatmap")

    assert response.status_code == 200

    data = response.json()

    assert "data_confidence" in data
    assert "zones" in data


def test_anomalies():
    response = client.get("/stores/STORE_BLR_002/anomalies")

    assert response.status_code == 200

    assert isinstance(response.json(), list)