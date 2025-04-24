from sqlalchemy import Column, String, Integer
from database import Base

class BusinessHours(Base):
    __tablename__ = "business_hours"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, index=True)
    day = Column(Integer)  # 0-6 for Monday-Sunday
    start_time_local = Column(String)
    end_time_local = Column(String) 