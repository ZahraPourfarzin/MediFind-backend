from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..core.security import require_role
from ..models.models import User, Pharmacy, Medicine, Inventory
from ..schemas.schemas import PharmacyCreate, PharmacyOut, InventoryUpdate, InventoryOut

router = APIRouter(prefix="/pharmacy", tags=["داروخانه"])

@router.post("/register", response_model=PharmacyOut, status_code=201)
def register_pharmacy(
    data: PharmacyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
):
    # فقط داروخانه‌داری که تأیید هویت شده می‌تونه داروخانه ثبت کنه
    if not current_user.pharmacist_verified:
        raise HTTPException(status_code=403, detail="هنوز کد نظام پزشکی شما تأیید نشده است")
    if db.query(Pharmacy).filter(Pharmacy.owner_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="شما قبلاً یک داروخانه ثبت کرده‌اید")

    pharmacy = Pharmacy(**data.model_dump(), owner_id=current_user.id)
    db.add(pharmacy)
    db.commit()
    db.refresh(pharmacy)
    return pharmacy

@router.get("/my", response_model=PharmacyOut)
def get_my_pharmacy(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
):
    pharmacy = db.query(Pharmacy).filter(Pharmacy.owner_id == current_user.id).first()
    if not pharmacy:
        raise HTTPException(status_code=404, detail="داروخانه‌ای ثبت نکرده‌اید")
    return pharmacy

@router.get("/inventory", response_model=List[InventoryOut])
def get_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
):
    pharmacy = db.query(Pharmacy).filter(Pharmacy.owner_id == current_user.id).first()
    if not pharmacy:
        raise HTTPException(status_code=404, detail="ابتدا داروخانه خود را ثبت کنید")

    rows = (
        db.query(Inventory, Medicine)
        .join(Medicine, Inventory.medicine_id == Medicine.id)
        .filter(Inventory.pharmacy_id == pharmacy.id)
        .all()
    )
    return [
        InventoryOut(
            medicine_id=m.id,
            medicine_name=m.name,
            quantity=inv.quantity,
            price=inv.price,
            updated_at=inv.updated_at,
        )
        for inv, m in rows
    ]

@router.put("/inventory/{medicine_id}", response_model=InventoryOut)
def update_inventory(
    medicine_id: int,
    data: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
):
    pharmacy = db.query(Pharmacy).filter(Pharmacy.owner_id == current_user.id).first()
    if not pharmacy:
        raise HTTPException(status_code=404, detail="ابتدا داروخانه خود را ثبت کنید")

    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="دارو یافت نشد")

    inv = db.query(Inventory).filter(
        Inventory.pharmacy_id == pharmacy.id,
        Inventory.medicine_id == medicine_id,
    ).first()

    if inv:
        inv.quantity = data.quantity
        if data.price is not None:
            inv.price = data.price
    else:
        inv = Inventory(
            pharmacy_id=pharmacy.id,
            medicine_id=medicine_id,
            quantity=data.quantity,
            price=data.price,
        )
        db.add(inv)

    db.commit()
    db.refresh(inv)
    return InventoryOut(
        medicine_id=medicine.id,
        medicine_name=medicine.name,
        quantity=inv.quantity,
        price=inv.price,
        updated_at=inv.updated_at,
    )

@router.delete("/inventory/{medicine_id}", status_code=204)
def remove_inventory(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
):
    pharmacy = db.query(Pharmacy).filter(Pharmacy.owner_id == current_user.id).first()
    if not pharmacy:
        raise HTTPException(status_code=404, detail="ابتدا داروخانه خود را ثبت کنید")

    inv = db.query(Inventory).filter(
        Inventory.pharmacy_id == pharmacy.id,
        Inventory.medicine_id == medicine_id,
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="این دارو در موجودی شما نیست")

    db.delete(inv)
    db.commit()
