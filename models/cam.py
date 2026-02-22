from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from core.database import Base

class CamReport(Base):
    __tablename__ = "cam_reports"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)

    wc_data = Column(JSON, nullable=True)
    agri_data = Column(JSON, nullable=True)
    banking_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
