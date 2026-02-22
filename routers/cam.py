from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models.cam import CAMReport

router = APIRouter(prefix="/cam", tags=["CAM Management"])

@router.post("/save")
def create_report(data: dict, db: Session = Depends(get_db)):
    if "customer_name" not in data:
        raise HTTPException(status_code=400, detail="Customer Name Required")
    
    new_report = CAMReport(
        customer_name=data["customer_name"],
        wc_data=data.get("wc_data", {}),
        agri_data=data.get("agri_data", {}),
        banking_data=data.get("banking_data", {})
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return {"id": new_report.id, "status": "Saved"}

@router.put("/update/{report_id}")
def autosave_report(report_id: int, data: dict, db: Session = Depends(get_db)):
    report = db.query(CAMReport).filter(CAMReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    for key, value in data.items():
        setattr(report, key, value)
        
    db.commit()
    return {"status": "Autosaved"}
