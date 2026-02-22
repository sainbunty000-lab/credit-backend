from sqlalchemy.orm import Session
from models.cam import CamReport
from datetime import datetime

def save_cam(db: Session, customer_name: str, wc_data=None, agri_data=None, banking_data=None):

    cam = CamReport(
        customer_name=customer_name,
        wc_data=wc_data,
        agri_data=agri_data,
        banking_data=banking_data,
        created_at=datetime.utcnow(),
        last_modified=datetime.utcnow()
    )

    db.add(cam)
    db.commit()
    db.refresh(cam)

    return cam
