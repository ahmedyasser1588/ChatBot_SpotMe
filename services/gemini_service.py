from google import genai
from google.genai import types
from typing import List, Dict, Any
from config import settings
from services.player_service import PlayerService
from models.schemas import ChatMessage

class GeminiService:
    def __init__(self, player_service: PlayerService):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.player_service = player_service
        
        with open(settings.SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

    def chat(self, messages: List[ChatMessage]) -> str:
        formatted_contents = []
        for msg in messages:
            role = "user" if msg.role.lower() in ["user", "human"] else "model"
            formatted_contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.content)]
                )
            )

        tools = [
            self.player_service.database_overview,
            self.player_service.query_players,
            self.player_service.get_player,
            self.player_service.stats_for
        ]

        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            tools=tools,
            temperature=0.2
        )

        # النماذج المتاحة والمؤكدة في حسابك بالترتيب
        candidate_models = [
            "models/gemini-2.5-flash",
            "models/gemini-2.5-pro",
            "models/gemini-3.5-flash"
        ]

        last_exception = None
        for model_name in candidate_models:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=formatted_contents,
                    config=config
                )
                return response.text or "لم يتم إرجاع أي نص من النموذج."
            except Exception as e:
                last_exception = e
                print(f"[Warning]: فشل الطلب باستخدام {model_name}، جاري المحاولة باستخدام النموذج التالي... التفاصيل: {e}")

        # إذا فشلت كل المحاولات
        print(f"\n[Gemini Error Details]: {last_exception}\n")
        raise last_exception