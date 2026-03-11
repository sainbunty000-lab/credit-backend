from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from core.database import Base


class CAMReport(Base):

    __tablename__ = "cam_reports"

    # ==================================================
    # PRIMARY KEY
    # ==================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ==================================================
    # CUSTOMER INFO
    # ==================================================

    customer_name = Column(
        String(255),
        nullable=False,
        index=True
    )

    # ==================================================
    # CREDIT ANALYSIS DATA
    # ==================================================

    wc_data = Column(
        JSONB,
        nullable=True,
        default=dict
    )

    agri_data = Column(
        JSONB,
        nullable=True,
        default=dict
    )

    banking_data = Column(
        JSONB,
        nullable=True,
        default=dict
    )

    # ==================================================
    # REPORT STATUS
    # ==================================================

    status = Column(
        String(50),
        default="Draft",
        index=True
    )

    # Example statuses:
    # Draft
    # Under Review
    # Approved
    # Rejected

    # ==================================================
    # METADATA
    # ==================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now()
    )

    # ==================================================
    # SOFT DELETE SUPPORT
    # ==================================================

    is_deleted = Column(
        Boolean,
        default=False
    )
