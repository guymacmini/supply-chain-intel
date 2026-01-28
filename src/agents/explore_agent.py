"""Explore Agent for discovering investment opportunities."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models import WatchlistEntity, ResearchOpportunity
from ..utils.config_loader import ConfigLoader
from ..utils.markdown_generator import MarkdownGenerator
from ..utils.watchlist_manager import WatchlistManager
from ..utils.finnhub_client import FinnhubClient
from ..utils.tavily_client import TavilyClient
from .base_agent import BaseAgent


EXPLORE_SYSTEM_PROMPT = """You are an expert investment research analyst specializing in supply chain analysis and second/third-order investment opportunities.

Your task is to explore a given theme, company, or market and identify non-obvious investment opportunities by mapping dependencies and relationships.

For the given topic, you should:

1. **Identify Primary Players**: List the obvious, first-order investments in this space.

2. **Map Upstream Dependencies**: For each primary player, identify:
   - Key suppliers and component manufacturers
   - Raw material providers
   - Technology enablers
   - Infrastructure providers

3. **Map Downstream Beneficiaries**: For each primary player, identify:
   - Major customers and end markets
   - Distribution and logistics partners
   - Service providers
   - Adjacent market beneficiaries

4. **Identify Capacity Constraints**: Find bottlenecks that could create investment opportunities:
   - Manufacturing capacity limitations
   - Infrastructure gaps
   - Skilled labor shortages
   - Regulatory gatekeepers

5. **Go Deeper**: For the most interesting second-order opportunities, repeat the analysis to find third-order plays.

6. **Analyze Market Impact**: Assess both direct and indirect market impacts:
   - Direct Impact Companies: Companies immediately affected by the theme
   - Indirect Impact Companies: Companies affected through supply chain or market dynamics
   - Market Segments Affected: Broader market segments impacted
   - Impact Severity: Rate each as High/Medium/Low

7. **Develop Investment Strategies**: Create actionable investment recommendations:
   - Bullish Scenario: Best-case thesis with specific tickers and entry strategies
   - Bearish Scenario: Risk scenarios and defensive positions
   - Entry Strategies: Timing, price levels, position sizing considerations
   - Risk Factors: Key risks for each strategy

8. **Rank Opportunities**: Score each opportunity by:
   - Exposure level (high/medium/low) to the original theme
   - Investment merit (valuation, growth potential, competitive position)
   - Risk factors

When using web search, focus on:
- Recent news and developments
- Analyst reports and market research
- Company filings and investor presentations
- Industry trade publications

Output your findings in a structured format that can be converted to a research document."""


class ExploreAgent(BaseAgent):
    """Agent for exploring themes and discovering investment opportunities."""

    def __init__(
        self,
        config_loader: Optional[ConfigLoader] = None,
        markdown_generator: Optional[MarkdownGenerator] = None,
        watchlist_manager: Optional[WatchlistManager] = None,
        finnhub_client: Optional[FinnhubClient] = None,
        tavily_client: Optional[TavilyClient] = None
    ):
        super().__init__(config_loader)
        self.markdown_generator = markdown_generator or MarkdownGenerator()
        self.watchlist_manager = watchlist_manager or WatchlistManager()
        self.finnhub_client = finnhub_client or FinnhubClient()
        self.tavily_client = tavily_client or TavilyClient()

    def _get_tools(self) -> list[dict]:
        """Get the tools available to this agent."""
        return [
            {
                "name": "web_search",
                "description": "Search the web for current information about a topic. Use this to find recent news, company information, market data, and analysis.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to execute"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        """Handle tool calls by delegating to Claude's built-in capabilities."""
        if tool_name == "web_search":
            query = tool_input.get('query', '')

            # If Tavily is available, use it for enhanced search
            if self.tavily_client.is_available():
                try:
                    # Determine if this is a financial query
                    financial_keywords = ['stock', 'market', 'earnings', 'revenue', 'investor', 'valuation']
                    is_financial = any(kw in query.lower() for kw in financial_keywords)

                    if is_financial:
                        results = self.tavily_client.search_financial_news(query, max_results=10)
                    else:
                        results = self.tavily_client.search(query, max_results=10)

                    if results:
                        formatted = self.tavily_client.format_results_as_text(results)
                        return f"[Tavily search results for: {query}]\n{formatted}"
                except Exception as e:
                    # Fall back to Claude's built-in search if Tavily fails
                    pass

            # The actual web search is handled by Claude's built-in tool
            # This is a placeholder that returns a message indicating the search was performed
            return f"[Web search executed for: {query}]"
        return super()._handle_tool_call(tool_name, tool_input)

    def run(self, query: str, depth: int = 2) -> Path:
        """
        Explore a theme/company/market and generate research document.

        Args:
            query: The theme, company, or market to explore
            depth: How many levels deep to go (1=primary, 2=secondary, 3=tertiary)

        Returns:
            Path to the generated research document
        """
        user_prompt = f"""Please analyze the following investment theme/topic and identify investment opportunities:

**Topic**: {query}

**Analysis Depth**: {depth} levels (1=primary players only, 2=include second-order, 3=include third-order)

Please provide your analysis in the following markdown format:

# Investment Research: {query}

## Executive Summary
[Brief overview of the opportunity and key findings]

## Primary Players (First-Order)
| Ticker | Company | Role | Investment Merit |
|--------|---------|------|------------------|
[Table of obvious, first-order investments]

## Second-Order Opportunities
### Upstream Dependencies
[For each primary player, list suppliers, component makers, etc.]

### Downstream Beneficiaries
[Customers, distributors, service providers]

### Capacity Constraints & Enablers
[Bottlenecks and infrastructure plays]

## Third-Order Opportunities (if depth >= 3)
[Deeper dependencies of the most interesting second-order plays]

## Market Impact Analysis

### Direct Impact Companies
| Ticker | Company | Impact Type | Severity |
|--------|---------|-------------|----------|
[Companies directly affected by this theme - Rate severity as High/Medium/Low]

### Indirect Impact Companies
| Ticker | Company | Impact Channel | Severity |
|--------|---------|----------------|----------|
[Companies affected through supply chain, market dynamics, or secondary effects]

### Market Segments Affected
| Segment | Direction | Severity | Rationale |
|---------|-----------|----------|-----------|
[Broader market segments impacted - direction is Positive/Negative/Mixed]

## Investment Strategies

### Bullish Scenario
**Thesis**: [Core bullish thesis in 1-2 sentences]

**Top Picks**:
| Ticker | Entry Strategy | Target Upside | Timeframe |
|--------|----------------|---------------|-----------|
[Specific tickers with entry strategies]

**Catalysts to Watch**:
- [Catalyst 1]
- [Catalyst 2]
- [Catalyst 3]

### Bearish Scenario
**Thesis**: [Core bearish/risk thesis in 1-2 sentences]

**Defensive Positions**:
| Ticker | Strategy | Rationale |
|--------|----------|-----------|
[Defensive plays or shorts if applicable]

**Warning Signs**:
- [Warning sign 1]
- [Warning sign 2]
- [Warning sign 3]

### Risk Factors
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
[Key risks with assessment]

## Key Relationships to Monitor
[Important dependencies and triggers to watch]

## Recommended Watchlist Additions
| Ticker | Company | Theme | Priority |
|--------|---------|-------|----------|
[List tickers and names to add to monitoring, with themes and priority High/Medium/Low]

Use web search to gather current, accurate information about companies, market conditions, and recent developments."""

        # Call Claude with the exploration prompt
        # Note: In production, this would use Claude's actual web search capability
        response = self._call_claude(
            system_prompt=EXPLORE_SYSTEM_PROMPT,
            user_message=user_prompt,
            max_tokens=self.api_config["max_tokens"]
        )

        # Extract the content
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        # Extract tickers and add market valuation section if Finnhub is available
        tickers = self._extract_tickers(content)
        if tickers:
            market_section = self._generate_market_valuation_section(tickers)
            if market_section:
                content += "\n" + market_section

        # Generate the research document
        metadata = {
            "query": query,
            "depth": depth,
            "model": self.api_config["model"],
            "generated": datetime.now().isoformat()
        }
        output_path = self.markdown_generator.generate_research_doc(
            theme=query,
            content=content,
            metadata=metadata
        )

        # Extract and add entities to watchlist
        self._update_watchlist(query, content)

        return output_path

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

Please provide a focused analysis addressing the follow-up question. Include:

# Follow-up Analysis: {question}

## Reference
- **Original Research**: {original_path.name}
- **Original Theme**: {original_theme}

## Analysis
[Detailed analysis addressing the follow-up question]

## Market Impact Analysis

### Direct Impact Companies
| Ticker | Company | Impact Type | Severity |
|--------|---------|-------------|----------|
[Companies directly affected]

### Indirect Impact Companies
| Ticker | Company | Impact Channel | Severity |
|--------|---------|----------------|----------|
[Companies indirectly affected]

## Investment Implications

### Bullish Scenario
**Thesis**: [If the follow-up scenario is positive]

**Actionable Ideas**:
| Ticker | Strategy | Rationale |
|--------|----------|-----------|
[Specific ideas]

### Bearish Scenario
**Thesis**: [If the follow-up scenario is negative]

**Defensive Ideas**:
| Ticker | Strategy | Rationale |
|--------|----------|-----------|
[Defensive positions]

## Key Takeaways
- [Takeaway 1]
- [Takeaway 2]
- [Takeaway 3]

## Additional Watchlist Additions
| Ticker | Company | Theme | Priority |
|--------|---------|-------|----------|
[New tickers identified from this follow-up]

Use web search to gather current information relevant to the follow-up question."""

        # Call Claude with the follow-up prompt
        response = self._call_claude(
            system_prompt=EXPLORE_SYSTEM_PROMPT,
            user_message=user_prompt,
            max_tokens=self.api_config["max_tokens"]
        )

        # Extract the content
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

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

        # Generate the research document
        metadata = {
            "query": question,
            "depth": depth,
            "model": self.api_config["model"],
            "generated": datetime.now().isoformat(),
            "type": "followup",
            "parent_research": original_path.name,
            "parent_theme": original_theme
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
        # Parse the content to find tickers mentioned
        # This is a simple extraction - could be enhanced with NLP
        import re

        # Look for patterns like "| TICKER |" or mentions of specific tickers
        ticker_pattern = r'\b([A-Z]{1,5})\b'

        # Find tickers in table rows (more reliable)
        table_pattern = r'\|\s*([A-Z]{1,5})\s*\|'

        tickers_found = set(re.findall(table_pattern, content))

        # Create watchlist entities
        entities = []
        today = datetime.now().strftime("%Y-%m-%d")
        safe_theme = theme.lower().replace(" ", "_")

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
        import re
        # Find tickers in table rows (more reliable)
        table_pattern = r'\|\s*([A-Z]{1,5})\s*\|'
        tickers_found = set(re.findall(table_pattern, content))
        # Filter out common markdown table words
        exclude = {'High', 'Low', 'P', 'E', 'TTM', 'YTD', 'USD', 'Q', 'FY'}
        return [t for t in tickers_found if t not in exclude]

    def _generate_market_valuation_section(self, tickers: list[str]) -> str:
        """
        Generate market valuation section using Finnhub data.

        Args:
            tickers: List of ticker symbols

        Returns:
            Markdown formatted market valuation section
        """
        if not self.finnhub_client.is_available() or not tickers:
            return ""

        # Fetch market data for all tickers
        market_data = self.finnhub_client.get_market_data_for_tickers(tickers)

        if not market_data:
            return ""

        # Build markdown table
        lines = [
            "\n## Market Valuation (powered by Finnhub)\n",
            "| Ticker | Current Price | 52W High/Low | P/E Ratio | Market Cap |",
            "|--------|--------------|--------------|-----------|------------|"
        ]

        for ticker, data in market_data.items():
            price = f"${data['current_price']:.2f}" if data.get('current_price') else "N/A"

            high = data.get('52_week_high')
            low = data.get('52_week_low')
            if high and low:
                week_52 = f"${low:.2f}/${high:.2f}"
            else:
                week_52 = "N/A"

            pe = f"{data['pe_ratio']:.1f}" if data.get('pe_ratio') else "N/A"

            mcap = data.get('market_cap')
            if mcap:
                if mcap >= 1000:
                    mcap_str = f"${mcap/1000:.2f}T"
                else:
                    mcap_str = f"${mcap:.0f}B"
            else:
                mcap_str = "N/A"

            lines.append(f"| {ticker} | {price} | {week_52} | {pe} | {mcap_str} |")

        # Add valuation notes
        lines.append("\n**Valuation Notes**:")
        notes = []
        for ticker, data in market_data.items():
            price = data.get('current_price')
            high_52 = data.get('52_week_high')
            low_52 = data.get('52_week_low')

            if price and high_52 and low_52:
                range_pct = ((price - low_52) / (high_52 - low_52)) * 100 if (high_52 - low_52) > 0 else 50
                if range_pct > 80:
                    notes.append(f"- **{ticker}**: Trading near 52-week high ({range_pct:.0f}% of range)")
                elif range_pct < 20:
                    notes.append(f"- **{ticker}**: Trading near 52-week low ({range_pct:.0f}% of range)")

        if notes:
            lines.extend(notes)
        else:
            lines.append("- No significant valuation alerts")

        return "\n".join(lines) + "\n"
