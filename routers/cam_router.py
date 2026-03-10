from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models.cam import CAMReport
from datetime import datetime
from services.pdf_generator import generate_cam_pdf
from fastapi.responses import FileResponse
import os

router = APIRouter(prefix="/cam", tags=["CAM Management"])


# ---------------- SAVE ----------------
@router.post("/save")
def create_report(data: dict, db: Session = Depends(get_db)):
    if not data.get("customer_name"):
        raise HTTPException(status_code=400, detail="Customer Name Required")

    report = CAMReport(
        customer_name=data["customer_name"],
        wc_data=data.get("wc_data", {}),
        agri_data=data.get("agri_data", {}),
        banking_data=data.get("banking_data", {}),
        status="Draft",
        created_at=datetime.utcnow()
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return {"id": report.id}


# ---------------- UPDATE ----------------
@router.put("/update/{report_id}")
def update_report(report_id: int, data: dict, db: Session = Depends(get_db)):
    report = db.query(CAMReport).filter(CAMReport.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report Not Found")

    report.customer_name = data.get("customer_name", report.customer_name)
    report.wc_data = data.get("wc_data", report.wc_data)
    report.agri_data = data.get("agri_data", report.agri_data)
    report.banking_data = data.get("banking_data", report.banking_data)

    db.commit()

    return {"message": "Updated Successfully"}


# ---------------- GET ONE ----------------
@router.get("/pdf/{report_id}")
def download_pdf(report_id: int, db: Session = Depends(get_db)):
    report = db.query(CAMReport).filter(CAMReport.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Not found")

    filename = generate_cam_pdf(report.__dict__, f"CAM_{report_id}.pdf")

    return FileResponse(
        path=f"downloads/{filename}",
        media_type="application/pdf",
        filename=filename,
    )

# ---------------- GET ALL ----------------
@router.get("/all")
def get_all_reports(db: Session = Depends(get_db)):
    reports = db.query(CAMReport).order_by(CAMReport.id.desc()).all()
    return reports
