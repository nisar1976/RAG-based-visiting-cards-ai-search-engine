# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Business Card Search Engine**

A system that extracts, indexes, and searches information from business card images using:
- OpenAI Vision API (`gpt-4o`) for OCR and structured field extraction (used at indexing time)
- Sentence-transformers (`all-MiniLM-L6-v2`, 384-dim) for local embedding generation (no API needed for search)
- PostgreSQL with BYTEA column for embedding storage and Python L2 distance computation for vector search
- FastAPI for the backend server
- Next.js for the web frontend

**Scale**: 350+ business card images across `assets/` (PNG) and `assets2/` (JPG) directories. 350+ cards indexed in PostgreSQL.

**Key Architecture**: OpenAI API is used only at indexing time (one-time cost). All search operations run locally using sentence-transformers embeddings and Python-based L2 distance computation against PostgreSQL BYTEA storage.

## Project Structure

```
root/
├── assets/                         # Business card images (PNG)
├── assets2/                        # Additional business card images (JPG)
├── backend/
│   ├── main.py                     # FastAPI app, lifespan, background startup/indexing
│   ├── .env                        # DATABASE_URL, OPENAI_API_KEY, HF_API_KEY, ASSETS_DIR
│   ├── api/
│   │   └── routes.py               # 11 API endpoints (routes registered on APIRouter)
│   ├── ocr/
│   │   ├── openai_vision.py        # OpenAI gpt-4o Vision OCR (PRIMARY, used for indexing)
│   │   ├── qwen_vision.py          # Qwen2.5-VL-7B via HF API (BROKEN - permissions issue)
│   │   ├── paddle_ocr.py           # Legacy PaddleOCR wrapper (NOT used in current pipeline)
│   │   ├── easy_ocr.py             # Legacy EasyOCR wrapper (NOT used in current pipeline)
│   │   ├── tesseract_ocr.py        # Legacy Tesseract wrapper (NOT used in current pipeline)
│   │   ├── trocr_ocr.py            # Legacy TrOCR wrapper (NOT used in current pipeline)
│   │   └── merger.py               # Legacy RapidFuzz merge (NOT used in current pipeline)
│   ├── rag/
│   │   ├── embeddings.py           # sentence-transformers all-MiniLM-L6-v2 (384-dim, local)
│   │   └── vector_search.py        # PostgreSQL BYTEA + Python L2 distance search
│   ├── db/
│   │   ├── models.py               # SQLAlchemy ORM Card model (with embedding BYTEA column)
│   │   ├── crud.py                 # Async DB CRUD operations
│   │   └── session.py              # asyncpg session factory
│   └── utils/
│       ├── image_loader.py         # Main indexing pipeline (OpenAI Vision OCR)
│       └── field_extractor.py      # JSON -> validated structured fields (phonenumbers/regex)
├── frontend/
│   ├── app/
│   │   ├── page.tsx                # Main page (search + results + card display)
│   │   ├── layout.tsx              # Root layout
│   │   └── admin/page.tsx          # Admin page (all cards table, edit, delete)
│   ├── components/
│   │   ├── SearchBar.tsx           # Query input, fires search
│   │   ├── ResultsList.tsx         # Ranked list of matched cards with similarity scores
│   │   ├── CardsTable.tsx          # Admin table for viewing/editing all cards
│   │   ├── CardDisplay.tsx         # Shows image + structured metadata
│   │   └── ActionButtons.tsx       # Download and Print buttons
│   ├── lib/
│   │   └── api.ts                  # All fetch calls to FastAPI backend
│   └── package.json
├── database/
│   ├── schema.sql                  # PostgreSQL DDL (cards table with BYTEA embedding)
│   ├── cards_backup.sql            # Full SQL dump backup
│   └── cards_export.csv            # CSV export backup
└── requirements.txt
```

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS cards (
    id           INTEGER PRIMARY KEY,
    name         TEXT,
    designation  TEXT,
    company      TEXT,
    country      TEXT,
    phone        TEXT,
    cell         TEXT,
    email        TEXT,
    address      TEXT,
    full_text    TEXT,
    image_path   TEXT UNIQUE,
    embedding    BYTEA NOT NULL,
    created_at   TIMESTAMP DEFAULT NOW()
);
```

**Column Sources**:
- `name`, `designation`, `company`, `country`, `phone`, `cell`, `email`, `address` -- extracted by `field_extractor.py` from OpenAI Vision JSON output
- `full_text` -- concatenation of non-"Not Available" extracted fields (used for embedding)
- `image_path` -- relative path: `assets/N.png` or `assets2/N.jpg`
- `embedding` -- 384-dim float32 vector stored as BYTEA (from sentence-transformers)
- `id` -- matches the filename number (1.png -> id=1)
- `created_at` -- database default

**Note**: The `cell` column is added via migration in `main.py` lifespan (`ALTER TABLE cards ADD COLUMN IF NOT EXISTS cell TEXT`).

## OCR Pipeline (Current)

For each image in `assets/` and `assets2/`:
1. **OpenAI Vision API** (`gpt-4o`) extracts JSON with 8 fields + confidence scores per field
2. `field_extractor.py` validates and normalizes fields:
   - Phone/cell validated with `phonenumbers` library
   - Email validated with regex
   - Country checked against 200+ country list
   - Name, designation, company validated for length/content
   - Missing/invalid fields set to `"Not Available"`
3. `embeddings.py` generates 384-dim L2-normalized embedding from full_text (locally, no API)
4. Card data + embedding stored in PostgreSQL via `crud.py`

**Legacy OCR files** (`paddle_ocr.py`, `easy_ocr.py`, `tesseract_ocr.py`, `trocr_ocr.py`, `merger.py`) still exist in `backend/ocr/` but are NOT imported or used by the current pipeline. The `image_loader.py` imports only `openai_vision` and `qwen_vision`.

## Data Flow

### Indexing Flow (startup background task / POST /process-assets)

```
assets/*.png + assets2/*.jpg
  |
image_loader.py        (scans both directories, sorts by filename number)
  |
openai_vision.py       (gpt-4o: image -> JSON with 8 fields + confidence)
  |
field_extractor.py     (validate/normalize fields, phonenumbers/regex)
  |
embeddings.py          (encode full_text -> 384-dim vector, locally)
  |
crud.py                (INSERT into PostgreSQL with BYTEA embedding)
```

### Search Flow (GET /search-card?q=&k=)

```
User query string
  |
routes.py              (GET /search-card endpoint, normalize query)
  |
embeddings.py          (encode query -> 384-dim vector, locally, no API)
  |
vector_search.py       (SELECT all embeddings from PostgreSQL BYTEA)
  |                    (compute L2 distances in Python, return top-k)
  |
crud.py                (SELECT * FROM cards WHERE id IN (...))
  |
routes.py              (return JSON: metadata + similarity scores)
  |
Frontend               (renders results in ResultsList + CardDisplay)
```

### Startup Flow

```
FastAPI lifespan starts
  |
Create tables / migrate (add cell column if missing)
  |
Launch background task:
  |-- Load sentence-transformers model (all-MiniLM-L6-v2)
  |-- Check existing card embeddings, re-embed if dimension mismatch
  |-- Count images in assets/ + assets2/
  |-- Compare DB count vs image count with 2% threshold
  |     (gap within threshold -> NO re-indexing)
  |-- Auto-index only if gap exceeds threshold
```

## API Endpoints

| Method | Path | Purpose | Notes |
|--------|------|---------|-------|
| POST | `/process-assets` | Trigger full indexing | Scans assets/ + assets2/, skips already-indexed |
| POST | `/add-card` | Manually add a card | Form data + optional image upload |
| GET | `/search-card?q=&k=` | Semantic search | Returns top-k results with similarity scores (default k=5, max 20) |
| GET | `/get-card/{id}` | Fetch card metadata | Returns full card row as JSON |
| PUT | `/update-card/{id}` | Update card fields | Re-generates embedding from updated fields |
| DELETE | `/delete-card/{id}` | Delete a card | Removes from database |
| GET | `/image/{id}` | Serve card image inline | Returns binary image from assets path |
| GET | `/download-card/{id}` | Download card image | Returns image as attachment |
| GET | `/all-cards` | List all cards | Returns all cards as JSON array |
| GET | `/export-csv` | Export all cards as CSV | Streaming CSV download |
| GET | `/health` | Health check | Returns embedder status, indexing status, card counts (defined in main.py) |

All route endpoints defined in `backend/api/routes.py` on an `APIRouter`, registered in `backend/main.py` via `app.include_router(routes.router)`. The `/health` endpoint is defined directly in `main.py`.

**CORS**: `CORSMiddleware` in `main.py` with `allow_origin_regex=r"http://localhost:\d+"` (matches any localhost port).

## Execution Steps

```bash
# Phase 1 -- Python environment
uv venv
uv pip install -r requirements.txt

# Phase 2 -- PostgreSQL setup
createdb visitingcards
psql visitingcards < database/schema.sql
# OR restore from backup:
psql visitingcards < database/cards_backup.sql

# Phase 3 -- Configure .env (backend/.env)
DATABASE_URL=postgresql+asyncpg://user:password@localhost/visitingcards
OPENAI_API_KEY=sk-...          # Required for indexing new cards
HF_API_KEY=hf_...              # For Qwen Vision (currently broken)
ASSETS_DIR=../assets

# Phase 4 -- Start backend (auto-indexes if needed on startup)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Phase 5 -- Start frontend (new terminal)
cd frontend
npm install
npm run dev   # http://localhost:3000
```

**Note**: With 350+ cards already indexed, the backend startup will NOT trigger re-indexing (2% threshold). Indexing only runs automatically if the gap between DB count and image count exceeds `max(1, total_images * 0.02)`.

## Frontend Architecture

- **Framework**: Next.js with App Router (`app/` directory)
- **Pages**: Main search page (`app/page.tsx`) + Admin page (`app/admin/page.tsx`)
- **API Integration**: All API calls via `lib/api.ts` to `http://localhost:8000`
- **Image Display**: `GET /image/{id}` served inline; rendered in `CardDisplay.tsx`
- **Download**: `GET /download-card/{id}` (attachment) via `ActionButtons.tsx`
- **Print**: `window.print()` scoped to `CardDisplay.tsx`
- **Admin**: `CardsTable.tsx` shows all cards with edit/delete capabilities
- **Component Flow**: `SearchBar` -> `ResultsList` -> `CardDisplay` + `ActionButtons`

## Key Technical Decisions

- **OpenAI Vision for OCR**: One-time cost at indexing; produces structured JSON with confidence scores directly (no multi-engine merging needed)
- **Sentence-transformers for local embeddings**: No API cost for search operations; `all-MiniLM-L6-v2` runs locally on CPU
- **PostgreSQL BYTEA for embedding storage**: Durable, no separate index files, works on Windows without pgvector C extension
- **Python L2 distance computation**: All embeddings loaded from DB and compared in Python; avoids FAISS dependency
- **2% threshold for auto-indexing**: Prevents unnecessary OpenAI API calls on restart when most cards are already indexed
- **Card IDs match filename numbers**: `1.png` -> `id=1`, `350.jpg` -> `id=350`; enforced via `autoincrement=False` on primary key

## Key Code Patterns

- **OCR Output**: OpenAI Vision returns JSON with 8 fields + `confidence` object (0-100 per field). `field_extractor.py` validates each field using the confidence score as a threshold.
- **Field Validation**: `phonenumbers` library for phone/cell validation, regex for email, country lookup against 200+ country set with aliases. Missing fields must be the string `"Not Available"` -- not null, not empty string.
- **Embedding Storage**: 384-dim float32 vectors stored as `BYTEA` in PostgreSQL. Converted via `vector.astype('float32').tobytes()` for storage, `np.frombuffer(bytes, dtype=np.float32)` for retrieval.
- **Vector Search**: `vector_search.py` fetches ALL card embeddings from DB, computes L2 distance in Python, converts to similarity percentage via `max(0, 1 - dist^2/2) * 100`, returns top-k sorted by similarity descending.
- **Embedding Normalization**: Embeddings are L2-normalized at encode time (`normalize_embeddings=True`), making L2 distance equivalent to cosine distance.
- **Async Database**: SQLAlchemy 2.0 async sessions with `asyncpg` driver. Session factory in `db/session.py`, injected via FastAPI `Depends()`.
- **Background Startup**: Sentence-transformer model loaded in a background `asyncio.create_task` during lifespan (server accepts requests immediately). Stored in `app.state.embedder`.
- **Re-embedding**: On startup, checks if existing embeddings match the current model's dimension; re-embeds all cards if dimension mismatch detected.
- **Rate Limiting**: 1.5-second delay between OpenAI API calls during indexing (`asyncio.sleep(1.5)`). Max 15 consecutive failures before stopping.
- **CORS**: `CORSMiddleware` with `allow_origin_regex=r"http://localhost:\d+"`, `allow_methods=["*"]`, `allow_headers=["*"]`.

## Dependencies Highlights

| Category | Key Packages |
|----------|--------------|
| **API** | fastapi, uvicorn, pydantic |
| **OCR** | openai (OpenAI Vision API client) |
| **Embeddings** | sentence-transformers, torch, numpy |
| **Database** | sqlalchemy, asyncpg |
| **Validation** | phonenumbers, regex (stdlib re) |
| **Image** | Pillow |
| **Utilities** | python-dotenv, python-multipart |
| **Frontend** | next, react, react-dom, typescript |

## Development Notes

- **PostgreSQL**: Must be running locally; connection details in `backend/.env`
- **OpenAI API Key**: Required in `backend/.env` only for indexing new cards; search does not use any API
- **Database Backups**: `database/cards_backup.sql` (full SQL dump) and `database/cards_export.csv` (CSV export) contain all indexed cards
- **Sentence Transformer Cache**: Models downloaded and cached by `sentence-transformers` on first load; defaults to `~/.cache/huggingface/`
- **Legacy OCR Files**: `paddle_ocr.py`, `easy_ocr.py`, `tesseract_ocr.py`, `trocr_ocr.py`, `merger.py` still exist in `backend/ocr/` but are dead code -- not imported by any active module
- **Qwen Vision**: `qwen_vision.py` exists and is imported by `image_loader.py` but never called (HF API key lacks permissions). OpenAI Vision is used as the sole OCR engine.
- **MAX_CARDS env var**: Set `MAX_CARDS=N` to limit indexing to first N images (0 or unset = no limit)
