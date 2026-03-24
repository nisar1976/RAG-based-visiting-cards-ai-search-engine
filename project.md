# AI Business Card Search Engine

## Project Description

The AI Business Card Search Engine is a full-stack intelligent system that automates the extraction, indexing, and semantic search of business card images. Built to solve the problem of managing large collections of physical business cards, the system leverages state-of-the-art AI vision models to extract structured contact information from card images and makes it instantly searchable through natural language queries.

The system combines OpenAI's Vision API (gpt-4o) for high-accuracy OCR with local sentence-transformers embeddings for cost-free semantic search. During a one-time indexing phase, each card image is processed to extract 8 structured fields — name, designation, company, country, phone, cell, email, and address — with per-field confidence scoring and validation. Once indexed, all search operations run entirely locally using 384-dimensional embeddings and Python-based L2 distance computation, delivering sub-100ms response times with zero ongoing API costs.

The application features a modern Next.js frontend with real-time search, an admin panel for card management, and full CRUD capabilities through a RESTful FastAPI backend. With 350+ business cards indexed and searchable, the system demonstrates production-grade architecture suitable for enterprise contact management use cases.

---

## Screenshots

### Frontend — Search Interface
![Frontend Search Interface](./screenshots/frontend-search.png)

*Main search page with semantic search bar, results list with similarity scores, and card detail view showing extracted metadata alongside the card image.*

### Frontend — Admin Panel
![Admin Panel](./screenshots/frontend-admin.png)

*Admin panel at `/admin` displaying all indexed cards in a sortable table with inline edit and delete capabilities.*

### Backend — API Documentation
![Backend API Docs](./screenshots/backend-api-docs.png)

*FastAPI auto-generated Swagger UI at `/docs` showing all 11 REST endpoints.*

### Backend — Health Check
![Backend Health](./screenshots/backend-health.png)

*Health endpoint response showing system status, embedder readiness, and indexing statistics.*

> **Note**: Replace placeholder screenshots with actual captures from your running system. See [SCREENSHOT_GUIDE.md](./SCREENSHOT_GUIDE.md) for capture instructions.

---

## Key Features

- **AI-Powered OCR** — OpenAI Vision API (gpt-4o) extracts structured JSON with confidence scores per field
- **Semantic Search** — Natural language queries matched against card content using sentence-transformers (local, sub-100ms)
- **8-Field Extraction** — Name, designation, company, country, phone, cell, email, address with validation
- **Field Validation** — Phone numbers validated via `phonenumbers` library (E.164), email via regex, 200+ country aliases
- **Confidence Scoring** — Per-field confidence (0-100%) with threshold-based filtering
- **Admin Panel** — Full CRUD: view, edit, delete cards at `/admin`
- **Download & Print** — Export card images as PNG; print-friendly layout
- **CSV Export** — Bulk export all card data as CSV
- **Responsive UI** — Desktop and mobile-friendly Next.js interface
- **Smart Re-indexing** — 2% threshold prevents unnecessary API calls on restart

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                    │
│         Search Bar → Results List → Card Display        │
│                    Admin Panel                          │
└────────────────────────┬────────────────────────────────┘
                         │
                    HTTP REST API
                         │
┌────────────────────────▼────────────────────────────────┐
│                  BACKEND (FastAPI)                       │
│                                                         │
│   Indexing: OpenAI Vision → Field Validation → DB       │
│   Search:  sentence-transformers → L2 Distance → DB    │
└────────────────────────┬────────────────────────────────┘
                         │
                    PostgreSQL
                         │
┌────────────────────────▼────────────────────────────────┐
│                     DATABASE                            │
│   Cards Table + Embeddings (BYTEA, 384-dim vectors)    │
└─────────────────────────────────────────────────────────┘
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| OpenAI Vision for OCR | One-time cost; structured JSON output with confidence scores |
| Local sentence-transformers | Zero ongoing cost for search; runs on CPU |
| PostgreSQL BYTEA storage | No pgvector C extension needed; works cross-platform |
| Python L2 distance | Avoids FAISS dependency; sufficient for 350+ cards |
| 2% threshold auto-indexing | Prevents redundant API calls on server restart |

---

## Technology Stack

### Backend
| Category | Technology |
|----------|-----------|
| Framework | FastAPI + Uvicorn |
| Language | Python 3.10+ |
| OCR | OpenAI Vision API (gpt-4o) |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 (384-dim, local) |
| Database | PostgreSQL 14+ (no pgvector extension needed) |
| ORM | SQLAlchemy 2.0 (async with asyncpg) |
| Validation | phonenumbers, regex |

### Frontend
| Category | Technology |
|----------|-----------|
| Framework | Next.js 14+ (App Router) |
| Language | TypeScript + React |
| Styling | CSS Modules (responsive) |
| API Client | Fetch API |

---

## Data Flow

### Indexing Pipeline (One-Time)

```
Business Card Images (PNG/JPG)
    ↓
OpenAI Vision API (gpt-4o) — structured JSON extraction
    ↓
Field Validation (phonenumbers, email regex, 200+ country aliases)
    ↓
sentence-transformers (full_text → 384-dim vector, LOCAL)
    ↓
PostgreSQL Storage (card metadata + BYTEA embedding)
    ↓
350+ Cards Indexed & Searchable
```

### Search Pipeline (Real-Time, Local)

```
User Query ("john smith from techcorp")
    ↓
sentence-transformers (query → 384-dim vector, LOCAL)
    ↓
Python L2 Distance Search (all embeddings from PostgreSQL)
    ↓
Top-K Results (ranked by similarity, < 100ms)
    ↓
Card Display (image + structured metadata)
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | System health check and indexing status |
| `POST` | `/process-assets` | Trigger card indexing pipeline |
| `GET` | `/search-card?q=&k=` | Semantic search (local, sub-100ms) |
| `GET` | `/all-cards` | List all indexed cards |
| `GET` | `/get-card/{id}` | Fetch card metadata by ID |
| `GET` | `/image/{id}` | Serve card image (inline) |
| `GET` | `/download-card/{id}` | Download card image (attachment) |
| `POST` | `/add-card` | Add a new card manually |
| `PUT` | `/update-card/{id}` | Update card metadata |
| `DELETE` | `/delete-card/{id}` | Delete a card |
| `GET` | `/export-csv` | Export all cards as CSV |

### Example Usage

```bash
# Search for a card
curl "http://localhost:8000/search-card?q=software+engineer+techcorp"

# Check system health
curl http://localhost:8000/health

# Export all cards
curl http://localhost:8000/export-csv -o cards.csv
```

---

## Setup Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (no pgvector extension needed)
- OpenAI API key (only needed for indexing; search is local)

### 1. Database Setup
```bash
createdb visitingcards
psql visitingcards < database/schema.sql
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt
```

### 3. Configure Environment
Edit `backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://user:****@localhost/visitingcards
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXX
ASSETS_DIR=assets
MAX_CARDS=0
```

### 4. Start Services
```bash
# Terminal 1: Backend
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend && npm install && npm run dev
```

Visit: **http://localhost:3000**

---

## Skills & Expertise Demonstrated

### AI & Machine Learning
- **Computer Vision**: OpenAI Vision API integration for structured OCR extraction
- **NLP & Embeddings**: Sentence-transformers for semantic text similarity
- **Vector Search**: L2 distance computation with normalized embeddings
- **Prompt Engineering**: Structured JSON extraction prompts with confidence scoring

### Backend Engineering
- **API Design**: RESTful API with 11 endpoints (FastAPI)
- **Async Programming**: Full async/await with SQLAlchemy 2.0 + asyncpg
- **Data Validation**: Phone number parsing (E.164), email validation, country normalization
- **Background Processing**: Non-blocking startup with model loading and auto-indexing
- **Rate Limiting**: Controlled API consumption with exponential backoff

### Frontend Development
- **Modern React**: Next.js 14 App Router with TypeScript
- **Responsive Design**: Desktop and mobile layouts with CSS Modules
- **Real-Time Search**: Debounced query input with instant results
- **Print & Export**: Browser print API and CSV download integration

### Database & Infrastructure
- **PostgreSQL**: Schema design, BYTEA binary storage, async connections
- **Data Pipeline**: End-to-end ETL from image to searchable structured data
- **Cost Optimization**: One-time indexing cost; zero ongoing API expenses for search

---

## Deliverables

### Core Application
- Full-stack web application (FastAPI + Next.js)
- 350+ business cards indexed and semantically searchable
- 11 REST API endpoints with full CRUD operations
- Admin panel for card management
- Download and print functionality
- CSV bulk export

### AI/ML Pipeline
- OpenAI Vision OCR integration with structured JSON output
- 8-field extraction with per-field confidence scoring
- Field validation suite (phonenumbers, email regex, 200+ country aliases)
- Local sentence-transformers embedding pipeline (384-dim)
- PostgreSQL BYTEA vector storage with Python L2 distance search

### Documentation & Infrastructure
- PostgreSQL database schema with migration support
- Database backups (SQL dump + CSV export)
- Comprehensive setup guides and troubleshooting documentation
- Project architecture documentation

---

## Performance Benchmarks

| Metric | Value | Notes |
|--------|-------|-------|
| Cards Indexed | 350+ | Business card images processed and searchable |
| Search Latency | < 100ms | Local sentence-transformers + Python L2 distance |
| Extraction Accuracy | 95%+ | Average across all fields |
| Phone Validation | 95%+ | E.164 format compliance |
| Frontend Load | < 500ms | After backend is ready |
| Initial Indexing Cost | ~$3-5 | One-time OpenAI Vision API; no ongoing costs |

---

## Troubleshooting

### OpenAI API Issues
- **"API key not found"**: Verify `OPENAI_API_KEY` in `backend/.env`
- **Rate limits**: Add delays between requests or upgrade OpenAI account
- **Quota exceeded**: Check API usage at platform.openai.com

### PostgreSQL Issues
- **Connection refused**: Ensure PostgreSQL is running (`pg_isready`)
- **Vector dimension mismatch**: Verify embedding dimensions are 384

### Search Issues
- **Low quality results**: Check card image quality (resolution, contrast)
- **Empty results**: Wait for full indexing to complete
- **Search is local**: No API call needed — uses sentence-transformers locally

---

## Future Enhancements

1. **Batch Processing** — Optimize API calls with batch embeddings
2. **Caching** — Cache embeddings to reduce computation
3. **Fine-tuning** — Custom OCR prompts for industry-specific cards
4. **Advanced Search** — Full-text search combined with semantic search
5. **Analytics** — Track search patterns and extraction quality metrics
6. **Mobile App** — React Native or Flutter mobile client
7. **Export Formats** — Excel and vCard formats (CSV already implemented)
8. **Duplicate Detection** — Identify duplicate or updated cards

---

## License & Attribution

Built with:
- OpenAI Vision API (gpt-4o) — OCR extraction
- sentence-transformers all-MiniLM-L6-v2 — local embeddings (384-dim)
- PostgreSQL with BYTEA vector storage
- FastAPI & Next.js
- Community libraries: phonenumbers, fuzzywuzzy, rapidfuzz

---

**Last Updated**: March 2026
**Status**: Production Ready — 350+ business cards indexed and searchable
