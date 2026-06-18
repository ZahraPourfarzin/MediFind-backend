from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from math import radians, cos, sin, asin, sqrt
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import User, Medicine, Pharmacy, Inventory, Prescription
from ..schemas.schemas import SearchResult, MedicineOut, PharmacyWithDistance

router = APIRouter(prefix="/search", tags=["جستجو"])

def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """فاصله دو نقطه جغرافیایی به کیلومتر"""
    R = 6371
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    return 2 * R * asin(sqrt(a))

# ─── جستجوی دارو بر اساس اسم ─────────────────────────────────────────────────

@router.get("/medicines", response_model=List[MedicineOut])
def search_medicines(
    name: str = Query(..., min_length=2, description="نام دارو"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = db.query(Medicine).filter(
        Medicine.name.ilike(f"%{name}%")
    ).limit(20).all()

    # به‌جای خطا، لیست خالی برمی‌گردونیم تا فرانت‌اند پیام "یافت نشد" را نشان دهد
    return results

# ─── داروخانه‌های نزدیک که دارو دارند ───────────────────────────────────────

@router.get("/pharmacies", response_model=SearchResult)
def find_pharmacies(
    medicine_id: int   = Query(..., description="شناسه دارو"),
    # موقعیت GPS (خودکار از مرورگر)
    lat: Optional[float] = Query(None, description="عرض جغرافیایی GPS"),
    lng: Optional[float] = Query(None, description="طول جغرافیایی GPS"),
    # موقعیت دستی (شهر)
    city: Optional[str]  = Query(None, description="نام شهر (اگه GPS نداری)"),
    radius_km: float     = Query(10.0, description="شعاع جستجو به کیلومتر"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # باید حداقل یکی از GPS یا شهر داده بشه
    if lat is None and city is None:
        raise HTTPException(
            status_code=400,
            detail="باید موقعیت GPS یا نام شهر را ارسال کنید"
        )

    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="دارو یافت نشد")

    # شهروند برای داروی نسخه‌دار باید نسخه تأیید شده داشته باشه
    #if medicine.requires_prescription and current_user.role == "citizen":
        approved = db.query(Prescription).filter(
            Prescription.user_id == current_user.id,
            Prescription.status == "approved"
        ).first()
        if not approved:
            raise HTTPException(
                status_code=403,
                detail="این دارو نسخه‌دار است. ابتدا نسخه پزشکی خود را آپلود و منتظر تأیید باشید"
            )

    # فیلتر موجودی
    query = (
        db.query(Inventory, Pharmacy)
        .join(Pharmacy, Inventory.pharmacy_id == Pharmacy.id)
        .filter(
            Inventory.medicine_id == medicine_id,
            Inventory.quantity > 0,
            Pharmacy.is_active == True,
        )
    )

    # اگه شهر داده شده فیلتر بزن
    if city:
        query = query.filter(Pharmacy.city.ilike(f"%{city}%"))

    inventories = query.all()

    results = []
    for inv, pharmacy in inventories:
        if lat is not None and lng is not None:
            # حالت GPS: فیلتر بر اساس شعاع
            distance = haversine(lat, lng, pharmacy.lat, pharmacy.lng)
            if distance > radius_km:
                continue
        else:
            # حالت شهر: فاصله نمایشی نداریم، صفر میذاریم
            distance = 0.0

        results.append(PharmacyWithDistance(
            id=pharmacy.id,
            name=pharmacy.name,
            address=pharmacy.address,
            city=pharmacy.city,
            phone=pharmacy.phone,
            lat=pharmacy.lat,
            lng=pharmacy.lng,
            is_active=pharmacy.is_active,
            distance_km=round(distance, 2),
            quantity=inv.quantity,
            price=inv.price,
        ))

    # مرتب‌سازی بر اساس فاصله
    results.sort(key=lambda x: x.distance_km)

    return SearchResult(
        medicine=MedicineOut.model_validate(medicine),
        pharmacies=results,
    )
