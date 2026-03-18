# OpenAI + PostgreSQL pgvector Architecture - Setup Guide

This document provides step-by-step instructions to set up and test the upgraded visiting card RAG system with OpenAI Vision API and PostgreSQL pgvector.

## Architecture Changes Summary

### Before (Offline)
- **OCR**: TrOCR (transformer-based, runs locally)
- **Embeddings**: sentence-transformers all-MiniLM-L6-v2 (384-dim)
- **Vector Search**: FAISS (local index, no persistence)
- **Database**: SQLite

### After (Cloud-Grade)
- **OCR**: OpenAI Vision API (gpt-4o model)
- **Embeddings**: OpenAI text-embedding-3-large (3072-dim, SOTA quality)
- **Vector Search**: PostgreSQL pgvector (local, persisted, indexed)
- **Database**: PostgreSQL with pgvector extension

## Prerequisites

### System Requirements
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (with pgvector extension)
- OpenAI API key with Vision API access

### Installation

#### 1. PostgreSQL + pgvector Setup

**On macOS (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**On Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

**On Windows:**
Download and install PostgreSQL from https://www.postgresql.org/download/windows/

Once PostgreSQL is running, create the database and install pgvector:

```bash
# Create database
createdb visitingcards

# Connect and install extension
psql visitingcards

# Inside psql:
CREATE EXTENSION IF NOT EXISTS vector;

# Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
-- Should return a row with vector extension

# Create tables (run the schema)
\i database/schema.sql

# Exit psql
\q
```

#### 2. OpenAI API Key

Get your OpenAI API key from https://platform.openai.com/api-keys

You need:
- Vision API access (for gpt-4o model)
- Embeddings API access (for text-embedding-3-large)

#### 3. Update Backend Environment

Edit `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/visitingcards
OPENAI_API_KEY=sk-proj-your-actual-key-here
ASSETS_DIR=assets
PGVECTOR_DIMENSIONS=3072
```

Replace:
- `postgres` with your PostgreSQL user (default is usually `postgres`)
- `password` with your PostgreSQL password
- `sk-proj-...` with your actual OpenAI API key

#### 4. Install Python Dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r ../requirements.txt
```

#### 5. Install Frontend Dependencies

```bash
cd frontend
npm install
```

## Running the System

### Phase 1: Backend Startup

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Starting up...
INFO:     Database tables created
INFO:     OpenAI embedder client initialized
INFO:     Auto-indexing needed. Starting in background...
```

### Phase 2: Trigger Indexing (First Time Only)

In another terminal:

```bash
curl -X POST http://localhost:8000/process-assets
```

Or use the frontend's UI to trigger it. The endpoint will:
1. Read all PNG files from `assets/` directory
2. Call OpenAI Vision API for each image (gpt-4o)
3. Extract structured fields using field_extractor
4. Generate embeddings using OpenAI text-embedding-3-large (3072-dim)
5. Store everything in PostgreSQL with pgvector vectors

**Progress Tracking:**
- Monitor the health endpoint: `curl http://localhost:8000/health`
- Check indexing status:
  ```json
  {
    "status": "ok",
    "embedder_ready": true,
    "indexing_status": "running",
    "cards_indexed": 123,
    "total_cards": 348
  }
  ```

### Phase 3: Frontend Startup

```bash
cd frontend
npm run dev
```

Open browser to http://localhost:3000

## Testing Checklist

### Backend Tests

#### 1. Health Check
```bash
curl http://localhost:8000/health
```
Expected response:
```json
{
  "status": "ok",
  "embedder_ready": true,
  "indexing_status": "done",
  "cards_indexed": 348,
  "total_cards": 348,
  "indexing_error": null
}
```

#### 2. Test Search Endpoint
```bash
curl "http://localhost:8000/search-card?q=john%20smith"
```
Expected response: Card JSON with full metadata including embedding

#### 3. Test All Cards Endpoint
```bash
curl http://localhost:8000/all-cards | jq '. | length'
```
Expected: `348` (or number of PNG files in assets/)

#### 4. Test Image Serving
```bash
curl http://localhost:8000/image/1 --output card_1.png
```
Expected: PNG file downloads successfully

#### 5. Verify Database
```bash
psql visitingcards

# Inside psql:
SELECT COUNT(*) FROM cards;
-- Should return 348 (or number of images)

SELECT embedding FROM cards LIMIT 1 \gx
-- Should show 3072-dimensional vector

-- Check index exists
SELECT indexname FROM pg_indexes WHERE tablename='cards' AND indexname LIKE 'idx_cards%';
-- Should list: idx_cards_embedding

-- Test pgvector search manually
SELECT id, name, embedding <-> ARRAY[...]::vector(3072) AS distance
FROM cards
ORDER BY embedding <-> ARRAY[...]::vector(3072)
LIMIT 1;
```

### Frontend Tests

1. **Load Page**
   - Navigate to http://localhost:3000
   - Verify CardsTable loads with all 348 cards
   - Verify no console errors

2. **Test Search**
   - Type "john" in search box
   - Wait for debounce (300ms)
   - Verify card results appear and CardDisplay updates
   - Check that results match query semantically

3. **Test Card Selection**
   - Click a row in the CardsTable
   - Verify CardDisplay updates with selected card
   - Verify image loads correctly
   - Verify metadata displays (name, designation, company, etc.)

4. **Test Download**
   - Click "Download" button on a selected card
   - Verify PNG file downloads with filename format `card_{id}.png`

5. **Test Print**
   - Click "Print" button
   - Verify print preview shows card with image and metadata
   - Verify other UI elements are hidden in print view

6. **Mobile Responsiveness**
   - Resize browser to mobile width (375px)
   - Verify table remains readable (horizontal scroll if needed)
   - Verify buttons stack vertically
   - Verify no layout breaks

## Performance Benchmarks

### Expected Performance

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Indexing 1 image | 2-5 seconds | OpenAI Vision API call (bottleneck) |
| Indexing 348 images | ~25-30 min | Sequential processing with API rate limits |
| Search query | <100ms | pgvector with ivfflat index |
| Embedding generation | ~100ms | OpenAI API round-trip |
| Frontend load | <500ms | After backend is ready |

### Cost Estimation

**Per Run (348 cards):**
- Vision API: ~$0.50-1.00 (depends on image resolution, ~40KB avg)
- Embeddings API: ~$0.15-0.20 (3072-dim model, ~20 tokens per card)
- **Total: ~$0.70-1.20 per full reindex**

**Monthly (assuming 2 full reindexes):**
- ~$1.50-2.50/month

## Troubleshooting

### Issue: "OPENAI_API_KEY not set"
**Solution:**
1. Ensure `backend/.env` has `OPENAI_API_KEY=sk-proj-...`
2. Restart backend: `uvicorn main:app --reload`

### Issue: "pgvector extension not found"
**Solution:**
1. Install pgvector: `CREATE EXTENSION vector;`
2. Verify: `SELECT * FROM pg_extension WHERE extname = 'vector';`

### Issue: "IndexError" in image_loader
**Solution:**
1. Check ASSETS_DIR path in `.env`
2. Ensure PNG files exist in `assets/` directory
3. Check file permissions

### Issue: Search returns "503 - Embedder not ready"
**Solution:**
1. Wait for auto-indexing to complete
2. Check health endpoint: `curl http://localhost:8000/health`
3. Verify OpenAI API key is valid

### Issue: PostgreSQL connection refused
**Solution:**
1. Ensure PostgreSQL is running: `pg_isready`
2. Check DATABASE_URL in `.env`
3. Verify username/password match your PostgreSQL setup

## File Changes Summary

### Backend Changes
- ✅ `backend/.env` - Updated with OpenAI key and PostgreSQL URL
- ✅ `backend/ocr/openai_vision.py` - NEW: OpenAI Vision wrapper
- ✅ `backend/rag/embeddings.py` - Updated: OpenAI embeddings client
- ✅ `backend/rag/vector_search.py` - NEW: pgvector search
- ✅ `backend/rag/search.py` - REMOVED: FAISS index (no longer used)
- ✅ `backend/db/models.py` - Updated: Added embedding Vector column
- ✅ `backend/db/crud.py` - No changes (handles embedding transparently)
- ✅ `backend/utils/image_loader.py` - Updated: Uses OpenAI Vision + pgvector
- ✅ `backend/api/routes.py` - Updated: Uses pgvector search
- ✅ `backend/main.py` - Updated: Removed FAISS, simplified startup

### Database Changes
- ✅ `database/schema.sql` - Updated: Added embedding vector(3072) column
- ✅ PostgreSQL: Added pgvector extension and ivfflat index

### Frontend Changes
- ✅ `frontend/lib/api.ts` - Updated: HealthStatus interface (removed faiss_ready)
- ✅ `frontend/app/page.tsx` - No changes needed (already has CardsTable)
- ✅ `frontend/components/CardsTable.tsx` - No changes (already functional)

### Requirements Changes
- ✅ `requirements.txt` - Updated: Removed torch, sentence-transformers, faiss-cpu
- ✅ `requirements.txt` - Updated: Added openai, pgvector

## Next Steps

1. **Verify Setup:**
   - Run backend health check
   - Start indexing with POST /process-assets
   - Monitor progress on frontend

2. **Monitor Costs:**
   - Track OpenAI API usage in dashboard
   - Adjust as needed based on actual costs

3. **Optimize Performance:**
   - Consider batch processing if indexing is slow
   - Monitor pgvector query times with EXPLAIN ANALYZE

4. **Production Deployment:**
   - Use environment-specific .env files
   - Set up database backups
   - Monitor API usage and costs
   - Consider using OpenAI rate limiting headers

## Additional Resources

- [OpenAI Vision API Docs](https://platform.openai.com/docs/guides/vision)
- [OpenAI Embeddings API Docs](https://platform.openai.com/docs/guides/embeddings)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [PostgreSQL Full Text Search](https://www.postgresql.org/docs/current/textsearch.html)

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review server logs: `tail -f backend.log`
3. Check database connectivity: `psql visitingcards`
4. Verify OpenAI API status at https://status.openai.com/
