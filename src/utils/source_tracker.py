"""Source tracking utility for research citations."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class ResearchSource:
    """A source used in research generation."""
    source_type: str  # 'tavily', 'finnhub', 'cache', 'anthropic'
    url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None  
    accessed_at: Optional[str] = None
    query: Optional[str] = None  # For search sources
    ticker: Optional[str] = None  # For market data sources
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'source_type': self.source_type,
            'url': self.url,
            'title': self.title,
            'description': self.description,
            'accessed_at': self.accessed_at,
            'query': self.query,
            'ticker': self.ticker
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ResearchSource':
        """Create from dictionary."""
        return cls(**data)


class SourceTracker:
    """Tracks sources used during research generation."""
    
    def __init__(self):
        """Initialize the source tracker."""
        self.sources: List[ResearchSource] = []
        self._url_cache: Set[str] = set()  # Prevent duplicate URLs
    
    def add_tavily_source(self, query: str, result: Dict) -> None:
        """Add a Tavily search result source.
        
        Args:
            query: The search query used
            result: Single result from Tavily search with 'url', 'title', 'content'
        """
        url = result.get('url')
        if not url or url in self._url_cache:
            return
            
        source = ResearchSource(
            source_type='tavily',
            url=url,
            title=result.get('title', '').strip(),
            description=result.get('content', '')[:200] + '...' if result.get('content') else None,
            accessed_at=datetime.now().isoformat(),
            query=query
        )
        
        self.sources.append(source)
        self._url_cache.add(url)
    
    def add_finnhub_source(self, ticker: str, data_type: str = 'market_data') -> None:
        """Add a Finnhub data source.
        
        Args:
            ticker: Stock ticker symbol
            data_type: Type of data retrieved (e.g., 'market_data', 'company_profile')
        """
        # Finnhub doesn't provide direct URLs but we can reference their service
        description = f"{data_type.replace('_', ' ').title()} for {ticker}"
        
        source = ResearchSource(
            source_type='finnhub',
            url=f"https://finnhub.io/api/v1/quote?symbol={ticker}",
            title=f"Finnhub - {ticker} Data",
            description=description,
            accessed_at=datetime.now().isoformat(),
            ticker=ticker
        )
        
        self.sources.append(source)
    
    def add_cache_source(self, query: str) -> None:
        """Add a cached search result source.
        
        Args:
            query: The original search query
        """
        source = ResearchSource(
            source_type='cache',
            title=f"Cached Search Results",
            description=f"Previously cached results for: {query}",
            accessed_at=datetime.now().isoformat(),
            query=query
        )
        
        self.sources.append(source)
    
    def add_anthropic_knowledge_source(self, topic: str) -> None:
        """Add Anthropic's knowledge base as a source.
        
        Args:
            topic: The topic/theme being researched
        """
        source = ResearchSource(
            source_type='anthropic',
            title="Anthropic Claude Knowledge Base",
            description=f"AI analysis and knowledge synthesis for: {topic}",
            accessed_at=datetime.now().isoformat(),
            query=topic
        )
        
        self.sources.append(source)
    
    def get_sources_by_type(self, source_type: str) -> List[ResearchSource]:
        """Get all sources of a specific type.
        
        Args:
            source_type: Type of source to filter by
            
        Returns:
            List of sources matching the type
        """
        return [s for s in self.sources if s.source_type == source_type]
    
    def get_tavily_urls(self) -> List[str]:
        """Get all Tavily URLs used in research."""
        return [s.url for s in self.sources if s.source_type == 'tavily' and s.url]
    
    def get_finnhub_tickers(self) -> List[str]:
        """Get all tickers that had Finnhub data retrieved."""
        return list(set(s.ticker for s in self.sources if s.source_type == 'finnhub' and s.ticker))
    
    def generate_sources_section(self) -> str:
        """Generate a markdown sources section for research documents.
        
        Returns:
            Markdown formatted sources section
        """
        if not self.sources:
            return ""
        
        lines = [
            "\n---",
            "\n## Sources & Data Attribution",
            "*This research incorporates data and insights from multiple sources:*\n"
        ]
        
        # Group sources by type
        tavily_sources = self.get_sources_by_type('tavily')
        finnhub_sources = self.get_sources_by_type('finnhub')
        cache_sources = self.get_sources_by_type('cache')
        anthropic_sources = self.get_sources_by_type('anthropic')
        
        # Tavily web research sources
        if tavily_sources:
            lines.append("### Web Research Sources")
            lines.append("*Powered by Tavily enhanced web search*\n")
            
            for i, source in enumerate(tavily_sources, 1):
                if source.url and source.title:
                    lines.append(f"{i}. **{source.title}**")
                    lines.append(f"   - URL: [{source.url}]({source.url})")
                    if source.query:
                        lines.append(f"   - Search Query: *{source.query}*")
                    if source.description:
                        lines.append(f"   - Preview: {source.description}")
                    lines.append("")
        
        # Finnhub market data sources  
        if finnhub_sources:
            lines.append("### Market Data Sources")
            lines.append("*Financial data provided by Finnhub*\n")
            
            tickers = self.get_finnhub_tickers()
            if tickers:
                lines.append(f"- **Market Data & Company Profiles**: {', '.join(sorted(tickers))}")
                lines.append(f"- **Data Provider**: [Finnhub](https://finnhub.io/)")
                lines.append(f"- **Coverage**: Stock prices, market cap, P/E ratios, company fundamentals")
                lines.append("")
        
        # AI Knowledge synthesis
        if anthropic_sources:
            lines.append("### AI Analysis & Synthesis")
            lines.append("- **Primary Analysis**: Anthropic Claude AI model")
            lines.append("- **Capabilities**: Industry knowledge, supply chain mapping, investment analysis")
            lines.append("- **Approach**: Combines multiple data sources with domain expertise for comprehensive research")
            lines.append("")
        
        # Cache sources (less prominent)
        if cache_sources:
            lines.append("### Additional Sources")
            lines.append("- Some data retrieved from previously cached research results")
            lines.append("")
        
        # Disclaimer
        lines.extend([
            "---",
            "*Research generated on " + datetime.now().strftime('%Y-%m-%d') + ". Market data may be delayed. This is not financial advice.*"
        ])
        
        return "\n".join(lines)
    
    def save_sources_to_file(self, output_path: Path) -> None:
        """Save sources to a JSON file for debugging/analysis.
        
        Args:
            output_path: Path to save sources JSON file
        """
        sources_data = {
            'generated_at': datetime.now().isoformat(),
            'total_sources': len(self.sources),
            'sources_by_type': {
                'tavily': len(self.get_sources_by_type('tavily')),
                'finnhub': len(self.get_sources_by_type('finnhub')),
                'cache': len(self.get_sources_by_type('cache')),
                'anthropic': len(self.get_sources_by_type('anthropic'))
            },
            'sources': [s.to_dict() for s in self.sources]
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sources_data, f, indent=2, ensure_ascii=False)
    
    def clear(self) -> None:
        """Clear all tracked sources."""
        self.sources.clear()
        self._url_cache.clear()
    
    def __len__(self) -> int:
        """Return the number of sources tracked."""
        return len(self.sources)
    
    def __str__(self) -> str:
        """Return a summary of tracked sources."""
        if not self.sources:
            return "SourceTracker: No sources tracked"
        
        types = {}
        for source in self.sources:
            types[source.source_type] = types.get(source.source_type, 0) + 1
        
        type_summary = ', '.join(f"{k}: {v}" for k, v in types.items())
        return f"SourceTracker: {len(self.sources)} sources ({type_summary})"