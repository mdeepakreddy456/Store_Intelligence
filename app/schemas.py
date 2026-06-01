from pydantic import BaseModel
from typing import Optional
from typing import List
from typing import Dict
from datetime import datetime


# -----------------------------
# Event Schemas
# -----------------------------
class EventMetadata(BaseModel):
    queue_depth: Optional[int] = None
    sku_zone: Optional[str] = None
    session_seq: Optional[int] = None


class EventBase(BaseModel):
    event_id: str
    store_id: str
    camera_id: str

    visitor_id: str

    event_type: str

    timestamp: datetime

    zone_id: Optional[str] = None

    dwell_ms: int = 0

    is_staff: bool = False

    confidence: float

    metadata: Optional[EventMetadata] = None


class EventCreate(EventBase):
    pass


class EventResponse(EventBase):
    id: int

    class Config:
        from_attributes = True


# -----------------------------
# Metrics Schema
# -----------------------------
class MetricsResponse(BaseModel):
    unique_visitors: int
    conversion_rate: float
    avg_dwell_per_zone: Dict[str, float]
    queue_depth: int
    abandonment_rate: float


# -----------------------------
# Funnel Schema
# -----------------------------
class FunnelResponse(BaseModel):
    entry_count: int
    zone_visit_count: int
    billing_queue_count: int
    purchase_count: int

    dropoff_percentage: Dict[str, float]


# -----------------------------
# Heatmap Schema
# -----------------------------
class ZoneHeatmap(BaseModel):
    zone_id: str
    visit_frequency: int
    avg_dwell_ms: float
    normalized_score: float


class HeatmapResponse(BaseModel):
    data_confidence: str
    zones: List[ZoneHeatmap]


# -----------------------------
# Anomaly Schema
# -----------------------------
class AnomalyResponse(BaseModel):
    anomaly_type: str
    severity: str
    message: str
    suggested_action: str


# -----------------------------
# Health Schema
# -----------------------------
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str