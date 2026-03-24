# AI Business Card Search Engine

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

A powerful AI-driven system for extracting, indexing, and searching business card information using OpenAI Vision (one-time indexing) and local sentence-transformers embeddings for search.

**350+ cards permanently indexed and searchable. No re-indexing needed. Local semantic search in sub-100ms.**

---

## ⚡ Quick Start (3 Steps)

### 1️⃣ Install Dependencies
```bash
# Backend
cd backend
pip install -r ../requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2️⃣ Configure Environment
Edit `backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://[username]:[password]@[host]:[port]/[database]
OPENAI_API_KEY=sk-proj-[YOUR_API_KEY]  # Only needed for re-indexing new cards
ASSETS_DIR=assets
MAX_CARDS=0  # All cards already processed
```

### 3️⃣ Run the System
```bash
# Terminal 1: Backend
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

**Open browser**: http://localhost:3000

---

## ✨ Features

- 🔍 **Semantic Search** - Find cards with natural language queries (LOCAL, sub-100ms)
- 📊 **95%+ Accuracy** - OpenAI Vision OCR with confidence scoring
- 🎯 **Structured Data** - Extract name, company, phone, email, address, etc.
- 📱 **Responsive UI** - Works on desktop and mobile
- ⚡ **Fast Search** - Sub-100ms with local sentence-transformers embeddings
- 📥 **Download Cards** - Export as PNG images
- 🖨️ **Print Cards** - Print-friendly layout
- 📋 **Admin Panel** - Manage cards at /admin
- 📤 **CSV Export** - Export all card data

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                   │
│         Search Bar → Card Table → Card Display          │
└────────────────────────┬────────────────────────────────┘
                         │
                    HTTP API
                         │
┌────────────────────────▼────────────────────────────────┐
│                  BACKEND (FastAPI)                      │
│   OpenAI Vision (indexing) → sentence-transformers     │
│   all-MiniLM-L6-v2 (384-dim, LOCAL embeddings)        │
└────────────────────────┬────────────────────────────────┘
                         │
                    PostgreSQL
                         │
┌────────────────────────▼────────────────────────────────┐
│                     DATABASE                            │
│   Business Cards + Embeddings (BYTEA, 384-dim)          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **PostgreSQL** 14+
- **OpenAI API Key** (only needed for re-indexing new cards; search uses local embeddings)

### Database Setup

```bash
# Create database
createdb visitingcards

# Install pgvector and create tables
psql visitingcards < database/schema.sql
```

---

## 📖 Usage

### Search for Cards
1. Open http://localhost:3000
2. Type in search box: "john smith from techcorp"
3. Results update in real-time
4. Click a card to view full details

### View Card Details
- Image preview
- Name, designation, company
- Phone, email, address
- Country and full metadata

### Download Card
Click "Download" button to save PNG to your computer

### Print Card
Click "Print" button for print-friendly view

---

## 🚀 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | System status |
| `POST` | `/process-assets` | Start indexing |
| `GET` | `/search-card?q=john` | Search (returns top match) |
| `GET` | `/all-cards` | List all cards |
| `GET` | `/cards/{id}` | Get card by ID |
| `GET` | `/image/{id}` | Download card image |
| `POST` | `/add-card` | Add a new card |
| `PUT` | `/update-card/{id}` | Update card metadata |
| `DELETE` | `/delete-card/{id}` | Delete a card |
| `GET` | `/export-csv` | Export all cards as CSV |

### Example: Search
```bash
curl "http://localhost:8000/search-card?q=software%20engineer"
```

---

## 📁 Project Structure

```
.
├── backend/                 # FastAPI server
│   ├── main.py             # Application entry
│   ├── .env                # Configuration
│   ├── api/
│   │   └── routes.py       # API endpoints
│   ├── ocr/
│   │   ├── openai_vision.py # Vision API wrapper
│   │   └── qwen_vision.py  # Qwen Vision (experimental)
│   ├── utils/
│   │   ├── image_loader.py # Process PNG/JPG files
│   │   └── field_extractor.py # Validate fields
│   ├── db/
│   │   ├── models.py       # Database schema
│   │   ├── crud.py         # Database operations
│   │   └── session.py      # Database connection
│   └── rag/
│       ├── embeddings.py   # sentence-transformers (local, 384-dim)
│       └── vector_search.py # Vector similarity search
│
├── frontend/               # Next.js web interface
│   ├── app/
│   │   ├── page.tsx        # Main page
│   │   └── admin/          # Admin page
│   ├── components/
│   │   ├── SearchBar.tsx   # Search input
│   │   ├── CardsTable.tsx  # Card list
│   │   ├── CardDisplay.tsx # Card detail
│   │   ├── ResultsList.tsx # Search results
│   │   └── ActionButtons.tsx # Download/Print
│   └── lib/
│       └── api.ts          # API client
│
├── database/
│   ├── schema.sql          # PostgreSQL DDL
│   ├── cards_backup.sql    # Database backup
│   └── cards_export.csv    # CSV export of all cards
│
├── assets/                 # Business card images (PNG)
├── assets2/                # Additional business card images (JPG)
│
└── [Documentation files]
    ├── project.md          # Full technical brief
    ├── SETUP_GUIDE.md      # Detailed setup
    └── TEST_GUIDE.md       # Testing procedures
```

---

## 🧪 Testing

### Verify Indexed Cards
```bash
# Check database (350+ cards already indexed)
psql -d visitingcards
SELECT id, name, company, designation FROM cards LIMIT 10;
```

### Re-indexing (only if needed for new cards)
```bash
# Set MAX_CARDS=0 in backend/.env (process all)
# Requires OPENAI_API_KEY for OCR
# Restart backend
```

---

## 📊 Performance

| Operation | Time |
|-----------|------|
| Search query | < 100ms (local embeddings, no API call) |
| Card indexing (1 image) | 2-5 seconds |
| Full indexing (350+ cards) | ~25-30 minutes |
| Cost (initial indexing) | One-time $3-5 (OpenAI Vision). No ongoing API costs. |

---

## 🛠️ Configuration

### Environment Variables

**`backend/.env`**:
```env
# Database connection
DATABASE_URL=postgresql+asyncpg://[username]:[password]@[host]:[port]/[database]

# OpenAI API key (only needed for re-indexing new cards)
OPENAI_API_KEY=sk-proj-[YOUR_API_KEY]

# Assets directory
ASSETS_DIR=assets

# Process all cards (0 = all; 350+ cards already indexed)
MAX_CARDS=0
```

### Modify OCR Behavior

Edit `backend/ocr/openai_vision.py`:
- Change `model="gpt-4o"` to use different Vision model
- Modify prompt to extract different fields
- Adjust confidence score thresholds

### Add Custom Field Validators

Edit `backend/utils/field_extractor.py`:
- Add new validation functions
- Expand country list
- Customize error handling

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: openai"
```bash
pip install -r requirements.txt
```

### "Connection refused: localhost:5432"
PostgreSQL is not running. Start it:
```bash
# macOS
brew services start postgresql

# Linux
sudo service postgresql start

# Windows
# Use pgAdmin or Services app
```

### "OPENAI_API_KEY not set"
Only needed for re-indexing new cards. Search uses local embeddings and does not require an API key.

### "Low search accuracy"
- Ensure all cards are indexed (`/health` endpoint)
- Check card image quality
- Try rephrasing search query

---

## 📝 API Examples

### Search for a Card
```bash
curl "http://localhost:8000/search-card?q=john%20smith"
```

### Get All Cards
```bash
curl http://localhost:8000/all-cards | jq '.[0:5]'
```

### Check System Health
```bash
curl http://localhost:8000/health
```

### Trigger Card Processing
```bash
curl -X POST http://localhost:8000/process-assets
```

---

## 📚 Documentation

For detailed information:

- **[project.md](./project.md)** - Complete technical specification
- **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Detailed setup instructions
- **[TEST_GUIDE.md](./TEST_GUIDE.md)** - Testing and validation procedures
- **[IMPLEMENTATION_COMPLETE.md](./IMPLEMENTATION_COMPLETE.md)** - Implementation details

---

## 🔐 Security Notes

- **API Key**: Keep `OPENAI_API_KEY` secret - never commit to git (only needed for re-indexing)
- **Database Password**: Use strong PostgreSQL password
- **CORS**: Frontend CORS is restricted to `localhost:3000`
- **Production**: Use environment-specific `.env` files
- **Note**: Search does not require any API keys (uses local embeddings)

---

## 💡 Tips & Tricks

### Search Tips
- Use complete phrases: "john smith from techcorp" instead of just "john"
- Combine name + company for better results
- Try different phrasings for semantic search
- Search is LOCAL (no API calls) -- sub-100ms response

### Cost Notes
- Initial indexing cost: one-time $3-5 (OpenAI Vision)
- Search: FREE (local sentence-transformers embeddings)
- No ongoing API costs

---

## 🚦 Status & Roadmap

**Current** ✅
- 350+ cards permanently indexed and searchable. No re-indexing needed.
- OpenAI Vision OCR (one-time cost at indexing, not ongoing)
- sentence-transformers all-MiniLM-L6-v2 (384-dim, LOCAL embeddings)
- PostgreSQL with embeddings stored as BYTEA
- Frontend with real-time search + admin page at /admin
- Download, print, CSV export functionality
- Add/update/delete card management

**Planned**
- Analytics dashboard
- Mobile app (React Native)
- Duplicate detection
- Advanced field customization

---

## 📞 Support

**Issues?** Check these resources:
1. [TEST_GUIDE.md](./TEST_GUIDE.md) - Testing checklist
2. [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Setup troubleshooting
3. PostgreSQL logs: `psql visitingcards` → check table
4. OpenAI status: https://status.openai.com/

---

## 📄 License

MIT License - See LICENSE file for details

---

**Built with**: OpenAI Vision (indexing) • sentence-transformers (search) • PostgreSQL • FastAPI • Next.js

**Last Updated**: March 24, 2026

---

**Ready to search your cards?** Start with `npm run dev` and visit http://localhost:3000 🎉
