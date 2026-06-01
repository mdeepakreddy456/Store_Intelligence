from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import JSON
from sqlalchemy import Text

from app.db import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(String, unique=True, nullable=False, index=True)

    store_id = Column(String, nullable=False, index=True)
    camera_id = Column(String, nullable=False)

    visitor_id = Column(String, nullable=False, index=True)

    event_type = Column(String, nullable=False)

    timestamp = Column(DateTime, nullable=False)

    zone_id = Column(String, nullable=True)

    dwell_ms = Column(Integer, default=0)

    is_staff = Column(Boolean, default=False)

    confidence = Column(Float, nullable=False)

    metadata_json = Column(JSON, nullable=True)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    visitor_id = Column(
        String,
        nullable=False,
        index=True
    )

    store_id = Column(
        String,
        nullable=False,
        index=True
    )

    entry_time = Column(DateTime)

    exit_time = Column(DateTime)

    converted = Column(
        Boolean,
        default=False
    )

    total_dwell_ms = Column(
        Integer,
        default=0
    )

    visited_zones = Column(
        JSON,
        nullable=True
    )


class POSTransaction(Base):
    __tablename__ = "pos_transactions"

    id = Column(Integer, primary_key=True, index=True)

    transaction_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    store_id = Column(
        String,
        nullable=False,
        index=True
    )

    timestamp = Column(
        DateTime,
        nullable=False
    )

    basket_value_inr = Column(
        Float,
        nullable=False
    )


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)

    store_id = Column(
        String,
        nullable=False,
        index=True
    )

    anomaly_type = Column(
        String,
        nullable=False
    )

    severity = Column(
        String,
        nullable=False
    )

    message = Column(Text)

    suggested_action = Column(Text)

    created_at = Column(DateTime)