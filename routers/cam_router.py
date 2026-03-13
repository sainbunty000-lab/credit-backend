from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from core.database import get_db
from models.cam import CAMReport
from datetime import datetime
from services.pdf_generator import generate_cam_pdf

router = APIRouter(prefix="/cam", tags=["CAM Dashboard"])


# ---------------- GET ALL ----------------
# Must be declared BEFORE /{report_id} so FastAPI does not try
# to parse the literal "all" as an integer report_id.
@router.get("/all")
def get_all_reports(db: Session = Depends(get_db)):

    reports = db.query(CAMReport).filter(
        CAMReport.is_deleted.is_(False)
    ).order_by(CAMReport.id.desc()).all()

    return [
        {
            "id": r.id,
            "customer_name": r.customer_name,
            "status": r.status,
            "created_at": r.created_at
        }
        for r in reports
    ]


# ---------------- CREATE CAM ----------------
@router.post("/create")
def create_cam(data: dict, db: Session = Depends(get_db)):

    if not data.get("customer_name"):
        raise HTTPException(status_code=400, detail="Customer Name Required")

    report = CAMReport(
        customer_name=data["customer_name"],
        analyst_name=data.get("analyst_name", "System"),
        loan_amount=data.get("loan_amount", 0),
        wc_data=data.get("wc_data", {}),
        agri_data=data.get("agri_data", {}),
        banking_data=data.get("banking_data", {}),
        status="Draft",
        created_at=datetime.utcnow(),
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return {"report_id": report.id}


# ---------------- AUTOSAVE CAM ----------------
@router.put("/autosave/{report_id}")
def autosave_cam(report_id: int, data: dict, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(
        CAMReport.id == report_id,
        CAMReport.is_deleted.is_(False),
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report Not Found")

    report.customer_name = data.get("customer_name", report.customer_name)
    report.analyst_name = data.get("analyst_name", report.analyst_name)
    report.loan_amount = data.get("loan_amount", report.loan_amount)
    report.wc_data = data.get("wc_data", report.wc_data)
    report.agri_data = data.get("agri_data", report.agri_data)
    report.banking_data = data.get("banking_data", report.banking_data)
    report.credit_grade = data.get("credit_grade", report.credit_grade)
    report.remarks = data.get("remarks", report.remarks)

    db.commit()

    return {"message": "Autosaved"}


# ---------------- SUBMIT CAM ----------------
@router.post("/submit/{report_id}")
def submit_cam(report_id: int, data: dict, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(
        CAMReport.id == report_id,
        CAMReport.is_deleted.is_(False),
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report Not Found")

    report.status = "Submitted"
    report.credit_grade = data.get("credit_grade", report.credit_grade)
    report.remarks = data.get("remarks", report.remarks)
    if data.get("approved_limit"):
        report.recommended_limit = data["approved_limit"]

    db.commit()

    return {"message": "CAM Submitted"}


# ---------------- DOWNLOAD PDF ----------------
# Generates PDF in /tmp (compatible with Cloud Run)
@router.get("/pdf/{report_id}")
def download_pdf(report_id: int, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(
        CAMReport.id == report_id,
        CAMReport.is_deleted.is_(False),
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Not Found")

    output_path = generate_cam_pdf(report.__dict__, f"CAM_{report_id}.pdf")

    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=f"CAM_{report_id}.pdf",
    )


# ---------------- GET CAM ----------------
@router.get("/{report_id}")
def get_cam(report_id: int, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(
        CAMReport.id == report_id,
        CAMReport.is_deleted.is_(False),
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Not Found")

    return {
        "id": report.id,
        "customer_name": report.customer_name,
        "analyst_name": report.analyst_name,
        "loan_amount": report.loan_amount,
        "wc_data": report.wc_data,
        "agri_data": report.agri_data,
        "banking_data": report.banking_data,
        "credit_grade": report.credit_grade,
        "recommended_limit": report.recommended_limit,
        "remarks": report.remarks,
        "status": report.status,
        "created_at": report.created_at,
    }


# ---------------- DELETE CAM ----------------
@router.delete("/{report_id}")
def delete_cam(report_id: int, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(
        CAMReport.id == report_id,
        CAMReport.is_deleted.is_(False),
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Not Found")

    report.is_deleted = True
    db.commit()

    return {"message": "Report Deleted"}

