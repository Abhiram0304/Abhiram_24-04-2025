from sqlalchemy import Column, String, DateTime, JSON
from database import Base

class Report(Base):
    __tablename__ = "reports"

    report_id = Column(String, primary_key=True, index=True)
    status = Column(String)  # 'Running', 'Complete', 'Failed'
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime)
    completed_at = Column(DateTime, nullable=True) 