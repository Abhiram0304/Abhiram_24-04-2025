from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import pandas as pd
from datetime import datetime
import pytz
from models.store import Store
from models.business_hours import BusinessHours
from models.store_status import StoreStatus
from database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
import os
import logging
import uuid

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_timestamp(timestamp_str: str) -> datetime:
    try:
        timestamp_str = timestamp_str.replace(' UTC', '')
        return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        try:
            return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {timestamp_str}")

@router.post("/upload/store-status")
async def upload_store_status(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        logger.info(f"Starting store status upload for file: {file.filename}")
        
        chunk_size = 1000
        total_rows = 0
        processed_rows = 0
        
        for chunk in pd.read_csv(file.file, chunksize=chunk_size):
            total_rows += len(chunk)
        
        file.file.seek(0)
        
        for chunk in pd.read_csv(file.file, chunksize=chunk_size):
            required_columns = ['store_id', 'timestamp_utc', 'status']
            if not all(col in chunk.columns for col in required_columns):
                raise HTTPException(status_code=400, detail="CSV must contain store_id, timestamp_utc, and status columns")
            
            records = []
            for _, row in chunk.iterrows():
                try:
                    timestamp = parse_timestamp(row['timestamp_utc'])
                    if timestamp.tzinfo is None:
                        timestamp = pytz.UTC.localize(timestamp)
                    
                    records.append({
                        'store_id': row['store_id'],
                        'timestamp_utc': timestamp,
                        'status': row['status']
                    })
                    
                    processed_rows += 1
                    if processed_rows % 1000 == 0:
                        logger.info(f"Processed {processed_rows}/{total_rows} rows")
                        
                except Exception as e:
                    logger.error(f"Error processing row: {row.to_dict()}, Error: {str(e)}")
                    continue
            
            if records:
                db.bulk_insert_mappings(StoreStatus, records)
                db.commit()
        
        logger.info("Store status upload completed successfully")
        return {"message": f"Store status data uploaded successfully. Processed {processed_rows} rows."}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error during store status upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/business-hours")
async def upload_business_hours(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        logger.info(f"Starting business hours upload for file: {file.filename}")
        
        df = pd.read_csv(file.file)
        
        if 'dayOfWeek' in df.columns:
            df = df.rename(columns={'dayOfWeek': 'day'})
        
        required_columns = ['store_id', 'day', 'start_time_local', 'end_time_local']
        if not all(col in df.columns for col in required_columns):
            missing_columns = [col for col in required_columns if col not in df.columns]
            error_msg = f"Missing required columns: {missing_columns}. Found columns: {df.columns.tolist()}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        try:
            df['day'] = df['day'].astype(int)
        except Exception as e:
            logger.error(f"Error converting day column to integer: {str(e)}")
            raise HTTPException(status_code=400, detail="Day column must contain integers (0-6)")
        
        total_rows = len(df)
        
        for index, row in df.iterrows():
            try:
                if not 0 <= row['day'] <= 6:
                    raise ValueError(f"Day value {row['day']} is not between 0-6")
                
                try:
                    datetime.strptime(row['start_time_local'], '%H:%M:%S')
                    datetime.strptime(row['end_time_local'], '%H:%M:%S')
                except ValueError:
                    raise ValueError(f"Invalid time format in row {index + 1}")
                
                business_hours = BusinessHours(
                    store_id=str(row['store_id']),
                    day=row['day'],
                    start_time_local=row['start_time_local'],
                    end_time_local=row['end_time_local']
                )
                db.add(business_hours)
                
                if (index + 1) % 1000 == 0:
                    db.commit()
            
            except Exception as e:
                logger.error(f"Error processing row {index + 1}: {row.to_dict()}, Error: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Error in row {index + 1}: {str(e)}")
        
        db.commit()
        logger.info("Business hours upload completed successfully")
        return {"message": "Business hours data uploaded successfully"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error during business hours upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/timezones")
async def upload_timezones(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        logger.info(f"Starting timezones upload for file: {file.filename}")
        
        df = pd.read_csv(file.file)
        
        required_columns = ['store_id', 'timezone_str']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail="CSV must contain store_id and timezone_str columns")
        
        total_rows = len(df)
        for index, row in df.iterrows():
            store = Store(
                store_id=row['store_id'],
                timezone_str=row['timezone_str']
            )
            db.add(store)
            
            if (index + 1) % 1000 == 0:
                db.commit()
        
        db.commit()
        logger.info("Timezones upload completed successfully")
        return {"message": "Timezone data uploaded successfully"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error during timezones upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))