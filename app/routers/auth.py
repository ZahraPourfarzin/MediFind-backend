from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import verify_password, hash_password, create_access_token, get_current_user
from ..models.models import User
from ..schemas.schemas import (
    CitizenRegister, RescuerRegister, PharmacistRegister,
    LoginRequest, TokenResponse, UserOut
)

router = APIRouter(prefix="/auth", tags=["احراز هویت"])

# ─── helper ──────────────────────────────────────────────────────────────────

def _check_duplicate(db: Session, phone: str, username: str):
    if db.query(User).filter(User.phone == phone).first():
        raise HTTPException(status_code=400, detail="این شماره تلفن قبلاً ثبت شده است")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="این نام کاربری قبلاً استفاده شده است")

# ─── ثبت‌نام شهروند ───────────────────────────────────────────────────────────

@router.post("/register/citizen", response_model=UserOut, status_code=201)
def register_citizen(data: CitizenRegister, db: Session = Depends(get_db)):
    _check_duplicate(db, data.phone, data.username)
    user = User(
        full_name=data.full_name,
        phone=data.phone,
        username=data.username,
        hashed_password=hash_password(data.password),
        role="citizen",
        is_active=True,   # شهروند بلافاصله فعاله
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ─── ثبت‌نام داروخانه‌دار ─────────────────────────────────────────────────────

@router.post("/register/pharmacist", response_model=UserOut, status_code=201)
def register_pharmacist(data: PharmacistRegister, db: Session = Depends(get_db)):
    _check_duplicate(db, data.phone, data.username)
    user = User(
        full_name=data.full_name,
        phone=data.phone,
        username=data.username,
        hashed_password=hash_password(data.password),
        role="pharmacist",
        medical_system_code=data.medical_system_code,
        is_active=False,          # تا ادمین تأیید نکنه غیرفعاله
        pharmacist_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# ─── لاگین (یکسان برای همه نقش‌ها) ──────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == data.phone).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="شماره تلفن یا رمز عبور اشتباه است")

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="حساب شما هنوز تأیید نشده است. منتظر بررسی توسط ادمین باشید"
        )

    token = create_access_token({"sub": str(user.id), "role": user.role})

    is_verified = True

    if user.role == "pharmacist":
        is_verified = user.pharmacist_verified

    return TokenResponse(
        access_token=token,
        role=user.role,
        full_name=user.full_name,
        is_verified=is_verified,
    )

# ─── پروفایل کاربر جاری ──────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
