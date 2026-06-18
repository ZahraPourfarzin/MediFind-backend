from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..core.security import require_role
from ..models.models import User, Medicine
from ..schemas.schemas import MedicineCreate, MedicineOut

router = APIRouter(prefix="/medicines", tags=["داروها"])

@router.get("/", response_model=List[MedicineOut])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("rescuer")),
):
    return db.query(Medicine).all()

@router.post("/", response_model=MedicineOut, status_code=201)
def create(
    data: MedicineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("rescuer")),
):
    if db.query(Medicine).filter(Medicine.name == data.name).first():
        raise HTTPException(status_code=400, detail="این دارو قبلاً ثبت شده")
    m = Medicine(**data.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.put("/{medicine_id}", response_model=MedicineOut)
def update(
    medicine_id: int,
    data: MedicineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("rescuer")),
):
    m = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="دارو یافت نشد")
    for k, v in data.model_dump().items():
        setattr(m, k, v)
    db.commit()
    db.refresh(m)
    return m

@router.delete("/{medicine_id}", status_code=204)
def delete(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("rescuer")),
):
    m = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="دارو یافت نشد")
    db.delete(m)
    db.commit()
