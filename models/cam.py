from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Index,
)
from sqlalchemy.sql import func

from core.database import Base, JSONType


class CAMReport(Base):

    __tablename__ = "cam_reports"

    # ==================================================
    # PRIMARY KEY
    # ==================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ==================================================
    # CUSTOMER INFORMATION
    # ==================================================

    customer_name = Column(
        String(255),
        nullable=False,
        index=True,
    )

    customer_id = Column(
        String(100),
        nullable=True,
        index=True,
    )

    # ==================================================
    # ANALYST INFORMATION
    # ==================================================

    analyst_name = Column(
        String(100),
        nullable=True,
        default="System",
    )

    # ==================================================
    # CREDIT ANALYSIS DATA
    # ==================================================

    wc_data = Column(
        JSONType,
        nullable=True,
        default=lambda: {},
    )

    agri_data = Column(
        JSONType,
        nullable=True,
        default=lambda: {},
    )

    banking_data = Column(
        JSONType,
        nullable=True,
        default=lambda: {},
    )

    # ==================================================
    # DECISION METRICS
    # ==================================================

    loan_amount = Column(
        Integer,
        nullable=True,
        default=0,
    )

    recommended_limit = Column(
        Integer,
        nullable=True,
    )

    risk_grade = Column(
        String(5),
        nullable=True,
    )

    credit_grade = Column(
        String(5),
        nullable=True,
    )

    remarks = Column(
        String(1000),
        nullable=True,
    )

    loan_type = Column(
        String(50),
        nullable=True,
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
        index=True,
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
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    created_by = Column(
        String(100),
        nullable=True,
    )

    # ==================================================
    # SOFT DELETE SUPPORT
    # ==================================================

    is_deleted = Column(
        Boolean,
        default=False,
        index=True,
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )


# ==================================================
# INDEXES (IMPORTANT FOR PERFORMANCE)
# ==================================================

Index(
    "idx_cam_customer_status",
    CAMReport.customer_name,
    CAMReport.status,
)

Index(
    "idx_cam_created_at",
    CAMReport.created_at,
)
