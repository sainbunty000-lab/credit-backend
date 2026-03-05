from sqlalchemy import Column, Integer, String, JSON, DateTime
from core.database import Base
from datetime import datetime


class CAMReport(Base):
    __tablename__ = "cam_reports"

    id = Column(Integer, primary_key=True, index=True)

    customer_name = Column(String, nullable=False)

    wc_data = Column(JSON, default=dict)
    agri_data = Column(JSON, default=dict)
    banking_data = Column(JSON, default=dict)

    status = Column(String, default="Draft")

    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
