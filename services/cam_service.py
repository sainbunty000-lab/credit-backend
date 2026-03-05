from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from models.cam import CAMReport
from schemas.cam_schema import CAMCreate, CAMUpdate, CAMSubmit

router = APIRouter(prefix="/cam", tags=["CAM Dashboard"])


# ---------------------------------------------------
# CREATE CAM REPORT
# ---------------------------------------------------

@router.post("/create")
def create_cam(data: CAMCreate, db: Session = Depends(get_db)):

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

    return {
        "report_id": report.id,
        "status": report.status,
        "message": "CAM Draft Created"
    }


# ---------------------------------------------------
# AUTOSAVE DASHBOARD
# ---------------------------------------------------

@router.put("/autosave/{report_id}")
def autosave_cam(report_id: int, data: CAMUpdate, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(CAMReport.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if data.wc_data is not None:
        report.wc_data = data.wc_data

    if data.agri_data is not None:
        report.agri_data = data.agri_data

    if data.banking_data is not None:
        report.banking_data = data.banking_data

    if data.loan_amount is not None:
        report.loan_amount = data.loan_amount

    if data.credit_grade is not None:
        report.credit_grade = data.credit_grade

    if data.remarks is not None:
        report.remarks = data.remarks

    db.commit()

    return {"status": "Autosaved"}
    

# ---------------------------------------------------
# SUBMIT FINAL CAM
# ---------------------------------------------------

@router.post("/submit/{report_id}")
def submit_cam(report_id: int, data: CAMSubmit, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(CAMReport.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.credit_grade = data.credit_grade
    report.remarks = data.remarks
    report.status = "Submitted"

    db.commit()

    return {"status": "CAM Submitted"}
    

# ---------------------------------------------------
# GET SINGLE REPORT
# ---------------------------------------------------

@router.get("/{report_id}")
def get_cam(report_id: int, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(CAMReport.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report


# ---------------------------------------------------
# LIST ALL CAM REPORTS
# ---------------------------------------------------

@router.get("/all")
def get_all_cams(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):

    reports = (
        db.query(CAMReport)
        .order_by(CAMReport.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return reports


# ---------------------------------------------------
# DELETE CAM
# ---------------------------------------------------

@router.delete("/{report_id}")
def delete_cam(report_id: int, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(CAMReport.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()

    return {"status": "Deleted"}
