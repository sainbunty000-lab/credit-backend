from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.cam import CAMReport


# ======================================================
# CREATE CAM REPORT
# ======================================================

def create_cam_report(data, db: Session):

    report = CAMReport(
        customer_name=data.customer_name,
        wc_data=data.wc_data,
        agri_data=data.agri_data,
        banking_data=data.banking_data,
        loan_amount=data.loan_amount,
        analyst_name=data.analyst_name
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return report


# ======================================================
# AUTOSAVE CAM REPORT
# ======================================================

def autosave_cam_report(report_id: int, data, db: Session):

    report = (
        db.query(CAMReport)
        .filter(CAMReport.id == report_id, CAMReport.is_deleted is False)
        .first()
    )

    if not report:
        return None

    if data.wc_data is not None:
        report.wc_data = data.wc_data

    if data.agri_data is not None:
        report.agri_data = data.agri_data

    if data.banking_data is not None:
        report.banking_data = data.banking_data

    if data.loan_amount is not None:
        report.loan_amount = data.loan_amount

    if hasattr(data, "credit_grade") and data.credit_grade is not None:
        report.credit_grade = data.credit_grade

    if hasattr(data, "remarks") and data.remarks is not None:
        report.remarks = data.remarks

    if hasattr(data, "status") and data.status is not None:
        report.status = data.status

    db.commit()

    return report


# ======================================================
# SUBMIT CAM REPORT
# ======================================================

def submit_cam_report(report_id: int, data, db: Session):

    report = (
        db.query(CAMReport)
        .filter(CAMReport.id == report_id, CAMReport.is_deleted is False)
        .first()
    )

    if not report:
        return None

    report.credit_grade = data.credit_grade
    report.remarks = data.remarks
    report.status = "Submitted"

    if hasattr(data, "approved_limit") and data.approved_limit:
        report.recommended_limit = data.approved_limit

    db.commit()

    return report


# ======================================================
# GET SINGLE CAM REPORT
# ======================================================

def get_cam_report(report_id: int, db: Session):

    return (
        db.query(CAMReport)
        .filter(CAMReport.id == report_id, CAMReport.is_deleted is False)
        .first()
    )


# ======================================================
# GET ALL CAM REPORTS
# ======================================================

def get_all_cam_reports(skip: int, limit: int, search: str, db: Session):

    query = db.query(CAMReport).filter(CAMReport.is_deleted is False)

    if search:
        query = query.filter(
            CAMReport.customer_name.ilike(f"%{search}%")
        )

    total = query.count()

    reports = (
        query
        .order_by(desc(CAMReport.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return total, reports


# ======================================================
# SOFT DELETE CAM REPORT
# ======================================================

def delete_cam_report(report_id: int, db: Session):

    report = (
        db.query(CAMReport)
        .filter(CAMReport.id == report_id, CAMReport.is_deleted is False)
        .first()
    )

    if not report:
        return None

    report.is_deleted = True

    db.commit()

    return report


# ======================================================
# RESTORE CAM REPORT
# ======================================================

def restore_cam_report(report_id: int, db: Session):

    report = (
        db.query(CAMReport)
        .filter(CAMReport.id == report_id, CAMReport.is_deleted is True)
        .first()
    )

    if not report:
        return None

    report.is_deleted = False

    db.commit()

    return report
