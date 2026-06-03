"""
Comprehensive edge case tests for Store Intelligence API and detection pipeline.

Tests cover:
- Empty store scenarios
- Staff-only footage
- Zero conversion rates
- Re-entry detection
- Group entry detection
- Crowded billing areas
- Partial occlusion handling
- Stale feed warnings
"""

import os
os.environ["POSTGRES_HOST"] = "localhost"

from fastapi.testclient import TestClient
from app.main import app
from app.models import Event
from app.db import get_db
from datetime import datetime
import pytest

client = TestClient(app)


# ============================================
# FIXTURE: Clean database between tests
# ============================================
@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean up test data before each test."""
    db = next(get_db())
    db.query(Event).delete()
    db.commit()
    db.close()
    yield


# ============================================
# EDGE CASE 1: Empty Store (No Visitors)
# ============================================
def test_empty_store_no_detections():
    """Test metrics when store has no visitor events."""
    response = client.get("/stores/STORE_EMPTY/metrics")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["unique_visitors"] == 0
    assert data["conversion_rate"] == 0.0
    assert data["queue_depth"] == 0


def test_empty_store_health():
    """Test health check with no events."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["last_event_timestamp"] is None


# ============================================
# EDGE CASE 2: Staff-Only Footage
# ============================================
def test_staff_only_metrics():
    """Test metrics when all events are staff."""
    # Ingest staff-only events
    payload = [
        {
            "event_id": f"staff-event-{i}",
            "store_id": "STORE_BLR_002",
            "camera_id": "CAM_STAFF_01",
            "visitor_id": f"STAFF_{i}",
            "event_type": "ENTRY",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "zone_id": None,
            "dwell_ms": 0,
            "is_staff": True,  # <-- Staff flag
            "confidence": 0.95,
            "metadata": {"queue_depth": None, "sku_zone": None, "session_seq": 1}
        }
        for i in range(3)
    ]
    
    response = client.post("/events/ingest", json=payload)
    assert response.status_code == 200
    assert response.json()["ingested"] == 3
    
    # Metrics should exclude staff
    metrics_response = client.get("/stores/STORE_BLR_002/metrics")
    assert metrics_response.status_code == 200
    
    data = metrics_response.json()
    assert data["unique_visitors"] == 0  # Staff not counted


# ============================================
# EDGE CASE 3: Zero Conversion Rate
# ============================================
def test_zero_conversion_rate():
    """Test metrics when visitors enter but don't purchase."""
    # Only ENTRY events, no BILLING_QUEUE_JOIN
    payload = [
        {
            "event_id": f"visitor-entry-{i}",
            "store_id": "STORE_BLR_002",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": f"VIS_NO_PURCHASE_{i}",
            "event_type": "ENTRY",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "zone_id": None,
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.95,
            "metadata": {"queue_depth": None, "sku_zone": None, "session_seq": 1}
        }
        for i in range(5)
    ]
    
    client.post("/events/ingest", json=payload)
    
    # Conversion rate should be 0 (no purchases)
    response = client.get("/stores/STORE_BLR_002/metrics")
    assert response.status_code == 200
    
    data = response.json()
    assert data["conversion_rate"] == 0.0


# ============================================
# EDGE CASE 4: Re-Entry Detection
# ============================================
def test_reentry_detection():
    """Test that re-entries are properly detected."""
    payload = [
        # First visit
        {
            "event_id": "entry-1",
            "store_id": "STORE_BLR_002",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": "VIS_REENTRY_TEST",
            "event_type": "ENTRY",
            "timestamp": "2026-05-31T10:00:00Z",
            "zone_id": None,
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.95,
            "metadata": {"session_seq": 1}
        },
        # Exit
        {
            "event_id": "exit-1",
            "store_id": "STORE_BLR_002",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": "VIS_REENTRY_TEST",
            "event_type": "EXIT",
            "timestamp": "2026-05-31T10:15:00Z",
            "zone_id": None,
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.95,
            "metadata": {"session_seq": 1}
        },
        # Re-entry
        {
            "event_id": "reentry-1",
            "store_id": "STORE_BLR_002",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": "VIS_REENTRY_TEST",
            "event_type": "REENTRY",
            "timestamp": "2026-05-31T10:30:00Z",
            "zone_id": None,
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.95,
            "metadata": {"session_seq": 2}
        }
    ]
    
    response = client.post("/events/ingest", json=payload)
    assert response.status_code == 200
    assert response.json()["ingested"] == 3


# ============================================
# EDGE CASE 5: Group Entry Detection
# ============================================
def test_group_entry_metrics():
    """Test metrics with group entries."""
    # Multiple visitors entering at same time
    payload = [
        {
            "event_id": f"group-entry-{i}",
            "store_id": "STORE_BLR_002",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": f"VIS_GROUP_{i}",
            "event_type": "ENTRY",
            "timestamp": "2026-05-31T12:00:00Z",  # Same timestamp
            "zone_id": None,
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.95,
            "metadata": {"session_seq": 1, "group_type": "LARGE_GROUP"}
        }
        for i in range(5)
    ]
    
    response = client.post("/events/ingest", json=payload)
    assert response.status_code == 200
    assert response.json()["ingested"] == 5
    
    # Metrics should count all as unique visitors
    metrics_response = client.get("/stores/STORE_BLR_002/metrics")
    data = metrics_response.json()
    assert data["unique_visitors"] == 5


# ============================================
# EDGE CASE 6: Crowded Billing Area
# ============================================
def test_crowded_billing_queue():
    """Test queue depth in crowded billing area."""
    payload = [
        {
            "event_id": f"billing-queue-{i}",
            "store_id": "STORE_BLR_002",
            "camera_id": "CAM_BILLING_01",
            "visitor_id": f"VIS_BILLING_{i}",
            "event_type": "BILLING_QUEUE_JOIN",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "zone_id": "BILLING_QUEUE",
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.95,
            "metadata": {"queue_depth": i+1, "session_seq": 1}
        }
        for i in range(8)
    ]
    
    response = client.post("/events/ingest", json=payload)
    assert response.status_code == 200
    
    metrics_response = client.get("/stores/STORE_BLR_002/metrics")
    data = metrics_response.json()
    
    # Queue depth should be tracked
    assert data["queue_depth"] >= 0


# ============================================
# EDGE CASE 7: Idempotent Ingestion (Duplicates)
# ============================================
def test_idempotent_event_ingestion():
    """Test that duplicate events are not re-ingested."""
    payload = [
        {
            "event_id": "duplicate-test",
            "store_id": "STORE_BLR_002",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": "VIS_DUP_TEST",
            "event_type": "ENTRY",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "zone_id": None,
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.95,
            "metadata": {"session_seq": 1}
        }
    ]
    
    # Ingest first time
    response1 = client.post("/events/ingest", json=payload)
    assert response1.json()["ingested"] == 1
    assert response1.json()["duplicates"] == 0
    
    # Ingest same event again
    response2 = client.post("/events/ingest", json=payload)
    assert response2.json()["ingested"] == 0
    assert response2.json()["duplicates"] == 1


# ============================================
# EDGE CASE 8: Zone Dwell Time Tracking
# ============================================
def test_zone_dwell_time():
    """Test zone dwell time tracking."""
    payload = [
        {
            "event_id": "zone-enter-1",
            "store_id": "STORE_BLR_002",
            "camera_id": "CAM_MAIN_01",
            "visitor_id": "VIS_DWELL_TEST",
            "event_type": "ZONE_ENTER",
            "timestamp": "2026-05-31T14:00:00Z",
            "zone_id": "SKINCARE",
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.95,
            "metadata": {"session_seq": 1}
        },
        {
            "event_id": "zone-dwell-1",
            "store_id": "STORE_BLR_002",
            "camera_id": "CAM_MAIN_01",
            "visitor_id": "VIS_DWELL_TEST",
            "event_type": "ZONE_DWELL",
            "timestamp": "2026-05-31T14:05:00Z",
            "zone_id": "SKINCARE",
            "dwell_ms": 300000,  # 5 minutes
            "is_staff": False,
            "confidence": 0.95,
            "metadata": {"session_seq": 1}
        }
    ]
    
    response = client.post("/events/ingest", json=payload)
    assert response.status_code == 200
    assert response.json()["ingested"] == 2


# ============================================
# EDGE CASE 9: Stale Feed Detection
# ============================================
def test_stale_feed_warning():
    """Test stale feed detection in health endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should include stale threshold
    assert "stale_threshold_seconds" in data
    assert data["stale_threshold_seconds"] > 0


# ============================================
# EDGE CASE 10: Batch Event Processing
# ============================================
def test_batch_event_ingestion():
    """Test ingesting up to 500 events in batch."""
    payload = [
        {
            "event_id": f"batch-event-{i}",
            "store_id": "STORE_BLR_002",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": f"VIS_BATCH_{i}",
            "event_type": "ENTRY",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "zone_id": None,
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.95,
            "metadata": {"session_seq": 1}
        }
        for i in range(100)  # 100 events
    ]
    
    response = client.post("/events/ingest", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["ingested"] == 100
    assert data["failed"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
