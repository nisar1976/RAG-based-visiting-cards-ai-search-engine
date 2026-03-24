# Running the AI Business Card Search Engine

## Prerequisites

Before starting, ensure you have:
- PostgreSQL installed and running locally
- Node.js/npm installed (for frontend)

## Step 1: Database Setup

### Windows (PowerShell or Command Prompt):
```bash
# Create the database
createdb visitingcards

# Load the schema
psql -U postgres visitingcards < database/schema.sql
```

### macOS/Linux:
```bash
createdb visitingcards
psql visitingcards < database/schema.sql
```

## Step 2: Configure Backend Environment

Update `backend/.env` with your PostgreSQL credentials:
```
DATABASE_URL=postgresql+asyncpg://user:****@localhost/visitingcards
ASSETS_DIR=../assets
```

## Step 3: Start Backend Server

```bash
# Activate virtual environment (if using uv)
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Start FastAPI server
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Server will be available at: **http://localhost:8000**

### Health Check:
```bash
curl http://localhost:8000/health
```

## Step 4: Start Frontend (New Terminal)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

## Step 5: Search for Cards (No Indexing Needed)

**350+ cards are already indexed.** You can start searching immediately.

Use the search interface at http://localhost:3000 to:
- Search by name, company, location, etc. (LOCAL, sub-100ms, no API key needed)
- View card image and extracted metadata
- Download cards as PNG
- Print cards
- Manage cards via admin page at /admin

### Re-indexing (only if adding new cards)
If you need to re-index, an OPENAI_API_KEY is required in backend/.env:
```bash
curl -X POST http://localhost:8000/process-assets
```

## API Endpoints

- `POST /process-assets` - Index all cards from assets/
- `GET /search-card?q=` - Semantic search (LOCAL, sub-100ms)
- `GET /all-cards` - List all cards
- `GET /cards/{id}` - Get card by ID
- `GET /get-card/{id}` - Fetch card metadata
- `GET /image/{id}` - Get card image (inline)
- `GET /download-card/{id}` - Download card image (attachment)
- `POST /add-card` - Add a new card
- `PUT /update-card/{id}` - Update card metadata
- `DELETE /delete-card/{id}` - Delete a card
- `GET /export-csv` - Export all cards as CSV
- `GET /health` - Health check

## Troubleshooting

### PostgreSQL Connection Error
- Ensure PostgreSQL is running
- Check DATABASE_URL in backend/.env
- Verify database user and password

### OCR / Indexing Notes
- OCR uses OpenAI Vision API (only needed for re-indexing new cards)
- 350+ cards are already indexed -- no re-indexing or API key needed for search
- Search uses local sentence-transformers embeddings (all-MiniLM-L6-v2, 384-dim)

### Frontend Connection Issues
- Ensure backend is running on port 8000
- Check CORS is enabled (should be for localhost:3000)
- Check browser console for errors

## Performance Notes

- 350+ cards already indexed from business card image directories
- Search: sub-100ms (local sentence-transformers embeddings, no API call)
- sentence-transformers model downloaded on first use (~80MB, cached locally)

