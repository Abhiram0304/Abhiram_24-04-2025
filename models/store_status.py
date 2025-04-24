from sqlalchemy import Column, String, DateTime, Integer
from database import Base

class StoreStatus(Base):
    __tablename__ = "store_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(String, index=True)
    timestamp_utc = Column(DateTime)
    status = Column(String)  # 'active' or 'inactive' 