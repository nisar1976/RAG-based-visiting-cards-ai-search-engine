# SPECIFICATIONS.md

**Offline RAG-Based Visiting Card AI System**

A comprehensive technical specification for implementing a fully offline system that extracts, indexes, and searches information from visiting card images using multi-engine OCR, FAISS semantic search, PostgreSQL metadata storage, FastAPI backend, and Next.js frontend.

---

## 1. System Overview

### Purpose
The system provides a **fully offline visiting card management platform** enabling users to:
- Extract structured information (name, designation, company, phone, email, address, country) from PNG images of visiting cards
- Index extracted text using semantic embeddings for fast, intelligent search
- Retrieve and display card details via a web interface
- Download and print card information

### Key Components
```
PNG Images (assets/)
  ↓
Multi-Engine OCR (PaddleOCR + EasyOCR + Tesseract)
  ↓
RapidFuzz Text Merging
  ↓
Field Extraction (Regex + Heuristics)
  ↓
PostgreSQL Metadata Storage
  ↓
Sentence-Transformers Embeddings
  ↓
FAISS Vector Search Index
  ↓
FastAPI Backend
  ↓
Next.js React Frontend
```

### Scale & Constraints
- **Data**: 348+ PNG visiting card images in `assets/` directory
- **Hardware**: Runs on standard laptops with 8GB RAM; no GPU required
- **Offline**: Zero external API calls at runtime — all processing is local
- **Scalability**: Architecture supports 1,000+ cards without re-engineering

---

## 2. Functional Requirements

### FR-01: OCR Processing
- Read all PNG files from `assets/` directory (initially 348 images; scalable)
- Execute **3 OCR engines per image**: PaddleOCR (primary), EasyOCR (secondary), Tesseract (validation)
- Merge OCR outputs using RapidFuzz similarity matching (threshold ≥ 85)
- Produce final merged text string (`full_text`) for each card
- Continue pipeline even if one OCR engine fails; log warnings

### FR-02: Structured Data Extraction
Extract exactly **7 fields** from merged OCR text using regex and heuristics:
1. **name** — person's full name
2. **designation** — job title / role
3. **company** — employer / organization
4. **country** — country / region
5. **phone** — contact phone number (any format)
6. **email** — email address
7. **address** — physical address

**Rules**:
- If a field is not detected, set to string `"Not Available"` (never null, never empty string)
- All 7 fields are required in output; missing fields must be explicitly `"Not Available"`

### FR-03: Semantic Search
- Accept natural language queries (e.g., "find John from Google in UAE")
- Encode user query to semantic embedding using sentence-transformers
- Search FAISS index to find the **top 1 most relevant card**
- Return matched card ID, metadata, and image path
- Search response must complete within 500ms after indexing

### FR-04: Card Retrieval
- Fetch any card by integer ID from PostgreSQL
- Return all metadata fields + `image_path` + `full_text` + `created_at`
- Support 404 HTTP response if card not found

### FR-05: Display & Visualization
- Display **only the selected card image** (no gallery, no thumbnails)
- Show structured metadata alongside the image in a readable format
- Image served dynamically from `assets/` directory; not embedded in database
- Fetch image via separate API endpoint (GET `/image/{id}`)

### FR-06: Download & Print Operations
- **Download**: Serve original PNG file with `Content-Disposition: attachment` header; trigger browser download
- **Print**: Open browser print dialog; CSS `@media print` hides all UI except card display area

---

## 3. Non-Functional Requirements

| ID | Requirement | Target / Specification |
|----|-----------|-----------------------|
| NFR-01 | Fully Offline | Zero external API calls at runtime. All models (OCR, embeddings, vector search) run locally. |
| NFR-02 | Search Performance | Query response < 500ms after initial indexing. FAISS `IndexFlatL2` ensures <1ms per search for ≤1,000 cards. |
| NFR-03 | Hardware Compatibility | Runs on standard laptop: 8GB RAM, Intel i5/i7, no GPU required. Python 3.10+, PostgreSQL 15+, Node.js 18+. |
| NFR-04 | Scalability | Architecture handles 1,000+ cards. For >10,000 cards, migrate FAISS index to `IndexIVFFlat(nlist=100)` without schema changes. |
| NFR-05 | Reliability | OCR pipeline continues if one engine fails. Graceful fallback to remaining engines. All 7 fields default to `"Not Available"` if not detected. |
| NFR-06 | Storage Efficiency | FAISS index + embeddings fit in <500MB for 348 cards. PNG images stored as binary in `assets/`, not database. |
| NFR-07 | Data Consistency | PostgreSQL single source of truth. FAISS index rebuilt from DB on process restart. `id_map.json` maintains ID correspondence. |
| NFR-08 | Error Recovery | Failed OCR on single image does not abort pipeline. Invalid queries return 422 validation error. Database connection failure fails loudly on startup. |

---

## 4. OCR Design

### Engine Selection & Priority

| Engine | Tool | Primary Purpose | Config |
|--------|------|-----------------|--------|
| **PaddleOCR** | `paddleocr==2.7.3` | Primary; best for business cards | `use_angle_cls=True`, `lang='en'` |
| **EasyOCR** | `easyocr` | Secondary; handles decorative/stylized fonts | Default English model |
| **Tesseract** | `pytesseract` | Validation; catches edge cases | `--oem 3 --psm 6` (full page mode) |

### Image Preprocessing
Before OCR, apply preprocessing via OpenCV to improve recognition:
- Convert to grayscale
- Detect and correct image skew (deskew)
- Normalize brightness and contrast
- Resize if image width < 300px (scale to 1.5x)

### Text Merging Strategy (RapidFuzz)
1. Collect all text lines from all 3 OCR engines
2. Use `rapidfuzz.fuzz.token_sort_ratio()` to compare lines between engines
3. **Threshold: 85** — lines with similarity ≥ 85 are duplicates
4. For duplicate lines, keep the version with highest confidence (if available) or first occurrence
5. Concatenate unique lines in order, preserving structural information (e.g., line breaks)
6. Final output = `full_text` string (may span multiple paragraphs)

**Example**:
```
PaddleOCR:  ["John Doe", "Senior Manager", "Google Inc.", "john@google.com"]
EasyOCR:    ["John Doe", "Senior Mgr", "Google", "john@google.com"]
Tesseract:  ["Jon Doe", "Sr Manager", "Google Inc", "john@google.com"]

→ Merged (threshold 85):
  - "John Doe" (PaddleOCR, EasyOCR similar; keep PaddleOCR)
  - "Senior Manager" (PaddleOCR vs "Senior Mgr" is 83% match; not above threshold; keep both or best?)
  - etc.
```

### Error Handling in OCR
- If PaddleOCR fails: continue with EasyOCR and Tesseract
- If EasyOCR fails: use PaddleOCR and Tesseract
- If Tesseract fails: use PaddleOCR and EasyOCR
- If all engines fail or return empty: set `full_text = ""`, trigger field_extractor fallback (all fields = `"Not Available"`)
- Log all failures with image filename for debugging

---

## 5. Data Architecture

### PostgreSQL Table: `cards`

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
    full_text    TEXT,
    image_path   TEXT,
    created_at   TIMESTAMP DEFAULT NOW()
);
```

### Column Definitions

| Column | Type | Source | Rules |
|--------|------|--------|-------|
| `id` | SERIAL PRIMARY KEY | Auto-generated | Unique identifier for each card |
| `name` | TEXT | Extracted by `field_extractor.py` | Default: `"Not Available"` if not detected |
| `designation` | TEXT | Extracted by `field_extractor.py` | Default: `"Not Available"` |
| `company` | TEXT | Extracted by `field_extractor.py` | Default: `"Not Available"` |
| `country` | TEXT | Extracted by `field_extractor.py` | Default: `"Not Available"` |
| `phone` | TEXT | Extracted by `field_extractor.py` | Default: `"Not Available"`; accepts any phone format |
| `email` | TEXT | Extracted by `field_extractor.py` | Default: `"Not Available"`; regex validation |
| `address` | TEXT | Extracted by `field_extractor.py` | Default: `"Not Available"` |
| `full_text` | TEXT | Produced by `merger.py` | Raw merged OCR text; used to generate embeddings |
| `image_path` | TEXT | Populated by `image_loader.py` | Relative path from project root (e.g., `assets/42.png`); unique constraint enforced |
| `created_at` | TIMESTAMP | Database default | Set automatically on INSERT |

### Database Connection
- **Driver**: `asyncpg` (async PostgreSQL driver)
- **URL Format**: `postgresql+asyncpg://user:password@localhost/visitingcards`
- **Connection Pool**: SQLAlchemy async session factory with default pooling
- **Session Injection**: FastAPI `Depends()` pattern for async context

### Indexing & Re-indexing
- **First Run**: `POST /process-assets` reads all 348 PNGs from `assets/`, processes, and populates entire `cards` table
- **Subsequent Runs**: `POST /process-assets` can be idempotent — check `image_path` uniqueness before re-processing. Option to truncate table and rebuild from scratch.
- **Uniqueness**: `image_path` should be unique; duplicate images not processed twice

---

## 6. RAG Architecture

### Embedding Model

**Model**: `sentence-transformers` pre-trained model (e.g., `all-MiniLM-L6-v2` or `all-mpnet-base-v2`)
- **Input**: Text string (`full_text` from each card or user query)
- **Output**: Dense vector (384-dimensional float32 for MiniLM; 768 for MPNet)
- **Loading**: Loaded once at FastAPI startup via lifespan event
- **Storage**: Cached in `app.state.embedder`
- **Fallback**: If model not cached locally, auto-downloaded from HuggingFace Hub on first run

### FAISS Index

| Property | Specification |
|----------|----------------|
| **Index Type** | `faiss.IndexFlatL2` (exact L2 distance search) |
| **Dimensionality** | Matches embedding model (384 or 768) |
| **Normalization** | L2-normalize vectors before indexing; L2 distance ≈ cosine similarity |
| **Persistence** | Saved as binary file to `embeddings/cards.index` |
| **ID Mapping** | Separate mapping file `embeddings/id_map.json`: `{faiss_position: postgres_id}` |
| **Startup Loading** | Loaded once into `app.state.faiss_index` via lifespan event |
| **Scalability** | Use `IndexFlatL2` for ≤1,000 cards (fast & exact). For >10,000 cards, migrate to `IndexIVFFlat(nlist=100)` without data schema changes. |

### Query-to-Result Flow

1. **User Query Input** (e.g., "John from Google")
2. **Encode Query**: Pass query string to `embeddings.py` → returns 384-dim float32 vector
3. **Normalize**: L2-normalize the query vector
4. **FAISS Search**: Call `faiss_index.search(query_vector, k=1)` → returns FAISS position + distance
5. **ID Lookup**: Consult `id_map.json` → map FAISS position to PostgreSQL `id`
6. **Database Fetch**: Execute `SELECT * FROM cards WHERE id = ?` → retrieve full card row
7. **Response**: Return JSON with all fields + `image_path` + `full_text`
8. **Frontend Render**: `CardDisplay.tsx` fetches image via `GET /image/{id}`

### Vector Building (Indexing Phase)

For each card in PostgreSQL:
1. Retrieve `full_text`
2. Encode via sentence-transformers → 384-dim vector
3. L2-normalize vector
4. Add to FAISS index at position = `row_number` (ascending card IDs)
5. Record mapping: `id_map[faiss_position] = postgres_id`
6. After processing all cards, save FAISS binary index + id_map.json

---

## 7. API Design (FastAPI)

**Base URL**: `http://localhost:8000`
**Framework**: FastAPI with Uvicorn
**CORS Policy**:
```
allow_origins=["http://localhost:3000"]
allow_methods=["*"]
allow_headers=["*"]
```
**Response Format**: JSON for all endpoints; binary PNG for image endpoints

### Endpoint 1: POST `/process-assets`

**Purpose**: Trigger full OCR, extraction, and FAISS indexing pipeline

**Request**:
- Method: POST
- Body: None (or empty JSON `{}`)

**Response** (200 OK):
```json
{
  "status": "ok",
  "cards_indexed": 348,
  "timestamp": "2026-03-17T10:45:23Z"
}
```

**Error Responses**:
- `500`: Database connection failure, OCR critical error
- Response: `{"detail": "Failed to process assets: <reason>"}`

**Behavior**:
- Read all `.png` files from `assets/` directory
- For each image, run full OCR + merge + extract + insert into PostgreSQL
- Build FAISS index from all `full_text` values
- Save `embeddings/cards.index` and `embeddings/id_map.json`
- **Idempotent**: Can be called multiple times; existing cards not re-processed (optional check by `image_path` uniqueness)

---

### Endpoint 2: GET `/search-card?q=<query>`

**Purpose**: Semantic search — find top-1 most relevant card

**Request**:
- Method: GET
- Query Parameter: `q` (required, non-empty string)
- Example: `/search-card?q=john%20from%20google%20in%20uae`

**Response** (200 OK):
```json
{
  "id": 42,
  "name": "John Doe",
  "designation": "Senior Manager",
  "company": "Google Inc.",
  "country": "UAE",
  "phone": "+971-50-1234567",
  "email": "john.doe@google.com",
  "address": "Dubai, UAE",
  "full_text": "John Doe\nSenior Manager\nGoogle Inc.\n+971-50-1234567\njohn.doe@google.com\nDubai, UAE",
  "image_path": "assets/42.png",
  "created_at": "2026-03-17T10:45:00Z"
}
```

**Error Responses**:
- `422 Unprocessable Entity`: Query parameter `q` missing or empty
  - Response: `{"detail": [{"loc": ["query", "q"], "msg": "Query parameter required"}]}`
- `404 Not Found`: No cards indexed yet
  - Response: `{"detail": "No cards available for search"}`
- `503 Service Unavailable`: FAISS index not loaded (startup incomplete)
  - Response: `{"detail": "Index not ready. Run /process-assets first."}`

**Behavior**:
- Encode query string via sentence-transformers → 384-dim vector
- L2-normalize query vector
- Search FAISS with `k=1` → get nearest card FAISS position
- Lookup FAISS position in `id_map.json` → get PostgreSQL `id`
- Query PostgreSQL: `SELECT * FROM cards WHERE id = ?`
- Return full card as JSON
- Response time: <500ms (excluding network latency)

---

### Endpoint 3: GET `/get-card/{id}`

**Purpose**: Fetch card metadata by ID

**Request**:
- Method: GET
- Path Parameter: `id` (integer)
- Example: `/get-card/42`

**Response** (200 OK):
```json
{
  "id": 42,
  "name": "John Doe",
  "designation": "Senior Manager",
  "company": "Google Inc.",
  "country": "UAE",
  "phone": "+971-50-1234567",
  "email": "john.doe@google.com",
  "address": "Dubai, UAE",
  "full_text": "John Doe\nSenior Manager\nGoogle Inc.\n+971-50-1234567\njohn.doe@google.com\nDubai, UAE",
  "image_path": "assets/42.png",
  "created_at": "2026-03-17T10:45:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Card ID does not exist
  - Response: `{"detail": "Card not found"}`
- `422 Unprocessable Entity`: Invalid `id` (non-integer)
  - Response: `{"detail": [{"loc": ["path", "id"], "msg": "value is not a valid integer"}]}`

**Behavior**:
- Query PostgreSQL: `SELECT * FROM cards WHERE id = ?`
- Return full card row as JSON
- No embedding/search involved; pure metadata fetch

---

### Endpoint 4: GET `/download-card/{id}`

**Purpose**: Serve card image as file download

**Request**:
- Method: GET
- Path Parameter: `id` (integer)
- Example: `/download-card/42`

**Response** (200 OK):
- Status: 200 OK
- Content-Type: `image/png`
- Content-Disposition: `attachment; filename="card_42.png"`
- Body: Binary PNG image data

**Error Responses**:
- `404 Not Found`: Card not found OR image file missing from `assets/`
  - Response: `{"detail": "Card not found"}`

**Behavior**:
- Lookup card in PostgreSQL by `id` → retrieve `image_path`
- Read PNG file from `image_path` (e.g., `assets/42.png`)
- Return with `Content-Disposition: attachment` header to trigger browser download
- Original filename preserved in download (e.g., `card_42.png`)

---

### Endpoint 5: GET `/image/{id}` (Implicit)

**Purpose**: Serve card image for inline display in frontend

**Request**:
- Method: GET
- Path Parameter: `id` (integer)
- Example: `/image/42`

**Response** (200 OK):
- Status: 200 OK
- Content-Type: `image/png`
- Body: Binary PNG image data

**Error Responses**:
- `404 Not Found`: Card not found OR image file missing

**Behavior**:
- Similar to `/download-card/{id}`, but WITHOUT `Content-Disposition: attachment` header
- Browser renders image inline in `<img>` tag
- Used by `CardDisplay.tsx` for display
- No download prompt

---

## 8. Frontend Design (Next.js)

### Framework & Architecture
- **Framework**: Next.js 14+ with App Router (`app/` directory structure)
- **Language**: TypeScript
- **Styling**: CSS Modules or Tailwind CSS (flexible)
- **State Management**: React hooks (useState, useContext) — no Redux/Zustand required
- **API Client**: Custom fetch wrapper in `lib/api.ts`

### Pages

| Route | File | Purpose |
|-------|------|---------|
| `/` | `app/page.tsx` | Main page: search input, results, card display, action buttons |

### Components

| Component | File | Responsibility |
|-----------|------|-----------------|
| **SearchBar** | `components/SearchBar.tsx` | Text input field + submit button; calls `POST /search-card?q=<text>`; handles loading state |
| **ResultsList** | `components/ResultsList.tsx` | Displays selected card name + company; allows re-selection (optional for future multi-result display) |
| **CardDisplay** | `components/CardDisplay.tsx` | Renders card image via `<img src="/image/{id}">` + all 7 structured fields in a readable layout |
| **ActionButtons** | `components/ActionButtons.tsx` | Download button (`<a href="/download-card/{id}" download>`) + Print button (`window.print()`) |

### API Client (`lib/api.ts`)

Provides typed fetch wrappers for all endpoints:

```typescript
// Example functions
async function searchCard(query: string): Promise<Card>
async function getCard(id: number): Promise<Card>
async function processAssets(): Promise<{status: string, cards_indexed: number}>
```

All calls target `http://localhost:8000`.

### UI Behavior & User Flow

1. **Page Load**: Display empty SearchBar + prompt "Enter a search query"
2. **User Types & Submits**: SearchBar shows loading spinner
3. **API Response**:
   - If successful: render ResultsList (card name + company) + CardDisplay (image + metadata) + ActionButtons
   - If error: show error message (e.g., "No cards found" or "Query required")
4. **Download Click**: Browser download dialog opens; saves PNG to Downloads folder
5. **Print Click**: Browser print dialog opens; CSS `@media print` hides SearchBar/ActionButtons; shows only CardDisplay
6. **New Search**: User enters new query; repeat from step 2

### Print Styling

CSS `@media print` rules (in `CardDisplay.tsx` or global stylesheet):
```css
@media print {
  body { margin: 0; padding: 0; }
  nav, header, footer, .search-bar, .action-buttons { display: none; }
  .card-display { width: 100%; page-break-after: avoid; }
  img { max-width: 100%; }
}
```

### Image Rendering

- All card images fetched dynamically from `/image/{id}` — not served as static assets
- Image URL: `http://localhost:8000/image/{id}`
- Used in `<img src="...">` tag in CardDisplay
- No base64 encoding; direct HTTP request

### Error Handling

- Network errors: "Failed to reach server. Check backend is running."
- 404 errors: "Card not found"
- 422 validation errors: "Please enter a valid search query"
- 503 Service Unavailable: "Index not ready. Please wait for /process-assets to complete."

### No Upload Feature (Initial Version)

- Upload/add new cards NOT required for initial implementation
- All 348 images pre-loaded in `assets/` directory
- Future enhancement: POST `/api/upload` endpoint + card re-indexing

---

## 9. Folder Structure

```
C:\Users\Nisar\Desktop\AI_chatbot_visitingcards\
│
├── assets/                                  # Source data: 348 PNG visiting card images
│   ├── 1.png
│   ├── 2.png
│   └── ...
│   └── 348.png
│
├── backend/                                 # FastAPI application
│   ├── main.py                              # FastAPI app: CORS setup, lifespan events, router registration
│   ├── .env                                 # Configuration: DATABASE_URL, ASSETS_DIR
│   ├── requirements.txt                     # Python dependencies (pinned versions)
│   │
│   ├── api/
│   │   └── routes.py                        # All 5 endpoint handlers (POST /process-assets, GET /search-card, etc.)
│   │
│   ├── ocr/
│   │   ├── paddle_ocr.py                    # Wrapper around PaddleOCR; input: image path → output: list of text lines
│   │   ├── easy_ocr.py                      # Wrapper around EasyOCR
│   │   ├── tesseract_ocr.py                 # Wrapper around Tesseract (system-level binary)
│   │   └── merger.py                        # RapidFuzz deduplication + merging; input: 3 OCR outputs → output: full_text string
│   │
│   ├── rag/
│   │   ├── embeddings.py                    # Sentence-transformers model loader + encode functions
│   │   └── search.py                        # FAISS index build, save, load, search; ID mapping management
│   │
│   ├── db/
│   │   ├── models.py                        # SQLAlchemy ORM: Card model (mirrors PostgreSQL schema)
│   │   ├── crud.py                          # Async CRUD functions: insert_card(), get_card_by_id(), get_all_cards(), delete_all_cards()
│   │   └── session.py                       # Async session factory; SQLAlchemy engine + session maker configuration
│   │
│   └── utils/
│       ├── image_loader.py                  # Main orchestrator: reads all PNGs, runs full pipeline per image, calls all modules
│       └── field_extractor.py               # Regex + heuristics: parse full_text → {name, designation, company, ...}
│
├── frontend/                                # Next.js React application
│   ├── app/
│   │   └── page.tsx                         # Main page: layout + integration of all components
│   │
│   ├── components/
│   │   ├── SearchBar.tsx                    # Text input + submit button
│   │   ├── ResultsList.tsx                  # Display selected card summary
│   │   ├── CardDisplay.tsx                  # Image + metadata display + print styles
│   │   └── ActionButtons.tsx                # Download + Print buttons
│   │
│   ├── lib/
│   │   └── api.ts                           # Fetch wrappers for all backend endpoints
│   │
│   ├── next.config.js                       # Next.js configuration
│   ├── package.json                         # Node.js dependencies
│   └── tsconfig.json                        # TypeScript configuration
│
├── database/
│   └── schema.sql                           # PostgreSQL DDL: CREATE TABLE cards (...)
│
├── embeddings/                              # Generated on first index run
│   ├── cards.index                          # FAISS binary index file
│   └── id_map.json                          # JSON mapping: {faiss_position: postgres_id}
│
├── requirements.txt                         # Python dependencies (root level, or inside backend/)
│
└── SPECIFICATIONS.md                        # This document
```

---

## 10. Data Flow (Step-by-Step)

### Pipeline A: Indexing — POST /process-assets

```
1. User/Admin Triggers:
   POST http://localhost:8000/process-assets

2. routes.py receives request:
   - Calls utils.image_loader.process_all_images()

3. image_loader.py orchestrates full pipeline:
   For each PNG file in assets/ (348 files):

     a) Read PNG from disk via OpenCV

     b) Preprocess image (grayscale, deskew, normalize)

     c) Run PaddleOCR:
        paddle_ocr.py → [list of text lines]

     d) Run EasyOCR:
        easy_ocr.py → [list of text lines]

     e) Run Tesseract:
        tesseract_ocr.py → [list of text lines]

     f) Merge OCR outputs:
        merger.py → full_text string (RapidFuzz dedup threshold=85)

     g) Extract structured fields:
        field_extractor.py → {name, designation, company, country, phone, email, address}

     h) Insert card into PostgreSQL:
        crud.py: INSERT INTO cards (name, designation, ..., full_text, image_path)
                 VALUES (?, ?, ..., ?, ?) → returns postgres_id

     i) Encode for embeddings:
        embeddings.py: encode(full_text) → 384-dim float32 vector

     j) Add to FAISS index:
        search.py: faiss_index.add(vector) at position N
                   id_map[N] = postgres_id

4. After processing all 348 images:
   - Save FAISS binary index: embeddings/cards.index
   - Save ID mapping: embeddings/id_map.json

5. routes.py returns response:
   {
     "status": "ok",
     "cards_indexed": 348,
     "timestamp": "2026-03-17T10:45:23Z"
   }
```

---

### Pipeline B: Search — GET /search-card?q=john%20from%20google

```
1. User enters query in SearchBar (e.g., "john from google")

2. Frontend (SearchBar.tsx) fires:
   GET http://localhost:8000/search-card?q=john%20from%20google

3. routes.py receives request:
   - Extracts query string: q="john from google"
   - Validates q is non-empty (422 if empty)
   - Calls search.py with query

4. search.py handles semantic search:

   a) Encode query via embeddings.py:
      embeddings.encode("john from google") → 384-dim float32 vector

   b) L2-normalize vector:
      vector /= ||vector||

   c) Search FAISS index:
      faiss_index.search(query_vector, k=1) → [distances, indices]
      Returns: faiss_position (integer index in FAISS array)

   d) Lookup ID mapping:
      postgres_id = id_map[faiss_position]

   e) Fetch card from PostgreSQL:
      crud.get_card_by_id(postgres_id) → full Card object

5. routes.py returns full card as JSON:
   {
     "id": 42,
     "name": "John Doe",
     "designation": "Senior Manager",
     "company": "Google Inc.",
     ...
     "image_path": "assets/42.png"
   }

6. Frontend (CardDisplay.tsx) renders:

   a) Display all metadata fields in structured format

   b) Fetch image:
      <img src="http://localhost:8000/image/42" alt="Card 42" />

   c) Render ActionButtons:
      - Download: <a href="/download-card/42" download>
      - Print: <button onClick={window.print()}>

   d) (Optional) ResultsList shows card name + company for context
```

---

### Pipeline C: Download — GET /download-card/42

```
1. User clicks "Download" button in ActionButtons

2. Frontend renders:
   <a href="http://localhost:8000/download-card/42" download>Download</a>

3. routes.py receives GET request:
   - Extracts id=42
   - Calls crud.get_card_by_id(42) → retrieves image_path
   - Reads binary PNG from assets/42.png
   - Returns with headers:
     Content-Type: image/png
     Content-Disposition: attachment; filename="card_42.png"

4. Browser receives response:
   - Triggers download dialog
   - Saves PNG to user's Downloads folder as "card_42.png"
```

---

### Pipeline D: Image Display — GET /image/42

```
1. Frontend (CardDisplay.tsx) renders:
   <img src="http://localhost:8000/image/42" alt="Card 42" />

2. routes.py receives GET request:
   - Extracts id=42
   - Calls crud.get_card_by_id(42) → retrieves image_path
   - Reads binary PNG from assets/42.png
   - Returns with headers:
     Content-Type: image/png
     (NO Content-Disposition header)

3. Browser receives response:
   - Renders image inline in <img> tag
   - (No download dialog)
```

---

## 11. Error Handling

| Scenario | Component | Detection | Handling | User Impact |
|----------|-----------|-----------|----------|------------|
| **OCR Engine Crash** | merger.py | Try-except around paddle_ocr.py/easy_ocr.py/tesseract_ocr.py | Continue with remaining engines; log warning | Card still indexed; fewer OCR sources but pipeline completes |
| **All 3 OCR Engines Fail** | field_extractor.py | Empty full_text string | Set all 7 fields to `"Not Available"`; insert card with empty full_text | Card indexed with minimal metadata; search may not find it well |
| **Corrupt or Unreadable PNG** | image_loader.py | Exception during PIL/OpenCV open | Skip file; log error with filename; continue to next PNG | Image not processed; gap in asset collection but pipeline continues |
| **Field Not Detected in Text** | field_extractor.py | Regex finds no match | Set field = `"Not Available"` | User sees "Not Available" in UI; clear signal of missing data |
| **Duplicate Image Path** | crud.py | image_path uniqueness check | Skip insert OR check on second run and skip re-processing | No duplicate entries; idempotent re-runs safe |
| **Card ID Not Found** | routes.py (GET /get-card/{id}, /image/{id}) | Database query returns None | Return HTTP 404: `{"detail": "Card not found"}` | Frontend displays "Card not found" message |
| **FAISS Index Not Built** | routes.py (GET /search-card) | app.state.faiss_index is None | Return HTTP 503: `{"detail": "Index not ready. Run /process-assets first."}` | Frontend prompts user to trigger indexing |
| **Database Connection Failure** | session.py (startup) | asyncpg connection error | Raise exception; FastAPI lifespan event fails; app doesn't start | Server fails loudly on startup; admin fixes DATABASE_URL in .env |
| **Invalid Query (Empty String)** | routes.py (GET /search-card) | Pydantic validation | Return HTTP 422: `{"detail": [{"loc": ["query", "q"], "msg": "Query parameter required"}]}` | Frontend shows validation error to user |
| **Query Missing Entirely** | routes.py (GET /search-card) | Query param not in request | Pydantic validation error; return 422 | Same as above |
| **Malformed Image Path in DB** | routes.py (GET /image/{id}) | File not found on disk | Return HTTP 404: `{"detail": "Image file not found"}` | Frontend shows "Image unavailable" |
| **Network Timeout (Frontend → Backend)** | SearchBar.tsx | fetch() timeout or error | Catch error in try-catch; display error message | User sees "Failed to reach server" message |
| **Search Takes >500ms** | search.py | FAISS search latency | Rare for <1,000 cards with IndexFlatL2 | Not a failure; just slower than target (still <1s typical) |
| **Out of Memory During OCR** | paddle_ocr.py / image_loader.py | MemoryError exception | Log error; skip image; continue | Card skipped; partial indexing completes |

---

## 12. Performance Strategy

### Batch Processing

**First Run (Full Index)**:
- `image_loader.py` processes all 348 PNG files **sequentially**
- Each image: OCR (~5–30s depending on image quality) + merge (~0.1s) + extract (~0.01s) + DB insert (~0.01s) + embedding (~0.1s)
- **Estimated total**: 5–15 minutes for 348 cards (OCR is the bottleneck)
- Display progress bar via `tqdm` library

**Idempotent Runs**:
- On second run, check `image_path` uniqueness
- Option 1: Skip cards already in DB (faster; incremental)
- Option 2: Truncate table and re-process all (slower; guarantees fresh data)

### Caching Strategies

| Component | Cache | Persistence | Benefits |
|-----------|-------|-------------|----------|
| **Sentence-Transformer Model** | HuggingFace cache directory | `~/.cache/huggingface/hub/` | Downloaded once; reused across app restarts |
| **FAISS Index** | Binary file | `embeddings/cards.index` | Loaded once at startup; not recomputed per search |
| **PostgreSQL Query Results** | SQLAlchemy session cache | Per-request (no cross-request caching) | Database handles query optimization via indexes |

### Efficient Search

- **Index Type**: `IndexFlatL2` for exact search
- **Cards ≤1,000**: <1ms per search query
- **Scalability Plan**: For >10,000 cards, migrate to `IndexIVFFlat(nlist=100)` for faster approximate search without schema changes

### Image Serving

- Images served directly from filesystem via FastAPI `FileResponse`
- No base64 encoding (would 4x file size)
- Browser caching via HTTP headers (optional: `Cache-Control: max-age=3600`)

### Database Optimization

- PostgreSQL index on `id` (primary key) — automatic
- No full-text search on PostgreSQL; FAISS handles semantic search
- SQLAlchemy connection pooling (default 5–10 connections)

### Frontend Optimization

- Search loading state (spinner) shown to user during fetch
- No pre-fetch or lazy-loading (single card view; not a gallery)
- CSS media queries for print (no JavaScript re-rendering)

---

## 13. Deployment (Local)

### Prerequisites

Before starting, ensure you have:

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Backend runtime |
| Node.js | 18+ | Frontend build and dev server |
| PostgreSQL | 15+ | Database server |
| `uv` package manager | Latest | Fast Python dependency installation |
| Tesseract OCR | Latest | System-level OCR binary |

**Installation**:
- **Python 3.10+**: https://www.python.org/
- **Node.js 18+**: https://nodejs.org/
- **PostgreSQL 15+**: https://www.postgresql.org/download/
- **Tesseract OCR**: https://github.com/UB-Mannheim/tesseract/wiki (Windows); `apt-get install tesseract-ocr` (Linux); `brew install tesseract` (macOS)
- **`uv` package manager**: `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Phase 1 — Python Environment

```bash
cd C:\Users\Nisar\Desktop\AI_chatbot_visitingcards

# Create virtual environment
uv venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install Python dependencies
uv pip install -r requirements.txt
```

**Expected Output**:
```
Resolved 47 packages in 0.23s
Prepared environment in 2.34s
Installed 47 packages in 3.45s
```

### Phase 2 — PostgreSQL Setup

Ensure PostgreSQL is running locally.

```bash
# Create database
createdb visitingcards

# Load schema
psql visitingcards < database/schema.sql
```

**Expected Output**:
```
CREATE TABLE
```

### Phase 3 — Environment Configuration

Create `backend/.env` file with the following content:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/visitingcards
ASSETS_DIR=../assets
```

**Notes**:
- Replace `postgres` with your PostgreSQL username
- Replace `password` with your PostgreSQL password
- ASSETS_DIR is relative path from `backend/` directory to `assets/`

### Phase 4 — Index All Cards (One-Time)

This processes all 348 PNG images and populates the database. **Estimated time: 5–15 minutes.**

```bash
cd backend
python -m utils.image_loader
```

**Expected Output**:
```
Processing images...
  assets/1.png (1 of 348)
  assets/2.png (2 of 348)
  ...
  assets/348.png (348 of 348)

Successfully indexed 348 cards.
FAISS index saved to embeddings/cards.index
ID mapping saved to embeddings/id_map.json
```

### Phase 5 — Start FastAPI Backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Verify**:
- Open browser to `http://localhost:8000/docs` — FastAPI Swagger UI should display all 5 endpoints

### Phase 6 — Start Next.js Frontend (New Terminal)

In a **new terminal window**:

```bash
cd frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```

**Expected Output**:
```
> next dev
  ▲ Next.js 14.0.0
  - Local:        http://localhost:3000
  - Environments: .env.local

Ready in 2.4s
```

**Verify**:
- Open browser to `http://localhost:3000`
- SearchBar should be visible
- Enter test query (e.g., "google") → should return top-1 card

---

## Verification Checklist

After following all steps, verify:

- [ ] PostgreSQL database created with `cards` table containing ~348 rows
- [ ] `embeddings/cards.index` file exists (size ~500MB for 348 cards)
- [ ] `embeddings/id_map.json` file exists and is valid JSON
- [ ] FastAPI `/docs` page shows 5 endpoints (POST /process-assets, GET /search-card, GET /get-card/{id}, GET /download-card/{id}, GET /image/{id})
- [ ] NextJS frontend loads at `http://localhost:3000`
- [ ] SearchBar accepts input
- [ ] Submitting query returns card with image + metadata
- [ ] Download button works (PNG downloads to Downloads folder)
- [ ] Print button opens print dialog (card image visible when printing)

---

## Appendix: Troubleshooting

### Backend Won't Start
- **Error**: `ModuleNotFoundError: No module named 'paddleocr'`
  - **Fix**: Re-run `uv pip install -r requirements.txt`

- **Error**: `psycopg2.OperationalError: connection failed`
  - **Fix**: Check DATABASE_URL in `.env`; ensure PostgreSQL is running: `psql -U postgres -d visitingcards`

### Frontend Can't Connect to Backend
- **Error**: `Failed to reach server`
  - **Fix**: Ensure FastAPI is running on port 8000; check CORS: `allow_origins=["http://localhost:3000"]` in `main.py`

### Search Returns No Results
- **Error**: `Index not ready. Run /process-assets first.`
  - **Fix**: Execute `python -m utils.image_loader` to build FAISS index

### Tesseract Not Found
- **Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'tesseract'`
  - **Fix**: Install Tesseract OCR binary at system level (not Python package)

---

**End of Specifications Document**
