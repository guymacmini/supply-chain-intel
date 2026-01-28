"""Monitor Agent for continuous news monitoring and alerts."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models import NewsItem
from ..utils.config_loader import ConfigLoader
from ..utils.markdown_generator import MarkdownGenerator
from ..utils.watchlist_manager import WatchlistManager
from ..utils.tavily_client import TavilyClient
from .base_agent import BaseAgent


MONITOR_SYSTEM_PROMPT = """You are a financial news analyst monitoring market developments for investment relevance.

Your task is to:

1. **Monitor Watchlist Entities**: Search for recent news about each entity in the watchlist.

2. **Score Relevance**: For each news item, score its investment relevance (1-10):
   - 1-3: Low relevance (routine news, no material impact)
   - 4-6: Medium relevance (notable but not urgent)
   - 7-10: High relevance (material impact, action may be needed)

3. **Match Against Triggers**: Check if any news matches active thesis triggers.

4. **Assess Impact**: For high-signal items (score >= 7):
   - Extract key facts
   - Assess impact on related theses
   - Suggest investor action if warranted

5. **Generate Digest**: Compile findings into a daily/hourly digest.

Focus on:
- Earnings and guidance changes
- Management changes
- Regulatory developments
- Competitive dynamics
- Macro factors affecting the sector
- Supply chain disruptions
- Capacity announcements

Filter out noise - only include news that could materially impact investment decisions."""


class MonitorAgent(BaseAgent):
    """Agent for monitoring news and generating alerts."""

    def __init__(
        self,
        config_loader: Optional[ConfigLoader] = None,
        markdown_generator: Optional[MarkdownGenerator] = None,
        watchlist_manager: Optional[WatchlistManager] = None,
        tavily_client: Optional[TavilyClient] = None
    ):
        super().__init__(config_loader)
        self.markdown_generator = markdown_generator or MarkdownGenerator()
        self.watchlist_manager = watchlist_manager or WatchlistManager()
        self.tavily_client = tavily_client or TavilyClient()

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        """Handle tool calls, using Tavily for web search if available."""
        if tool_name == "web_search":
            query = tool_input.get('query', '')

            # If Tavily is available, use it for enhanced financial news search
            if self.tavily_client.is_available():
                try:
                    # Monitor agent always searches for financial news
                    results = self.tavily_client.search_financial_news(query, max_results=10)

                    if results:
                        formatted = self.tavily_client.format_results_as_text(results)
                        return f"[Tavily search results for: {query}]\n{formatted}"
                except Exception as e:
                    # Fall back to Claude's built-in search if Tavily fails
                    pass

            # Fall back to Claude's built-in web search
            return f"[Web search executed for: {query}]"
        return super()._handle_tool_call(tool_name, tool_input)

    def run(self, sources_file: Optional[str] = None) -> Path:
        """
        Run monitoring scan and generate digest.

        Args:
            sources_file: Optional custom sources configuration file

        Returns:
            Path to the generated digest
        """
        # Load watchlist
        entities = self.watchlist_manager.get_all()
        if not entities:
            return self._generate_empty_digest()

        # Load active theses triggers
        theses = self.markdown_generator.list_theses(status="active")
        triggers = self._load_triggers(theses)

        # Load sources
        if sources_file:
            sources = self.config_loader.load_json(sources_file)
        else:
            sources = self.config_loader.get_sources()

        # Build the monitoring prompt
        entity_list = "\n".join([f"- {e.ticker}: {e.name} (themes: {', '.join(e.themes)})" for e in entities])
        trigger_list = "\n".join([f"- {t}" for t in triggers]) if triggers else "No active triggers"
        source_list = ", ".join([s for tier in sources.values() for s in tier])

        user_prompt = f"""Please scan for recent news affecting these monitored entities and theses.

## Watchlist Entities
{entity_list}

## Active Thesis Triggers
{trigger_list}

## Preferred Sources
{source_list}

Please provide your monitoring digest in the following markdown format:

# Investment Monitor Digest
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Thesis Alerts (Triggers Fired)
[List any news that matches thesis triggers, with impact assessment]

| Trigger | News | Source | Impact | Action |
|---------|------|--------|--------|--------|
[Table of triggered alerts, or "No triggers fired" if none]

## High-Signal News (Score >= 7)
[Important news items requiring attention]

### [Ticker]: [Headline]
**Relevance Score**: [1-10]
**Source**: [Source name]
**Key Facts**:
- [Fact 1]
- [Fact 2]

**Investment Impact**: [Assessment]
**Suggested Action**: [If any]

## Watchlist Summary
| Ticker | News Count | Highest Score | Status |
|--------|------------|---------------|--------|
[Summary table for all watched entities]

## No Significant News
[List entities with no material news]

Use web search to find recent news for each entity."""

        # Call Claude with the monitoring prompt
        response = self._call_claude(
            system_prompt=MONITOR_SYSTEM_PROMPT,
            user_message=user_prompt,
            max_tokens=self.api_config["max_tokens"]
        )

        # Extract content
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        # Generate digest
        metadata = {
            "entities_monitored": len(entities),
            "triggers_active": len(triggers),
            "model": self.api_config["model"]
        }

        return self.markdown_generator.generate_digest(content, metadata)

    def _load_triggers(self, thesis_paths: list[Path]) -> list[str]:
        """Load triggers from active theses."""
        import frontmatter

        triggers = []
        for path in thesis_paths:
            try:
                post = frontmatter.load(path)
                thesis_triggers = post.metadata.get("triggers", [])
                triggers.extend(thesis_triggers)
            except Exception:
                continue
        return list(set(triggers))

    def _generate_empty_digest(self) -> Path:
        """Generate a digest when watchlist is empty."""
        content = """# Investment Monitor Digest

**Generated**: {timestamp}

## Status

No entities in watchlist. Use `supply-chain-intel explore` to add entities to monitor.

### Getting Started

1. Explore a theme: `supply-chain-intel explore "AI infrastructure"`
2. Add a thesis: `supply-chain-intel thesis "I think..."`
3. Manually add: `supply-chain-intel watchlist add NVDA --theme AI`

Then run `supply-chain-intel monitor` again.
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"))

        return self.markdown_generator.generate_digest(content, {"status": "empty_watchlist"})

    def scan_entity(self, ticker: str) -> dict:
        """Scan a single entity for news. Returns structured data."""
        user_prompt = f"""Search for recent news about {ticker} and provide:

1. Recent headlines (last 7 days)
2. Investment relevance score (1-10) for each
3. Key facts extracted
4. Overall assessment

Format as JSON:
{{
    "ticker": "{ticker}",
    "news_items": [
        {{
            "title": "...",
            "source": "...",
            "date": "...",
            "relevance_score": 7,
            "key_facts": ["...", "..."]
        }}
    ],
    "overall_assessment": "...",
    "action_required": true/false
}}"""

        response = self._call_claude(
            system_prompt=MONITOR_SYSTEM_PROMPT,
            user_message=user_prompt,
            max_tokens=4000
        )

        # Extract and parse JSON
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        # Try to extract JSON from response
        import json
        import re

        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {
            "ticker": ticker,
            "news_items": [],
            "overall_assessment": content,
            "action_required": False
        }
