from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.database import engine, Base
from app.routers import auth, search, pharmacy, prescriptions, medicines, admin, chat

# ساخت خودکار جداول در SQL Server
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MediFind API",
    description="سیستم جستجوی دارو — شهروند / امدادگر / داروخانه‌دار",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://medifind-last.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads/prescriptions", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(search.router)
app.include_router(pharmacy.router)
app.include_router(prescriptions.router)
app.include_router(medicines.router)
app.include_router(admin.router)
app.include_router(chat.router)

@app.get("/", tags=["سلامت"])
def root():
    return {"status": "ok", "message": "MediFind API v2 🚀"}
