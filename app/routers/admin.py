from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..core.security import require_role
from ..models.models import User
from ..schemas.schemas import UserOut

router = APIRouter(prefix="/admin", tags=["ادمین"])

# نکته: در این پروژه ادمین = امدادگر تأیید‌شده است
# می‌تونی بعداً نقش admin جداگانه اضافه کنی

@router.get("/pending", response_model=List[UserOut])
def get_pending_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("rescuer")),
):
    """لیست کاربرانی که منتظر تأیید هستند"""
    return (
        db.query(User)
        .filter(
            User.is_active == False,
            User.role.in_(["rescuer", "pharmacist"])
        )
        .all()
    )

@router.patch("/verify/{user_id}")
def verify_user(
    user_id: int,
    approve: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("rescuer")),
):
    """تأیید یا رد ثبت‌نام امدادگر / داروخانه‌دار"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")
    if user.role not in ("rescuer", "pharmacist"):
        raise HTTPException(status_code=400, detail="فقط امدادگر و داروخانه‌دار نیاز به تأیید دارند")

    if approve:
        user.is_active = True
        if user.role == "rescuer":
            user.rescuer_verified = True
        elif user.role == "pharmacist":
            user.pharmacist_verified = True
        msg = "کاربر تأیید شد"
    else:
        user.is_active = False
        msg = "کاربر رد شد"

    db.commit()
    return {"message": msg, "user_id": user_id, "role": user.role}
