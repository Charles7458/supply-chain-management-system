from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from services.policy_generator import generate_policies

router = APIRouter(prefix="/policies", tags=["Policies"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/generate")
def generate_inventory_policies(db: Session = Depends(get_db)):
    generate_policies(db)
    return {"message": "Policies generated successfully"}