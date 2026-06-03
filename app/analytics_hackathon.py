"""
Advanced analytics for Purplle hackathon data.

Provides:
- Demographics insights (age, gender distribution)
- Queue analysis (wait times, abandonment)
- Zone performance (revenue zones, dwell time)
- Group behavior analysis
- Conversion funnel with real POS data
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Dict

from app.models_hackathon import Event, PosTransaction, Queue, Zone, VisitorSession


class HackathonAnalytics:
    """Analytics for real hackathon data."""

    def __init__(self, db: Session):
        self.db = db

    # ============================================
    # Demographics & Visitor Insights
    # ============================================

    def get_visitor_demographics(self, store_id: str) -> Dict:
        """Analyze visitor demographics (age, gender)."""
        
        # Gender distribution
        gender_dist = (
            self.db.query(
                Event.gender_pred,
                func.count(Event.id_token).label("count")
            )
            .filter(
                Event.store_id == store_id,
                Event.event_type == 'entry',
                Event.gender_pred.isnot(None)
            )
            .group_by(Event.gender_pred)
            .all()
        )
        
        # Age bucket distribution
        age_dist = (
            self.db.query(
                Event.age_bucket,
                func.count(Event.id_token).label("count")
            )
            .filter(
                Event.store_id == store_id,
                Event.event_type == 'entry',
                Event.age_bucket.isnot(None)
            )
            .group_by(Event.age_bucket)
            .all()
        )
        
        # Average age
        avg_age = (
            self.db.query(func.avg(Event.age_pred))
            .filter(
                Event.store_id == store_id,
                Event.event_type == 'entry',
                Event.age_pred.isnot(None)
            )
            .scalar()
        ) or 0
        
        return {
            "gender_distribution": dict(gender_dist),
            "age_bucket_distribution": dict(age_dist),
            "average_age": round(float(avg_age), 1),
            "total_visitors": (
                self.db.query(Event.id_token).filter(
                    Event.store_id == store_id,
                    Event.event_type == 'entry'
                ).distinct().count()
            )
        }

    def get_group_analysis(self, store_id: str) -> Dict:
        """Analyze group visitor behavior."""
        
        # Group size distribution
        group_dist = (
            self.db.query(
                Event.group_size,
                func.count(Event.id_token).label("count")
            )
            .filter(
                Event.store_id == store_id,
                Event.event_type == 'entry',
                Event.group_size.isnot(None)
            )
            .group_by(Event.group_size)
            .all()
        )
        
        # Single vs group visitors
        single_visitors = (
            self.db.query(Event.id_token).filter(
                Event.store_id == store_id,
                Event.event_type == 'entry',
                Event.group_size == 1
            ).distinct().count()
        )
        
        group_visitors = (
            self.db.query(Event.id_token).filter(
                Event.store_id == store_id,
                Event.event_type == 'entry',
                Event.group_size > 1
            ).distinct().count()
        )
        
        return {
            "group_size_distribution": dict(group_dist),
            "single_visitors": single_visitors,
            "group_visitors": group_visitors,
            "group_percentage": round(
                (group_visitors / (single_visitors + group_visitors) * 100) if (single_visitors + group_visitors) > 0 else 0,
                2
            )
        }

    # ============================================
    # Queue Analysis
    # ============================================

    def get_queue_analytics(self, store_id: str) -> Dict:
        """Analyze billing queue behavior."""
        
        queue_events = self.db.query(Event).filter(
            Event.store_id == store_id,
            Event.event_type.in_(['queue_completed', 'queue_abandoned'])
        ).all()
        
        completed = [e for e in queue_events if not e.abandoned]
        abandoned = [e for e in queue_events if e.abandoned]
        
        # Wait time analysis
        wait_times = [e.wait_seconds for e in completed if e.wait_seconds]
        
        avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0
        max_wait = max(wait_times) if wait_times else 0
        min_wait = min(wait_times) if wait_times else 0
        
        # Queue position analysis
        queue_positions = [e.queue_position_at_join for e in queue_events if e.queue_position_at_join]
        
        avg_position = sum(queue_positions) / len(queue_positions) if queue_positions else 0
        
        return {
            "queue_completed": len(completed),
            "queue_abandoned": len(abandoned),
            "abandonment_rate": round(
                (len(abandoned) / len(queue_events) * 100) if len(queue_events) > 0 else 0,
                2
            ),
            "avg_wait_seconds": round(avg_wait, 1),
            "max_wait_seconds": max_wait,
            "min_wait_seconds": min_wait,
            "avg_queue_position": round(avg_position, 1),
            "total_queue_events": len(queue_events)
        }

    def get_queue_demographics(self, store_id: str) -> Dict:
        """Analyze queue by demographics."""
        
        # Gender-based queue abandonment
        gender_queue = (
            self.db.query(
                Event.gender_pred,
                func.count(Event.id).label("total"),
                func.sum(func.case((Event.abandoned == True, 1), else_=0)).label("abandoned")
            )
            .filter(
                Event.store_id == store_id,
                Event.event_type.in_(['queue_completed', 'queue_abandoned']),
                Event.gender_pred.isnot(None)
            )
            .group_by(Event.gender_pred)
            .all()
        )
        
        # Age-based queue abandonment
        age_queue = (
            self.db.query(
                Event.age_bucket,
                func.count(Event.id).label("total"),
                func.sum(func.case((Event.abandoned == True, 1), else_=0)).label("abandoned")
            )
            .filter(
                Event.store_id == store_id,
                Event.event_type.in_(['queue_completed', 'queue_abandoned']),
                Event.age_bucket.isnot(None)
            )
            .group_by(Event.age_bucket)
            .all()
        )
        
        return {
            "by_gender": [
                {
                    "gender": row[0],
                    "total": row[1],
                    "abandoned": row[2] or 0,
                    "abandonment_rate": round((row[2] or 0) / row[1] * 100, 2)
                }
                for row in gender_queue
            ],
            "by_age_bucket": [
                {
                    "age_bucket": row[0],
                    "total": row[1],
                    "abandoned": row[2] or 0,
                    "abandonment_rate": round((row[2] or 0) / row[1] * 100, 2)
                }
                for row in age_queue
            ]
        }

    # ============================================
    # Zone Analysis
    # ============================================

    def get_zone_performance(self, store_id: str) -> Dict:
        """Analyze zone visit patterns."""
        
        zone_visits = (
            self.db.query(
                Event.zone_id,
                Event.zone_name,
                Event.zone_type,
                Event.is_revenue_zone,
                func.count(Event.id_token).label("visitors"),
                func.avg(
                    func.extract('epoch', Event.queue_exit_ts - Event.queue_join_ts)
                ).label("avg_dwell_seconds")
            )
            .filter(
                Event.store_id == store_id,
                Event.event_type.in_(['zone_entered', 'zone_exited']),
                Event.zone_id.isnot(None)
            )
            .group_by(Event.zone_id, Event.zone_name, Event.zone_type, Event.is_revenue_zone)
            .all()
        )
        
        return {
            "zones": [
                {
                    "zone_id": row[0],
                    "zone_name": row[1],
                    "zone_type": row[2],
                    "is_revenue_zone": row[3],
                    "unique_visitors": row[4],
                    "avg_dwell_seconds": round(row[5] or 0, 1)
                }
                for row in zone_visits
            ],
            "revenue_zones_count": sum(1 for row in zone_visits if row[3]),
            "total_zones": len(zone_visits)
        }

    def get_revenue_zone_focus(self, store_id: str) -> Dict:
        """Analyze revenue zone performance."""
        
        # Visitors who visited revenue zones
        revenue_zone_visitors = (
            self.db.query(Event.id_token).filter(
                Event.store_id == store_id,
                Event.is_revenue_zone == True,
                Event.event_type.in_(['zone_entered', 'zone_exited'])
            ).distinct().count()
        )
        
        # Total visitors
        total_visitors = (
            self.db.query(Event.id_token).filter(
                Event.store_id == store_id,
                Event.event_type == 'entry'
            ).distinct().count()
        )
        
        # Average dwell in revenue zones
        avg_dwell = (
            self.db.query(
                func.avg(
                    func.extract('epoch', Event.queue_exit_ts - Event.queue_join_ts)
                )
            )
            .filter(
                Event.store_id == store_id,
                Event.is_revenue_zone == True,
                Event.event_type.in_(['zone_entered', 'zone_exited'])
            )
            .scalar()
        ) or 0
        
        return {
            "revenue_zone_visitors": revenue_zone_visitors,
            "revenue_zone_penetration": round(
                (revenue_zone_visitors / total_visitors * 100) if total_visitors > 0 else 0,
                2
            ),
            "avg_dwell_seconds": round(avg_dwell, 1),
            "total_visitors": total_visitors
        }

    # ============================================
    # Conversion Funnel
    # ============================================

    def get_conversion_funnel(self, store_id: str) -> Dict:
        """Analyze conversion funnel from entry to billing."""
        
        # Stage 1: Entry
        entries = (
            self.db.query(Event.id_token).filter(
                Event.store_id == store_id,
                Event.event_type == 'entry'
            ).distinct().count()
        )
        
        # Stage 2: Zone visit (actual browsing)
        zone_visitors = (
            self.db.query(Event.id_token).filter(
                Event.store_id == store_id,
                Event.event_type.in_(['zone_entered', 'zone_exited'])
            ).distinct().count()
        )
        
        # Stage 3: Queue visit (intent to purchase)
        queue_visitors = (
            self.db.query(Event.id_token).filter(
                Event.store_id == store_id,
                Event.event_type.in_(['queue_completed', 'queue_abandoned'])
            ).distinct().count()
        )
        
        # Stage 4: Completed (no abandonment)
        completed = (
            self.db.query(Event.id_token).filter(
                Event.store_id == store_id,
                Event.event_type == 'queue_completed',
                Event.abandoned == False
            ).distinct().count()
        )
        
        return {
            "stage_1_entry": entries,
            "stage_2_zone_browse": zone_visitors,
            "stage_3_queue_visit": queue_visitors,
            "stage_4_completed_purchase": completed,
            "conversion_rate_entry_to_zone": round(
                (zone_visitors / entries * 100) if entries > 0 else 0, 2
            ),
            "conversion_rate_zone_to_queue": round(
                (queue_visitors / zone_visitors * 100) if zone_visitors > 0 else 0, 2
            ),
            "conversion_rate_queue_to_completed": round(
                (completed / queue_visitors * 100) if queue_visitors > 0 else 0, 2
            ),
            "overall_conversion_rate": round(
                (completed / entries * 100) if entries > 0 else 0, 2
            )
        }

    # ============================================
    # Comprehensive Report
    # ============================================

    def get_comprehensive_report(self, store_id: str) -> Dict:
        """Generate comprehensive analytics report."""
        
        return {
            "store_id": store_id,
            "timestamp": datetime.utcnow().isoformat(),
            "demographics": self.get_visitor_demographics(store_id),
            "groups": self.get_group_analysis(store_id),
            "queue": self.get_queue_analytics(store_id),
            "queue_by_demographics": self.get_queue_demographics(store_id),
            "zones": self.get_zone_performance(store_id),
            "revenue_zones": self.get_revenue_zone_focus(store_id),
            "funnel": self.get_conversion_funnel(store_id)
        }
