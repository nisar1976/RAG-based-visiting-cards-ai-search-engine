# 🚀 Quick Start Guide

## ✅ What's Ready

- **Backend**: All 14 Python files created, dependencies installed via `uv`
- **Frontend**: All 9 React/TypeScript files created, npm dependencies installed
- **Database**: PostgreSQL schema created
- **Project Structure**: 27 files, fully implemented

## 📋 Before You Start

### Required:
1. **PostgreSQL** - Must be running locally
   - Default: `postgresql://postgres@localhost`
   - Can verify with: `psql --version`

2. **Internet Connection** - Needed once for:
   - Downloading OCR models (~400MB total)
   - Downloading embedding model (~200MB)
   - After first run, everything works offline

## 🏃 3-Step Startup

### Step 1️⃣: Database Setup (Run Once)

**Windows (Command Prompt or PowerShell):**
```cmd
createdb visitingcards
psql -U postgres visitingcards < database/schema.sql
```

**macOS/Linux:**
```bash
createdb visitingcards
psql visitingcards < database/schema.sql
```

### Step 2️⃣: Start Backend (Terminal 1)

```bash
# Activate virtual environment (Windows):
.venv\Scripts\activate

# Or macOS/Linux:
source .venv/bin/activate

# Start server
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3️⃣: Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

**Expected Output:**
```
> next dev
  ▲ Next.js 14.2.0
  - Local:        http://localhost:3000
```

## 🎯 First Run: Index Your Cards

1. Open **http://localhost:3000**
2. Click **"Index Cards (First Run)"** button
3. ⏳ Wait 5-15 minutes (processing 350+ images)
   - You'll see progress in backend terminal
4. ✅ When done, you're ready to search!

## 🔍 Try It Out

1. Search bar appears at top
2. Type: "John" or "Manager" or "Dubai"
3. See:
   - Card image on left
   - Extracted metadata on right
   - Download & Print buttons

## 🛠️ Configuration

**`backend/.env`** - Update if needed:
```
DATABASE_URL=postgresql+asyncpg://user:****@localhost/visitingcards
ASSETS_DIR=../assets
```

Replace `user` and `****` with your PostgreSQL username and password.

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                        │
│              http://localhost:3000                           │
│   SearchBar → ResultsList → CardDisplay → ActionButtons     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│              http://localhost:8000                           │
│  Routes ↔ OCR (Paddle/Easy/Tesseract) ↔ FAISS ↔ PostgreSQL  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    assets/      embeddings/      Database
   (PNG files)  (FAISS index)    (Metadata)
```

## 🔗 API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/process-assets` | POST | Index all cards (first run) |
| `/search-card?q=` | GET | Search by query (returns top-1) |
| `/get-card/{id}` | GET | Fetch card metadata |
| `/image/{id}` | GET | Get card image (view inline) |
| `/download-card/{id}` | GET | Download card as PNG |
| `/health` | GET | Check system status |

**Example:**
```bash
# Search
curl "http://localhost:8000/search-card?q=John+Manager"

# Get image
curl http://localhost:8000/image/1 -o card.png

# Check health
curl http://localhost:8000/health
```

## 📁 Project Structure

```
AI_chatbot_visitingcards/
├── backend/                    # FastAPI server
│   ├── main.py                # App entry point
│   ├── api/routes.py          # 5 API endpoints
│   ├── ocr/                   # 3 OCR engines + merger
│   ├── rag/                   # Embeddings + FAISS
│   ├── db/                    # SQLAlchemy models + CRUD
│   ├── utils/                 # Field extraction + image loading
│   └── .env                   # Configuration
├── frontend/                   # Next.js React app
│   ├── app/                   # Pages and layout
│   ├── components/            # React components
│   ├── lib/api.ts            # API client
│   └── package.json          # Dependencies
├── database/schema.sql         # PostgreSQL DDL
├── embeddings/                # FAISS index (auto-generated)
├── assets/                    # 350+ PNG business cards
└── requirements.txt           # Python dependencies
```

## ⚡ Performance

| Operation | Time |
|-----------|------|
| First indexing (350+ cards) | 5-15 minutes |
| Search query (top-1) | <1 second |
| Image download | <1 second |
| Model download (first run) | 2-5 minutes |

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
# Windows: netstat -ano | findstr :8000
# macOS/Linux: lsof -i :8000

# Try different port:
uvicorn main:app --port 8001
```

### PostgreSQL connection error
```bash
# Check PostgreSQL is running
# Windows: sc query postgresql-*
# macOS: brew services list | grep postgres
# Linux: systemctl status postgresql

# Test connection:
psql -U postgres -c "SELECT version();"
```

### Frontend can't reach backend
1. Ensure backend is running on `http://localhost:8000`
2. Check browser console (F12) for CORS errors
3. Verify CORS is enabled in `backend/main.py`

### OCR model download fails
- Need internet connection for first run only
- Models downloaded to: `~/.cache/huggingface/`
- Can manually download if needed

## 📝 Key Features

✅ **Multi-OCR**: PaddleOCR (primary) + EasyOCR + Tesseract
✅ **Smart Merging**: RapidFuzz deduplication (85% threshold)
✅ **Vector Search**: FAISS IndexFlatL2 (L2-normalized)
✅ **Embeddings**: sentence-transformers `all-MiniLM-L6-v2`
✅ **7 Fields**: Name, Designation, Company, Country, Phone, Email, Address
✅ **Fully Offline**: No external APIs after initial setup
✅ **Responsive UI**: Desktop & mobile friendly
✅ **Print Support**: Print business card directly from UI

## 🎓 Next Steps

1. ✅ Start both servers
2. ✅ Index cards via web UI
3. ✅ Search for cards
4. ✅ Download/Print as needed

For detailed troubleshooting, see `SETUP_AND_RUN.md`

---

**Happy searching! 🎯**
