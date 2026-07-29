import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

class Settings:
    # مفتاح API الخاص بـ Google Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # مسار ملف البيانات
    DATA_PATH: str = os.getenv("DATA_PATH", "data/players.json")
    # مسار التعليمات الأساسية للنموذج (System Prompt)
    SYSTEM_PROMPT_PATH: str = os.getenv("SYSTEM_PROMPT_PATH", "prompts/system_prompt.txt")

settings = Settings()