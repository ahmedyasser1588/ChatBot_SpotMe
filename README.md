# SPOTME Scout Assistant — RAG Chatbot

RAG-based chatbot بيرد على أسئلة السكاوتس عن اللاعبين، بناءً على قاعدة بيانات لاعبين حقيقية بس (بدون اختلاق).

## الفكرة في 4 مراحل

```
Phase 1 (ingest.py)        : الداتا -> تنظيف -> وصف نصي لكل لاعب -> embeddings -> Chroma vector DB
Query Parsing (query_parser.py) : سؤال المستخدم -> Gemini (structured output) -> فلاتر منظمة (رياضة/نادي/مركز/أرقام/ترتيب/تجميع)
Phase 2 (retrieve.py)      : الفلاتر -> Chroma where clause -> استرجاع/ترتيب/حساب تجميعي
Phase 3 (generate.py)      : النتيجة + السؤال -> prompt -> Gemini -> إجابة نهائية
main.py                    : FastAPI endpoint بيلف كل ده في API واحد
```

**ليه فيه مرحلة "Query Parsing" منفصلة؟**
جربنا الأول نلاقط كل حالة (رياضة، نادي...) بكود keyword-matching يدوي، واكتشفنا إنه بيتكسر مع أي حقل جديد (مركز، عمر، مقارنات رقمية، أسئلة تجميع زي "كام لاعب؟"). فبدل ما نضيف دالة `_detect_X()` جديدة كل مرة، بنبعت السؤال لـ Gemini نفسه ونطلب منه JSON منظم بالفلاتر (`response_schema` في الـ API)، وبعدين `retrieve.py` بيستخدمها generic تمامًا. التكلفة: كل سؤال بيعمل استدعاءين لـ Gemini بدل واحد (parsing + generation) - trade-off واعي لصالح الدقة.

## التشغيل

### 1) التجهيز (مرة واحدة)

```bash
pip install -r requirements.txt
cp .env.example .env
# افتح .env وحط GEMINI_API_KEY الحقيقي بتاعك (من https://aistudio.google.com/app/apikey)
```

### 2) بناء الـ vector store (مرة واحدة، أو كل ما تتحدث بيانات اللاعبين)

من الفولدر الرئيسي (اللي فيه backend/ و data/):

```bash
python -m backend.ingest
```

هيا هينزّل موديل embedding من HuggingFace أول مرة بس (~470MB)، وبعدها هيخزن كل اللاعبين في `data/vector_store/`.

### 3) تشغيل السيرفر

```bash
uvicorn backend.main:app --reload --port 8000
```

⚠️ لازم تشغل الأمر ده من الفولدر الرئيسي (مش من جوه `backend/`)، لأن الملفات بتستخدم relative imports.

## الـ API Contract (للتيم)

**Base URL:** `http://localhost:8000` (أو الـ URL الحقيقي بعد الـ deployment)

### `GET /health`
للتأكد إن السيرفر شغال.

Response:
```json
{"status": "ok"}
```

### `POST /chat`
السؤال والإجابة.

Request:
```json
{
  "question": "مين أحسن لاعب في الباسكت؟",
  "top_k": 5
}
```
- `question`: نص عربي أو إنجليزي، مطلوب.
- `top_k`: عدد اللاعبين اللي يترجعوا كـ context (اختياري، افتراضي 5).

Response (200):
```json
{"answer": "..."}
```

Errors:
| Status | السبب |
|---|---|
| 400 | السؤال فاضي أو غير صالح |
| 502 | مشكلة في الـ vector store أو في Gemini API (مفتاح غلط، rate limit، الخ) |
| 500 | خطأ غير متوقع |

## ملاحظات مهمة للتيم

- **الـ `.env` الحقيقي ملوش commit خالص** — كل واحد يعمل نسخته من `.env.example` بمفتاحه الخاص.
- **`data/vector_store/` متعمَلوش commit** — بيتولد محليًا من `python -m backend.ingest`. لو غيّرتوا الداتا في `data/sources/chatbot_data.js`، لازم تشغلوا `ingest.py` تاني.
- **الفلترة بقت عامة (generic)**: أي سؤال بيمر على `query_parser.py` الأول، اللي بيستخرج رياضة/نادي/مركز/اسم لاعب/مقارنات رقمية (أكبر من/أقل من)/طلب ترتيب/طلب تجميع. `retrieve.py` بعد كده بيبني `where` clause من الفلاتر دي مباشرة - مفيش حاجة hardcoded.
- **قيم النادي/المركز/الاسم بتتوحّد وتتسامح مع الأخطاء الإملائية (`_resolve_value`)**: القيمة اللي Gemini بيستخرجها ممكن تختلف شكليًا عن المخزّن (همزة زيادة/ناقصة، تشكيل، مسافات) أو فيها خطأ إملائي بسيط (حرف ناقص/زيادة/غلط). فبندور على أقرب قيمة *حقيقية* في الداتا على 3 مستويات: تطابق كامل بعد توحيد الشكل → تطابق جزئي → تطابق تقريبي (fuzzy، عن طريق `difflib`) بيسامح الأخطاء البسيطة. لو مفيش تطابق واثق حتى بعد الثلاثة، الفلتر بيتجاهل بدل ما يرجع صفر نتايج غلط.
- **أسئلة الترتيب** ("أحسن لاعب في كذا") بترجع كل المطابقين للفلاتر مرتبين رقميًا حسب الحقل المناسب (`sort_by`)، مش بالـ semantic similarity.
- **أسئلة التجميع** ("كام لاعب في الأهلي؟"، "متوسط عمر لاعبين الباسكت؟") بتتحسب مباشرة على الداتا كلها (`compute_aggregation`)، مش بتمر على الـ RAG العادي - لأن أي `top_k` محدود هيدي رقم غلط لسؤال تجميعي.
- **لو `query_parser.py` فشل لأي سبب** (شبكة، rate limit)، بيرجع فلاتر فاضية بدل ما يوقف السيرفر - يعني بيرجع لسلوك semantic search عادي بدون فلاتر (أأمن من كسر الـ request).
- لسه معمول persona واحدة بس (Scout Assistant). الـ AI Coach persona (فيدباك للاعبين نفسهم) محتاجة knowledge base وpipeline منفصلين تمامًا، لسه معمولة.

## هيكل المشروع

```
.
├── backend/
│   ├── __init__.py
│   ├── ingest.py        # Phase 1
│   ├── query_parser.py  # Query Parsing (Gemini structured output)
│   ├── retrieve.py      # Phase 2
│   ├── generate.py      # Phase 3
│   └── main.py          # FastAPI app
├── data/
│   └── sources/
│       └── chatbot_data.js
├── requirements.txt
├── .env.example
└── .gitignore
```
