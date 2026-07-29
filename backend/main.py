"""
backend/main.py
=====================================================================
الـ API اللي التيم هيتعامل معاه. مش المفروض حد بره الـ RAG module يعرف
تفاصيل ingest/retrieve/generate - كل اللي محتاجينه: يبعتوا سؤال،
يرجعلهم جواب.
=====================================================================
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .generate import generate_answer

load_dotenv()

app = FastAPI(
    title="SPOTME Scout Assistant API",
    description="RAG chatbot بيدور على لاعبين بناءً على سؤال طبيعي باللغة العربية.",
    version="1.0.0",
)

# لازم تحدد الـ origins الحقيقية بتاعة الـ frontend في .env
# (ALLOWED_ORIGINS=https://spotme.app,http://localhost:3000)
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)


class ChatResponse(BaseModel):
    answer: str


@app.get("/health")
def health():
    """للتأكد إن السيرفر شغال قبل أي حاجة تانية."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    نقطة الدخول الوحيدة للتيم:
    Request:  {"question": "مين أحسن لاعب في الباسكت؟", "top_k": 5}
    Response: {"answer": "..."}
    """
    try:
        answer = generate_answer(req.question, top_k=req.top_k)
    except ValueError as e:
        # سؤال فاضي أو غير صالح - خطأ من المستخدم
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # مشكلة في الـ vector store أو في Gemini API - خطأ من السيرفر
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ غير متوقع: {e}")

    return ChatResponse(answer=answer)
