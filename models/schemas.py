from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

# نمط رسالة الدردشة
class ChatMessage(BaseModel):
    role: str  # "user" أو "model" / "assistant"
    content: str

# طلب المحادثة
class ChatRequest(BaseModel):
    messages: List[ChatMessage]

# معايير البحث والفلترة للاعبين
class QueryPlayersInput(BaseModel):
    sport: Optional[str] = None
    name_contains: Optional[str] = None
    club_contains: Optional[str] = None
    position: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    min_ai_score: Optional[float] = None
    max_ai_score: Optional[float] = None
    min_height_cm: Optional[float] = None
    max_height_cm: Optional[float] = None
    max_injuries: Optional[int] = None
    min_recovery: Optional[float] = None
    sort_by: Optional[str] = "ai_score"
    order: Optional[str] = "desc"
    limit: Optional[int] = 10

# طلب الإحصائيات لمؤشر معين
class MetricStatsInput(BaseModel):
    sport: Optional[str] = None
    metric: str