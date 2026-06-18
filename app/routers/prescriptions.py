import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..core.security import get_current_user, require_role
from ..core.config import settings
from ..models.models import User, Prescription
from ..schemas.schemas import PrescriptionOut

router = APIRouter(prefix="/prescriptions", tags=["نسخه‌ها"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_MB = 5

# ─── شهروند: آپلود نسخه ──────────────────────────────────────────────────────

@router.post("/upload", response_model=PrescriptionOut, status_code=201)
async def upload_prescription(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("citizen")),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="فقط JPG، PNG و WEBP مجاز است")

    content = await file.read()
    if len(content) > MAX_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"حجم فایل نباید بیشتر از {MAX_MB} مگابایت باشد")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = (file.filename or "img").rsplit(".", 1)[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    p = Prescription(user_id=current_user.id, image_url=filepath, status="pending")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

@router.get("/my", response_model=List[PrescriptionOut])
def my_prescriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("citizen")),
):
    return (
        db.query(Prescription)
        .filter(Prescription.user_id == current_user.id)
        .order_by(Prescription.created_at.desc())
        .all()
    )

# ─── امدادگر: مشاهده و تأیید نسخه‌ها ────────────────────────────────────────

@router.get("/all", response_model=List[PrescriptionOut])
def all_prescriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("rescuer")),
):
    return db.query(Prescription).order_by(Prescription.created_at.desc()).all()

@router.patch("/{prescription_id}/verify")
def verify_prescription(
    prescription_id: int,
    new_status: str,        # approved / rejected
    note: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("rescuer")),
):
    if new_status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="وضعیت باید approved یا rejected باشد")

    p = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="نسخه یافت نشد")

    p.status = new_status
    if note:
        p.note = note
    db.commit()
    db.refresh(p)
    return p
