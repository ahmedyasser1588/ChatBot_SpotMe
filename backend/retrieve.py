"""
backend/retrieve.py
=====================================================================
Phase 2 - Retrieval (live, per question)
  Filters -> Chroma where clause -> Search/Sort -> Chunks
=====================================================================
النسخة دي بقت بتاخد الفلاتر المنظمة اللي رجعها query_parser.py (رياضة/
نادي/مركز/اسم/مقارنات رقمية/ترتيب) بدل ما تحاول تلاقط كل حالة بكود
keyword-matching منفصل. الفلترة بقت generic تمامًا: أي حقل معروف في
الداتا تقدر تفلتر عليه، بدل ما نضيف _detect_X() جديدة كل مرة نلاقي
حالة جديدة.

- لو فيه sort_by -> بنجيب كل المطابقين للفلاتر ونرتبهم رقميًا (مش
  semantic) - لأن أسئلة الترتيب محتاجة أعلى/أقل رقم فعلي، مش أقرب
  نص لغويًا.
- غير كده -> semantic search عادي، مقيّد بالفلاتر (where) لو فيه.
=====================================================================
"""

import difflib
import re
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

VECTOR_STORE_DIR = Path(__file__).parent.parent / "data" / "vector_store"
COLLECTION_NAME = "players"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

_OP_MAP = {">": "$gt", ">=": "$gte", "<": "$lt", "<=": "$lte", "==": "$eq"}

_client = None
_collection = None
_known_values_cache: dict[str, set] = {}


def _normalize_ar(text: str) -> str:
    """
    بتوحّد أشكال الحروف اللي بتختلف بين صياغات مختلفة لنفس الكلمة -
    الهمزات (أ/إ/آ) بترجع لـ ا، التاء المربوطة لـ ه، الياء المقصورة
    لـ ي، وبنشيل التشكيل والمسافات الزيادة. بدون ده، "إنبي" و"انبي"
    بيتعاملوا كقيمتين مختلفتين تمامًا رغم إنهم نفس النادي.
    """
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)  # حذف التشكيل
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ٱ", "ا")
    text = text.replace("ة", "ه").replace("ى", "ي")
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def get_collection():
    """
    بيفتح نفس الـ collection اللي عملها ingest.py، جاهزة للبحث.
    محفوظة كـ singleton (module-level cache) عشان منعملش reload لموديل
    الـ embedding من الصفر في كل سؤال.
    """
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        try:
            _collection = _client.get_collection(
                name=COLLECTION_NAME, embedding_function=embedding_fn
            )
        except Exception as e:
            raise RuntimeError(
                "مش لاقي vector store. لازم تشغل 'python -m backend.ingest' "
                "مرة واحدة الأول قبل ما تسأل أي سؤال."
            ) from e
    return _collection


def _get_known_values(field: str) -> set:
    """بيجيب كل القيم الحقيقية الموجودة لحقل معين في الداتا (مرة واحدة، بـ cache)."""
    if field not in _known_values_cache:
        collection = get_collection()
        all_data = collection.get(include=["metadatas"])
        _known_values_cache[field] = {
            m.get(field) for m in all_data["metadatas"] if m.get(field)
        }
    return _known_values_cache[field]


def _resolve_value(raw_value: str, field: str) -> str | None:
    """
    query_parser.py بيستخرج القيمة زي ما فهمها من كلام المستخدم (ممكن
    يبقى فيها أخطاء إملائية، أو شكل التشكيل/الهمزة مختلف عن المخزّن
    بالظبط). هنا بندور على أقرب قيمة *حقيقية موجودة في الداتا* على 3
    مستويات متصاعدة في التساهل:
      1. تطابق كامل بعد توحيد الشكل (همزات/تشكيل/مسافات)
      2. تطابق جزئي (القيمة جوه قيمة تانية أو العكس)
      3. تطابق تقريبي (fuzzy) بيسامح أخطاء إملائية زي حرف ناقص/زيادة/غلط
    لو مفيش تطابق واثق حتى بعد الثلاثة، بنرجع None بدل ما نستخدم قيمة
    غلط هترجع صفر نتايج.
    """
    if not raw_value:
        return None

    normalized_raw = _normalize_ar(raw_value)
    candidates = _get_known_values(field)
    if not candidates:
        return None

    normalized_map = {_normalize_ar(c): c for c in candidates}

    # 1) تطابق كامل
    if normalized_raw in normalized_map:
        return normalized_map[normalized_raw]

    # 2) تطابق جزئي
    for norm_c, original in normalized_map.items():
        if normalized_raw in norm_c or norm_c in normalized_raw:
            return original

    # 3) تطابق تقريبي (typo-tolerant) - بيمسك أخطاء إملائية بسيطة
    close = difflib.get_close_matches(
        normalized_raw, normalized_map.keys(), n=1, cutoff=0.7
    )
    if close:
        return normalized_map[close[0]]

    return None


def build_where(filters: dict) -> dict | None:
    """بيحول الفلاتر المنظمة (من query_parser) لـ Chroma where clause."""
    conditions = []

    if filters.get("sport"):
        conditions.append({"sport": filters["sport"]})
    if filters.get("club"):
        resolved_club = _resolve_value(filters["club"], "current_club")
        if resolved_club:
            conditions.append({"current_club": resolved_club})
    if filters.get("position"):
        resolved_position = _resolve_value(filters["position"], "position")
        if resolved_position:
            conditions.append({"position": resolved_position})
    if filters.get("player_name"):
        resolved_name = _resolve_value(filters["player_name"], "name")
        if resolved_name:
            conditions.append({"name": resolved_name})

    for nf in filters.get("numeric_filters") or []:
        op = _OP_MAP.get(nf["op"])
        if op:
            conditions.append({nf["field"]: {op: nf["value"]}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


# ---------------------------------------------------------------
# STAGE: Sorted retrieval (metadata filter + sort رقمي، مش semantic)
# ---------------------------------------------------------------
def _get_sorted(where: dict | None, sort_by: str, sort_direction: str, top_k: int) -> list[dict]:
    """بيجيب كل اللاعبين المطابقين للفلاتر ويرتبهم حسب sort_by."""
    collection = get_collection()
    results = collection.get(where=where, include=["documents", "metadatas"])

    players = []
    for i in range(len(results["ids"])):
        players.append({
            "id": results["ids"][i],
            "text": results["documents"][i],
            "metadata": results["metadatas"][i],
            "distance": None,  # مش نتيجة semantic search - مرتّبة رقميًا
        })

    def value_of(p: dict) -> float:
        try:
            return float(p["metadata"].get(sort_by, 0))
        except (TypeError, ValueError):
            return float("-inf")

    players.sort(key=value_of, reverse=(sort_direction != "asc"))
    return players[:top_k]


# ---------------------------------------------------------------
# STAGE: Question -> Embed Query -> Search -> Chunks (semantic، مع فلترة اختيارية)
# ---------------------------------------------------------------
def _semantic_search(question: str, top_k: int, where: dict | None) -> list[dict]:
    collection = get_collection()
    query_kwargs = {"query_texts": [question], "n_results": top_k}
    if where:
        query_kwargs["where"] = where
    results = collection.query(**query_kwargs)

    relevant_players = []
    for i in range(len(results["ids"][0])):
        relevant_players.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],  # أصغر رقم = أقرب معنى
        })
    return relevant_players


def get_relevant_players(question: str, filters: dict, top_k: int = 5) -> list[dict]:
    """
    نقطة الدخول من generate.py. بياخد الفلاتر جاهزة من query_parser.py
    (مش بيحاول يفهمها بنفسه) ويقرر الاستراتيجية:
    - فيه sort_by -> ranking retrieval (sort رقمي)
    - غير كده -> semantic search، مقيّد بالفلاتر لو فيها
    """
    if not question or not question.strip():
        return []

    where = build_where(filters)

    if filters.get("sort_by"):
        sorted_players = _get_sorted(
            where, filters["sort_by"], filters.get("sort_direction") or "desc", top_k
        )
        if sorted_players:
            return sorted_players
        # لو الفلاتر دي مفيش لاعبين مطابقين، نكمل بالـ semantic كـ fallback

    return _semantic_search(question, top_k, where)


# ---------------------------------------------------------------
# STAGE: Aggregation (كام لاعب / متوسط / أعلى / أقل - حساب مباشر)
# ---------------------------------------------------------------
def compute_aggregation(filters: dict) -> dict:
    """
    أسئلة زي "كام لاعب في الأهلي؟" مش أسئلة retrieval أصلًا - هي أسئلة
    حسابية على الداتا كلها. بنحسبها مباشرة بدل ما نمررها كـ RAG عادي
    (لأن أي top_k محدود هيدي رقم غلط لأي سؤال تجميعي).
    """
    collection = get_collection()
    where = build_where(filters)
    results = collection.get(where=where, include=["metadatas"])
    metadatas = results["metadatas"]

    agg_type = filters.get("aggregation_type") or "count"
    agg_field = filters.get("aggregation_field")

    if agg_type == "count" or not agg_field:
        return {"type": "count", "field": None, "value": len(metadatas), "matched_count": len(metadatas)}

    values = []
    for m in metadatas:
        try:
            values.append(float(m.get(agg_field)))
        except (TypeError, ValueError):
            continue

    if not values:
        return {"type": agg_type, "field": agg_field, "value": None, "matched_count": len(metadatas)}

    if agg_type == "average":
        value = sum(values) / len(values)
    elif agg_type == "max":
        value = max(values)
    elif agg_type == "min":
        value = min(values)
    else:
        value = len(metadatas)

    return {
        "type": agg_type,
        "field": agg_field,
        "value": round(value, 2),
        "matched_count": len(metadatas),
    }


# ---------------------------------------------------------------
# تجربة سريعة
# ---------------------------------------------------------------
if __name__ == "__main__":
    from .query_parser import parse_query

    for question in [
        "مين أحسن لاعب في الباسكت؟",
        "عايز لاعب بيلعب في إنبي",
        "كام لاعب في الأهلي؟",
    ]:
        print(f"Question: {question}")
        filters = parse_query(question)
        print("Filters:", filters)

        if filters.get("is_aggregation"):
            print("Aggregation result:", compute_aggregation(filters))
        else:
            results = get_relevant_players(question, filters, top_k=5)
            for r in results:
                print(f"  - {r['metadata']['name']} ({r['metadata'].get('current_club')})")
        print()
