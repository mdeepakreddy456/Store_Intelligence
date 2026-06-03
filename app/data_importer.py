"""
Data import and validation for Purplle hackathon data.

Imports:
- POS transactions from CSV
- CCTV events from JSONL
- Validates schema
- Links conversion data
"""

import json
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session

from app.models_hackathon import Event, PosTransaction, Queue, Zone, VisitorSession

logger = logging.getLogger(__name__)


class DataImporter:
    """Handles import of hackathon data."""

    def __init__(self, db: Session):
        self.db = db
        self.events_imported = 0
        self.events_duplicates = 0
        self.events_errors = 0
        self.pos_imported = 0
        self.pos_duplicates = 0

    def import_pos_transactions(self, csv_path: str) -> Dict:
        """
        Import POS transactions from CSV file.
        
        Args:
            csv_path: Path to POS transactions CSV
            
        Returns:
            Import statistics
        """
        stats = {
            "imported": 0,
            "duplicates": 0,
            "errors": 0
        }

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        # Check for duplicates
                        existing = self.db.query(PosTransaction).filter(
                            PosTransaction.order_id == row['order_id']
                        ).first()
                        
                        if existing:
                            stats["duplicates"] += 1
                            continue
                        
                        # Parse fields
                        transaction = PosTransaction(
                            order_id=row['order_id'],
                            order_date=row['order_date'],
                            order_time=row['order_time'],
                            store_id=row['store_id'],
                            product_id=row['product_id'],
                            brand_name=row['brand_name'],
                            total_amount=float(row['total_amount'])
                        )
                        
                        self.db.add(transaction)
                        stats["imported"] += 1
                        
                    except Exception as e:
                        logger.error(f"Error importing POS row: {e}")
                        stats["errors"] += 1
                
                self.db.commit()
                
        except FileNotFoundError:
            logger.error(f"POS file not found: {csv_path}")
            stats["errors"] += 1

        return stats

    def import_events_jsonl(self, jsonl_path: str) -> Dict:
        """
        Import CCTV events from JSONL file.
        
        Args:
            jsonl_path: Path to events JSONL file
            
        Returns:
            Import statistics
        """
        stats = {
            "imported": 0,
            "duplicates": 0,
            "errors": 0,
            "by_type": {}
        }

        try:
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        if not line.strip():
                            continue
                        
                        event_data = json.loads(line)
                        
                        # Generate event_id if not present
                        event_id = event_data.get(
                            'queue_event_id',
                            f"{event_data.get('id_token', event_data.get('track_id'))}-{line_num}"
                        )
                        
                        # Check for duplicates
                        existing = self.db.query(Event).filter(
                            Event.event_id == event_id
                        ).first()
                        
                        if existing:
                            stats["duplicates"] += 1
                            continue
                        
                        # Parse event
                        event_type = event_data.get('event_type', 'unknown')
                        
                        # Parse timestamp
                        timestamp_str = event_data.get(
                            'event_timestamp',
                            event_data.get('event_time')
                        )
                        
                        try:
                            event_timestamp = datetime.fromisoformat(
                                timestamp_str.replace('Z', '+00:00')
                            )
                        except:
                            event_timestamp = datetime.utcnow()
                        
                        # Build event
                        event = Event(
                            event_id=event_id,
                            id_token=event_data.get('id_token'),
                            track_id=event_data.get('track_id'),
                            store_id=event_data.get('store_id', event_data.get('store_code')),
                            store_code=event_data.get('store_code'),
                            camera_id=event_data.get('camera_id'),
                            zone_id=event_data.get('zone_id'),
                            zone_name=event_data.get('zone_name'),
                            event_type=event_type,
                            event_timestamp=event_timestamp,
                            gender_pred=event_data.get('gender_pred', event_data.get('gender')),
                            age_pred=event_data.get('age_pred', event_data.get('age')),
                            age_bucket=event_data.get('age_bucket'),
                            is_face_hidden=event_data.get('is_face_hidden', False),
                            group_id=event_data.get('group_id'),
                            group_size=event_data.get('group_size'),
                            is_staff=event_data.get('is_staff', False),
                            zone_type=event_data.get('zone_type'),
                            is_revenue_zone=event_data.get('is_revenue_zone', True),
                            zone_hotspot_x=event_data.get('zone_hotspot_x'),
                            zone_hotspot_y=event_data.get('zone_hotspot_y'),
                            queue_join_ts=self._parse_timestamp(event_data.get('queue_join_ts')),
                            queue_served_ts=self._parse_timestamp(event_data.get('queue_served_ts')),
                            queue_exit_ts=self._parse_timestamp(event_data.get('queue_exit_ts')),
                            wait_seconds=event_data.get('wait_seconds'),
                            queue_position_at_join=event_data.get('queue_position_at_join'),
                            abandoned=event_data.get('abandoned', False),
                            confidence=event_data.get('confidence', 0.95),
                            metadata_json=event_data
                        )
                        
                        self.db.add(event)
                        stats["imported"] += 1
                        
                        # Track by event type
                        if event_type not in stats["by_type"]:
                            stats["by_type"][event_type] = 0
                        stats["by_type"][event_type] += 1
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parsing error at line {line_num}: {e}")
                        stats["errors"] += 1
                    except Exception as e:
                        logger.error(f"Error importing event at line {line_num}: {e}")
                        stats["errors"] += 1
                
                self.db.commit()
                
        except FileNotFoundError:
            logger.error(f"Events file not found: {jsonl_path}")
            stats["errors"] += 1

        return stats

    def _parse_timestamp(self, ts_str: str) -> datetime:
        """Parse ISO timestamp string to datetime."""
        if not ts_str:
            return None
        try:
            return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        except:
            return None

    def validate_imported_data(self) -> Dict:
        """
        Validate imported data quality.
        
        Returns:
            Validation report
        """
        report = {
            "total_events": 0,
            "events_by_type": {},
            "total_visitors": 0,
            "total_stores": 0,
            "date_range": {},
            "issues": []
        }

        try:
            # Event counts
            events = self.db.query(Event).all()
            report["total_events"] = len(events)
            
            for event in events:
                event_type = event.event_type
                if event_type not in report["events_by_type"]:
                    report["events_by_type"][event_type] = 0
                report["events_by_type"][event_type] += 1
            
            # Visitor counts
            visitors = self.db.query(Event.id_token).distinct().count()
            report["total_visitors"] = visitors
            
            # Store coverage
            stores = self.db.query(Event.store_id).distinct().count()
            report["total_stores"] = stores
            
            # Date range
            if events:
                timestamps = sorted([e.event_timestamp for e in events if e.event_timestamp])
                if timestamps:
                    report["date_range"] = {
                        "start": timestamps[0].isoformat(),
                        "end": timestamps[-1].isoformat()
                    }
            
            # Data quality checks
            missing_demographics = self.db.query(Event).filter(
                Event.gender_pred == None,
                Event.event_type == 'entry'
            ).count()
            
            if missing_demographics > 0:
                report["issues"].append(
                    f"Missing demographics in {missing_demographics} entry events"
                )
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            report["issues"].append(str(e))

        return report


def import_hackathon_data(db: Session, resources_dir: str = "resources") -> Dict:
    """
    Import all hackathon data from resources folder.
    
    Args:
        db: Database session
        resources_dir: Path to resources directory
        
    Returns:
        Complete import report
    """
    report = {}
    importer = DataImporter(db)
    
    resources_path = Path(resources_dir)
    
    # Find and import POS data
    pos_files = list(resources_path.glob("*transactions*.csv"))
    if pos_files:
        logger.info(f"Importing POS data from {pos_files[0]}")
        report["pos"] = importer.import_pos_transactions(str(pos_files[0]))
    else:
        logger.warning("No POS transaction file found")
    
    # Find and import event data
    event_files = list(resources_path.glob("*events*.jsonl"))
    if event_files:
        logger.info(f"Importing event data from {event_files[0]}")
        report["events"] = importer.import_events_jsonl(str(event_files[0]))
    else:
        logger.warning("No event file found")
    
    # Validate
    report["validation"] = importer.validate_imported_data()
    
    return report
