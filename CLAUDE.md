# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Offline RAG-Based Visiting Card AI System**

A fully offline system that extracts, indexes, and searches information from visiting card images using:
- Multi-engine OCR (PaddleOCR, EasyOCR, Tesseract) for robust text extraction
- FAISS for local semantic search and retrieval
- PostgreSQL for metadata storage
- FastAPI for the backend server
- Next.js for the web frontend

**Scale**: 348+ PNG visiting card images in `assets/` directory.

**Key Constraint**: Completely offline — no external APIs, all processing runs locally on 1–2 laptops.

## Project Structure

```
root/
├── assets/                         # Input: PNG visiting card images (source of truth)
├── backend/
│   ├── main.py                     # FastAPI app entry, CORS, lifespan events
│   ├── .env                        # DATABASE_URL, ASSETS_DIR
│   ├── api/
│   │   └── routes.py               # All 4 API endpoints
│   ├── ocr/
│   │   ├── paddle_ocr.py           # PaddleOCR wrapper (primary)
│   │   ├── easy_ocr.py             # EasyOCR wrapper (secondary)
│   │   ├── tesseract_ocr.py        # Tesseract wrapper (validation)
│   │   └── merger.py               # RapidFuzz merge of 3 OCR outputs
│   ├── rag/
│   │   ├── embeddings.py           # sentence-transformers encode/load
│   │   └── search.py               # FAISS index load and search
│   ├── db/
│   │   ├── models.py               # SQLAlchemy ORM Card model
│   │   ├── crud.py                 # Async DB read/write operations
│   │   └── session.py              # asyncpg session factory
│   └── utils/
│       ├── image_loader.py         # Reads all PNGs from assets/, triggers pipeline
│       └── field_extractor.py      # Parses merged OCR text into structured fields
├── frontend/
│   ├── app/
│   │   └── page.tsx                # Main page (search + results + card display)
│   ├── components/
│   │   ├── SearchBar.tsx           # Query input, fires search
│   │   ├── ResultsList.tsx         # Ranked list of matched cards
│   │   ├── CardDisplay.tsx         # Shows image + structured metadata
│   │   └── ActionButtons.tsx       # Download and Print buttons
│   ├── lib/
│   │   └── api.ts                  # All fetch calls to FastAPI backend
│   ├── next.config.js
│   └── package.json
├── database/
│   └── schema.sql                  # PostgreSQL DDL (cards table)
├── embeddings/                     # FAISS index binary files (auto-generated)
└── requirements.txt
```

## Database Schema

```sql
CREATE TABLE cards (
    id           SERIAL PRIMARY KEY,
    name         TEXT,
    designation  TEXT,
    company      TEXT,
    country      TEXT,
    phone        TEXT,
    email        TEXT,
    address      TEXT,
    full_text    TEXT,               -- merged raw OCR output
    image_path   TEXT,               -- relative path: assets/filename.png
    created_at   TIMESTAMP DEFAULT NOW()
);
```

**Column Sources**:
- `name`, `designation`, `company`, `country`, `phone`, `email`, `address` ← extracted by `field_extractor.py` from merged OCR
- `full_text` ← `merger.py` (merged OCR text from all 3 engines)
- `image_path` ← `image_loader.py` (relative path to assets/)
- `created_at` ← database default

## OCR Pipeline

For each image in `assets/`:
1. Run **PaddleOCR** (primary, best for business cards)
2. Run **EasyOCR** (secondary, handles stylized fonts)
3. Run **Tesseract OCR** (validation)
4. Merge outputs using RapidFuzz similarity matching
5. Extract structured fields:
   - Name, Designation, Company, Country
   - Phone, Email, Address
   - (Use "Not Available" if field is missing)

## Data Flow

### Indexing Flow (startup / POST /api/index)

```
assets/*.png
  ↓
image_loader.py        (reads all PNG files)
  ↓
paddle_ocr.py          (primary OCR)
  ↓
easy_ocr.py            (secondary OCR)
  ↓
tesseract_ocr.py       (validation OCR)
  ↓
merger.py              (RapidFuzz deduplication → full_text)
  ↓
field_extractor.py     (parse name/company/phone/email/address/etc.)
  ↓
crud.py                (INSERT into PostgreSQL cards table)
  ↓
embeddings.py          (encode full_text → vector)
  ↓
search.py              (add vector to FAISS index, save to embeddings/)
```

### Search Flow (GET /api/search?q=)

```
User query string
  ↓
routes.py              (GET /api/search endpoint)
  ↓
embeddings.py          (encode query → vector)
  ↓
search.py              (FAISS.search() → top-1 card id)
  ↓
crud.py                (SELECT * FROM cards WHERE id = ?)
  ↓
routes.py              (return JSON: metadata + image_path)
  ↓
Frontend CardDisplay   (renders image via /api/image/{id})
```

## API Endpoints

| Method | Path | Purpose | Notes |
|--------|------|---------|-------|
| POST | `/api/index` | Trigger full re-indexing | Idempotent; clears and rebuilds FAISS + DB |
| GET | `/api/search?q=` | Semantic search | Returns top-1 card with metadata + image_path |
| GET | `/api/cards/{id}` | Fetch card metadata | Returns full cards row as JSON |
| GET | `/api/image/{id}` | Serve card image | Returns binary image from assets/ |

All endpoints defined in `backend/api/routes.py`, registered in `backend/main.py`.

**CORS**: `CORSMiddleware` in `main.py` with `allow_origins=["http://localhost:3000"]`.

## Execution Steps (6 Phases)

```bash
# Phase 1 — Python environment
uv venv
uv pip install -r requirements.txt

# Phase 2 — PostgreSQL setup
createdb visitingcards
psql visitingcards < database/schema.sql

# Phase 3 — Configure .env (backend/.env)
DATABASE_URL=postgresql+asyncpg://user:password@localhost/visitingcards
ASSETS_DIR=../assets

# Phase 4 — Index all cards (first run; takes several minutes for 348+ images)
cd backend
python -m utils.image_loader

# Phase 5 — Start backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Phase 6 — Start frontend (new terminal)
cd frontend
npm install
npm run dev   # http://localhost:3000
```

## Frontend Architecture

- **Framework**: Next.js with App Router (`app/` directory, not `pages/`)
- **API Integration**: All API calls via `lib/api.ts` to `http://localhost:8000`
- **Image Display**: `GET /api/image/{id}` (not static files); rendered in `CardDisplay.tsx`
- **Download**: `<a href="/api/image/{id}" download>` in `ActionButtons.tsx`
- **Print**: `window.print()` scoped to `CardDisplay.tsx`
- **Component Flow**: `SearchBar` → `ResultsList` → `CardDisplay` + `ActionButtons`

## Key Technical Decisions

- **Multi-OCR Merging**: RapidFuzz handles OCR discrepancies and conflicting results
- **FAISS over Database Search**: FAISS provides fast semantic/vector search; PostgreSQL holds metadata for fallback and structured queries
- **Sentence Transformers**: Pre-trained models (no fine-tuning needed) for embeddings; avoids dependency on external models
- **Local Storage**: Embeddings cached in `embeddings/`, images in `assets/`; FAISS index is a binary file

## Key Code Patterns

- **OCR Merging**: Use `rapidfuzz.fuzz.token_sort_ratio` with threshold ~85 for deduplication. Three OCR outputs merged; lines above threshold treated as duplicates.
- **FAISS Index**: `faiss.IndexFlatL2` with L2-normalized embeddings (equivalent to cosine similarity). Saved as binary to `embeddings/`; loaded once at FastAPI startup.
- **Async Database**: SQLAlchemy 2.0 async sessions with `asyncpg` driver. Session factory in `db/session.py`, injected via FastAPI `Depends()`.
- **Field Confidence**: Missing fields must be the string `"Not Available"` — not null, not empty string. Consistent across all 8 fields (name, designation, company, country, phone, email, address).
- **Startup Loading**: FAISS index and sentence-transformer model loaded in FastAPI `lifespan` event (not per-request). Stored in `app.state`.
- **CORS**: `CORSMiddleware` in `main.py`: `allow_origins=["http://localhost:3000"]`, `allow_methods=["*"]`, `allow_headers=["*"]`.

## Dependencies Highlights

| Category | Key Packages |
|----------|--------------|
| **API** | fastapi, uvicorn, pydantic |
| **OCR** | paddleocr, easyocr, pytesseract |
| **Embeddings** | sentence-transformers, transformers, torch |
| **Vector DB** | faiss-cpu |
| **Database** | sqlalchemy, psycopg2-binary, asyncpg |
| **Image** | opencv-python, Pillow, numpy |
| **Utilities** | python-dotenv, rapidfuzz, python-multipart |
| **Frontend** | next, react, react-dom, typescript |

## Development Notes

- **PostgreSQL**: Must be running locally; connection details in `.env`
- **FAISS Index**: Generated on first run or when new images are added to `assets/`
- **OCR Fallback**: If one engine fails, the system continues with remaining engines
- **Sentence Transformer Cache**: Models are downloaded and cached by `sentence-transformers` on first load; cache location controlled by `SENTENCE_TRANSFORMERS_HOME` environment variable (defaults to `~/.cache/huggingface/`)
