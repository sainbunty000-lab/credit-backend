from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models.cam import CAMReport
from schemas.cam_schema import CAMCreate, CAMUpdate, CAMSubmit
from services.pdf_generator import generate_cam_pdf
from fastapi.responses import FileResponse

router = APIRouter(prefix="/cam", tags=["CAM Dashboard"])


# ---------------- GET ALL ----------------
@router.get("/all")
def get_all_reports(db: Session = Depends(get_db)):

    reports = db.query(CAMReport).filter(CAMReport.is_deleted == False).order_by(CAMReport.id.desc()).all()

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
def create_cam(data: CAMCreate, db: Session = Depends(get_db)):

    report = CAMReport(
        customer_name=data.customer_name,
        wc_data=data.wc_data,
        agri_data=data.agri_data,
        banking_data=data.banking_data,
        loan_amount=data.loan_amount,
        analyst_name=data.analyst_name,
        status="Draft",
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return {"report_id": report.id}


# ---------------- AUTOSAVE CAM ----------------
@router.put("/autosave/{report_id}")
def autosave_cam(report_id: int, data: CAMUpdate, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(CAMReport.id == report_id, CAMReport.is_deleted == False).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report Not Found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(report, field, value)

    db.commit()

    return {"message": "Autosaved"}


# ---------------- SUBMIT CAM ----------------
@router.post("/submit/{report_id}")
def submit_cam(report_id: int, data: CAMSubmit, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(CAMReport.id == report_id, CAMReport.is_deleted == False).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report Not Found")

    report.credit_grade = data.credit_grade
    report.remarks = data.remarks
    report.status = "Submitted"

    if data.approved_limit is not None:
        report.recommended_limit = data.approved_limit

    db.commit()

    return {"message": "CAM Submitted"}


# ---------------- DOWNLOAD PDF ----------------
@router.get("/pdf/{report_id}")
def download_pdf(report_id: int, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(CAMReport.id == report_id, CAMReport.is_deleted == False).first()

    if not report:
        raise HTTPException(status_code=404, detail="Not Found")

    filename = generate_cam_pdf(report.__dict__, f"CAM_{report_id}.pdf")

    return FileResponse(
        path=f"downloads/{filename}",
        media_type="application/pdf",
        filename=filename,
    )


# ---------------- GET CAM ----------------
@router.get("/{report_id}")
def get_cam(report_id: int, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(CAMReport.id == report_id, CAMReport.is_deleted == False).first()

    if not report:
        raise HTTPException(status_code=404, detail="Not Found")

    return {
        "id": report.id,
        "customer_name": report.customer_name,
        "wc_data": report.wc_data,
        "agri_data": report.agri_data,
        "banking_data": report.banking_data,
        "status": report.status,
        "created_at": report.created_at
    }


# ---------------- DELETE CAM ----------------
@router.delete("/{report_id}")
def delete_cam(report_id: int, db: Session = Depends(get_db)):

    report = db.query(CAMReport).filter(CAMReport.id == report_id, CAMReport.is_deleted == False).first()

    if not report:
        raise HTTPException(status_code=404, detail="Not Found")

    report.is_deleted = True
    db.commit()

    return {"message": "Report Deleted"}
