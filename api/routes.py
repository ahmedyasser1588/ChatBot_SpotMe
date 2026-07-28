from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, QueryPlayersInput, MetricStatsInput
from services.player_service import PlayerService
from services.gemini_service import GeminiService

router = APIRouter()

# إعداد الخدمات (Dependency Injection)
player_service = PlayerService()
gemini_service = GeminiService(player_service=player_service)

@router.post("/chat")
async def chat(request: ChatRequest):
    """مسار الدردشة مع مساعد SpotMe الذكي"""
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages is required")

    try:
        # إرجاع رد نصي عادي يظهر بسهولة في Swagger UI
        return gemini_service.chat(request.messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_players(input_data: QueryPlayersInput):
    """مسار البحث المباشر عن اللاعبين وفلترتهم"""
    return player_service.query_players(input_data.model_dump(exclude_none=True))

@router.get("/players/{id_or_name}")
async def get_player_details(id_or_name: str):
    """مسار جلب تفاصيل لاعب محدد"""
    res = player_service.get_player(id_or_name)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.get("/overview")
async def get_overview():
    """مسار جلب نظرة عامة على قاعدة البيانات"""
    return player_service.database_overview()

@router.post("/stats")
async def get_metric_stats(input_data: MetricStatsInput):
    """مسار جلب إحصائيات مؤشر معين"""
    return player_service.stats_for(sport=input_data.sport, metric=input_data.metric)