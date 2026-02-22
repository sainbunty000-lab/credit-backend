from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from core.database import Base

class CAMReport(Base):
    __tablename__ = "cam_reports"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    wc_data_json = Column(JSON, nullable=True)
    agri_data_json = Column(JSON, nullable=True)
    banking_data_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    last_modified = Column(DateTime, onupdate=func.now())
