#!/usr/bin/env python3
"""
Hackathon data import and analysis utility.

Usage:
    python data_utils.py import_all
    python data_utils.py analyze <store_id>
    python data_utils.py report <store_id>
    python data_utils.py validate
"""

import os
import sys
import json
import logging
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db import SessionLocal, engine
from app.models_hackathon import Base
from app.data_importer import DataImporter, import_hackathon_data
from app.analytics_hackathon import HackathonAnalytics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database with hackathon models."""
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def import_all_data():
    """Import all hackathon data."""
    logger.info("Starting data import process...")
    
    db = SessionLocal()
    
    try:
        report = import_hackathon_data(db, resources_dir="resources")
        
        logger.info("Import Summary:")
        logger.info(f"  POS Transactions: {report.get('pos', {}).get('imported', 0)} imported, "
                   f"{report.get('pos', {}).get('duplicates', 0)} duplicates")
        logger.info(f"  Events: {report.get('events', {}).get('imported', 0)} imported, "
                   f"{report.get('events', {}).get('duplicates', 0)} duplicates")
        logger.info(f"  Event types: {report.get('events', {}).get('by_type', {})}")
        
        logger.info("Data Validation:")
        validation = report.get('validation', {})
        logger.info(f"  Total events: {validation.get('total_events', 0)}")
        logger.info(f"  Total visitors: {validation.get('total_visitors', 0)}")
        logger.info(f"  Total stores: {validation.get('total_stores', 0)}")
        logger.info(f"  Date range: {validation.get('date_range', {}).get('start', 'N/A')} to "
                   f"{validation.get('date_range', {}).get('end', 'N/A')}")
        
        if validation.get('issues'):
            logger.warning("Data Quality Issues:")
            for issue in validation['issues']:
                logger.warning(f"  - {issue}")
        
        return report
    
    finally:
        db.close()


def analyze_store(store_id: str):
    """Analyze specific store."""
    logger.info(f"Analyzing store: {store_id}")
    
    db = SessionLocal()
    
    try:
        analytics = HackathonAnalytics(db)
        report = analytics.get_comprehensive_report(store_id)
        
        return report
    
    finally:
        db.close()


def generate_report(store_id: str):
    """Generate and print analytics report."""
    logger.info(f"Generating report for store: {store_id}")
    
    report = analyze_store(store_id)
    
    print("\n" + "="*80)
    print(f"COMPREHENSIVE ANALYTICS REPORT - {store_id}")
    print("="*80)
    
    # Demographics
    print("\n📊 VISITOR DEMOGRAPHICS")
    print("-" * 80)
    demo = report['demographics']
    print(f"  Total Visitors: {demo['total_visitors']}")
    print(f"  Average Age: {demo['average_age']}")
    print(f"  Gender Distribution: {demo['gender_distribution']}")
    print(f"  Age Bucket Distribution: {demo['age_bucket_distribution']}")
    
    # Groups
    print("\n👥 GROUP ANALYSIS")
    print("-" * 80)
    groups = report['groups']
    print(f"  Single Visitors: {groups['single_visitors']}")
    print(f"  Group Visitors: {groups['group_visitors']}")
    print(f"  Group Percentage: {groups['group_percentage']}%")
    print(f"  Group Size Distribution: {groups['group_size_distribution']}")
    
    # Queue
    print("\n⏳ QUEUE ANALYTICS")
    print("-" * 80)
    queue = report['queue']
    print(f"  Queue Completed: {queue['queue_completed']}")
    print(f"  Queue Abandoned: {queue['queue_abandoned']}")
    print(f"  Abandonment Rate: {queue['abandonment_rate']}%")
    print(f"  Avg Wait Time: {queue['avg_wait_seconds']}s")
    print(f"  Max Wait Time: {queue['max_wait_seconds']}s")
    print(f"  Avg Queue Position: {queue['avg_queue_position']}")
    
    # Queue by Demographics
    print("\n⏳ QUEUE BY DEMOGRAPHICS")
    print("-" * 80)
    queue_demo = report['queue_by_demographics']
    print("  By Gender:")
    for item in queue_demo['by_gender']:
        print(f"    {item['gender']}: {item['total']} total, "
              f"{item['abandoned']} abandoned, {item['abandonment_rate']}%")
    print("  By Age:")
    for item in queue_demo['by_age_bucket']:
        print(f"    {item['age_bucket']}: {item['total']} total, "
              f"{item['abandoned']} abandoned, {item['abandonment_rate']}%")
    
    # Zones
    print("\n🏬 ZONE PERFORMANCE")
    print("-" * 80)
    zones = report['zones']
    print(f"  Total Zones: {zones['total_zones']}")
    print(f"  Revenue Zones: {zones['revenue_zones_count']}")
    for zone in zones['zones']:
        print(f"    {zone['zone_name']} ({zone['zone_type']}): "
              f"{zone['unique_visitors']} visitors, {zone['avg_dwell_seconds']}s avg dwell")
    
    # Revenue Zones
    print("\n💰 REVENUE ZONE FOCUS")
    print("-" * 80)
    revenue = report['revenue_zones']
    print(f"  Revenue Zone Visitors: {revenue['revenue_zone_visitors']}")
    print(f"  Revenue Zone Penetration: {revenue['revenue_zone_penetration']}%")
    print(f"  Avg Dwell in Revenue Zones: {revenue['avg_dwell_seconds']}s")
    
    # Funnel
    print("\n🔄 CONVERSION FUNNEL")
    print("-" * 80)
    funnel = report['funnel']
    print(f"  Stage 1 (Entry): {funnel['stage_1_entry']}")
    print(f"  Stage 2 (Zone Browse): {funnel['stage_2_zone_browse']} "
          f"({funnel['conversion_rate_entry_to_zone']}%)")
    print(f"  Stage 3 (Queue Visit): {funnel['stage_3_queue_visit']} "
          f"({funnel['conversion_rate_zone_to_queue']}%)")
    print(f"  Stage 4 (Completed): {funnel['stage_4_completed_purchase']} "
          f"({funnel['conversion_rate_queue_to_completed']}%)")
    print(f"\n  📈 Overall Conversion Rate: {funnel['overall_conversion_rate']}%")
    
    print("\n" + "="*80)
    
    return report


def validate_data():
    """Validate data integrity."""
    logger.info("Validating data integrity...")
    
    db = SessionLocal()
    
    try:
        importer = DataImporter(db)
        validation = importer.validate_imported_data()
        
        print("\n" + "="*80)
        print("DATA VALIDATION REPORT")
        print("="*80)
        
        print(f"\nTotal Events: {validation['total_events']}")
        print("Events by Type:")
        for event_type, count in validation['events_by_type'].items():
            print(f"  {event_type}: {count}")
        
        print(f"\nTotal Visitors: {validation['total_visitors']}")
        print(f"Total Stores: {validation['total_stores']}")
        
        if validation['date_range']:
            print(f"Date Range: {validation['date_range']['start']} to {validation['date_range']['end']}")
        
        if validation['issues']:
            print("\n⚠️ Issues Found:")
            for issue in validation['issues']:
                print(f"  - {issue}")
        else:
            print("\n✅ No issues found - data looks good!")
        
        print("\n" + "="*80)
        
    finally:
        db.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "import_all":
        init_database()
        import_all_data()
    
    elif command == "analyze":
        if len(sys.argv) < 3:
            print("Usage: python data_utils.py analyze <store_id>")
            sys.exit(1)
        store_id = sys.argv[2]
        report = analyze_store(store_id)
        print(json.dumps(report, indent=2, default=str))
    
    elif command == "report":
        if len(sys.argv) < 3:
            print("Usage: python data_utils.py report <store_id>")
            sys.exit(1)
        store_id = sys.argv[2]
        generate_report(store_id)
    
    elif command == "validate":
        validate_data()
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
