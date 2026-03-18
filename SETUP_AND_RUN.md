# Running the Visiting Card AI System

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
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost/visitingcards
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

## Step 5: Index Visiting Cards

### Option A: Via Web UI
1. Open http://localhost:3000
2. Click "Index Cards (First Run)" button
3. Wait 5-15 minutes for 348+ cards to be processed

### Option B: Via API
```bash
curl -X POST http://localhost:8000/process-assets
```

## Step 6: Search for Cards

Use the search interface at http://localhost:3000 to:
- Search by name, company, location, etc.
- View card image and extracted metadata
- Download cards as PNG
- Print cards

## API Endpoints

- `POST /process-assets` - Index all cards from assets/
- `GET /search-card?q=` - Semantic search (returns top-1 match)
- `GET /get-card/{id}` - Fetch card metadata
- `GET /image/{id}` - Get card image (inline)
- `GET /download-card/{id}` - Download card image (attachment)
- `GET /health` - Health check

## Troubleshooting

### PostgreSQL Connection Error
- Ensure PostgreSQL is running
- Check DATABASE_URL in backend/.env
- Verify database user and password

### OCR Engine Errors
- PaddleOCR: First run downloads ~200MB model (requires internet)
- EasyOCR: First run downloads model (~200MB)
- Tesseract: Must be installed separately (install tesseract-ocr package)

### FAISS Index Issues
- Index files stored in `embeddings/` directory
- Auto-generated on first `/process-assets` call
- Clear `embeddings/` to rebuild index

### Frontend Connection Issues
- Ensure backend is running on port 8000
- Check CORS is enabled (should be for localhost:3000)
- Check browser console for errors

## Performance Notes

- First indexing: 5-15 minutes for 348+ cards (one-time)
- Subsequent searches: <1 second (FAISS L2 distance)
- Model downloads happen on first use (requires internet briefly)

