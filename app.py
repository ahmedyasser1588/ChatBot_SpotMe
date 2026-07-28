from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router

# إنشاء تطبيق FastAPI
app = FastAPI(
    title="SpotMe Scouting API",
    version="1.0.0",
    description="Backend service for SpotMe talent discovery powered by FastAPI and Google Gemini API."
)

# إعداد CORS للسماح بالاتصال من أي واجهة أمامية
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # يتيح لأي موقع/تطبيق الاتصال بالـ API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تضمين المسارات تحت البادئة /api
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    # تشغيل السيرفر على البورت 8000
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)