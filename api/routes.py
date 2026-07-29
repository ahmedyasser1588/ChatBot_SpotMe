from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from services.groq_service import run_groq_chat, player_service

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class SearchRequest(BaseModel):
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

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    response = run_groq_chat(request.messages)
    return {"response": response}

@router.post("/search")
async def search_endpoint(request: SearchRequest):
    return player_service.query_players(**request.dict(exclude_unset=True))

@router.get("/players/{id_or_name}")
async def get_player_endpoint(id_or_name: str):
    return player_service.get_player(id_or_name)

@router.get("/overview")
async def database_overview_endpoint():
    return player_service.database_overview()