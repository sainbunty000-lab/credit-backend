from fastapi import APIRouter, Depends, HTTPException
from models.cam import CAMReport
# ... imports for DB session

router = APIRouter(prefix="/cam")

@router.post("/save")
async def save_cam(data: dict, db: Session = Depends(get_db)):
    if "customer_name" not in data:
        raise HTTPException(status_code=400, detail="Customer name required for first save")
    
    new_report = CAMReport(**data)
    db.add(new_report)
    db.commit()
    return {"id": new_report.id, "message": "Saved"}

@router.put("/update/{cam_id}")
async def update_cam(cam_id: int, data: dict, db: Session = Depends(get_db)):
    # Simple JSON update for autosave
    db.query(CAMReport).filter(CAMReport.id == cam_id).update(data)
    db.commit()
    return {"status": "Updated"}
