from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

# ─── نقش‌های کاربری ────────────────────────────────────────────────────────
# citizen    → شهروند عادی
# rescuer    → امدادگر
# pharmacist → داروخانه‌دار

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    full_name       = Column(String(100), nullable=False)
    phone           = Column(String(15),  unique=True, nullable=False, index=True)
    username        = Column(String(50),  unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(String(20),  nullable=False, default="citizen")
    is_active       = Column(Boolean, default=False)   # تا تأیید نشده غیرفعاله
    created_at      = Column(DateTime, server_default=func.now()) # اصلاح شد

    # فیلدهای اضافه برای تأیید هویت
    rescuer_code    = Column(String(50),  nullable=True)
    rescuer_verified = Column(Boolean,  default=False)
    medical_system_code = Column(String(50), nullable=True)
    pharmacist_verified = Column(Boolean, default=False)

    pharmacy        = relationship("Pharmacy",     back_populates="owner",    uselist=False)
    prescriptions   = relationship("Prescription", back_populates="user")


class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(150), nullable=False)
    address     = Column(Text,        nullable=False)
    city        = Column(String(100), nullable=False)
    phone       = Column(String(15))
    lat         = Column(Float,       nullable=False)
    lng         = Column(Float,       nullable=False)
    is_active   = Column(Boolean, default=True)
    owner_id    = Column(Integer, ForeignKey("users.id"), unique=True)
    created_at  = Column(DateTime, server_default=func.now()) # اصلاح شد

    owner       = relationship("User",        back_populates="pharmacy")
    inventory   = relationship("Inventory", back_populates="pharmacy")


class Medicine(Base):
    __tablename__ = "medicines"

    id                  = Column(Integer, primary_key=True, index=True)
    name                = Column(String(200), nullable=False, index=True)
    generic_name        = Column(String(200))
    category            = Column(String(100))
    requires_prescription = Column(Boolean, default=False)
    description         = Column(Text)
    created_at          = Column(DateTime, server_default=func.now()) # اصلاح شد

    inventory = relationship("Inventory", back_populates="medicine")


class Inventory(Base):
    __tablename__ = "inventory"

    id          = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"),  nullable=False)
    quantity    = Column(Integer, default=0)
    price       = Column(Float)
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now()) # اصلاح شد

    pharmacy = relationship("Pharmacy", back_populates="inventory")
    medicine = relationship("Medicine", back_populates="inventory")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_url   = Column(String(500), nullable=False)
    status      = Column(String(20),  default="pending")
    note        = Column(Text)
    created_at  = Column(DateTime, server_default=func.now()) # اصلاح شد

    user = relationship("User", back_populates="prescriptions")