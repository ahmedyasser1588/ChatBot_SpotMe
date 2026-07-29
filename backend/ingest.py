"""
backend/ingest.py
=====================================================================
Phase 1 - Knowledge Ingestion (offline, ahead of time)
  Sources -> Load -> Clean -> Chunk -> Embed -> Store
=====================================================================
بيتشغل مرة واحدة (أو كل ما تتحدث بيانات اللاعبين)، مش وقت سؤال المستخدم.

بيستخدم chromadb عشان يتولى خطوتي Embed وStore عننا: بندّيله النصوص بس،
وهو داخليًا بيحوّلها لمتجهات (embeddings) بموديل sentence-transformers،
ويخزنها في مجلد data/vector_store بشكل دائم (persistent).
=====================================================================
"""

import json
import re
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

SOURCE_FILE = Path(__file__).parent.parent / "data" / "sources" / "chatbot_data.js"
VECTOR_STORE_DIR = Path(__file__).parent.parent / "data" / "vector_store"
COLLECTION_NAME = "players"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # بيدعم العربي


# ---------------------------------------------------------------
# STAGE: Sources
# ---------------------------------------------------------------
def load_sources(js_file_path: Path) -> dict:
    """يقرا data/sources/chatbot_data.js ويرجع SPORTS_DATA كـ dict بايثون."""
    text = js_file_path.read_text(encoding="utf-8")
    text = re.sub(r"^//.*\n", "", text)
    text = text.split("const SPORTS_DATA =", 1)[1].strip()
    if text.endswith(";"):
        text = text[:-1]
    return json.loads(text)


# ---------------------------------------------------------------
# STAGE: Load
# ---------------------------------------------------------------
def load_all_players(sports_data: dict) -> list[dict]:
    """بيحوّل الداتا المقسّمة برياضة لقايمة واحدة مسطحة فيها كل اللاعبين."""
    all_players = []
    for sport_name, players in sports_data.items():
        for p in players:
            p["_sport_key"] = sport_name
            all_players.append(p)
    return all_players


# ---------------------------------------------------------------
# STAGE: Clean
# ---------------------------------------------------------------
def clean_players(players: list[dict]) -> list[dict]:
    """بيشيل التكرار والبيانات الناقصة، وبيوضّح القيم الفاضية (None)."""
    seen_ids = set()
    cleaned = []
    for p in players:
        pid = p.get("player_id")
        if not pid or pid in seen_ids:
            continue
        if not p.get("name") or not p.get("sport"):
            continue
        seen_ids.add(pid)

        clean_p = {k: ("غير مسجل" if v is None else v) for k, v in p.items()}
        cleaned.append(clean_p)
    return cleaned


# ---------------------------------------------------------------
# STAGE: Chunk
# ---------------------------------------------------------------
def describe_player(p: dict) -> str:
    """بيحوّل بيانات لاعب واحد لجملة نصية وصفية (أسهل على موديل الـ embedding)."""
    sport = p.get("sport", "")
    base = (
        f"اللاعب {p['name']}، رياضة {sport}، يلعب في نادي {p.get('current_club', 'غير محدد')}، "
        f"مركزه {p.get('position', 'غير محدد')}، عمره {p.get('age', '?')} سنة، "
        f"طوله {p.get('height_cm', '?')} سم ووزنه {p.get('weight_kg', '?')} كجم."
    )

    extra = []
    if sport == "Football":
        extra.append(
            f"دقة تمريره {p.get('pass_accuracy_pct','?')}% ودقة تسديده {p.get('shot_accuracy_pct','?')}%، "
            f"سرعته {p.get('speed_kmh','?')} كم/س."
        )
    elif sport == "Basketball":
        extra.append(
            f"معدل نقاطه {p.get('points_per_game','?')} في المباراة، متابعاته {p.get('rebounds_per_game','?')}، "
            f"تمريراته الحاسمة {p.get('assists_per_game','?')}، ودقة الثلاث نقاط {p.get('three_point_pct','?')}%."
        )
    elif sport == "Handball":
        extra.append(
            f"معدل أهدافه {p.get('goals_per_game','?')} في المباراة، تمريراته الحاسمة {p.get('assists_per_game','?')}، "
            f"دقة تسديده {p.get('shot_accuracy_pct','?')}%."
        )
    elif sport == "Volleyball":
        extra.append(
            f"دقة هجومه {p.get('attack_pct','?')}%، دقة حائطه {p.get('block_pct','?')}%، "
            f"دقة إرساله {p.get('serve_pct','?')}%."
        )

    extra.append(
        f"تقييم أدائه بالذكاء الاصطناعي {p.get('ai_score','?')} من 100، "
        f"ونسبة تحسنه الشهري {p.get('monthly_improvement_pct','?')}%."
    )
    return base + " " + " ".join(extra)


def chunk_players(players: list[dict]) -> list[dict]:
    """كل لاعب -> chunk فيه (id, text, metadata) جاهز يتبعت لـ chromadb."""
    return [
        {"id": p["player_id"], "text": describe_player(p), "metadata": p}
        for p in players
    ]


# ---------------------------------------------------------------
# STAGE: Embed + Store (chromadb بيعمل الاتنين مع بعض في نفس الاستدعاء)
# ---------------------------------------------------------------
def embed_and_store(chunks: list[dict]) -> None:
    """
    chromadb.add() بتاخد النصوص، وتستخدم موديل sentence-transformers
    عشان تحولها لمتجهات (Embed)، وتخزنها فورًا في VECTOR_STORE_DIR (Store) -
    مفيش خطوة يدوية منفصلة زي ما كنا بنعمل قبل كده بـ numpy.
    """
    client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    # لو الكولكشن موجود من قبل (تشغيل سابق)، بنشيله ونعمله من جديد
    # عشان نضمن إن الداتا محدّثة بالكامل مش متكدسة فوق القديمة
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)

    collection = client.create_collection(
        name=COLLECTION_NAME, embedding_function=embedding_fn
    )

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )
    print(f"اتخزن {len(chunks)} لاعب في data/vector_store (collection: {COLLECTION_NAME})")


# ---------------------------------------------------------------
# تشغيل المرحلة كاملة
# ---------------------------------------------------------------
def run_ingestion() -> None:
    print("1) Sources + Load ...")
    sports_data = load_sources(SOURCE_FILE)
    players = load_all_players(sports_data)
    print(f"   إجمالي اللاعبين: {len(players)}")

    print("2) Clean ...")
    players = clean_players(players)
    print(f"   بعد التنظيف: {len(players)}")

    print("3) Chunk ...")
    chunks = chunk_players(players)
    print(f"   عدد الـ chunks: {len(chunks)}")
    print("   مثال:", chunks[0]["text"][:100], "...")

    print("4+5) Embed + Store ... (أول مرة هينزّل الموديل من النت)")
    embed_and_store(chunks)

    print("خلصت Phase 1.")


if __name__ == "__main__":
    run_ingestion()
