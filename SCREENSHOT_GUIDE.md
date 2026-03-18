# Frontend Screenshot Capture Guide

## Overview

This guide explains how to capture a screenshot of the working frontend system at http://localhost:3000.

---

## Quick Capture Steps

### 1. Start the Services

**Terminal 1: Backend**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2: Frontend**
```bash
cd frontend
npm run dev
```

Wait for both services to start. You should see:
- Backend: `INFO:     Uvicorn running on http://0.0.0.0:8000`
- Frontend: `ready - started server on 0.0.0.0:3000, url: http://localhost:3000`

### 2. Open Browser

Open http://localhost:3000 in your web browser (Chrome, Firefox, Safari, etc.)

### 3. Wait for Data Load

The frontend should:
- Load the main page
- Display the search bar
- Show the cards table with all indexed cards
- Display extracted data (name, designation, company, phone, email, etc.)

**Expected Loading Time**: 2-5 seconds (depends on indexing status)

### 4. Capture Screenshot

Use your browser's built-in screenshot tool:

**Chrome/Edge**:
1. Press `Ctrl+Shift+S` (Windows) or `Cmd+Shift+5` (Mac)
2. Select "Capture full page"
3. Save as `frontend-screenshot.png`

**Firefox**:
1. Press `Ctrl+Shift+S` (Windows) or `Cmd+Shift+S` (Mac)
2. Click "Save full page"
3. Save as `frontend-screenshot.png`

**macOS/Safari**:
1. Press `Cmd+Shift+3` for full screen
2. Select area or use default full-page capture

### 5. Save Screenshot

Save the screenshot to the project root directory as:
```
C:\Users\Nisar\Desktop\AI_chatbot_visitingcards\frontend-screenshot.png
```

---

## Expected Frontend Layout

The screenshot should show the following layout:

```
┌─────────────────────────────────────────────────────────────┐
│                    VISITING CARD SEARCH SYSTEM              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Search: [_________________________] 🔍              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ID │ Name              │ Company       │ Country    │  │
│  ├────┼───────────────────┼───────────────┼────────────┤  │
│  │ 1  │ Amer Ahmed Hashmi │ Creative Sols │ UAE        │  │
│  │ 2  │ Sarah Johnson     │ TechCorp Inc  │ USA        │  │
│  │ 3  │ Ehtesham Jerral   │ Global Ent    │ Pakistan   │  │
│  │ 4  │ Prof. Shakil Mali │ University    │ India      │  │
│  │ 5  │ John Smith        │ InnovateTech  │ UK         │  │
│  │ ... │                   │               │            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ SELECTED CARD DETAILS                                │  │
│  │  ┌─────────────────┐                                 │  │
│  │  │   [Card Image]  │  Name: Amer Ahmed Hashmi       │  │
│  │  │   (PNG Preview) │  Designation: Graphic Designer │  │
│  │  │                 │  Company: Creative Solutions   │  │
│  │  │                 │  Country: United Arab Emirates │  │
│  │  │                 │  Phone: +971-4-123-4567       │  │
│  │  │                 │  Email: amer@creative.ae       │  │
│  │  │                 │  Address: Dubai, UAE           │  │
│  │  │                 │                                 │  │
│  │  │  [Download] [Print]                             │  │
│  │  └─────────────────┘                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Elements to Verify in Screenshot

When capturing the screenshot, verify these elements are visible:

- ✅ **Header**: "Visiting Card Search System" or similar title
- ✅ **Search Bar**: Input field with placeholder text
- ✅ **Cards Table**: Shows multiple cards with:
  - ID numbers (1, 2, 3, 4, ...)
  - Names (person names extracted)
  - Companies (company names)
  - Designations (job titles)
  - Countries (location)
  - Additional fields (phone, email, etc.)
- ✅ **Card Details Section**: Shows:
  - Card image preview
  - Name, designation, company
  - Phone, email, address
  - Country information
- ✅ **Action Buttons**: Download and Print buttons
- ✅ **Data Quality**: All fields populated (not showing "Not Available" mostly)

---

## If Cards Are Not Showing

If the cards table is empty:

1. **Check Backend Status**
   ```bash
   curl http://localhost:8000/health
   ```

   Should show: `"indexing_status": "done"` and `"cards_indexed": 348` (or number of cards)

2. **Trigger Indexing** (if needed)
   ```bash
   curl -X POST http://localhost:8000/process-assets
   ```

   Wait 2-3 minutes for first 20 cards (or 25-30 min for all 348)

3. **Check Database**
   ```bash
   psql -U postgres -d visitingcards -c "SELECT COUNT(*) FROM cards;"
   ```

   Should return a number > 0

4. **Check Browser Console**
   - Press F12 to open Developer Tools
   - Check Console tab for errors
   - Check Network tab to verify API calls are succeeding

---

## Manual Screenshot as Fallback

If you prefer not to run the services:

1. Create a markdown mockup showing the expected layout
2. Save it as `frontend-screenshot.md`
3. Include actual card data from TEST_GUIDE.md examples

**Example**:
```markdown
# Frontend Screenshot (Expected Layout)

## Main Page View

### Search Bar
- Input field with placeholder "Search cards..."

### Cards Table
| ID | Name | Designation | Company | Country |
|---|---|---|---|---|
| 1 | Amer Ahmed Hashmi | Graphic Designer | Creative Solutions LLC | UAE |
| 2 | Sarah Johnson | Product Manager | InnovateTech | USA |
| 3 | Ehtesham Jerral | Business Dev Manager | Global Enterprises | Pakistan |
| 4 | Prof. Shakil Jehangir Mali | Dept Head, CS | University of Technology | India |

### Card Details (when selected)
- Image: card_001.png (showing visiting card image)
- Name: Amer Ahmed Hashmi
- Designation: Graphic Designer
- Company: Creative Solutions LLC
- Phone: +971-4-123-4567
- Email: amer@creative.ae
- Address: Dubai, UAE
```

---

## Troubleshooting Screenshot Capture

### Services Won't Start

**Error**: `Connection refused`
```bash
# Ensure PostgreSQL is running
psql -c "SELECT 1"

# Ensure OpenAI API key is valid
echo $OPENAI_API_KEY

# Check ports are free
netstat -tlnp | grep -E '3000|8000'
```

### Frontend Doesn't Load

**Blank page or error**:
1. Check browser console (F12)
2. Verify backend is healthy: `curl http://localhost:8000/health`
3. Check CORS settings in `backend/main.py`
4. Restart both services

### Cards Not Visible

**Empty table**:
1. Check indexing status: `curl http://localhost:8000/health`
2. If `"cards_indexed": 0`, trigger: `curl -X POST http://localhost:8000/process-assets`
3. Wait 2-3 minutes for cards to process
4. Refresh browser (Ctrl+R)

---

## Screenshot Naming & Storage

Save your screenshot as:
```
frontend-screenshot.png
```

**Location**: `C:\Users\Nisar\Desktop\AI_chatbot_visitingcards\frontend-screenshot.png`

**Format**: PNG (recommended) or JPG
**Dimensions**: Full page (capture entire page, not just viewport)
**Size**: No specific limit, but < 5MB recommended

---

## Using the Screenshot in Documentation

Once captured, the screenshot can be:

1. **Embedded in project.md**:
   ```markdown
   ![Frontend Screenshot](./frontend-screenshot.png)
   ```

2. **Embedded in README.md**:
   ```markdown
   ## Screenshot
   ![Visiting Card Search System](./frontend-screenshot.png)
   ```

3. **Used for**: Portfolio, documentation, blog posts, presentations

---

## Automated Screenshot (Advanced)

If you want to automate this with code:

```python
# Option 1: Playwright (Node.js)
npm install -g playwright
python -m pip install playwright
playwright install

# Option 2: Selenium (Python)
pip install selenium

# Option 3: Puppeteer (JavaScript)
npm install puppeteer
```

Then create a script to capture automatically.

---

## Next Steps

After capturing the screenshot:

1. ✅ Save as `frontend-screenshot.png`
2. ✅ Verify it shows:
   - Search bar
   - Cards table with data
   - Card detail view
   - Action buttons
3. ✅ Add to project documentation
4. ✅ Use for presentations/portfolio

---

## Summary Checklist

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] Cards indexed (check `/health` endpoint)
- [ ] Frontend page loads with search bar
- [ ] Cards table displays with actual data
- [ ] Screenshot captured
- [ ] Saved as `frontend-screenshot.png`
- [ ] Used in project documentation

---

**Created**: March 18, 2026
**Purpose**: Capture visual evidence of working system
