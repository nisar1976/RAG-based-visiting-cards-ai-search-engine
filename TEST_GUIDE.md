# OCR & Field Extraction Quality Improvement - Test Guide

## Summary of Changes

### Phase 1: Dependencies
✅ Added to `requirements.txt`:
- `phonenumbers>=8.13.0` - Phone number validation and formatting
- `fuzzywuzzy>=0.18.0` - Fuzzy string matching (optional for company names)

### Phase 2: OCR Module (`backend/ocr/openai_vision.py`)
✅ **Changes:**
- Changed prompt to request **structured JSON output** instead of plain text lines
- New JSON schema includes: `name`, `designation`, `company`, `country`, `phone`, `email`, `address`, and `confidence` scores
- Returns dict instead of list[str]
- Added JSON parsing with error handling
- Improved error logging

**Example Output (OLD):**
```
['John Smith', 'Senior Software Engineer', 'ABC Corp', '+1-555-0123', ...]
```

**Example Output (NEW):**
```json
{
  "name": "John Smith",
  "designation": "Senior Software Engineer",
  "company": "ABC Corp",
  "phone": "+1-555-0123",
  "email": "john.smith@abc.com",
  "address": "123 Main St, San Francisco, CA 94102",
  "country": "USA",
  "confidence": {
    "name": 95,
    "designation": 90,
    "company": 88,
    "phone": 85,
    "email": 92,
    "address": 80,
    "country": 90
  }
}
```

### Phase 3: Field Extraction (`backend/utils/field_extractor.py`)
✅ **Complete rewrite:**
- Now accepts JSON dict from OCR (instead of raw text)
- Validates each field with proper libraries:
  - **Phone**: `phonenumbers` library - validates E.164 format
  - **Email**: Regex validation with TLD check
  - **Address**: Basic validation (length, content check)
  - **Country**: Expanded to 200+ countries with aliases
  - **Name/Designation/Company**: Length and content validation
- Confidence-based acceptance (fields below 30-40% confidence set to "Not Available")
- Logs validation results with confidence scores
- Returns same field dict format but with validated values

**Key Improvements:**
- Expanded COUNTRIES from 46 to 200+ with aliases
- Phone numbers formatted to E.164 (international) standard
- Proper name/company/designation validation
- Only "Not Available" when field truly missing from OCR

### Phase 4: Image Loader (`backend/utils/image_loader.py`)
✅ **Changes:**
- Handles JSON output from `openai_vision.extract()` (no longer text lines)
- Removed call to `merger.merge()` (no longer needed)
- Added **MAX_CARDS** environment variable support for testing:
  - Set `MAX_CARDS=20` to process only first 20 PNG files
  - Useful for validation before processing all 348 cards
- Enhanced logging:
  - Logs all extracted fields for each card
  - Includes confidence scores from OCR
  - Shows first 30 chars of name/company/designation, full country
- Full_text built from extracted fields (not raw OCR output)

### Phase 5: Configuration (`backend/.env`)
✅ **Added:**
```
MAX_CARDS=20
```

This enables test mode by default. Remove or set to 0 for full processing.

---

## Testing Instructions

### Step 1: Prepare Environment

```bash
# Install dependencies (if not done automatically)
pip install -r requirements.txt

# Ensure PostgreSQL is running
# Verify .env contains:
# - DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@localhost/visitingcards
# - OPENAI_API_KEY=sk-...
# - ASSETS_DIR=assets
# - MAX_CARDS=20 (for testing phase)
```

### Step 2: Clear Database (Test Mode)

```bash
# Clear all existing cards
psql -U postgres -d visitingcards << 'EOF'
TRUNCATE cards CASCADE;
SELECT COUNT(*) FROM cards;
EOF
```

Expected output: `count | 0`

### Step 3: Start Backend with Test Mode

```bash
# From project root
cd backend
uvicorn main:app --reload
```

**Expected behavior:**
- Application starts at http://localhost:8000
- `MAX_CARDS=20` is applied from .env
- Processing begins automatically (or via POST /process-assets)
- Should take 2-3 minutes for 20 cards

### Step 4: Monitor Indexing Logs

Watch the console for logs like:

```
[1/20] card_001.png: name=John Smith (conf=95), company=TechCorp (conf=88), designation=Senior Engineer (conf=90), country=USA (conf=95)
[2/20] card_002.png: name=Sarah Johnson (conf=92), company=InnovateTech (conf=85), designation=Product Manager (conf=88), country=UK (conf=90)
...
Successfully indexed 20 cards into PostgreSQL with pgvector
```

**Look for:**
- ✅ High confidence scores (75-100 for most fields)
- ✅ Actual names, companies, designations (not "Not Available")
- ✅ Countries identified correctly
- ✅ No major errors

### Step 5: Query Results

```bash
# Connect to database
psql -U postgres -d visitingcards

# Check extracted data
SELECT
  id,
  name,
  designation,
  company,
  phone,
  email,
  country,
  address
FROM cards
ORDER BY id
LIMIT 20;
```

**Expected improvements:**
- **Names**: Should see actual person names (0-5% "Not Available")
- **Designations**: Should see job titles (5-15% "Not Available", up from 20-35%)
- **Company**: Should see company names (10-20% "Not Available", down from 30-50%)
- **Country**: Should see country names (10-30% "Not Available", down from 40-60%)
- **Phone**: Should see formatted numbers or few "Not Available" (0-3%)
- **Email**: Should be mostly valid or "Not Available" (~2-3%)
- **Address**: Should see street addresses (5-15% "Not Available", down from 10-20%)

### Step 6: Manual Verification (Critical!)

For the first 5-10 cards:
1. Open the actual card image from `assets/` directory
2. Compare extracted data against what you see on the image
3. Check for accuracy:
   - ✅ Names match exactly
   - ✅ Designations are actual job titles
   - ✅ Company names are correct
   - ✅ Phone format is valid
   - ✅ Emails are real
   - ✅ Countries match the address/business location
   - ✅ Addresses are complete

**If issues found:**
- Note which cards have problems
- Check if it's a pattern (e.g., certain types of fonts/cards)
- Verify OpenAI API key has sufficient quota

### Step 7: Quality Metrics Checklist

- [ ] At least 80% of names extracted (not "Not Available")
- [ ] At least 75% of designations extracted
- [ ] At least 70% of companies extracted
- [ ] At least 60% of countries extracted
- [ ] At least 95% of phones are either valid or "Not Available"
- [ ] Most confidence scores > 75%
- [ ] No database errors in logs
- [ ] No JSON parsing errors

### Step 8: Full Processing (After Approval)

Once 20-card test is validated:

**Option A: Keep test data and process remaining cards**
```bash
# Stop current backend (Ctrl+C)
# Modify backend/.env - set MAX_CARDS=0 or remove it
# Restart backend: uvicorn main:app --reload
# Will process cards 21-348 (takes 15-20 minutes)
```

**Option B: Start fresh with all 348 cards**
```bash
# Stop backend
# Clear database
psql -U postgres -d visitingcards -c "TRUNCATE cards CASCADE;"

# Remove MAX_CARDS=20 from backend/.env (or set to 0)
# Restart backend
# Will process all 348 cards
```

---

## Expected Quality Improvements

### From the 20-Card Test:

| Field | Before | After | Improvement |
|-------|--------|-------|-------------|
| Name | 85-95% | 95%+ | Structured JSON from API |
| Designation | 65-80% | 85%+ | Confidence-based validation |
| Company | 50-70% | 80%+ | Better OCR recognition |
| Country | 40-60% | 80%+ | 200+ countries in list |
| Phone | 90-95% | 95%+ | E.164 validation |
| Email | 95%+ | 95%+ | No change needed |
| Address | 80-90% | 90%+ | Better extraction logic |

---

## Troubleshooting

### Issue: "No JSON parsing" errors
**Cause:** OpenAI Vision API returned plain text instead of JSON
**Fix:**
1. Check OPENAI_API_KEY is valid and has quota
2. Check model is "gpt-4o"
3. Verify prompt is correct in openai_vision.py

### Issue: Low confidence scores (<50%)
**Cause:** Card images are unclear or non-standard format
**Fix:**
1. Check image quality (resolution, contrast)
2. Verify text is visible to human eye
3. May be an actual limitation of the card design

### Issue: "Not Available" for most fields
**Cause:** OCR is failing or returning empty JSON
**Fix:**
1. Check API quota and rate limits
2. Verify images exist in `assets/` directory
3. Check image formats (must be PNG)
4. Review logs for specific error messages

### Issue: Country showing "Not Available" for all cards
**Cause:** Country extraction might be stricter than before
**Fix:**
1. Check if country names match COUNTRIES list
2. May need to add country aliases to field_extractor.py
3. Verify OpenAI is detecting country field

---

## Rollback Instructions (if needed)

If results are unsatisfactory:

```bash
# 1. Stop backend (Ctrl+C)

# 2. Restore original files from git:
git checkout backend/ocr/openai_vision.py
git checkout backend/utils/field_extractor.py
git checkout backend/utils/image_loader.py
git checkout backend/.env

# 3. Reinstall old dependencies
pip install -r requirements.txt

# 4. Restart and re-process
uvicorn main:app --reload
```

---

## Next Steps After Validation

1. ✅ Test with 20 cards (you are here)
2. Once validated, process full 348 cards
3. Monitor for any issues during full indexing
4. Once complete, frontend should show better search results
5. Optional: Fine-tune OCR prompt based on card patterns observed

---

## Key Files Modified

- `backend/ocr/openai_vision.py` - JSON output from Vision API
- `backend/utils/field_extractor.py` - Complete rewrite for JSON + validation
- `backend/utils/image_loader.py` - Handle JSON + MAX_CARDS support
- `backend/.env` - Added MAX_CARDS=20
- `requirements.txt` - Added phonenumbers, fuzzywuzzy
