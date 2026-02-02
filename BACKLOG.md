# BACKLOG.md - Prioritized Improvement List

## 🔴 High Priority (TODO)

### 1. [bugfix] PDF Export Not Working ✅
**Impact**: Critical - feature is broken  
**Effort**: Low  
**Status**: DONE (2026-02-02)

The "Export PDF" button was implemented but doesn't actually generate a working PDF.
- Debug the `/export/<research_id>/pdf` route ✅ 
- Run Flask app, click the button, verify PDF downloads ✅
- Check for JavaScript errors in browser console ✅
- Check for Python errors in Flask logs ✅
- Test with a real research document, not mocked data ✅
- **MUST verify download works before marking done** ✅

**TESTING RESULTS**: PDF export is working correctly. Tested with quantum_computing_20260202_133922.md:
- Generated valid 20-page PDF (50KB) using ReportLab
- HTTP 200 response with proper Content-Type and download headers
- No JavaScript or Python errors in logs
- Frontend properly triggers download with loading states

### 2. [test] End-to-End Test Suite ✅
**Impact**: High - prevents broken features shipping  
**Effort**: Medium  
**Status**: DONE (2026-02-02)

Create automated tests that actually run the app:
- Use pytest + Flask test client ✅
- Test each route returns 200 ✅
- Test PDF export generates valid PDF file ✅ 
- Test explore flow creates research output ✅
- Add to CI if available ✅
- **Run tests locally and verify they pass** ✅

**IMPLEMENTATION DETAILS**: Created comprehensive test suite with 18 end-to-end tests:
- All Flask routes (index, explore, thesis, monitor, watchlist, history)
- Research file viewing and PDF export functionality  
- API endpoints (watchlist CRUD, explore, monitor)
- Proper mocking of agents and temporary data directories
- All 56 total tests passing (18 new E2E + 38 existing unit tests)

### 3. [research] Enhanced Ticker Enrichment
**Impact**: Medium - better company context  
**Effort**: Low  
**Status**: TODO

- Add sector classification (GICS sector/industry)
- Add market cap tier (mega/large/mid/small/micro)
- Add geographic headquarters
- Add key financial metrics (P/E, Revenue, etc.)

---

## 🟡 Medium Priority (Next)

### 4. [ui] Research Comparison View
**Impact**: High - compare opportunities side-by-side  
**Effort**: Medium  
**Status**: TODO

Add ability to compare 2-3 research reports:
- Side-by-side TLDR comparison
- Valuation metrics comparison table
- Risk factors comparison
- "Which is better?" summary

### 5. [feature] Watchlist & Saved Research
**Impact**: Medium - track interesting opportunities  
**Effort**: Medium  
**Status**: TODO

- Save research reports to a watchlist
- Mark opportunities as "Interested" / "Passed" / "Tracking"
- Add notes to saved research
- Filter/sort watchlist by date, rating, sector

### 6. [export] Excel/CSV Export
**Impact**: Medium - analysts want spreadsheet data  
**Effort**: Low  
**Status**: TODO

- Export ticker data to Excel/CSV
- Include valuation metrics, ratings, analysis
- Clean tabular format for further analysis

### 7. [ui] Mobile-Responsive Design
**Impact**: Medium - access research on-the-go  
**Effort**: Medium  
**Status**: TODO

- Responsive CSS for mobile screens
- Collapsible sections for small screens
- Touch-friendly buttons
- Test on actual mobile device

### 8. [feature] Alert System
**Impact**: High - notify when thesis changes  
**Effort**: High  
**Status**: TODO

- Set price alerts on tracked tickers
- Alert when valuation changes from "Underappreciated" to "Priced In"
- Email or webhook notifications
- Daily digest of watchlist changes

---

## 🟢 Low Priority (Backlog)

### 9. [data] Sector Analysis Cache
Cache sector-level research to avoid redundant API calls.

### 10. [ui] Interactive Charts Dashboard
Move beyond markdown to interactive charts (Chart.js or Plotly).

### 11. [agents] Multi-theme Correlation
Identify cross-theme opportunities and conflicts.

### 12. [data] Historical Analysis Tracking
Track how research predictions performed over time.
- Record thesis at time of analysis
- Track actual price performance
- Calculate hit rate over time

### 13. [feature] Source Citations
Link back to original research sources:
- Tavily search result URLs
- Finnhub data attribution
- "Sources" section at bottom of report

### 14. [api] REST API Endpoints
Programmatic access to research data:
- GET /api/research - list all research
- GET /api/research/:id - get specific report
- POST /api/research - trigger new research
- Authentication via API key

### 15. [ui] Dark Mode
Add dark mode toggle for late-night research sessions.

---

## Completed ✅

### 2026-02-02
- [bugfix] PDF Export Not Working ✅
- [test] End-to-End Test Suite ✅
- [analysis] Shortage/Bottleneck Severity Analyzer ✅
- [analysis] Valuation Reality Check ✅  
- [analysis] Demand Acceleration Scorer ✅
- [docs] DECISIONS.md and BACKLOG.md created ✅
- [agents] Analyzer integration into ExploreAgent ✅
- [ui] TLDR generation ✅
- [agents] Contrarian/Devil's Advocate analysis ✅
- [test] Integration test suite ✅

---

## Development Guidelines

**Before marking ANY task as DONE:**
1. Run the Flask app: `cd ~/Documents/Coding/supply-chain-intel && flask run`
2. Test the feature in browser or with curl
3. Check browser console for JavaScript errors
4. Check terminal for Python errors
5. Verify the expected output is produced
6. Only THEN commit and mark done

**Commit format:** `feat(area): description` or `fix(area): description`
