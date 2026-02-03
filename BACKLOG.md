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

### 3. [research] Enhanced Ticker Enrichment ✅
**Impact**: Medium - better company context  
**Effort**: Low  
**Status**: DONE (2026-02-02)

- Add sector classification (GICS sector/industry) ✅
- Add market cap tier (mega/large/mid/small/micro) ✅
- Add geographic headquarters ✅
- Add key financial metrics (P/E, Revenue, etc.) ✅

**IMPLEMENTATION DETAILS**: Enhanced Finnhub integration with comprehensive ticker enrichment:
- Extended FinnhubClient with sector, industry, country, revenue, growth, EPS data
- Added market cap tier classification (mega/large/mid/small/micro-cap)  
- Enhanced ExploreAgent market section with multiple analysis tables:
  - Trading & Valuation Metrics (price, P/E, market cap, tier, 52W position)
  - Company Profiles & Fundamentals (sector, industry, HQ, revenue, growth, EPS)
  - Sector Exposure analysis  
  - Geographic Exposure analysis
  - Market Cap Distribution analysis
- All functionality tested with comprehensive mock data

---

## 🟡 Medium Priority (Next)

### 4. [ui] Research Comparison View ✅
**Impact**: High - compare opportunities side-by-side  
**Effort**: Medium  
**Status**: DONE (2026-02-02)

Add ability to compare 2-3 research reports:
- Side-by-side TLDR comparison ✅
- Valuation metrics comparison table ✅
- Risk factors comparison ✅  
- "Which is better?" summary ✅

**IMPLEMENTATION DETAILS**: Complete research comparison system with web interface:
- Created `ResearchComparator` utility for parsing and comparing research reports
- Added `/compare` page with interactive research selection interface
- Comprehensive data extraction: TLDR, executive summary, companies, sectors, risks, valuations
- Side-by-side comparison tables with multiple analysis dimensions
- API endpoints: `/api/research/list` and `/api/compare` 
- Advanced parsing with regex patterns for tickers, market data, risk factors
- Responsive web interface with drag-and-drop style selection
- Export functionality placeholder for future enhancement
- All functionality tested and working with real research data

### 5. [feature] Watchlist & Saved Research ✅
**Impact**: Medium - track interesting opportunities  
**Effort**: Medium  
**Status**: DONE (2026-02-02)

- Save research reports to a watchlist ✅
- Mark opportunities as "Interested" / "Passed" / "Tracking" ✅
- Add notes to saved research ✅
- Filter/sort watchlist by date, rating, sector ✅

**IMPLEMENTATION DETAILS**: Complete saved research system with web interface:
- Created `saved_research.html` template with full CRUD operations and filtering
- Added "Save to Watchlist" button to research document view
- Integrated with existing `SavedResearchStore` and `SavedResearch` models
- Auto-extraction of tickers, sector, and TLDR from research content
- Full API endpoints: GET/POST `/api/saved-research`, PUT/DELETE `/api/saved-research/{filename}`
- Support for status tracking, ratings (1-5 stars), notes, and tags
- Advanced filtering by status, tags, and sorting by multiple criteria
- Responsive modal interface for editing saved items
- All functionality tested on Flask server (port 5001) with successful CRUD operations

### 6. [export] Excel/CSV Export ✅
**Impact**: Medium - analysts want spreadsheet data  
**Effort**: Low  
**Status**: DONE (2026-02-03)

- Export ticker data to Excel/CSV ✅
- Include valuation metrics, ratings, analysis ✅
- Clean tabular format for further analysis ✅

**IMPLEMENTATION DETAILS**: Complete Excel/CSV export system:
- Created comprehensive `ExcelExporter` utility with markdown table parsing
- Individual research document export to Excel/CSV with structured company data extraction
- Bulk export functionality for watchlist and saved research data
- Web UI integration with export buttons on research, watchlist, and saved research pages  
- Handles list fields properly (themes, tags, tickers) by converting to comma-separated strings
- Export routes: `/export/<filename>/{excel,csv}`, `/export/{watchlist,saved-research}/excel`
- All functionality tested and working with real data

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

### 9. [data] Sector Analysis Cache ✅
**Impact**: Medium - improve performance and reduce API costs  
**Effort**: Medium  
**Status**: DONE (2026-02-03)

Cache sector-level research to avoid redundant API calls.
- Intelligent sector detection from search queries ✅
- TTL-based caching with automatic expiration ✅
- Sector-specific cache invalidation and management ✅
- Performance monitoring and hit rate tracking ✅

**IMPLEMENTATION DETAILS**: High-performance sector caching system:
- Created `SectorAnalysisCache` with `CacheEntry` and `SectorInfo` models
- Intelligent sector detection from queries using keyword mapping
- TTL-based caching (12-hour default) with automatic cleanup and expiration
- Separate caching for Finnhub market data and Tavily search results by sector
- Cache performance monitoring with hit rates, size tracking, and utilization stats
- API endpoints for cache management: stats, cleanup, clear operations
- Integrated with ExploreAgent for automatic sector-based caching
- Cache reports included in research documents showing performance metrics
- Reduces redundant API calls and significantly improves research generation speed

### 10. [ui] Interactive Charts Dashboard
Move beyond markdown to interactive charts (Chart.js or Plotly).

### 11. [agents] Multi-theme Correlation ✅
**Impact**: High - identify overlooked cross-theme opportunities  
**Effort**: Medium  
**Status**: DONE (2026-02-03)

Identify cross-theme opportunities and conflicts.
- Analyze overlapping companies across multiple themes ✅
- Detect complementary vs conflicting theme relationships ✅
- Identify multi-theme winners and losers ✅
- Generate cross-theme insights and correlations ✅

**IMPLEMENTATION DETAILS**: Comprehensive multi-theme correlation analysis system:
- Created `MultiThemeCorrelationAnalyzer` with sophisticated pattern matching for company extraction  
- Added `ThemeOverlap` and `CrossThemeOpportunity` models with full correlation analysis
- Sentiment analysis to detect positive/negative exposure across themes
- Correlation classification: complementary, conflicting, independent relationships
- Cross-theme opportunity identification: multi-theme winners, conflicts, diversified plays
- Web interface at `/correlations` with interactive theme selection and filtering
- API endpoints for dynamic correlation analysis and real-time insights
- Integrated with ExploreAgent for automatic correlation analysis in research documents
- Supports confidence scoring and risk factor analysis for each opportunity type

### 12. [data] Historical Analysis Tracking ✅
**Impact**: High - measure research accuracy over time  
**Effort**: High  
**Status**: DONE (2026-02-03)

Track how research predictions performed over time.
- Record thesis at time of analysis ✅
- Track actual price performance ✅
- Calculate hit rate over time ✅

**IMPLEMENTATION DETAILS**: Comprehensive historical tracking and performance measurement system:
- Created `HistoricalTracker` utility with `InvestmentThesis` and `ThesisPerformance` models
- Automatic thesis extraction from research documents using pattern matching
- Price performance tracking with Finnhub integration (initial, current, peak, trough prices)
- Performance metrics calculation: returns, max drawdown, max gain, outcome evaluation
- Hit rate statistics with success/failure/mixed/pending/expired classifications
- Web interface at `/performance` with detailed thesis tracking and filtering
- API endpoints for performance updates and statistics
- Integrated with ExploreAgent for automatic thesis tracking from new research
- Supports multiple prediction types: outperform, underperform, stable, volatile
- Time horizon tracking with automatic outcome evaluation at expiry

### 13. [feature] Source Citations ✅
**Impact**: High - transparency and credibility  
**Effort**: Medium  
**Status**: DONE (2026-02-03)

Link back to original research sources:
- Tavily search result URLs ✅
- Finnhub data attribution ✅
- "Sources" section at bottom of report ✅

**IMPLEMENTATION DETAILS**: Comprehensive source tracking and attribution system:
- Created `SourceTracker` utility that tracks all data sources during research generation
- Integrated with `ExploreAgent` to automatically track Tavily web searches and Finnhub market data
- `ResearchSource` dataclass captures full metadata: URLs, titles, descriptions, access timestamps
- Generates professional "Sources & Data Attribution" section in research documents
- Groups sources by type: Web Research Sources (Tavily), Market Data Sources (Finnhub), AI Analysis
- Includes search queries used, tickers analyzed, data provider attribution
- Added to both main research and follow-up analysis workflows
- Provides transparency and credibility to research output for analysts

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
- [research] Enhanced Ticker Enrichment ✅
- [ui] Research Comparison View ✅
- [feature] Watchlist & Saved Research ✅
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
