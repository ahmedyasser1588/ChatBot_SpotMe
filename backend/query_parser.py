"""
backend/query_parser.py
=====================================================================
Query Understanding
  Question -> Gemini (structured output) -> فلاتر منظمة (JSON)
=====================================================================
بدل ما نلاقط كل حالة (رياضة، نادي، مركز، عمر، ترتيب، تجميع...) بكود
keyword-matching منفصل لكل حقل - أسلوب بيتوسع وبيتكسر كل ما نلاقي حالة
جديدة - بنبعت السؤال لـ Gemini ونطلب منه JSON منظم بالـ "structured
output" الرسمي بتاع الـ API (response_schema)، فمضمون شكل الرد.

ده بيغطي مرة واحدة: رياضة، نادي، مركز، اسم لاعب، مقارنات رقمية
(أكبر من/أقل من)، ترتيب حسب أي حقل، وأسئلة تجميع (كام لاعب/متوسط).
=====================================================================
"""

import json
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

# بنحمّل .env هنا مباشرة (مش بس في main.py) عشان الملف ده يشتغل لوحده
# برضه لو حد شغّله standalone (زي python -m backend.retrieve) من غير
# ما يمر على FastAPI startup خالص.
load_dotenv()

MODEL_NAME = "gemini-2.5-flash"

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY مش موجود في environment variables.")
        _client = genai.Client(api_key=api_key)
    return _client


# القيم الحقيقية الموجودة في الداتا - بنديها لـ Gemini عشان يحول صياغة
# المستخدم الحرة ("حارس مرمى") لنفس القيمة المخزنة بالظبط ("GK")
KNOWN_SPORTS = ["Football", "Basketball", "Handball", "Volleyball"]

KNOWN_POSITIONS = {
    "Football": ["GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST"],
    "Basketball": ["PG", "SG", "SF", "PF", "C"],
    "Handball": [
        "Goalkeeper", "Left Back", "Right Back", "Center Back",
        "Left Wing", "Right Wing", "Line Player",
    ],
    "Volleyball": ["Setter", "Outside Hitter", "Opposite", "Middle Blocker", "Libero"],
}

NUMERIC_FIELDS = [
    "age", "height_cm", "weight_kg", "injuries_last_2y", "recovery_percentage",
    "ai_score", "monthly_improvement_pct", "profile_views_last_week",
    "speed_kmh", "pass_accuracy_pct", "shot_accuracy_pct",
    "points_per_game", "rebounds_per_game", "assists_per_game", "three_point_pct",
    "goals_per_game", "save_percentage",
    "attack_pct", "block_pct", "serve_pct",
]

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "sport": {"anyOf": [{"type": "string", "enum": KNOWN_SPORTS}, {"type": "null"}]},
        "club": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "position": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "player_name": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "numeric_filters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string", "enum": NUMERIC_FIELDS},
                    "op": {"type": "string", "enum": [">", ">=", "<", "<=", "=="]},
                    "value": {"type": "number"},
                },
                "required": ["field", "op", "value"],
            },
        },
        "sort_by": {"anyOf": [{"type": "string", "enum": NUMERIC_FIELDS}, {"type": "null"}]},
        "sort_direction": {"anyOf": [{"type": "string", "enum": ["asc", "desc"]}, {"type": "null"}]},
        "is_aggregation": {"type": "boolean"},
        "aggregation_type": {
            "anyOf": [{"type": "string", "enum": ["count", "average", "max", "min"]}, {"type": "null"}]
        },
        "aggregation_field": {"anyOf": [{"type": "string", "enum": NUMERIC_FIELDS}, {"type": "null"}]},
    },
    "required": [
        "sport", "club", "position", "player_name", "numeric_filters",
        "sort_by", "sort_direction", "is_aggregation", "aggregation_type", "aggregation_field",
    ],
}

SYSTEM_INSTRUCTIONS = f"""
إنت query parser لقاعدة بيانات لاعبين رياضيين. مهمتك الوحيدة: تحول سؤال
المستخدم لفلاتر JSON منظمة - من غير ما تجاوب على السؤال نفسه.

الرياضات المتاحة بالظبط: {KNOWN_SPORTS}
المراكز المتاحة لكل رياضة بالظبط: {json.dumps(KNOWN_POSITIONS, ensure_ascii=False)}
الحقول الرقمية المتاحة بالظبط: {NUMERIC_FIELDS}

قواعد مهمة:
1. استخدم بس القيم اللي في القوايم دي بالظبط (مش ترجمة حرة). مثلاً "حارس
   مرمى" في فوتبول -> "GK"، وفي هاندبول -> "Goalkeeper".
2. لو مش متأكد من قيمة حقل، سيبه null - ممنوع تخمن أو تخترع قيمة.
3. numeric_filters بس للمقارنات الصريحة ("أكبر من 25 سنة" -> age > 25).
   ممنوع تحط فيها فلتر لحقل نوع اللاعب (زي الرياضة أو المركز).
4. sort_by يتحط بس لو السؤال بيطلب ترتيب/أفضلية ("أحسن"، "أعلى"، "أقل").
5. is_aggregation = true بس لو السؤال بيسأل عن رقم إجمالي (كام لاعب،
   متوسط، أعلى قيمة، أقل قيمة) مش عن قايمة لاعبين بالاسم.
6. لو السؤال عادي وبيدور على لاعبين بالوصف من غير فلاتر واضحة، سيب كل
   الحقول null و is_aggregation=false - وده أمر طبيعي وصحيح.
""".strip()


def _empty_filters() -> dict:
    return {
        "sport": None,
        "club": None,
        "position": None,
        "player_name": None,
        "numeric_filters": [],
        "sort_by": None,
        "sort_direction": None,
        "is_aggregation": False,
        "aggregation_type": None,
        "aggregation_field": None,
    }


def parse_query(question: str) -> dict:
    """
    بيبعت السؤال لـ Gemini ويرجع فلاتر منظمة. لو أي حاجة فشلت (شبكة،
    JSON غير متوقع، الخ)، بنرجع فلاتر فاضية بدل ما نوقف الـ pipeline -
    وده بيرجّعنا لسلوك semantic search عادي بدون فلاتر، أأمن من كسر
    السيرفر.
    """
    question = (question or "").strip()
    if not question:
        return _empty_filters()

    try:
        client = get_client()
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"سؤال المستخدم:\n{question}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTIONS,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
                temperature=0,
            ),
        )
        parsed = json.loads(response.text)
    except Exception as e:
        # بنطبع السبب الحقيقي في stderr عشان تظهر وقت التطوير/الاختبار،
        # وبنرجع فلاتر فاضية عشان السيرفر مايوقفش لو حصلت مشكلة شبكة
        # أو rate limit في بيئة الإنتاج.
        print(f"[query_parser] فشل الـ parsing: {type(e).__name__}: {e}", file=sys.stderr)
        return _empty_filters()

    defaults = _empty_filters()
    defaults.update({k: v for k, v in parsed.items() if k in defaults})

    # فلترة أمان: نتأكد إن numeric_filters فيها بس حقول معروفة وoperators صالحة
    safe_filters = []
    for nf in defaults.get("numeric_filters") or []:
        if (
            isinstance(nf, dict)
            and nf.get("field") in NUMERIC_FIELDS
            and nf.get("op") in (">", ">=", "<", "<=", "==")
            and isinstance(nf.get("value"), (int, float))
        ):
            safe_filters.append(nf)
    defaults["numeric_filters"] = safe_filters

    return defaults


# ---------------------------------------------------------------
# تجربة سريعة
# ---------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        "مين أحسن لاعب في الباسكت؟",
        "عايز لاعب بيلعب في إنبي",
        "لاعب فوتبول أكبر من 30 سنة ودقة تمريره فوق 85%",
        "كام لاعب في الأهلي؟",
        "متوسط عمر لاعبين الباسكت؟",
        "عايز حارس مرمى كويس",
    ]
    for q in tests:
        print(q)
        print(json.dumps(parse_query(q), ensure_ascii=False, indent=2))
        print()
