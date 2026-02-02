# BACKLOG.md - Prioritized Improvement List

## 🔴 High Priority (This Session)

### 1. [analysis] Shortage/Bottleneck Severity Analyzer ✅
**Impact**: High - identifies chokepoints before they become obvious  
**Effort**: Medium  
**Status**: DONE (2026-02-02)

Create `src/analysis/shortage_analyzer.py`:
- Severity scoring: 🔴 CRITICAL / 🟡 WATCH / 🟢 ADEQUATE
- Inputs: lead times, source concentration, capacity utilization
- Output: structured JSON + markdown summary
- Integration: Hook into ExploreAgent output

### 2. [analysis] Valuation Reality Check ✅
**Impact**: High - prevents buying at the top  
**Effort**: Medium  
**Status**: DONE (2026-02-02)

Create `src/analysis/valuation_checker.py`:
- Compare current P/E to 5Y average
- Calculate implied growth rate from current price
- Verdict: PRICED IN / FAIR VALUE / UNDERAPPRECIATED / SPECULATIVE
- Scenario analysis: bull/base/bear upside/downside

### 3. [analysis] Demand Acceleration Scorer ✅
**Impact**: Medium-High - identifies demand multipliers  
**Effort**: Medium  
**Status**: DONE (2026-02-02)

Create `src/analysis/demand_analyzer.py`:
- Demand multiplier: If end market +10%, this tier grows X%
- Scale lead time: Months to add capacity
- Current utilization %
- Pricing power assessment

---

## 🟡 Medium Priority (Next Session)

### 4. [agents] Contrarian Sub-Agent ✅
**Impact**: Medium - challenges consensus thinking  
**Effort**: Low  
**Status**: DONE (2026-02-02)
Create prompt template for contrarian analysis:
- What could go wrong?
- Who benefits if thesis fails?
- What are investors missing?

### 5. [ui] Output Signal-to-Noise Optimization ✅
**Impact**: Medium - makes outputs more scannable  
**Effort**: Medium  
**Status**: DONE (2026-02-02)
- Add TLDR section (2-3 sentences) ✅
- Compress tables (remove low-value columns)
- Highlight actionable insights with 📌
- Add "Key Takeaway" callouts

### 6. [agents] Analyzer Integration ✅
**Impact**: High - brings all analysis together  
**Effort**: Medium  
**Status**: DONE (2026-02-02)
- Integrated shortage_analyzer into ExploreAgent
- Integrated valuation_checker into ExploreAgent  
- Integrated demand_analyzer into ExploreAgent
- Added LLM extraction prompts for structured data
- Analysis sections auto-generated after research

### 8. [research] Enhanced Ticker Enrichment
**Impact**: Medium - better company context  
**Effort**: Low  
- Add sector classification
- Add market cap tier (mega/large/mid/small/micro)
- Add geographic headquarters

---

## 🟢 Low Priority (Backlog)

### 7. [data] Sector Analysis Cache
Cache sector-level research to avoid redundant API calls.

### 8. [ui] Interactive Web Dashboard
Move beyond markdown to interactive charts.

### 9. [agents] Multi-theme Correlation
Identify cross-theme opportunities and conflicts.

### 10. [data] Historical Analysis Tracking
Track how research predictions performed over time.

---

## Completed ✅

### 2026-02-02
- [analysis] Shortage/Bottleneck Severity Analyzer ✅
- [analysis] Valuation Reality Check ✅  
- [analysis] Demand Acceleration Scorer ✅
- [docs] DECISIONS.md and BACKLOG.md created ✅
- [agents] Analyzer integration into ExploreAgent ✅
- [ui] TLDR generation ✅
- [agents] Contrarian/Devil's Advocate analysis ✅
- [test] Integration test suite ✅
