"""
Data models aligned with Purplle hackathon data structure.

Includes enhanced schemas for:
- Real CCTV event data with demographics
- Queue events with wait times and abandonment
- Zone-based retail analytics
- Group visitor tracking
- POS transaction linking
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Event(Base):
    """Enhanced event model matching real hackathon data."""
    
    __tablename__ = "events"
    
    # Core identifiers
    event_id = Column(String, primary_key=True, index=True)
    id_token = Column(String, unique=True, index=True)  # Visitor identifier
    track_id = Column(Integer, nullable=True, index=True)
    
    # Store and location
    store_id = Column(String, index=True)
    store_code = Column(String, nullable=True)
    camera_id = Column(String)
    zone_id = Column(String, nullable=True)
    zone_name = Column(String, nullable=True)
    
    # Event details
    event_type = Column(String, index=True)  # entry, exit, zone_entered, zone_exited, queue_join, queue_abandoned
    event_timestamp = Column(DateTime, index=True)
    
    # Demographics
    gender_pred = Column(String, nullable=True)  # M, F
    age_pred = Column(Integer, nullable=True)
    age_bucket = Column(String, nullable=True)  # 18-24, 25-34, etc.
    is_face_hidden = Column(Boolean, default=False)
    
    # Group tracking
    group_id = Column(String, nullable=True)
    group_size = Column(Integer, nullable=True)
    
    # Staff classification
    is_staff = Column(Boolean, default=False)
    
    # Zone metadata
    zone_type = Column(String, nullable=True)  # SHELF, DISPLAY, BILLING, etc.
    is_revenue_zone = Column(Boolean, default=True)
    zone_hotspot_x = Column(Float, nullable=True)
    zone_hotspot_y = Column(Float, nullable=True)
    
    # Queue-specific (for billing events)
    queue_join_ts = Column(DateTime, nullable=True)
    queue_served_ts = Column(DateTime, nullable=True)
    queue_exit_ts = Column(DateTime, nullable=True)
    wait_seconds = Column(Integer, nullable=True)
    queue_position_at_join = Column(Integer, nullable=True)
    abandoned = Column(Boolean, default=False)
    
    # Metadata and confidence
    confidence = Column(Float, default=0.0)
    metadata_json = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PosTransaction(Base):
    """POS transaction data linked to visitor events."""
    
    __tablename__ = "pos_transactions"
    
    order_id = Column(String, primary_key=True, index=True)
    order_date = Column(String)
    order_time = Column(String)
    store_id = Column(String, index=True)
    product_id = Column(String)
    brand_name = Column(String)
    total_amount = Column(Float)
    
    # Link to visitor event (if conversion tracking enabled)
    visitor_id = Column(String, nullable=True, index=True)
    linked_event_id = Column(String, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class Queue(Base):
    """Billing queue analytics."""
    
    __tablename__ = "queue_analytics"
    
    queue_event_id = Column(String, primary_key=True, index=True)
    track_id = Column(Integer, index=True)
    store_id = Column(String, index=True)
    
    # Queue event details
    queue_join_ts = Column(DateTime)
    queue_served_ts = Column(DateTime, nullable=True)
    queue_exit_ts = Column(DateTime)
    
    # Analysis
    wait_seconds = Column(Integer)
    queue_position_at_join = Column(Integer)
    abandoned = Column(Boolean, default=False)
    
    # Demographics
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    age_bucket = Column(String, nullable=True)
    
    # Metadata
    zone_id = Column(String)
    zone_name = Column(String)
    camera_id = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Zone(Base):
    """Store zone configuration and analytics."""
    
    __tablename__ = "zones"
    
    zone_id = Column(String, primary_key=True, index=True)
    store_id = Column(String, index=True)
    zone_name = Column(String)
    zone_type = Column(String)  # SHELF, DISPLAY, BILLING, ENTRANCE, etc.
    is_revenue_zone = Column(Boolean, default=True)
    
    # Zone hotspot (center coordinates)
    hotspot_x = Column(Float, nullable=True)
    hotspot_y = Column(Float, nullable=True)
    
    # Analytics
    visitor_count = Column(Integer, default=0)
    avg_dwell_time_seconds = Column(Float, default=0)
    
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class VisitorSession(Base):
    """Complete visitor session from entry to exit/conversion."""
    
    __tablename__ = "visitor_sessions"
    
    session_id = Column(String, primary_key=True, index=True)
    visitor_id = Column(String, index=True)
    store_id = Column(String, index=True)
    
    # Session timing
    entry_timestamp = Column(DateTime)
    exit_timestamp = Column(DateTime, nullable=True)
    total_session_seconds = Column(Integer, nullable=True)
    
    # Demographics
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    age_bucket = Column(String, nullable=True)
    group_id = Column(String, nullable=True)
    group_size = Column(Integer, nullable=True)
    is_staff = Column(Boolean, default=False)
    
    # Behavioral
    zones_visited = Column(Integer, default=0)
    revenue_zones_visited = Column(Integer, default=0)
    avg_zone_dwell_seconds = Column(Float, default=0)
    
    # Conversion
    visited_billing = Column(Boolean, default=False)
    queue_wait_seconds = Column(Integer, nullable=True)
    queue_abandoned = Column(Boolean, default=False)
    converted = Column(Boolean, default=False)
    purchase_amount = Column(Float, nullable=True)
    
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
