"""Explore Agent for discovering investment opportunities."""

from datetime import datetime
from pathlib import Path
from typing import Optional
import re
import hashlib
import json
import logging

from ..models import WatchlistEntity, ResearchOpportunity
from ..utils.config_loader import ConfigLoader
from ..utils.markdown_generator import MarkdownGenerator
from ..utils.watchlist_manager import WatchlistManager
from ..utils.finnhub_client import FinnhubClient
from ..utils.tavily_client import TavilyClient
from ..utils.source_tracker import SourceTracker
from ..analysis.shortage_analyzer import ShortageAnalyzer, analyze_bottlenecks
from ..analysis.valuation_checker import ValuationChecker, check_valuations
from ..analysis.demand_analyzer import DemandAnalyzer, analyze_demand
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Cache directory for search results
CACHE_DIR = Path(__file__).parent.parent.parent / "data" / ".cache"


EXPLORE_SYSTEM_PROMPT = """You are an expert investment research analyst specializing in supply chain analysis and second/third-order investment opportunities for fundamental investors.

Your task is to create institutional-quality research that maps the full investment landscape around a theme, identifying non-obvious opportunities that most investors miss.

## Research Framework

### 1. SECTOR BREAKDOWN
Categorize all opportunities into these sectors:
- **Materials**: Raw materials, chemicals, commodities, mining
- **Hardware**: Physical products, components, equipment, manufacturing
- **Software**: Applications, platforms, enterprise tools, AI/ML
- **Services**: Consulting, logistics, maintenance, professional services
- **Infrastructure**: Data centers, networks, utilities, real estate

### 2. SUPPLY CHAIN TIERS
Map relationships at each tier:
- **Tier 1 (Direct)**: Companies directly serving/competing in the theme
- **Tier 2 (Suppliers)**: Suppliers TO the Tier 1 companies
- **Tier 3 (Raw/Commodities)**: Fundamental inputs - raw materials, commodities, basic infrastructure

### 3. GEOGRAPHIC CONCENTRATION RISK
Identify concentration risks:
- Manufacturing hubs (Taiwan semiconductors, China rare earths)
- Single points of failure
- Regulatory jurisdiction exposure
- Currency risks

### 4. COMPETITIVE DYNAMICS
For each major player:
- Market share and position
- Moat type (cost, network, switching, intangible, scale)
- Pricing power (high/medium/low)
- Customer concentration risk

### 5. REGULATORY & POLICY EXPOSURE
- Trade policy sensitivity
- Environmental regulations
- Industry-specific rules
- Subsidy/incentive programs

### 6. PICKS AND SHOVELS
For each theme, identify:
- Testing/measurement equipment
- Enabling software/tools
- Infrastructure providers
- Service providers
- These often have better risk/reward than direct plays

### 7. EXPOSURE SCORING
Rate each opportunity 1-10 on:
- **Theme Exposure**: How directly affected by the theme
- **Competitive Position**: Moat strength and market position
- **Valuation**: Current price vs. intrinsic value opportunity
- **Risk/Reward**: Upside vs downside asymmetry

## Output Guidelines
- Be specific with company names and tickers (use US listings when available)
- Include market cap classifications (mega/large/mid/small/micro)
- Prioritize actionable, differentiated insights
- Identify contrarian opportunities
- Note key catalysts and timelines
- Include both long and short ideas"""


EXPLORE_USER_PROMPT_TEMPLATE = """Analyze the following investment theme and create comprehensive research:

**Topic**: {query}
**Analysis Depth**: {depth} levels

Generate your research using this exact structure:

# Investment Research: {query}
**Generated**: {date}
**Depth**: {depth}-level analysis

---

## Executive Summary
[2-3 paragraph overview: What is this theme? Why does it matter now? What are the key investment implications?]

---

## Sector Breakdown

### Materials
| Ticker | Company | Market Cap | Role | Exposure Score |
|--------|---------|------------|------|----------------|
[Companies in materials/commodities related to this theme]

### Hardware
| Ticker | Company | Market Cap | Role | Exposure Score |
|--------|---------|------------|------|----------------|
[Physical products, components, equipment manufacturers]

### Software
| Ticker | Company | Market Cap | Role | Exposure Score |
|--------|---------|------------|------|----------------|
[Software, platforms, and digital services]

### Services
| Ticker | Company | Market Cap | Role | Exposure Score |
|--------|---------|------------|------|----------------|
[Professional services, consulting, logistics]

### Infrastructure
| Ticker | Company | Market Cap | Role | Exposure Score |
|--------|---------|------------|------|----------------|
[Data centers, networks, utilities, real estate]

---

## Supply Chain Analysis

### Tier 1 - Direct Exposure
| Ticker | Company | Position | Market Share | Moat Type |
|--------|---------|----------|--------------|-----------|
[Companies directly in this market]

**Key Dynamics**: [Analysis of competitive landscape at Tier 1]

### Tier 2 - Supplier Network
| Ticker | Company | Supplies To | Criticality | Alternatives |
|--------|---------|-------------|-------------|--------------|
[Suppliers to Tier 1 companies]

**Key Dynamics**: [Analysis of supplier relationships and dependencies]

### Tier 3 - Raw Materials & Commodities
| Ticker/Asset | Name | Input Type | Supply Constraints |
|--------------|------|------------|-------------------|
[Fundamental inputs - commodities, raw materials]

**Key Dynamics**: [Analysis of raw material supply/demand]

---

## Geographic Concentration Risk

| Region | % of Supply Chain | Risk Level | Key Exposures |
|--------|-------------------|------------|---------------|
[Analysis of geographic dependencies]

**Critical Vulnerabilities**:
- [Vulnerability 1 with affected companies]
- [Vulnerability 2 with affected companies]

---

## Competitive Dynamics

### Market Leaders
| Ticker | Company | Market Share | Moat | Pricing Power | Threat Level |
|--------|---------|--------------|------|---------------|--------------|
[Top 5-10 players with competitive analysis]

### Emerging Challengers
| Ticker | Company | Strategy | Disruption Potential |
|--------|---------|----------|---------------------|
[Companies gaining share or disrupting]

### Moat Analysis
[Deep analysis of which moats are durable vs. eroding]

---

## Regulatory & Policy Exposure

| Policy Area | Direction | Impact | Most Affected |
|-------------|-----------|--------|---------------|
[Regulatory trends and their investment implications]

**Key Policy Catalysts**:
- [Policy catalyst 1 with timeline]
- [Policy catalyst 2 with timeline]

---

## Picks and Shovels Plays

| Ticker | Company | Role | Why It Works | Risk |
|--------|---------|------|--------------|------|
[Companies that benefit regardless of who wins]

**Best Risk-Adjusted Plays**:
[Analysis of which picks & shovels offer best risk/reward]

---

## Scenario Analysis

### Bull Case (25% probability)
**Thesis**: [What needs to happen]
**Upside**: [Magnitude and beneficiaries]
| Ticker | Target Upside | Catalyst |
|--------|---------------|----------|

### Base Case (50% probability)
**Thesis**: [Most likely scenario]
**Outcome**: [Expected returns and positioning]
| Ticker | Expected Return | Positioning |
|--------|-----------------|-------------|

### Bear Case (25% probability)
**Thesis**: [What could go wrong]
**Downside**: [Magnitude and most at risk]
| Ticker | Downside Risk | Hedge |
|--------|---------------|-------|

---

## Investment Strategies

### Long Ideas (Ranked by Conviction)
| Rank | Ticker | Company | Thesis | Entry | Target | Stop |
|------|--------|---------|--------|-------|--------|------|
[Top 5 long ideas with specifics]

### Short/Avoid Ideas
| Ticker | Company | Thesis | Risk |
|--------|---------|--------|------|
[Companies to avoid or short]

### Pairs Trades
| Long | Short | Thesis | Spread Target |
|------|-------|--------|---------------|
[Market-neutral ideas]

---

## Key Catalysts Timeline

| Date/Period | Catalyst | Affected Tickers | Expected Impact |
|-------------|----------|------------------|-----------------|
[Upcoming catalysts with dates]

---

## Risk Factors

| Risk | Probability | Impact | Mitigation | Most Exposed |
|------|-------------|--------|------------|--------------|
[Key risks with analysis]

---

## Recommended Watchlist

| Ticker | Company | Theme | Priority | Entry Trigger |
|--------|---------|-------|----------|---------------|
[Tickers to monitor with specific triggers]

---

## Research Sources
[Note which searches provided key insights]

Use web search extensively to gather current, accurate information. Search for:
- Recent earnings calls and investor presentations
- Industry reports and market research
- Company announcements and press releases
- Analyst coverage and price targets
- Trade publications and expert opinions"""


BOTTLENECK_EXTRACTION_PROMPT = """Based on the research content below, identify the key supply chain bottlenecks and constraints.

For each bottleneck, provide:
1. component: Name of the constrained component/resource
2. lead_time_months: Estimated lead time (null if unknown)
3. source_concentration: "single-source", "dual-source", "concentrated", or "diversified"
4. geographic_risk: Primary geography (e.g., "Taiwan", "China", or null)
5. capacity_utilization: Estimated utilization % (null if unknown)
6. affected_companies: List of ticker symbols most affected

Return as JSON array. Example:
```json
[
  {
    "component": "CoWoS Advanced Packaging",
    "lead_time_months": 9,
    "source_concentration": "single-source",
    "geographic_risk": "Taiwan",
    "capacity_utilization": 95,
    "affected_companies": ["NVDA", "AMD", "TSM"]
  }
]
```

Research content:
{content}

Return ONLY the JSON array, no other text."""


DEMAND_EXTRACTION_PROMPT = """Based on the research content below, identify supply chain tiers and their demand characteristics.

For each tier, provide:
1. tier_name: Descriptive name
2. tier_level: 0=raw materials, 1=components, 2=subsystems, 3=integration
3. demand_multiplier: How much this tier grows vs end market (e.g., 2.0 = grows 20% when end market grows 10%)
4. scale_lead_time_months: Months to add meaningful capacity
5. current_utilization: Estimated utilization % (null if unknown)
6. pricing_power: "high", "medium", or "low"
7. key_players: List of {{"company": "name", "ticker": "SYM"}}

Return as JSON array. Example:
```json
[
  {
    "tier_name": "Advanced GPU Memory (HBM)",
    "tier_level": 1,
    "demand_multiplier": 1.8,
    "scale_lead_time_months": 18,
    "current_utilization": 85,
    "pricing_power": "medium",
    "key_players": [{{"company": "SK Hynix", "ticker": "HXSCF"}}, {{"company": "Samsung", "ticker": "SSNLF"}}]
  }
]
```

Research content:
{content}

Return ONLY the JSON array, no other text."""


VALUATION_EXTRACTION_PROMPT = """Based on the research content and tickers below, provide valuation context for each ticker.

For each ticker, estimate (or mark null if unknown):
1. ticker: The symbol
2. company: Company name
3. current_pe: Approximate current P/E ratio
4. pe_5y_avg: Historical average P/E (estimate)
5. pe_sector_avg: Sector average P/E
6. revenue_growth: Recent YoY revenue growth %
7. earnings_growth: Recent YoY earnings growth %

Return as JSON array. Example:
```json
[
  {{"ticker": "NVDA", "company": "NVIDIA", "current_pe": 55, "pe_5y_avg": 40, "pe_sector_avg": 25, "revenue_growth": 122, "earnings_growth": 150}}
]
```

Tickers to analyze: {tickers}

Research content:
{content}

Return ONLY the JSON array, no other text."""


TLDR_GENERATION_PROMPT = """Based on the research below, generate a 2-3 sentence TLDR that captures:
1. The single most important insight
2. The best actionable opportunity (specific ticker if possible)
3. The biggest risk to watch

Be specific and actionable. No fluff.

Research content:
{content}

TLDR:"""


CONTRARIAN_ANALYSIS_PROMPT = """You are a skeptical, contrarian analyst. Challenge the bull case in this research.

Generate a "Devil's Advocate" section that includes:

## What Could Go Wrong?
[3-5 specific risks that aren't just generic market risk]

## Who Wins If This Thesis Fails?
[Companies/sectors that benefit if the bull case doesn't play out - be specific with tickers]

## What Are Investors Missing?
[2-3 blind spots in the consensus view]

## Counter-Thesis Trades
| If Bull Case Fails | Consider | Ticker | Rationale |
|-------------------|----------|--------|-----------|
[2-3 alternative trades]

Research content:
{content}

Generate the contrarian analysis:"""


class ExploreAgent(BaseAgent):
    """Agent for exploring themes and discovering investment opportunities."""

    def __init__(
        self,
        config_loader: Optional[ConfigLoader] = None,
        markdown_generator: Optional[MarkdownGenerator] = None,
        watchlist_manager: Optional[WatchlistManager] = None,
        finnhub_client: Optional[FinnhubClient] = None,
        tavily_client: Optional[TavilyClient] = None,
        enable_cache: bool = True
    ):
        super().__init__(config_loader)
        self.markdown_generator = markdown_generator or MarkdownGenerator()
        self.watchlist_manager = watchlist_manager or WatchlistManager()
        self.finnhub_client = finnhub_client or FinnhubClient()
        self.tavily_client = tavily_client or TavilyClient()
        self.enable_cache = enable_cache
        self.source_tracker = SourceTracker()
        
        # Ensure cache directory exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, query: str) -> str:
        """Generate a cache key for a search query."""
        return hashlib.md5(query.lower().encode()).hexdigest()

    def _get_cached_search(self, query: str) -> Optional[str]:
        """Get cached search result if available and fresh (24h)."""
        if not self.enable_cache:
            return None
            
        cache_key = self._get_cache_key(query)
        cache_file = CACHE_DIR / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    # Check if cache is less than 24 hours old
                    cached_time = datetime.fromisoformat(data['timestamp'])
                    if (datetime.now() - cached_time).total_seconds() < 86400:
                        logger.debug(f"Cache hit for query: {query}")
                        return data['result']
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")
        
        return None

    def _save_to_cache(self, query: str, result: str):
        """Save search result to cache."""
        if not self.enable_cache:
            return
            
        cache_key = self._get_cache_key(query)
        cache_file = CACHE_DIR / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'query': query,
                    'timestamp': datetime.now().isoformat(),
                    'result': result
                }, f)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _get_tools(self) -> list[dict]:
        """Get the tools available to this agent."""
        return [
            {
                "name": "web_search",
                "description": """Search the web for current information. Use for:
- Company financials, earnings, and market data
- Industry news and analysis
- Supply chain relationships and dependencies
- Competitive landscape information
- Analyst reports and price targets
- Geographic and regulatory information

Craft specific, targeted queries for best results.""",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query - be specific and include relevant keywords"
                        },
                        "search_type": {
                            "type": "string",
                            "enum": ["general", "financial", "news", "company"],
                            "description": "Type of search to optimize results"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        """Handle tool calls with Tavily integration and caching."""
        if tool_name == "web_search":
            query = tool_input.get('query', '')
            search_type = tool_input.get('search_type', 'general')

            # Check cache first
            cached = self._get_cached_search(query)
            if cached:
                self.source_tracker.add_cache_source(query)
                return f"[Cached search results for: {query}]\n{cached}"

            # Try Tavily first
            if self.tavily_client.is_available():
                try:
                    logger.info(f"Executing Tavily search: {query}")
                    
                    if search_type == 'financial':
                        results = self.tavily_client.search_financial_news(query, max_results=10)
                    elif search_type == 'company':
                        results = self.tavily_client.search_company_info(query, max_results=8)
                    else:
                        results = self.tavily_client.search(query, max_results=10)

                    if results and results.get('results'):
                        # Track Tavily sources
                        for result in results.get('results', []):
                            self.source_tracker.add_tavily_source(query, result)
                        
                        formatted = self.tavily_client.format_results_as_text(results)
                        self._save_to_cache(query, formatted)
                        return f"[Tavily search results for: {query}]\n{formatted}"
                        
                except Exception as e:
                    logger.warning(f"Tavily search failed: {e}")

            # Return placeholder - in production this would use Claude's built-in search
            return f"[Web search executed for: {query}] - No results available. Please use your knowledge to provide analysis."
            
        return super()._handle_tool_call(tool_name, tool_input)

    def run(self, query: str, depth: int = 2, max_retries: int = 3) -> Path:
        """
        Explore a theme/company/market and generate research document.

        Args:
            query: The theme, company, or market to explore
            depth: How many levels deep to go (1=primary, 2=secondary, 3=tertiary)
            max_retries: Maximum retry attempts on failure

        Returns:
            Path to the generated research document
        """
        # Clear any previous sources for this research generation
        self.source_tracker.clear()
        
        user_prompt = EXPLORE_USER_PROMPT_TEMPLATE.format(
            query=query,
            depth=depth,
            date=datetime.now().strftime("%Y-%m-%d %H:%M")
        )

        # Retry loop for resilience
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"Running exploration for '{query}' (attempt {attempt + 1}/{max_retries})")
                
                # Call Claude with tools for web search
                content, tool_results = self._call_claude_with_tools(
                    system_prompt=EXPLORE_SYSTEM_PROMPT,
                    user_message=user_prompt,
                    tools=self._get_tools(),
                    max_iterations=15  # Allow more iterations for thorough research
                )

                if not content or len(content) < 500:
                    raise ValueError("Response too short, likely incomplete")

                break
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        else:
            raise RuntimeError(f"Failed after {max_retries} attempts. Last error: {last_error}")

        # Extract tickers for analysis
        tickers = self._extract_tickers(content)
        
        # Generate TLDR (added at the top of the document)
        logger.info("Generating TLDR...")
        tldr_section = self._generate_tldr(content)
        
        # Generate analysis sections
        logger.info("Running bottleneck analysis...")
        bottleneck_section = self._extract_and_analyze_bottlenecks(content)
        
        logger.info("Running demand acceleration analysis...")
        demand_section = self._extract_and_analyze_demand(content)
        
        # Valuation check using extracted tickers
        logger.info(f"Checking valuations for {len(tickers)} tickers...")
        valuation_section = self._extract_and_check_valuations(content, tickers)
        
        # Live market data if Finnhub is available
        if tickers:
            market_section = self._generate_market_valuation_section(tickers)
            if market_section:
                content += "\n" + market_section
        
        # Add analysis sections
        if bottleneck_section:
            content += bottleneck_section
        if demand_section:
            content += demand_section
        if valuation_section:
            content += valuation_section
        
        # Contrarian analysis (devil's advocate)
        logger.info("Generating contrarian analysis...")
        contrarian_section = self._generate_contrarian_analysis(content)
        if contrarian_section:
            content += contrarian_section

        # Add Anthropic knowledge as a source since we use Claude for analysis
        self.source_tracker.add_anthropic_knowledge_source(query)
        
        # Add sources section
        logger.info(f"Adding sources section with {len(self.source_tracker)} sources...")
        sources_section = self.source_tracker.generate_sources_section()
        if sources_section:
            content += sources_section

        # Add research metadata section
        content += self._generate_research_metadata(query, depth, tool_results)
        
        # Prepend TLDR at the top (after the title)
        if tldr_section:
            # Find the first --- after the header and insert TLDR after it
            if "---" in content:
                parts = content.split("---", 2)
                if len(parts) >= 2:
                    content = parts[0] + "---\n\n" + tldr_section + "\n" + "---".join(parts[1:])
            else:
                content = tldr_section + "\n" + content

        # Generate the research document
        metadata = {
            "query": query,
            "depth": depth,
            "model": self.api_config["model"],
            "generated": datetime.now().isoformat(),
            "tool_calls": len(tool_results),
            "tickers_found": len(tickers)
        }
        output_path = self.markdown_generator.generate_research_doc(
            theme=query,
            content=content,
            metadata=metadata
        )

        # Extract and add entities to watchlist
        self._update_watchlist(query, content)

        logger.info(f"Research saved to: {output_path}")
        return output_path

    def _generate_research_metadata(self, query: str, depth: int, tool_results: list) -> str:
        """Generate metadata section for the research document."""
        lines = [
            "\n---",
            "\n## Research Metadata",
            f"- **Query**: {query}",
            f"- **Depth**: {depth}",
            f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Model**: {self.api_config['model']}",
            f"- **Web Searches**: {len(tool_results)}",
        ]
        
        if tool_results:
            lines.append("\n### Search Queries Used")
            for i, result in enumerate(tool_results[:10], 1):
                query_used = result.get('input', {}).get('query', 'N/A')
                lines.append(f"{i}. {query_used}")
        
        return "\n".join(lines)

    def run_followup(self, original_research_path: str, question: str, depth: int = 1) -> Path:
        """
        Run a follow-up analysis based on existing research.

        Args:
            original_research_path: Path to the original research document
            question: The follow-up question to analyze
            depth: Analysis depth (default 1 for follow-ups)

        Returns:
            Path to the generated follow-up research document
        """
        # Clear any previous sources for this research generation
        self.source_tracker.clear()
        
        # Load original research
        original_path = Path(original_research_path)
        if not original_path.exists():
            # Try looking in data/research directory
            data_dir = Path(__file__).parent.parent.parent / "data" / "research"
            original_path = data_dir / original_research_path
            if not original_path.exists():
                raise FileNotFoundError(f"Original research not found: {original_research_path}")

        with open(original_path, 'r') as f:
            original_content = f.read()

        # Extract original theme from filename
        original_theme = original_path.stem.rsplit('_', 1)[0].replace('_', ' ')

        user_prompt = f"""Based on the following original research, please analyze this follow-up question:

## Original Research
{original_content}

---

## Follow-up Question
{question}

---

Please provide a focused analysis addressing the follow-up question. Use the same analytical framework from the original research. Include:

# Follow-up Analysis: {question}

## Reference
- **Original Research**: {original_path.name}
- **Original Theme**: {original_theme}

## Analysis
[Detailed analysis addressing the follow-up question with the same rigor as the original]

## Supply Chain Impact
[How this affects the supply chain map from the original research]

## Updated Sector Exposure
| Sector | Change | Rationale |
|--------|--------|-----------|
[Which sectors are more/less attractive based on this development]

## Scenario Implications
### If Bullish
[How this changes the bull case]

### If Bearish
[How this changes the bear case]

## Updated Investment Ideas
### New Longs
| Ticker | Thesis | Entry |
|--------|--------|-------|

### New Shorts/Avoids
| Ticker | Thesis | Risk |
|--------|--------|------|

### Position Changes
| Ticker | Action | Rationale |
|--------|--------|-----------|
[Changes to positions from original research]

## Key Takeaways
- [Takeaway 1]
- [Takeaway 2]
- [Takeaway 3]

## Additional Watchlist Additions
| Ticker | Company | Theme | Priority | Entry Trigger |
|--------|---------|-------|----------|---------------|

Use web search to gather current information relevant to the follow-up question."""

        # Call Claude with tools
        content, tool_results = self._call_claude_with_tools(
            system_prompt=EXPLORE_SYSTEM_PROMPT,
            user_message=user_prompt,
            tools=self._get_tools(),
            max_iterations=10
        )

        # Extract tickers and add market valuation section if Finnhub is available
        tickers = self._extract_tickers(content)
        if tickers:
            market_section = self._generate_market_valuation_section(tickers)
            if market_section:
                content += "\n" + market_section

        # Generate follow-up filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_stem = original_path.stem
        followup_theme = f"{original_stem}_followup_{timestamp}"

        # Add Anthropic knowledge as a source since we use Claude for analysis
        self.source_tracker.add_anthropic_knowledge_source(question)
        
        # Add sources section
        sources_section = self.source_tracker.generate_sources_section()
        if sources_section:
            content += sources_section

        # Generate the research document
        metadata = {
            "query": question,
            "depth": depth,
            "model": self.api_config["model"],
            "generated": datetime.now().isoformat(),
            "type": "followup",
            "parent_research": original_path.name,
            "parent_theme": original_theme,
            "tool_calls": len(tool_results)
        }

        output_path = self.markdown_generator.generate_research_doc(
            theme=followup_theme,
            content=content,
            metadata=metadata
        )

        # Extract and add entities to watchlist
        self._update_watchlist(followup_theme, content)

        return output_path

    def _update_watchlist(self, theme: str, content: str) -> int:
        """Extract entities from research and add to watchlist."""
        # Find tickers in table rows (more reliable)
        table_pattern = r'\|\s*([A-Z]{1,5})\s*\|'
        tickers_found = set(re.findall(table_pattern, content))
        
        # Filter out common non-ticker words
        exclude = {'High', 'Low', 'P', 'E', 'TTM', 'YTD', 'USD', 'Q', 'FY', 
                   'N', 'A', 'NA', 'TBD', 'YES', 'NO', 'ALL', 'NEW', 'TOP'}
        tickers_found = {t for t in tickers_found if t not in exclude and len(t) >= 2}

        # Create watchlist entities
        entities = []
        today = datetime.now().strftime("%Y-%m-%d")
        safe_theme = theme.lower().replace(" ", "_")[:50]

        for ticker in tickers_found:
            entity = WatchlistEntity(
                ticker=ticker,
                name=ticker,  # Name would be enriched in production
                themes=[safe_theme],
                added_date=today,
                source_research=f"{safe_theme}_{datetime.now().strftime('%Y%m%d')}.md"
            )
            entities.append(entity)

        return self.watchlist_manager.add_many(entities)

    def _extract_tickers(self, content: str) -> list[str]:
        """Extract ticker symbols from markdown content."""
        # Find tickers in table rows (more reliable)
        table_pattern = r'\|\s*([A-Z]{1,5})\s*\|'
        tickers_found = set(re.findall(table_pattern, content))
        
        # Filter out common markdown table words and short strings
        exclude = {'High', 'Low', 'P', 'E', 'TTM', 'YTD', 'USD', 'Q', 'FY',
                   'N', 'A', 'NA', 'TBD', 'YES', 'NO', 'ALL', 'NEW', 'TOP',
                   'BUY', 'SELL', 'HOLD', 'LONG', 'AVG', 'MAX', 'MIN'}
        return [t for t in tickers_found if t not in exclude and len(t) >= 2]

    def _generate_tldr(self, content: str) -> str:
        """Generate a concise TLDR for the research."""
        try:
            prompt = TLDR_GENERATION_PROMPT.format(content=content[:15000])
            
            response = self.client.messages.create(
                model=self.api_config["model"],
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            tldr = response.content[0].text.strip()
            
            return f"""## 📌 TLDR

{tldr}

---
"""
        except Exception as e:
            logger.warning(f"Failed to generate TLDR: {e}")
            return ""

    def _generate_contrarian_analysis(self, content: str) -> str:
        """Generate contrarian/devil's advocate analysis."""
        try:
            prompt = CONTRARIAN_ANALYSIS_PROMPT.format(content=content[:15000])
            
            response = self.client.messages.create(
                model=self.api_config["model"],
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis = response.content[0].text.strip()
            
            return f"""
---

## 😈 Devil's Advocate

{analysis}
"""
        except Exception as e:
            logger.warning(f"Failed to generate contrarian analysis: {e}")
            return ""

    def _extract_and_analyze_bottlenecks(self, content: str) -> str:
        """Extract bottleneck data from research and run analysis."""
        try:
            prompt = BOTTLENECK_EXTRACTION_PROMPT.format(content=content[:15000])
            
            response = self.client.messages.create(
                model=self.api_config["model"],
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            json_str = response.content[0].text.strip()
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            components = json.loads(json_str)
            
            if not components:
                return ""
            
            # Use the analyzer
            analyzer = ShortageAnalyzer()
            _, markdown = analyzer.analyze_supply_chain(components)
            
            return f"\n---\n\n{markdown}"
            
        except Exception as e:
            logger.warning(f"Failed to analyze bottlenecks: {e}")
            return ""

    def _extract_and_analyze_demand(self, content: str) -> str:
        """Extract demand tier data from research and run analysis."""
        try:
            prompt = DEMAND_EXTRACTION_PROMPT.format(content=content[:15000])
            
            response = self.client.messages.create(
                model=self.api_config["model"],
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            json_str = response.content[0].text.strip()
            # Extract JSON from response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            tiers = json.loads(json_str)
            
            if not tiers:
                return ""
            
            # Use the analyzer
            analyzer = DemandAnalyzer()
            _, markdown = analyzer.analyze_supply_chain(tiers)
            
            return f"\n---\n\n{markdown}"
            
        except Exception as e:
            logger.warning(f"Failed to analyze demand: {e}")
            return ""

    def _extract_and_check_valuations(self, content: str, tickers: list[str]) -> str:
        """Extract valuation data and run analysis for given tickers."""
        if not tickers:
            return ""
            
        try:
            # Limit to top 15 tickers
            tickers_str = ", ".join(tickers[:15])
            prompt = VALUATION_EXTRACTION_PROMPT.format(
                content=content[:12000],
                tickers=tickers_str
            )
            
            response = self.client.messages.create(
                model=self.api_config["model"],
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            json_str = response.content[0].text.strip()
            # Extract JSON from response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            stocks = json.loads(json_str)
            
            if not stocks:
                return ""
            
            # Use the checker
            checker = ValuationChecker()
            _, markdown = checker.analyze_portfolio(stocks)
            
            return f"\n---\n\n{markdown}"
            
        except Exception as e:
            logger.warning(f"Failed to check valuations: {e}")
            return ""

    def _generate_market_valuation_section(self, tickers: list[str]) -> str:
        """
        Generate enhanced market valuation section using Finnhub data.

        Args:
            tickers: List of ticker symbols

        Returns:
            Markdown formatted market valuation section with enriched company data
        """
        if not self.finnhub_client.is_available() or not tickers:
            return ""

        # Limit to top 20 tickers to avoid rate limiting
        tickers = tickers[:20]
        
        # Fetch market data for all tickers
        market_data = self.finnhub_client.get_market_data_for_tickers(tickers)

        if not market_data:
            return ""

        # Track Finnhub sources for successful data retrieval
        for ticker in market_data.keys():
            self.source_tracker.add_finnhub_source(ticker, 'market_data')

        # Build enhanced market data tables
        lines = [
            "\n---",
            "\n## Enhanced Market Data & Company Profiles",
            "*Data from Finnhub. Prices may be delayed.*\n"
        ]

        # Primary market data table
        lines.extend([
            "### Trading & Valuation Metrics",
            "| Ticker | Price | 52W Range | P/E | Market Cap | Tier | Position |",
            "|--------|-------|-----------|-----|------------|------|----------|"
        ])

        valuation_notes = []
        company_profiles = []
        
        for ticker, data in market_data.items():
            price = f"${data['current_price']:.2f}" if data.get('current_price') else "N/A"

            high = data.get('52_week_high')
            low = data.get('52_week_low')
            if high and low:
                week_52 = f"${low:.0f}-${high:.0f}"
            else:
                week_52 = "N/A"

            pe = f"{data['pe_ratio']:.1f}" if data.get('pe_ratio') else "-"

            mcap = data.get('market_cap')
            if mcap:
                if mcap >= 1000000:  # $1T+
                    mcap_str = f"${mcap/1000000:.2f}T"
                elif mcap >= 1000:  # $1B+
                    mcap_str = f"${mcap/1000:.1f}B"
                else:  # <$1B
                    mcap_str = f"${mcap:.0f}M"
            else:
                mcap_str = "-"

            # Market cap tier
            tier = data.get('market_cap_tier', '-').title()

            # Position in 52-week range
            current = data.get('current_price')
            if current and high and low and (high - low) > 0:
                range_pct = ((current - low) / (high - low)) * 100
                range_str = f"{range_pct:.0f}%"
                
                # Note extreme positions
                if range_pct > 90:
                    valuation_notes.append(f"- **{ticker}**: Near 52-week high ({range_pct:.0f}%) - momentum or overextended?")
                elif range_pct < 10:
                    valuation_notes.append(f"- **{ticker}**: Near 52-week low ({range_pct:.0f}%) - value or value trap?")
            else:
                range_str = "-"

            lines.append(f"| {ticker} | {price} | {week_52} | {pe} | {mcap_str} | {tier} | {range_str} |")

            # Collect company profile data
            if any(data.get(field) for field in ['sector', 'industry', 'country']):
                company_profiles.append({
                    'ticker': ticker,
                    'sector': data.get('sector', 'N/A'),
                    'industry': data.get('industry', 'N/A'), 
                    'country': data.get('country', 'N/A'),
                    'revenue_ttm': data.get('revenue_ttm'),
                    'revenue_growth': data.get('revenue_growth'),
                    'eps_ttm': data.get('eps_ttm')
                })

        # Add company profiles table
        if company_profiles:
            lines.extend([
                "\n### Company Profiles & Fundamentals",
                "| Ticker | Sector | Industry | HQ Country | Revenue (TTM) | Growth | EPS |",
                "|--------|--------|----------|------------|---------------|--------|-----|"
            ])

            for profile in company_profiles:
                sector = profile['sector'][:20] if profile['sector'] != 'N/A' else 'N/A'
                industry = profile['industry'][:20] if profile['industry'] != 'N/A' else 'N/A'
                country = profile['country'] if profile['country'] != 'N/A' else 'N/A'
                
                revenue = f"${profile['revenue_ttm']/1000:.1f}B" if profile['revenue_ttm'] and profile['revenue_ttm'] >= 1000 else f"${profile['revenue_ttm']:.0f}M" if profile['revenue_ttm'] else '-'
                growth = f"{profile['revenue_growth']:.1f}%" if profile['revenue_growth'] is not None else '-'
                eps = f"${profile['eps_ttm']:.2f}" if profile['eps_ttm'] is not None else '-'

                lines.append(f"| {profile['ticker']} | {sector} | {industry} | {country} | {revenue} | {growth} | {eps} |")

        # Add sector and geographic analysis
        if company_profiles:
            sectors = {}
            countries = {}
            tiers = {}
            
            for ticker, data in market_data.items():
                # Collect sector data
                if data.get('sector') and data['sector'] != 'N/A':
                    sectors[data['sector']] = sectors.get(data['sector'], 0) + 1
                # Collect country data  
                if data.get('country') and data['country'] != 'N/A':
                    countries[data['country']] = countries.get(data['country'], 0) + 1
                # Collect tier data
                if data.get('market_cap_tier'):
                    tier = data['market_cap_tier'].title()
                    tiers[tier] = tiers.get(tier, 0) + 1

            if sectors:
                lines.append("\n### Sector Exposure")
                for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"- **{sector}**: {count} companies")

            if countries:
                lines.append("\n### Geographic Exposure")
                for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"- **{country}**: {count} companies")

            if tiers:
                lines.append("\n### Market Cap Distribution")
                for tier, count in sorted(tiers.items(), key=lambda x: ['Mega', 'Large', 'Mid', 'Small', 'Micro'].index(x[0])):
                    lines.append(f"- **{tier}-cap**: {count} companies")

        # Add valuation commentary
        if valuation_notes:
            lines.append("\n### Valuation Alerts")
            lines.extend(valuation_notes)

        return "\n".join(lines) + "\n"


# Convenience functions for CLI usage
def explore(query: str, depth: int = 2) -> Path:
    """Quick explore function for CLI/notebook usage."""
    agent = ExploreAgent()
    return agent.run(query, depth=depth)


def followup(research_path: str, question: str) -> Path:
    """Quick follow-up function for CLI/notebook usage."""
    agent = ExploreAgent()
    return agent.run_followup(research_path, question)
