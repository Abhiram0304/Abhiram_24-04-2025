from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List
import uuid
import pandas as pd
from datetime import datetime, timedelta
import pytz
from models.store import Store
from models.business_hours import BusinessHours
from models.store_status import StoreStatus
from models.report import Report
from database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi.responses import StreamingResponse
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
reports: Dict[str, Dict] = {}

def calculate_uptime_downtime(store_id: str, start_time: datetime, end_time: datetime, db: Session) -> Dict:
    try:
        store = db.query(Store).filter(Store.store_id == store_id).first()
        timezone = pytz.timezone(store.timezone_str if store else 'America/Chicago')
        
        if start_time.tzinfo is None:
            start_time = pytz.UTC.localize(start_time)
        else:
            start_time = start_time.astimezone(pytz.UTC)
            
        if end_time.tzinfo is None:
            end_time = pytz.UTC.localize(end_time)
        else:
            end_time = end_time.astimezone(pytz.UTC)
        
        business_hours = db.query(BusinessHours).filter(BusinessHours.store_id == store_id).all()
        status_records = db.query(StoreStatus).filter(
            StoreStatus.store_id == store_id,
            StoreStatus.timestamp_utc >= start_time,
            StoreStatus.timestamp_utc <= end_time
        ).order_by(StoreStatus.timestamp_utc).all()
        
        total_uptime = timedelta()
        total_downtime = timedelta()
        
        current_time = start_time
        day_count = 0
        max_days = 7
        
        while current_time < end_time and day_count < max_days:
            day_count += 1
            local_time = current_time.astimezone(timezone)
            day_of_week = local_time.weekday()
            
            day_hours = next((bh for bh in business_hours if bh.day == day_of_week), None)
            
            if day_hours:
                start_time_parts = day_hours.start_time_local.split(':')
                end_time_parts = day_hours.end_time_local.split(':')
                
                start_hour = int(start_time_parts[0])
                start_minute = int(start_time_parts[1])
                end_hour = int(end_time_parts[0])
                end_minute = int(end_time_parts[1])
                
                business_start = local_time.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                business_end = local_time.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
                
                if business_start.tzinfo is None:
                    business_start = timezone.localize(business_start)
                if business_end.tzinfo is None:
                    business_end = timezone.localize(business_end)
                
                if business_end < business_start:
                    business_end += timedelta(days=1)
                
                period_records = [r for r in status_records if 
                                business_start <= r.timestamp_utc.astimezone(timezone) <= business_end]
                
                if period_records:
                    for i in range(len(period_records) - 1):
                        current_record = period_records[i]
                        next_record = period_records[i + 1]
                        duration = next_record.timestamp_utc - current_record.timestamp_utc
                        
                        if current_record.status == 'active':
                            total_uptime += duration
                        else:
                            total_downtime += duration
                    
                    last_record = period_records[-1]
                    duration = business_end - last_record.timestamp_utc.astimezone(timezone)
                    if last_record.status == 'active':
                        total_uptime += duration
                    else:
                        total_downtime += duration
                
                current_time = business_end.astimezone(pytz.UTC)
            else:
                current_time = end_time
        
        return {
            'uptime': total_uptime.total_seconds() / 60,
            'downtime': total_downtime.total_seconds() / 60
        }
    
    except Exception as e:
        logger.error(f"Error calculating uptime/downtime for store {store_id}: {str(e)}")
        raise

def generate_report(report_id: str, db: Session):
    try:
        logger.info(f"Starting report generation for report_id: {report_id}")
        
        stores = db.query(Store).all()
        max_timestamp = db.query(StoreStatus.timestamp_utc).order_by(StoreStatus.timestamp_utc.desc()).first()
        if not max_timestamp:
            raise ValueError("No store status records found")
        current_time = max_timestamp[0]
        
        report_data = []
        total_stores = len(stores)
        
        for index, store in enumerate(stores, 1):
            logger.info(f"Calculating for store {store.store_id}")
            
            last_hour = calculate_uptime_downtime(
                store.store_id,
                current_time - timedelta(hours=1),
                current_time,
                db
            )
            
            last_day = calculate_uptime_downtime(
                store.store_id,
                current_time - timedelta(days=1),
                current_time,
                db
            )
            
            last_week = calculate_uptime_downtime(
                store.store_id,
                current_time - timedelta(weeks=1),
                current_time,
                db
            )
            
            report_data.append({
                'store_id': store.store_id,
                'uptime_last_hour': last_hour['uptime'],
                'uptime_last_day': last_day['uptime'] / 60,
                'uptime_last_week': last_week['uptime'] / 60,
                'downtime_last_hour': last_hour['downtime'],
                'downtime_last_day': last_day['downtime'] / 60,
                'downtime_last_week': last_week['downtime'] / 60
            })
        
        df = pd.DataFrame(report_data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        reports[report_id] = {
            'status': 'Complete',
            'data': csv_content
        }
        logger.info(f"Report generation completed for report_id: {report_id}")
        
    except Exception as e:
        logger.error(f"Error during report generation: {str(e)}")
        reports[report_id] = {
            'status': 'Failed',
            'error': str(e)
        }

@router.post("/trigger_report")
async def trigger_report(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    report_id = str(uuid.uuid4())
    reports[report_id] = {'status': 'Running'}
    background_tasks.add_task(generate_report, report_id, db)
    return {"report_id": report_id}

@router.get("/get_report/{report_id}")
async def get_report(report_id: str):
    if report_id not in reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = reports[report_id]
    
    if report['status'] == 'Running':
        return {"status": "Running"}
    elif report['status'] == 'Failed':
        raise HTTPException(status_code=500, detail=f"Report generation failed: {report['error']}")
    else:
        return StreamingResponse(
            io.StringIO(report['data']),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=report_{report_id}.csv"}
        )