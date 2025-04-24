import pandas as pd
import os
from datetime import datetime
from sqlalchemy.orm import Session
from database import engine, Base
from models.store import Store
from models.business_hours import BusinessHours
from models.store_status import StoreStatus

def load_store_activities(csv_path: str, db: Session):
    """Load store activities from CSV"""
    print("Loading store activities...")
    df = pd.read_csv(csv_path)
    
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
    
    records = []
    for _, row in df.iterrows():
        record = StoreStatus(
            store_id=row['store_id'],
            timestamp_utc=row['timestamp_utc'],
            status=row['status']
        )
        records.append(record)
    
    if records:
        db.bulk_save_objects(records)
        db.commit()
    print(f"Loaded {len(records)} store activities")

def load_business_hours(csv_path: str, db: Session):
    """Load business hours from CSV"""
    print("Loading business hours...")
    df = pd.read_csv(csv_path)
    
    records = []
    for _, row in df.iterrows():
        record = BusinessHours(
            store_id=row['store_id'],
            day=row['day'],
            start_time_local=row['start_time_local'],
            end_time_local=row['end_time_local']
        )
        records.append(record)
    
    if records:
        db.bulk_save_objects(records)
        db.commit()
    print(f"Loaded {len(records)} business hours")

def load_store_timezones(csv_path: str, db: Session):
    """Load store timezones from CSV"""
    print("Loading store timezones...")
    df = pd.read_csv(csv_path)
    
    records = []
    for _, row in df.iterrows():
        record = Store(
            store_id=row['store_id'],
            timezone_str=row['timezone_str']
        )
        records.append(record)
    
    if records:
        db.bulk_save_objects(records)
        db.commit()
    print(f"Loaded {len(records)} store timezones")

def main():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session
    db = Session(engine)
    
    try:
        # Clear existing data
        db.query(StoreStatus).delete()
        db.query(BusinessHours).delete()
        db.query(Store).delete()
        db.commit()
        
        # Load new data
        load_store_activities("data/store_activities.csv", db)
        load_business_hours("data/business_hours.csv", db)
        load_store_timezones("data/store_timezones.csv", db)
        
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 