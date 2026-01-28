# Product Requirements Document: Supply Chain Intel

## Product Overview

**Product Name:** Supply Chain Intel  
**Version:** 1.0 MVP  
**Author:** Guy (Director of Product, eToro)  
**Date:** January 28, 2026  
**Target Users:** Fundamental investors seeking second and third-order investment opportunities

---

## Executive Summary

Supply Chain Intel is a lightweight research platform that helps fundamental investors identify non-obvious investment opportunities by discovering second and third-order market dependencies. While most investors focus on direct plays (e.g., NVDA for AI), significant alpha exists in upstream suppliers, downstream beneficiaries, and capacity-constrained enablers. This platform surfaces these opportunities through intelligent research agents and continuous monitoring.

### The Problem

Fundamental investors miss significant investment opportunities because:

1. **Information Overload**: Too much data, not enough signal
2. **First-Order Thinking**: Focus on obvious plays while hidden beneficiaries compound gains
3. **Stale Research**: Market conditions change faster than traditional research can adapt
4. **Hypothesis Drift**: No systematic way to validate or refute investment theses over time

### The Solution

A three-agent system powered by Claude Opus that:

1. **Discovers** second and third-order opportunities from themes/companies/markets
2. **Validates** investment hypotheses with supporting and contradicting evidence
3. **Monitors** news continuously to alert investors when new information impacts their theses

---

## Goals and Objectives

### Primary Goals

1. Help investors discover non-obvious investment opportunities through dependency analysis
2. Provide systematic hypothesis validation with evidence scoring
3. Deliver high-signal, low-noise alerts when market events impact user theses

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to first insight | < 2 minutes | From query to actionable research |
| Signal-to-noise ratio | > 70% relevant | User feedback on alert quality |
| Hypothesis accuracy | Track over time | Confirmed vs refuted thesis outcomes |
| User engagement | Daily active usage | Monitor digest open rates |

### Non-Goals (Out of Scope for MVP)

- Real-time streaming data (batch is sufficient)
- Portfolio integration or trade execution
- Backtesting or quantitative analysis
- Mobile application
- Multi-user collaboration

---

## User Personas

### Primary Persona: Independent Fundamental Investor

**Name:** Alex Chen  
**Role:** Independent investor managing personal portfolio ($500K-$5M)  
**Goals:** Find asymmetric opportunities before institutional discovery  
**Pain Points:**
- Spends 3+ hours daily on research with diminishing returns
- Misses second-order plays that outperform obvious bets
- No systematic way to track thesis validity over time
- Information overload from multiple sources

**Needs:**
- Efficient discovery of non-obvious opportunities
- Evidence-based hypothesis validation
- Proactive alerts when news impacts positions

### Secondary Persona: RIA/Small Fund Analyst

**Name:** Sarah Martinez  
**Role:** Research analyst at boutique investment firm  
**Goals:** Generate differentiated research for clients  
**Pain Points:**
- Limited time across multiple coverage sectors
- Difficulty explaining second-order reasoning to clients
- Need audit trail for investment recommendations

---

## Core Features and Requirements

### Feature 1: Explore Agent

**Purpose:** Discover second and third-order investment opportunities from a theme, market, or company.

**User Story:**  
As an investor, I want to explore a theme or company and discover non-obvious related opportunities so that I can find investments before they become mainstream.

**Input:** Natural language query (e.g., "AI infrastructure", "ASML", "renewable energy transition")

**Process:**
1. Identify primary players in the space
2. For each primary player, map:
   - Upstream dependencies (suppliers, components, raw materials)
   - Downstream beneficiaries (customers, distributors, enablers)
   - Capacity constraints (bottlenecks, infrastructure)
   - Regulatory/policy dependencies
3. Go one level deeper on most interesting findings
4. Rank opportunities by exposure level and investment merit

**Output:** Markdown research document containing:
- Primary players table (obvious bets)
- Second-order opportunities with relationship explanations
- Third-order opportunities (deeper dependencies)
- Key relationships to monitor
- Risk factors
- Auto-generated watchlist for monitoring

**Technical Requirements:**
- Use Claude Opus 4.5 API for reasoning
- Web search tool for current information
- Output as structured markdown file
- Append discovered entities to watchlist.json

**Acceptance Criteria:**
- Query completes in < 60 seconds
- Research document is actionable and well-structured
- At least 5 second-order opportunities identified per query
- Entities automatically added to monitoring watchlist

---

### Feature 2: Hypothesis Agent

**Purpose:** Validate or refute user investment hypotheses with evidence-based analysis.

**User Story:**  
As an investor, I want to submit my investment thesis and have it systematically validated with supporting and contradicting evidence so that I can make more informed decisions.

**Input:** Natural language investment thesis (e.g., "I think VRT is undervalued because AI data center demand is accelerating faster than expected and they have 35% market share in thermal management.")

**Process:**
1. Parse thesis into discrete, testable claims
2. For each claim:
   - Search for supporting evidence
   - Search for contradicting evidence (steel-man the counter)
   - Score confidence level (verified/supported/partially supported/unsupported)
3. Identify key assumptions that must be true
4. Identify risks that would break the thesis
5. Construct steel-man counter-thesis
6. Calculate overall confidence score
7. Generate monitoring triggers

**Output:** Markdown thesis document containing:
- Thesis statement (user's original)
- Core claims with validation status and evidence
- Key assumptions table with monitoring triggers
- Risk factors with likelihood and impact
- Counter-thesis (steel-man bear case)
- Confidence score with component breakdown
- Monitoring triggers added to system
- Thesis log for future updates

**Technical Requirements:**
- Use Claude Opus 4.5 API for reasoning and judgment
- Web search for evidence gathering
- Confidence scoring algorithm (clarity, evidence strength, counter-evidence, verifiability, risk/reward)
- Output as structured markdown with frontmatter

**Acceptance Criteria:**
- Thesis parsed into at least 2 testable claims
- Both supporting and contradicting evidence provided
- Confidence score between 0-100 with reasoning
- Counter-thesis presents genuine bear case
- Monitoring triggers automatically generated

---

### Feature 3: Monitor Agent

**Purpose:** Continuously scan news sources and alert users when new information impacts their theses or watchlist.

**User Story:**  
As an investor, I want to receive high-signal alerts when news impacts my investment theses so that I can react quickly to material changes.

**Input:**
- watchlist.json (entities to track)
- Active theses from /theses/active/
- Whitelisted news sources configuration

**Process:**
1. Fetch recent news for each watchlist entity
2. Score each article for investment relevance (1-10)
3. Filter to high-signal items (score ≥ 7)
4. For high-signal items:
   - Extract key facts
   - Match against active thesis triggers
   - Assess impact on relevant theses
   - Suggest investor action
5. Update thesis confidence scores when triggers fire
6. Compile into daily/hourly digest

**Output:** Markdown digest containing:
- Thesis-specific alerts (triggers fired)
- Updated confidence scores with reasoning
- General high-signal news for watchlist
- Watchlist summary table
- Entities with no significant news

**Technical Requirements:**
- Scheduled execution (configurable: hourly or daily)
- Whitelisted news source configuration (JSON)
- Web search and fetch for news retrieval
- Relevance scoring algorithm
- Thesis trigger matching logic
- Output as timestamped markdown digest

**Whitelisted Sources (Default):**
```json
{
  "tier1_financial": ["reuters.com", "bloomberg.com", "wsj.com", "ft.com"],
  "tier2_industry": ["semiconductorengineering.com", "datacenterdynamics.com"],
  "tier3_filings": ["sec.gov/edgar"],
  "tier4_analysis": ["seekingalpha.com"]
}
```

**Acceptance Criteria:**
- Processes all watchlist entities
- Relevance scoring filters out low-signal noise
- Thesis triggers correctly matched and fired
- Confidence scores updated with reasoning
- Digest generated within 5 minutes

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SUPPLY CHAIN INTEL                         │
│                     Powered by Claude Opus                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                        │
│                         (Python CLI)                            │
└───────────┬─────────────────┬─────────────────┬─────────────────┘
            │                 │                 │
            ▼                 ▼                 ▼
     ┌────────────┐    ┌────────────┐    ┌────────────┐
     │  EXPLORE   │    │ HYPOTHESIS │    │  MONITOR   │
     │   AGENT    │    │   AGENT    │    │   AGENT    │
     └─────┬──────┘    └─────┬──────┘    └─────┬──────┘
           │                 │                 │
           └────────────┬────┴────┬────────────┘
                        │         │
                        ▼         ▼
              ┌──────────────────────────────┐
              │      CLAUDE OPUS 4.5         │
              │   claude-opus-4-5-20251101   │
              │                              │
              │  • Deep reasoning            │
              │  • Multi-step analysis       │
              │  • Nuanced judgment          │
              │  • Evidence weighing         │
              └──────────────┬───────────────┘
                             │
                     ┌───────┴───────┐
                     │               │
                     ▼               ▼
              ┌────────────┐  ┌────────────┐
              │ Web Search │  │  Web Fetch │
              │    Tool    │  │    Tool    │
              └────────────┘  └────────────┘
```

### File Structure

```
supply-chain-intel/
├── src/
│   ├── agents/
│   │   ├── explore_agent.py
│   │   ├── hypothesis_agent.py
│   │   └── monitor_agent.py
│   ├── tools/
│   │   ├── web_search.py
│   │   └── web_fetch.py
│   └── utils/
│       ├── markdown_generator.py
│       └── config_loader.py
├── config/
│   ├── sources.json
│   └── prompts/
│       ├── explore_prompt.md
│       ├── hypothesis_prompt.md
│       └── monitor_prompt.md
├── data/
│   ├── watchlist.json
│   ├── research/
│   ├── theses/
│   │   ├── active/
│   │   ├── confirmed/
│   │   └── refuted/
│   └── digests/
├── main.py
├── scheduler.py
├── requirements.txt
└── README.md
```

### Data Models

**Watchlist Entity:**
```json
{
  "ticker": "VRT",
  "name": "Vertiv Holdings",
  "themes": ["ai_infrastructure", "data_centers"],
  "added_date": "2026-01-28",
  "source_research": "ai_infrastructure_20260128.md"
}
```

**Thesis Frontmatter:**
```yaml
---
id: vrt_datacenter_20260128
status: active
confidence: 72
created: 2026-01-28
updated: 2026-01-28
triggers:
  - "hyperscaler capex"
  - "VRT earnings"
  - "data center construction"
entities:
  - VRT
  - MSFT
  - GOOG
---
```

---

## Technical Constraints and Preferences

### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.11+ | Best LLM ecosystem, familiar |
| LLM | Claude Opus 4.5 | Best reasoning, tool use |
| CLI Framework | Click or Typer | Clean CLI interface |
| Scheduling | APScheduler or cron | Simple, reliable |
| Data Storage | JSON + Markdown files | No database overhead |
| Configuration | JSON/YAML files | Human-readable |

### API Configuration

```python
ANTHROPIC_MODEL = "claude-opus-4-5-20251101"
MAX_TOKENS = 16000
TEMPERATURE = 0.7  # Some creativity for research
```

### Dependencies

```
anthropic>=0.40.0
click>=8.0.0
python-dateutil>=2.8.0
pyyaml>=6.0
schedule>=1.2.0
```

### Constraints

1. **No persistent database** - Files only (markdown, JSON)
2. **Single-user** - No auth, no multi-tenancy
3. **Local execution** - CLI tool, not web service
4. **Anthropic API only** - No other LLM providers
5. **Batch processing** - No real-time streaming

---

## Priority Levels and Phases

### Phase 1: Core MVP (Week 1-2)

**Priority: P0 - Must Have**

1. Explore Agent with basic research output
2. File structure and CLI scaffolding
3. Web search integration via Anthropic API
4. Markdown output generation
5. Basic watchlist management

**Deliverable:** User can explore a theme and get research document.

### Phase 2: Hypothesis Validation (Week 3)

**Priority: P0 - Must Have**

1. Hypothesis Agent with claim parsing
2. Evidence gathering (supporting + contradicting)
3. Confidence scoring algorithm
4. Thesis file management
5. Counter-thesis generation

**Deliverable:** User can submit thesis and get validation report.

### Phase 3: Monitoring System (Week 4)

**Priority: P1 - Should Have**

1. Monitor Agent with news fetching
2. Relevance scoring
3. Thesis trigger matching
4. Digest generation
5. Scheduler integration

**Deliverable:** System generates daily digests with thesis alerts.

### Phase 4: Polish and Refinement (Week 5)

**Priority: P2 - Nice to Have**

1. Thesis lifecycle management (confirm/refute/archive)
2. Historical thesis tracking
3. Source quality weighting
4. Improved prompts based on usage
5. Documentation and examples

---

## CLI Interface Specification

### Commands

```bash
# Explore a theme/company/market
supply-chain-intel explore "AI infrastructure"
supply-chain-intel explore "ASML"
supply-chain-intel explore --help

# Create/manage investment theses
supply-chain-intel thesis "I think VRT is undervalued because..."
supply-chain-intel thesis update vrt_datacenter --add "Management buying back shares"
supply-chain-intel thesis list
supply-chain-intel thesis show vrt_datacenter
supply-chain-intel thesis resolve vrt_datacenter --confirmed
supply-chain-intel thesis resolve vrt_datacenter --refuted --reason "Thesis broken by..."

# Run monitoring
supply-chain-intel monitor
supply-chain-intel monitor --sources custom_sources.json

# Manage watchlist
supply-chain-intel watchlist
supply-chain-intel watchlist add NVDA --theme "AI"
supply-chain-intel watchlist remove NVDA
supply-chain-intel unwatch --theme "Renewable Energy"

# View outputs
supply-chain-intel digests
supply-chain-intel research list
```

### Output Locations

| Command | Output Location |
|---------|-----------------|
| explore | data/research/{theme}_{timestamp}.md |
| thesis | data/theses/active/{id}.md |
| monitor | data/digests/{date}_digest.md |

---

## Success Criteria

### MVP Success Criteria

1. **Functional:** All three agents work end-to-end
2. **Useful:** Research output is actionable for investment decisions
3. **Reliable:** No crashes, graceful error handling
4. **Fast:** Query responses under 60 seconds
5. **Clear:** Output is well-structured and readable

### User Validation Questions

1. Did the research surface opportunities you hadn't considered?
2. Was the hypothesis validation helpful for your decision?
3. Did the monitoring alerts provide actionable signal?
4. Would you use this tool in your daily research workflow?

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM hallucinations | Medium | High | Cross-reference with web search, cite sources |
| API rate limits | Low | Medium | Implement backoff, batch requests |
| News source changes | Medium | Low | Configurable sources, graceful degradation |
| Stale information | Medium | Medium | Clear timestamps, freshness indicators |
| Scope creep | High | High | Strict MVP definition, phase gates |

---

## Appendix

### Example Explore Output

See separate file: `examples/explore_output_example.md`

### Example Thesis Output

See separate file: `examples/thesis_output_example.md`

### Example Digest Output

See separate file: `examples/digest_output_example.md`

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-28 | Guy | Initial PRD |
