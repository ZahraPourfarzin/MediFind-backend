from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

# ─── Auth ────────────────────────────────────────────────────────────────────

class CitizenRegister(BaseModel):
    full_name: str
    phone: str
    username: str
    password: str

class RescuerRegister(BaseModel):
    full_name: str
    phone: str
    username: str
    password: str
    rescuer_code: str          # شماره پرسنلی / مجوز امدادگر

class PharmacistRegister(BaseModel):
    full_name: str
    phone: str
    username: str
    password: str
    medical_system_code: str   # کد نظام پزشکی

class LoginRequest(BaseModel):
    phone: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    is_verified: bool          # آیا تأیید هویت شده؟

class UserOut(BaseModel):
    id: int
    full_name: str
    phone: str
    username: str
    role: str
    is_active: bool
    rescuer_verified: Optional[bool] = None
    pharmacist_verified: Optional[bool] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ─── Medicine ────────────────────────────────────────────────────────────────

class MedicineCreate(BaseModel):
    name: str
    generic_name: Optional[str] = None
    category: Optional[str] = None
    requires_prescription: bool = False
    description: Optional[str] = None

class MedicineOut(BaseModel):
    id: int
    name: str
    generic_name: Optional[str]
    category: Optional[str]
    requires_prescription: bool
    description: Optional[str]

    class Config:
        from_attributes = True

# ─── Pharmacy ────────────────────────────────────────────────────────────────

class PharmacyCreate(BaseModel):
    name: str
    address: str
    city: str
    phone: Optional[str] = None
    lat: float
    lng: float

class PharmacyOut(BaseModel):
    id: int
    name: str
    address: str
    city: str
    phone: Optional[str]
    lat: float
    lng: float
    is_active: bool

    class Config:
        from_attributes = True

class PharmacyWithDistance(PharmacyOut):
    distance_km: float
    quantity: int
    price: Optional[float]

# ─── Inventory ───────────────────────────────────────────────────────────────

class InventoryUpdate(BaseModel):
    quantity: int
    price: Optional[float] = None

class InventoryOut(BaseModel):
    medicine_id: int
    medicine_name: str
    quantity: int
    price: Optional[float]
    updated_at: datetime

    class Config:
        from_attributes = True

# ─── Prescription ────────────────────────────────────────────────────────────

class PrescriptionOut(BaseModel):
    id: int
    image_url: str
    status: str
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ─── Search ──────────────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    medicine: MedicineOut
    pharmacies: List[PharmacyWithDistance]
