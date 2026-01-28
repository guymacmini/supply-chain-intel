# Ralph Fix Plan

## High Priority

- [x] Set up basic project structure and build system
- [x] Define core data structures and types
- [x] Implement basic input/output handling
- [x] Create test framework and initial tests
- [x] Create basic and neat GUI for the platform (explore, thesis, monitoring, watchlist, history)
- [x] Modify Explore Agent to analyze direct and indirect market impacts - Add structured analysis section with "Direct Impact Companies", "Indirect Impact Companies", "Market Segments Affected" with impact severity ratings (High/Medium/Low) - Files: `src/agents/explore_agent.py`
- [x] Add thesis-based investment recommendations to research output - Add "Bullish Scenario" and "Bearish Scenario" sections with specific tickers, entry strategies, and risk factors - Files: `src/agents/explore_agent.py`
- [x] Update research markdown template to include new sections - Add "## Market Impact Analysis" and "## Investment Strategies" sections to generated markdown - Files: `src/agents/explore_agent.py` (prompt templates)
- [x] Add optional API keys to environment configuration - Update `.env.example` with `FINNHUB_API_KEY` and `TAVILY_API_KEY` (optional), update ConfigLoader to read without failing if missing - Files: `.env.example`, `src/utils/config_loader.py`
- [x] Implement Finnhub integration for market data - Create `src/utils/finnhub_client.py`, fetch 52-week high/low, current price, P/E ratio, market cap for researched companies, add "Market Valuation" section to research output, handle gracefully if API key not provided - Files: `src/utils/finnhub_client.py` (new), `src/agents/explore_agent.py` - Dependencies: `finnhub-python>=1.4.0`
- [x] Implement Tavily integration for enhanced web search - Create `src/utils/tavily_client.py`, use Tavily API if key provided, fallback to Anthropic web search otherwise - Files: `src/utils/tavily_client.py` (new), `src/agents/explore_agent.py`, `src/agents/monitor_agent.py` - Dependencies: `tavily-python>=0.3.0`
- [x] Add "Ask Follow-up Question" button to research document viewer in GUI - Add UI element and form with text input for follow-up questions - Files: `src/web/templates/document.html`
- [x] Create API endpoint for follow-up questions - New route `/api/research/followup` (POST), accept original research filename and question text, generate new research file `{original_name}_followup_{timestamp}.md` with reference to original - Files: `src/web/app.py`
- [x] Create follow-up agent or extend Explore Agent - Add method `run_followup(original_research_path, question, depth=1)` that reads original research, maintains context, generates focused analysis - Files: `src/agents/explore_agent.py`
- [x] Update GUI to show follow-up chain/history - Display "Related Research" section with visual indicators for follow-up documents vs original research - Files: `src/web/templates/document.html`, `src/web/templates/history.html`

## Medium Priority
- [x] Add error handling and validation
- [x] Implement core business logic (Explore, Hypothesis, Monitor agents)
- [x] Add configuration management
- [x] Create user documentation (README)

## Low Priority
- [ ] Performance optimization
- [ ] Extended feature set
- [ ] Integration with external services
- [ ] Advanced error recovery

## Completed
- [x] Project initialization
- [x] Python project structure with pyproject.toml
- [x] Core data models (WatchlistEntity, Thesis, Claim, etc.)
- [x] CLI scaffolding with Click
- [x] Explore Agent implementation
- [x] Hypothesis Agent implementation
- [x] Monitor Agent implementation
- [x] Utility modules (ConfigLoader, MarkdownGenerator, WatchlistManager)
- [x] Configuration files (sources.json, watchlist.json)
- [x] Test suite for models and utilities
- [x] README documentation
- [x] Web-based GUI with Flask
- [x] Enhanced Explore Agent with Market Impact Analysis
- [x] Investment Strategies (Bullish/Bearish scenarios)
- [x] Follow-up question functionality in GUI
- [x] Follow-up API endpoint and agent method
- [x] Related research display in document viewer

## Implementation Summary

### Core Features Implemented

1. **Explore Agent** (`src/agents/explore_agent.py`)
   - Discovers second/third-order investment opportunities
   - Maps upstream dependencies and downstream beneficiaries
   - Generates markdown research documents
   - Auto-populates watchlist with discovered entities
   - **NEW**: Market Impact Analysis (Direct/Indirect/Segments)
   - **NEW**: Investment Strategies (Bullish/Bearish scenarios)
   - **NEW**: Follow-up question analysis with context preservation

2. **Hypothesis Agent** (`src/agents/hypothesis_agent.py`)
   - Parses investment theses into testable claims
   - Gathers supporting and contradicting evidence
   - Calculates confidence scores
   - Generates counter-theses (steel-man bear case)
   - Creates monitoring triggers

3. **Monitor Agent** (`src/agents/monitor_agent.py`)
   - Scans news for watchlist entities
   - Scores relevance (1-10 scale)
   - Matches against thesis triggers
   - Generates digest documents

4. **Web GUI** (`src/web/`)
   - Dashboard with statistics
   - Explore page for theme discovery
   - Thesis management page
   - Monitor page with digest viewer
   - Watchlist management
   - Document history view with follow-up indicators
   - **NEW**: Follow-up question form on research documents
   - **NEW**: Related research linking (parent/follow-up)

### CLI Commands Implemented
- `supply-chain-intel explore <query>` - Explore themes/companies
- `supply-chain-intel thesis create <statement>` - Create thesis
- `supply-chain-intel thesis list/show/update/resolve` - Manage theses
- `supply-chain-intel monitor` - Run monitoring scan
- `supply-chain-intel watchlist list/add/remove` - Manage watchlist
- `supply-chain-intel digests` - View monitoring digests
- `supply-chain-intel research list` - View research documents
- `supply-chain-intel gui` - Launch web-based GUI

### Data Storage
- All data stored as JSON/Markdown files (no database)
- Research documents: `data/research/`
- Theses: `data/theses/{active|confirmed|refuted}/`
- Digests: `data/digests/`
- Watchlist: `data/watchlist.json`

## Implementation Notes

### Task Priorities
**Phase 1 (Highest Impact)** - COMPLETE:
- Task 1.1, 1.2, 1.3 - Enhanced research analysis (core value proposition improvement)

**Phase 2 (High Value)** - PENDING:
- Task 2.1, 2.2 - Finnhub integration (market data adds significant credibility)

**Phase 3 (Enhanced Capability)** - COMPLETE:
- Task 3.1, 3.2, 3.3, 3.4 - Interactive follow-ups (better user engagement)

**Phase 4 (Optional Enhancement)** - PENDING:
- Task 2.3 - Tavily integration (nice-to-have, Anthropic search already works)

### Testing Requirements for New Tasks
- **Task 1.x**: Test with bullish and bearish scenarios, verify markdown formatting
- **Task 2.2**: Test with valid/invalid Finnhub API keys, handle rate limits
- **Task 2.3**: Test with valid/invalid Tavily API keys, verify fallback to Anthropic search
- **Task 3.x**: Test follow-up chain, verify context preservation, check file naming

### Dependencies to Add
```txt
# requirements.txt and pyproject.toml
finnhub-python>=1.4.0  # For Task 2.2
tavily-python>=0.3.0   # For Task 2.3
```

### Key Design Decisions
1. **Optional APIs**: All new API integrations must be optional - system should work without them
2. **Graceful Degradation**: If Finnhub/Tavily unavailable, skip those sections (don't fail)
3. **Follow-up Context**: Each follow-up file should reference parent research for traceability
4. **Backward Compatibility**: Existing research documents should still work in GUI

## General Notes
- Application uses Claude Opus 4.5 API for reasoning
- Web search functionality integrated via Anthropic API
- Single-user, local CLI tool as per PRD specifications
- GUI accessible via `supply-chain-intel gui` command
- Focus on MVP functionality first
- Ensure each feature is properly tested
- Update this file after each major milestone
