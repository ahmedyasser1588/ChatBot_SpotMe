import json
from typing import Dict, List, Any, Optional
from config import settings

class PlayerService:
    SPORTS = ["football", "basketball", "handball", "volleyball"]

    def __init__(self, data_path: str = settings.DATA_PATH):
        with open(data_path, "r", encoding="utf-8") as f:
            self._data: Dict[str, List[Dict[str, Any]]] = json.load(f)

    def get_all_players(self, sport: Optional[str] = None) -> List[Dict[str, Any]]:
        if sport and sport.lower() in self.SPORTS:
            return self._data.get(sport.lower(), [])
        return [player for s in self.SPORTS for player in self._data.get(s, [])]

    def query_players(
        self,
        sport: Optional[str] = None,
        name_contains: Optional[str] = None,
        club_contains: Optional[str] = None,
        position: Optional[str] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        min_ai_score: Optional[float] = None,
        max_ai_score: Optional[float] = None,
        min_height_cm: Optional[float] = None,
        max_height_cm: Optional[float] = None,
        max_injuries: Optional[int] = None,
        min_recovery: Optional[float] = None,
        sort_by: Optional[str] = "ai_score",
        order: Optional[str] = "desc",
        limit: Optional[int] = 10
    ) -> Dict[str, Any]:
        """البحث والفلترة والترتيب في قائمة لاعبي SpotMe."""
        rows = self.get_all_players(sport)

        def includes(val: Any, needle: str) -> bool:
            return needle.lower() in str(val or "").lower()

        if name_contains:
            rows = [p for p in rows if includes(p.get("name"), name_contains)]
        if club_contains:
            rows = [p for p in rows if includes(p.get("current_club"), club_contains)]
        if position:
            rows = [p for p in rows if includes(p.get("position"), position)]
        if min_age is not None:
            rows = [p for p in rows if p.get("age", 0) >= min_age]
        if max_age is not None:
            rows = [p for p in rows if p.get("age", 0) <= max_age]
        if min_ai_score is not None:
            rows = [p for p in rows if p.get("ai_score", 0) >= min_ai_score]
        if max_ai_score is not None:
            rows = [p for p in rows if p.get("ai_score", 0) <= max_ai_score]
        if min_height_cm is not None:
            rows = [p for p in rows if p.get("height_cm", 0) >= min_height_cm]
        if max_height_cm is not None:
            rows = [p for p in rows if p.get("height_cm", 0) <= max_height_cm]
        if max_injuries is not None:
            rows = [p for p in rows if p.get("injuries_last_2y", 0) <= max_injuries]
        if min_recovery is not None:
            rows = [p for p in rows if p.get("recovery_percentage", 0) >= min_recovery]

        total = len(rows)
        sort_by_field = sort_by or "ai_score"
        reverse = (order or "desc").lower() != "asc"

        def sort_key(player: Dict[str, Any]):
            val = player.get(sort_by_field)
            if isinstance(val, (int, float)):
                return (0, val)
            return (1, str(val or ""))

        rows.sort(key=sort_key, reverse=reverse)
        lim = min(max(limit or 10, 1), 50)
        
        return {
            "total_matches": total,
            "returned": min(lim, total),
            "players": rows[:lim]
        }

    def get_player(self, id_or_name: str) -> Dict[str, Any]:
        """البحث عن لاعب واحد بالاسم أو المعرف (ID)"""
        rows = self.get_all_players()
        target = id_or_name.lower()
        
        for p in rows:
            if str(p.get("player_id", "")).lower() == target:
                return p
        for p in rows:
            if target in str(p.get("name", "")).lower():
                return p
                
        return {"error": "لم يتم العثور على لاعب بهذا الاسم أو الرقم في قاعدة بيانات SpotMe"}

    def stats_for(self, sport: Optional[str] = None, metric: str = "ai_score") -> Dict[str, Any]:
        """حساب الإحصائيات لمؤشر معين"""
        rows = [p for p in self.get_all_players(sport) if isinstance(p.get(metric), (int, float))]
        if not rows:
            return {"error": f"لا توجد بيانات رقمية للمؤشر {metric}"}

        values = [float(p[metric]) for p in rows]
        values_sorted = sorted(values)
        total_sum = sum(values)
        best_player = max(rows, key=lambda x: x[metric])

        return {
            "sport": sport or "all",
            "metric": metric,
            "count": len(rows),
            "average": round(total_sum / len(values), 2),
            "median": values_sorted[len(values_sorted) // 2],
            "min": values_sorted[0],
            "max": values_sorted[-1],
            "top_player": {
                "name": best_player.get("name"),
                "player_id": best_player.get("player_id"),
                "value": best_player.get(metric)
            }
        }

    def database_overview(self) -> Dict[str, Any]:
        """عرض نظرة عامة شاملة على قاعدة البيانات"""
        sports_summary = []
        for s in self.SPORTS:
            players = self._data.get(s, [])
            if players:
                fields = list(players[0].keys())
                clubs = list(set(p.get("current_club") for p in players if p.get("current_club")))
                positions = list(set(p.get("position") for p in players if p.get("position")))
            else:
                fields, clubs, positions = [], [], []

            sports_summary.append({
                "sport": s,
                "players": len(players),
                "fields": fields,
                "clubs": clubs,
                "positions": positions
            })

        return {
            "sports": sports_summary,
            "total_players": len(self.get_all_players())
        }