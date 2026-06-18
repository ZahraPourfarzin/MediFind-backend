# routers/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
from ..core.config import settings

load_dotenv()

router = APIRouter(prefix="/chat", tags=["چت"])

class ChatRequest(BaseModel):
    message: str
    history: list[dict]

class ChatResponse(BaseModel):
    reply: str

# تنظیم کلید به روش قدیمی
openai.api_key = settings.gapgpt_api_key
# اگر gapgpt آدرس خاصی نیاز داره، این خط رو اضافه کن
openai.api_base = "https://api.gapgpt.app/v1"

@router.post("/ask", response_model=ChatResponse)
async def ask_ai(request: ChatRequest):
    try:
        messages = [
            {"role": "system", "content": "تو یک دستیار هوشمند برای سامانه دارویی MediFind هستی."}
        ]
        for msg in request.history:
            messages.append(msg)
        messages.append({"role": "user", "content": request.message})

        # استفاده از روش قدیمی
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
        )
        reply = response.choices[0].message.content
        return ChatResponse(reply=reply)

    except Exception as e:
        print(f"❌ خطا: {e}")
        raise HTTPException(status_code=500, detail=str(e))