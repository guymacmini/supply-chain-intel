# DECISIONS.md - Architectural Decisions Log

## 2026-02-02: Autonomous Improvement Agent Setup

**Decision**: Implement continuous improvement framework with orchestrator + sub-agent architecture.

**Context**: The platform needs to evolve from basic supply chain mapping to actionable investment intelligence with:
- Demand acceleration scoring
- Shortage/bottleneck severity ratings
- Valuation reality checks ("is it priced in?")

**Approach**:
- Orchestrator (Opus) handles code, architecture, coordination
- Research sub-agents (Sonnet) handle parallel web research
- All improvements must pass the "Is this actionable?" quality bar

---

## 2026-02-02: Analysis Framework Gaps Identified

**Current State**:
- ✅ Supply chain tier mapping (Tier 1/2/3)
- ✅ Sector breakdown (Materials/Hardware/Software/Services/Infrastructure)
- ✅ Basic market data via Finnhub
- ✅ Web search via Tavily
- ⚠️ Valuation analysis (basic - just P/E and 52W range)

**Missing**:
- ❌ Demand acceleration analysis (multipliers, scale lead time)
- ❌ Shortage/bottleneck severity scoring (🔴🟡🟢 system)
- ❌ "Is it priced in?" valuation reality check
- ❌ Contrarian analysis (who wins if thesis fails?)
- ❌ Signal-to-noise optimization (outputs too verbose)

**Priority Order**:
1. Shortage/bottleneck analyzer (highest alpha potential)
2. Valuation reality check (prevents buying at the top)
3. Demand acceleration scoring (identifies asymmetric opportunities)
4. Output compression (reduce fluff, increase actionability)

---
