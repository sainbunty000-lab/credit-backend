from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Index,
    Text
)

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
    # CUSTOMER INFORMATION
    # ==================================================

    customer_name = Column(
        String(255),
        nullable=False,
        index=True
    )

    customer_id = Column(
        String(100),
        nullable=True,
        index=True
    )

    # ==================================================
    # CREDIT ANALYSIS DATA
    # ==================================================

    wc_data = Column(
        JSONB,
        nullable=True,
        default=lambda: {}
    )

    agri_data = Column(
        JSONB,
        nullable=True,
        default=lambda: {}
    )

    banking_data = Column(
        JSONB,
        nullable=True,
        default=lambda: {}
    )

    # ==================================================
    # DECISION METRICS (OPTIONAL BUT IMPORTANT)
    # ==================================================

    loan_amount = Column(
        Integer,
        nullable=True,
        default=0
    )

    recommended_limit = Column(
        Integer,
        nullable=True
    )

    risk_grade = Column(
        String(5),
        nullable=True
    )

    credit_grade = Column(
        String(5),
        nullable=True
    )

    remarks = Column(
        Text,
        nullable=True
    )

    loan_type = Column(
        String(50),
        nullable=True
    )

    # Example loan types
    # Working Capital
    # Agriculture
    # Personal
    # MSME

    # ==================================================
    # REPORT STATUS
    # ==================================================

    status = Column(
        String(50),
        default="Draft",
        index=True
    )

    # Possible statuses
    # Draft
    # Under Review
    # Approved
    # Rejected

    # ==================================================
    # AUDIT / METADATA
    # ==================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    created_by = Column(
        String(100),
        nullable=True
    )

    analyst_name = Column(
        String(100),
        nullable=True,
        default="System"
    )

    # ==================================================
    # SOFT DELETE SUPPORT
    # ==================================================

    is_deleted = Column(
        Boolean,
        default=False,
        index=True
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True
    )


# ==================================================
# INDEXES (IMPORTANT FOR PERFORMANCE)
# ==================================================

Index(
    "idx_cam_customer_status",
    CAMReport.customer_name,
    CAMReport.status
)

Index(
    "idx_cam_created_at",
    CAMReport.created_at
)
