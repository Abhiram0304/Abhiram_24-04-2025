from sqlalchemy import Column, String
from database import Base

class Store(Base):
    __tablename__ = "stores"

    store_id = Column(String, primary_key=True, index=True)
    timezone_str = Column(String) 