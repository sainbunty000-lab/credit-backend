from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models.cam import CAMReport
from schemas.cam_schema import CAMCreate, CAMUpdate
from datetime import datetime

router = APIRouter(prefix="/cam", tags=["CAM Management"])


# ---------------- CREATE REPORT ----------------
@router.post("/create")
def create_report(data: CAMCreate, db: Session = Depends(get_db)):

    new_report = CAMReport(
        customer_name=data.customer_name,
        wc_data=data.wc_data,
        agri_data=data.agri_data,
        banking_data=data.banking_data,
        status="Draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return {
        "report_id": new_report.id,
        "status": "Draft",
        "message": "CAM Report Created"
    }


# ---------------- AUTOSAVE ----------------
@router.put("/autosave/{report_id}")
def autosave_report(report_id: int, data: CAMUpdate, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(CAMReport.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if data.wc_data is not None:
        report.wc_data = data.wc_data

    if data.agri_data is not None:
        report.agri_data = data.agri_data

    if data.banking_data is not None:
        report.banking_data = data.banking_data

    report.updated_at = datetime.utcnow()

    db.commit()

    return {"status": "Autosaved"}


# ---------------- GET SINGLE REPORT ----------------
@router.get("/{report_id}")
def get_case(report_id: int, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(CAMReport.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Case not found")

    return report


# ---------------- GET ALL REPORTS ----------------
@router.get("/all")
def get_all_cases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):

    reports = (
        db.query(CAMReport)
        .order_by(CAMReport.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return reports


# ---------------- DELETE REPORT ----------------
@router.delete("/{report_id}")
def delete_case(report_id: int, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(CAMReport.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()

    return {"status": "Deleted"}
