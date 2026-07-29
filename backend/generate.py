"""
backend/generate.py
=====================================================================
Phase 3 - Generation (live, per question)
  Query Parsing -> Retrieval/Aggregation -> Context Injection ->
  Prompt Construction -> Prompt Augmentation -> LLM Response
=====================================================================
بيتشغل بعد query_parser.py و retrieve.py: بياخد فلاتر السؤال المنظمة،
يجيب بيها اللاعبين المطابقين (أو يحسب aggregation مباشرة لو السؤال
تجميعي)، يحقنهم كـ context جوه prompt، يضيف تعليمات الـ persona
(Scout Assistant)، ويبعته لـ Gemini عشان يرجع إجابة نهائية بالعربي.

يعتمد على:
    pip install google-genai
    GEMINI_API_KEY في environment variables (أو ملف .env)
=====================================================================
"""

import os

from google import genai
from google.genai import errors as genai_errors

from .query_parser import parse_query
from .retrieve import get_relevant_players, compute_aggregation

MODEL_NAME = "gemini-2.5-flash"

_client: genai.Client | None = None


def get_client() -> genai.Client:
    """بيرجع نفس الـ client في كل مرة (singleton) بدل ما نعمل واحد جديد كل سؤال."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY مش موجود في environment variables. "
                "حطه في ملف .env أو بـ: set GEMINI_API_KEY=..."
            )
        _client = genai.Client(api_key=api_key)
    return _client


# ---------------------------------------------------------------
# STAGE: Context Injection
# ---------------------------------------------------------------
def build_context(players: list[dict]) -> str:
    """بياخد الـ chunks اللي رجعها get_relevant_players() ويحولها لبلوك نص واحد."""
    if not players:
        return "لا يوجد لاعبين مطابقين في قاعدة البيانات."

    lines = []
    for i, p in enumerate(players, start=1):
        lines.append(f"[{i}] {p['text']}")
    return "\n".join(lines)


def build_aggregation_context(agg: dict) -> str:
    """
    نفس فكرة build_context بس لأسئلة التجميع (كام لاعب/متوسط/أعلى/أقل) -
    بندي Gemini الرقم المحسوب فعليًا (مش لاعبين) عشان يصيغه بجملة طبيعية،
    بدل ما نسيبه يخمن الرقم من top-k لاعبين ناقصين.
    """
    if agg["type"] == "count":
        return f"نتيجة حسابية من قاعدة البيانات: عدد اللاعبين المطابقين = {agg['value']}."

    if agg["value"] is None:
        return "نتيجة حسابية من قاعدة البيانات: لا توجد قيم رقمية كافية لحساب المطلوب."

    label = {"average": "المتوسط", "max": "أعلى قيمة", "min": "أقل قيمة"}.get(agg["type"], agg["type"])
    return (
        f"نتيجة حسابية من قاعدة البيانات: {label} لحقل '{agg['field']}' "
        f"= {agg['value']} (من إجمالي {agg['matched_count']} لاعب مطابق للفلاتر)."
    )


# ---------------------------------------------------------------
# STAGE: Prompt Construction
# ---------------------------------------------------------------
def build_base_prompt(question: str, context: str) -> str:
    return (
        f"معلومات مسترجعة من قاعدة البيانات:\n"
        f"{context}\n\n"
        f"سؤال المستخدم:\n{question}"
    )


# ---------------------------------------------------------------
# STAGE: Prompt Augmentation
# ---------------------------------------------------------------
def augment_prompt(base_prompt: str) -> str:
    """بيضيف تعليمات الـ persona (Scout Assistant) وقواعد الـ grounding."""
    system_rules = (
        "إنت Scout Assistant جوه منصة SPOTME، بتساعد سكاوتس يلاقوا لاعبين "
        "مناسبين بناءً على بيانات حقيقية بس.\n"
        "قواعد لازم تلتزم بيها:\n"
        "1. جاوب بالاعتماد فقط على المعلومات المذكورة تحت - ممنوع تختلق "
        "أي لاعب أو رقم مش موجود فيها.\n"
        "2. لو المعلومات المتاحة مش كافية للإجابة، قول ده بوضوح بدل ما تخمن.\n"
        "3. رد بالعربي، بأسلوب مختصر واحترافي مناسب لسكاوت بيقيّم لاعبين.\n"
        "4. لو في أكتر من لاعب مناسب، رتبهم حسب الأنسب للسؤال واذكر السبب باختصار.\n"
    )
    return f"{system_rules}\n{base_prompt}"


# ---------------------------------------------------------------
# STAGE: LLM Response
# ---------------------------------------------------------------
def call_llm(prompt: str) -> str:
    """بيبعت الـ prompt النهائي لـ Gemini ويرجع نص الإجابة، مع error handling عربي."""
    client = get_client()
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    except genai_errors.ClientError as e:
        if getattr(e, "code", None) == 401 or "UNAUTHENTICATED" in str(e):
            raise RuntimeError("مفتاح GEMINI_API_KEY غلط أو منتهي.") from e
        if getattr(e, "code", None) == 429:
            raise RuntimeError("تجاوزنا حد الاستخدام المسموح لـ Gemini API، حاول تاني بعد شوية.") from e
        raise RuntimeError(f"مشكلة في الاتصال بـ Gemini: {e}") from e
    except Exception as e:
        raise RuntimeError(f"مشكلة غير متوقعة أثناء توليد الإجابة: {e}") from e

    if not response.text:
        raise RuntimeError("Gemini رجع رد فاضي.")
    return response.text


# ---------------------------------------------------------------
# تشغيل المرحلة كاملة: Question -> Answer
# ---------------------------------------------------------------
def generate_answer(question: str, top_k: int = 5) -> str:
    """
    Question -> query_parser.py (فلاتر) -> retrieve.py (لاعبين أو حساب
    تجميعي) -> Context Injection -> Prompt Construction -> Prompt
    Augmentation -> LLM Response -> Answer
    """
    question = (question or "").strip()
    if not question:
        raise ValueError("السؤال فاضي.")

    filters = parse_query(question)

    if filters.get("is_aggregation"):
        agg_result = compute_aggregation(filters)
        context = build_aggregation_context(agg_result)
    else:
        players = get_relevant_players(question, filters, top_k=top_k)
        context = build_context(players)

    base_prompt = build_base_prompt(question, context)
    final_prompt = augment_prompt(base_prompt)

    return call_llm(final_prompt)


# ---------------------------------------------------------------
# تجربة سريعة
# ---------------------------------------------------------------
if __name__ == "__main__":
    for question in [
        "مين أحسن لاعب في الباسكت؟",
        "عايز لاعب بيلعب في إنبي",
        "كام لاعب في الأهلي؟",
    ]:
        print(f"Question: {question}")
        print(generate_answer(question, top_k=5))
        print()
