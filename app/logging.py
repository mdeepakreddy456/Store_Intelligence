"""
Structured logging configuration for Store Intelligence API.

Provides JSON-formatted structured logs with trace_id, store_id, endpoint,
latency, event count, and status for production observability.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Any, Optional
from pythonjsonlogger import jsonlogger


class StructuredLogger:
    """Produces structured JSON logs for monitoring and debugging."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(level)s %(trace_id)s %(store_id)s %(endpoint)s %(latency_ms)s %(event_count)d %(status)s %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_event_ingest(
        self,
        event_count: int,
        ingested: int,
        duplicates: int,
        failed: int,
        latency_ms: float,
        status: str = "success",
        store_id: str = "UNKNOWN"
    ):
        """Log event ingestion metrics."""
        trace_id = str(uuid.uuid4())
        self.logger.info(
            f"Event ingestion completed",
            extra={
                "timestamp": datetime.utcnow().isoformat(),
                "trace_id": trace_id,
                "store_id": store_id,
                "endpoint": "/events/ingest",
                "latency_ms": latency_ms,
                "event_count": event_count,
                "status": status,
                "ingested": ingested,
                "duplicates": duplicates,
                "failed": failed,
            }
        )

    def log_api_call(
        self,
        endpoint: str,
        method: str,
        latency_ms: float,
        status_code: int,
        store_id: str = "UNKNOWN",
        event_count: int = 0
    ):
        """Log API endpoint calls."""
        trace_id = str(uuid.uuid4())
        status = "success" if 200 <= status_code < 300 else "error"

        self.logger.info(
            f"{method} {endpoint}",
            extra={
                "timestamp": datetime.utcnow().isoformat(),
                "trace_id": trace_id,
                "store_id": store_id,
                "endpoint": endpoint,
                "latency_ms": latency_ms,
                "event_count": event_count,
                "status": status,
                "method": method,
                "status_code": status_code,
            }
        )

    def log_database_error(
        self,
        store_id: str = "UNKNOWN",
        endpoint: str = "UNKNOWN"
    ):
        """Log database connectivity issues."""
        trace_id = str(uuid.uuid4())
        self.logger.error(
            "Database connection failed",
            extra={
                "timestamp": datetime.utcnow().isoformat(),
                "trace_id": trace_id,
                "store_id": store_id,
                "endpoint": endpoint,
                "latency_ms": 0,
                "event_count": 0,
                "status": "error",
                "error": "database_unavailable",
            }
        )

    def log_stale_feed(
        self,
        store_id: str,
        last_event_timestamp: Optional[str],
        stale_threshold_seconds: int = 300
    ):
        """Log stale feed warnings."""
        trace_id = str(uuid.uuid4())
        self.logger.warning(
            f"Stale feed detected for store {store_id}",
            extra={
                "timestamp": datetime.utcnow().isoformat(),
                "trace_id": trace_id,
                "store_id": store_id,
                "endpoint": "/health",
                "latency_ms": 0,
                "event_count": 0,
                "status": "warning",
                "last_event_timestamp": last_event_timestamp,
                "stale_threshold_seconds": stale_threshold_seconds,
            }
        )


# Global logger instance
logger = StructuredLogger("store_intelligence")
