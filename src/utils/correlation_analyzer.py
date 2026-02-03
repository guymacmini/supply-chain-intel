"""Multi-theme correlation analyzer for identifying cross-theme opportunities and conflicts."""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import math


@dataclass
class ThemeCompany:
    """A company identified in a research theme."""
    ticker: str
    company_name: str
    theme: str
    exposure_level: str  # high, medium, low
    sentiment: str  # positive, negative, neutral
    role: str  # description of company's role in the theme
    rationale: Optional[str] = None
    research_file: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'ticker': self.ticker,
            'company_name': self.company_name,
            'theme': self.theme,
            'exposure_level': self.exposure_level,
            'sentiment': self.sentiment,
            'role': self.role,
            'rationale': self.rationale,
            'research_file': self.research_file
        }


@dataclass 
class ThemeOverlap:
    """Overlap analysis between two themes."""
    theme1: str
    theme2: str
    common_tickers: List[str]
    overlap_score: float  # 0.0 to 1.0
    correlation_type: str  # "complementary", "conflicting", "independent"
    insights: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'theme1': self.theme1,
            'theme2': self.theme2,
            'common_tickers': self.common_tickers,
            'overlap_score': self.overlap_score,
            'correlation_type': self.correlation_type,
            'insights': self.insights
        }


@dataclass
class CrossThemeOpportunity:
    """A cross-theme investment opportunity."""
    ticker: str
    company_name: str
    themes: List[str]
    opportunity_type: str  # "multi_theme_winner", "theme_conflict", "diversified_play"
    confidence_score: float  # 0.0 to 1.0
    description: str
    supporting_themes: List[str] = field(default_factory=list)
    conflicting_themes: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'ticker': self.ticker,
            'company_name': self.company_name,
            'themes': self.themes,
            'opportunity_type': self.opportunity_type,
            'confidence_score': self.confidence_score,
            'description': self.description,
            'supporting_themes': self.supporting_themes,
            'conflicting_themes': self.conflicting_themes,
            'risk_factors': self.risk_factors
        }


class MultiThemeCorrelationAnalyzer:
    """Analyze correlations and conflicts across multiple investment themes."""
    
    def __init__(self, data_dir: Path):
        """Initialize the correlation analyzer.
        
        Args:
            data_dir: Directory containing research files
        """
        self.data_dir = data_dir
        self.research_dir = data_dir / 'research'
        self.correlation_dir = data_dir / 'correlations'
        self.correlation_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for theme data
        self._theme_companies: Dict[str, List[ThemeCompany]] = {}
        self._research_metadata: Dict[str, Dict] = {}
    
    def extract_companies_from_research(self, research_content: str, research_filename: str) -> List[ThemeCompany]:
        """Extract company mentions and sentiment from research content.
        
        Args:
            research_content: Full research document content
            research_filename: Name of research file
            
        Returns:
            List of ThemeCompany objects
        """
        companies = []
        
        # Extract theme from filename or content
        theme = self._extract_theme_from_content(research_content, research_filename)
        
        # Look for markdown tables with ticker information
        table_pattern = r'\|[^|]*([A-Z]{1,5})[^|]*\|([^|]*)\|([^|]*)\|([^|]*)\|[^|]*\|'
        table_matches = re.findall(table_pattern, research_content)
        
        for match in table_matches:
            ticker, company_col, role_col, extra_col = match
            ticker = ticker.strip()
            
            if len(ticker) < 2 or ticker in ['PE', 'YOY', 'USD', 'CEO']:
                continue
            
            # Determine sentiment from surrounding context
            sentiment = self._analyze_sentiment_context(research_content, ticker)
            
            # Extract exposure level if available
            exposure_level = self._extract_exposure_level(role_col + ' ' + extra_col)
            
            # Get company name
            company_name = self._extract_company_name_from_context(research_content, ticker)
            
            company = ThemeCompany(
                ticker=ticker,
                company_name=company_name,
                theme=theme,
                exposure_level=exposure_level,
                sentiment=sentiment,
                role=role_col.strip()[:100],  # Limit length
                rationale=extra_col.strip()[:200] if extra_col.strip() else None,
                research_file=research_filename
            )
            companies.append(company)
        
        # Also look for ticker mentions in text with positive/negative context
        text_tickers = self._extract_tickers_from_narrative(research_content, theme, research_filename)
        companies.extend(text_tickers)
        
        # Deduplicate by ticker
        seen_tickers = set()
        unique_companies = []
        for company in companies:
            if company.ticker not in seen_tickers:
                seen_tickers.add(company.ticker)
                unique_companies.append(company)
        
        return unique_companies
    
    def _extract_theme_from_content(self, content: str, filename: str) -> str:
        """Extract theme name from content or filename."""
        # Try to extract from title
        title_match = re.search(r'# Investment Research:\s*([^\n]+)', content)
        if title_match:
            return title_match.group(1).strip()
        
        # Try from YAML frontmatter
        theme_match = re.search(r'theme:\s*([^\n]+)', content)
        if theme_match:
            return theme_match.group(1).strip()
        
        # Fall back to filename
        base_name = Path(filename).stem
        return base_name.split('_')[0].replace('_', ' ').title()
    
    def _analyze_sentiment_context(self, content: str, ticker: str) -> str:
        """Analyze sentiment around ticker mentions."""
        # Look for ticker mentions and surrounding context
        pattern = rf'\b{ticker}\b.{{0,200}}'
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        positive_words = ['buy', 'strong', 'outperform', 'undervalued', 'opportunity', 
                         'growth', 'bullish', 'upside', 'compelling', 'attractive',
                         'winner', 'leader', 'dominant', 'benefit', 'gain']
        negative_words = ['sell', 'weak', 'underperform', 'overvalued', 'risk',
                         'decline', 'bearish', 'downside', 'concern', 'threat',
                         'lose', 'vulnerable', 'challenged', 'disrupted', 'avoid']
        
        positive_score = 0
        negative_score = 0
        
        for match in matches:
            match_lower = match.lower()
            for word in positive_words:
                positive_score += match_lower.count(word)
            for word in negative_words:
                negative_score += match_lower.count(word)
        
        if positive_score > negative_score:
            return "positive"
        elif negative_score > positive_score:
            return "negative"
        else:
            return "neutral"
    
    def _extract_exposure_level(self, text: str) -> str:
        """Extract exposure level from text."""
        text_lower = text.lower()
        if any(word in text_lower for word in ['high', '9/10', '10/10', '8/10']):
            return "high"
        elif any(word in text_lower for word in ['medium', '5/10', '6/10', '7/10']):
            return "medium"
        elif any(word in text_lower for word in ['low', '1/10', '2/10', '3/10', '4/10']):
            return "low"
        else:
            return "medium"  # default
    
    def _extract_company_name_from_context(self, content: str, ticker: str) -> str:
        """Extract company name from context around ticker."""
        # Look for patterns like "Apple (AAPL)" or "AAPL (Apple Inc)"
        patterns = [
            rf'([^|(),\n]{{5,50}})\s*\(\s*{ticker}\s*\)',
            rf'{ticker}\s*\(([^)]+)\)',
            rf'\|\s*{ticker}\s*\|\s*([^|]+?)\s*\|'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up common artifacts
                name = re.sub(r'^[\*\s]+|[\*\s]+$', '', name)
                if len(name) > 3 and not name.isupper():
                    return name
        
        return f"Unknown ({ticker})"
    
    def _extract_tickers_from_narrative(self, content: str, theme: str, filename: str) -> List[ThemeCompany]:
        """Extract tickers mentioned in narrative text with sentiment."""
        companies = []
        
        # Look for ticker patterns in investment recommendations sections
        sections = ['Investment Opportunities', 'Top Picks', 'Key Plays', 'Recommendations']
        
        for section in sections:
            section_match = re.search(f'#{2,3}\\s*{section}.*?(?=#{2,3}|$)', content, re.DOTALL | re.IGNORECASE)
            if section_match:
                section_content = section_match.group(0)
                
                # Find ticker mentions with context
                ticker_pattern = r'\b([A-Z]{2,5})\b'
                tickers = re.findall(ticker_pattern, section_content)
                
                for ticker in set(tickers):
                    if len(ticker) >= 2 and ticker not in ['THE', 'AND', 'FOR', 'API', 'CEO', 'IPO', 'ETF']:
                        sentiment = self._analyze_sentiment_context(section_content, ticker)
                        company_name = self._extract_company_name_from_context(content, ticker)
                        
                        # Extract surrounding context for rationale
                        context_match = re.search(f'{ticker}[^.]*\\.', section_content)
                        rationale = context_match.group(0) if context_match else None
                        
                        company = ThemeCompany(
                            ticker=ticker,
                            company_name=company_name,
                            theme=theme,
                            exposure_level="medium",  # Default for narrative mentions
                            sentiment=sentiment,
                            role="Mentioned in investment recommendations",
                            rationale=rationale,
                            research_file=filename
                        )
                        companies.append(company)
        
        return companies
    
    def analyze_theme_correlations(self, themes: List[str] = None) -> List[ThemeOverlap]:
        """Analyze correlations between themes.
        
        Args:
            themes: List of theme names to analyze, or None for all available themes
            
        Returns:
            List of ThemeOverlap objects
        """
        # Load theme data
        if themes is None:
            themes = self._get_available_themes()
        
        theme_data = {}
        for theme in themes:
            theme_data[theme] = self._get_or_load_theme_companies(theme)
        
        overlaps = []
        
        # Compare each pair of themes
        for i, theme1 in enumerate(themes):
            for theme2 in themes[i+1:]:
                companies1 = {c.ticker: c for c in theme_data[theme1]}
                companies2 = {c.ticker: c for c in theme_data[theme2]}
                
                common_tickers = set(companies1.keys()) & set(companies2.keys())
                
                if common_tickers:
                    # Calculate overlap score
                    total_unique = len(set(companies1.keys()) | set(companies2.keys()))
                    overlap_score = len(common_tickers) / total_unique if total_unique > 0 else 0.0
                    
                    # Determine correlation type
                    correlation_type = self._determine_correlation_type(
                        common_tickers, companies1, companies2
                    )
                    
                    # Generate insights
                    insights = self._generate_correlation_insights(
                        theme1, theme2, common_tickers, companies1, companies2
                    )
                    
                    overlap = ThemeOverlap(
                        theme1=theme1,
                        theme2=theme2,
                        common_tickers=sorted(list(common_tickers)),
                        overlap_score=overlap_score,
                        correlation_type=correlation_type,
                        insights=insights
                    )
                    overlaps.append(overlap)
        
        # Sort by overlap score descending
        overlaps.sort(key=lambda x: x.overlap_score, reverse=True)
        return overlaps
    
    def _determine_correlation_type(self, common_tickers: Set[str], 
                                  companies1: Dict[str, ThemeCompany], 
                                  companies2: Dict[str, ThemeCompany]) -> str:
        """Determine if themes are complementary, conflicting, or independent."""
        sentiment_matches = 0
        sentiment_conflicts = 0
        
        for ticker in common_tickers:
            c1 = companies1[ticker]
            c2 = companies2[ticker]
            
            if c1.sentiment == c2.sentiment and c1.sentiment != "neutral":
                sentiment_matches += 1
            elif (c1.sentiment == "positive" and c2.sentiment == "negative") or \
                 (c1.sentiment == "negative" and c2.sentiment == "positive"):
                sentiment_conflicts += 1
        
        if sentiment_conflicts > sentiment_matches:
            return "conflicting"
        elif sentiment_matches > 0:
            return "complementary"
        else:
            return "independent"
    
    def _generate_correlation_insights(self, theme1: str, theme2: str, 
                                     common_tickers: Set[str],
                                     companies1: Dict[str, ThemeCompany],
                                     companies2: Dict[str, ThemeCompany]) -> List[str]:
        """Generate insights about theme correlation."""
        insights = []
        
        # Common companies insight
        if len(common_tickers) > 3:
            insights.append(f"Strong overlap with {len(common_tickers)} companies exposed to both themes")
        
        # Sentiment analysis
        positive_both = []
        conflicted = []
        
        for ticker in common_tickers:
            c1, c2 = companies1[ticker], companies2[ticker]
            if c1.sentiment == "positive" and c2.sentiment == "positive":
                positive_both.append(ticker)
            elif c1.sentiment != c2.sentiment and "neutral" not in [c1.sentiment, c2.sentiment]:
                conflicted.append(ticker)
        
        if positive_both:
            insights.append(f"Multi-theme winners: {', '.join(positive_both[:3])}")
        
        if conflicted:
            insights.append(f"Theme conflicts detected in: {', '.join(conflicted[:3])}")
        
        # Exposure level analysis
        high_exposure = [ticker for ticker in common_tickers 
                        if companies1.get(ticker, {}).exposure_level == "high" and 
                           companies2.get(ticker, {}).exposure_level == "high"]
        if high_exposure:
            insights.append(f"High dual exposure: {', '.join(high_exposure[:2])}")
        
        return insights
    
    def identify_cross_theme_opportunities(self, min_themes: int = 2) -> List[CrossThemeOpportunity]:
        """Identify companies with significant exposure to multiple themes.
        
        Args:
            min_themes: Minimum number of themes a company must appear in
            
        Returns:
            List of CrossThemeOpportunity objects
        """
        # Build ticker to themes mapping
        ticker_themes = defaultdict(list)
        all_companies = {}
        
        themes = self._get_available_themes()
        for theme in themes:
            companies = self._get_or_load_theme_companies(theme)
            for company in companies:
                ticker_themes[company.ticker].append(company)
                all_companies[company.ticker] = company  # Keep one instance for name
        
        opportunities = []
        
        for ticker, theme_companies in ticker_themes.items():
            if len(theme_companies) >= min_themes:
                themes_list = [c.theme for c in theme_companies]
                
                # Analyze sentiment consistency
                sentiments = [c.sentiment for c in theme_companies]
                positive_count = sentiments.count("positive")
                negative_count = sentiments.count("negative")
                
                # Determine opportunity type and confidence
                if positive_count >= len(theme_companies) * 0.8:
                    opportunity_type = "multi_theme_winner"
                    confidence = 0.8 + (positive_count / len(theme_companies)) * 0.2
                elif negative_count >= len(theme_companies) * 0.8:
                    opportunity_type = "multi_theme_loser"
                    confidence = 0.6 + (negative_count / len(theme_companies)) * 0.2
                elif positive_count > 0 and negative_count > 0:
                    opportunity_type = "theme_conflict"
                    confidence = 0.5 + abs(positive_count - negative_count) / len(theme_companies) * 0.3
                else:
                    opportunity_type = "diversified_play"
                    confidence = 0.4
                
                # Generate description
                description = self._generate_opportunity_description(
                    ticker, theme_companies, opportunity_type
                )
                
                # Categorize themes
                supporting_themes = [c.theme for c in theme_companies if c.sentiment == "positive"]
                conflicting_themes = [c.theme for c in theme_companies if c.sentiment == "negative"]
                
                # Generate risk factors
                risk_factors = self._generate_risk_factors(theme_companies, opportunity_type)
                
                opportunity = CrossThemeOpportunity(
                    ticker=ticker,
                    company_name=all_companies[ticker].company_name,
                    themes=themes_list,
                    opportunity_type=opportunity_type,
                    confidence_score=min(confidence, 1.0),
                    description=description,
                    supporting_themes=supporting_themes,
                    conflicting_themes=conflicting_themes,
                    risk_factors=risk_factors
                )
                opportunities.append(opportunity)
        
        # Sort by confidence score and number of themes
        opportunities.sort(key=lambda x: (x.confidence_score, len(x.themes)), reverse=True)
        return opportunities
    
    def _generate_opportunity_description(self, ticker: str, theme_companies: List[ThemeCompany], 
                                        opportunity_type: str) -> str:
        """Generate description for cross-theme opportunity."""
        themes_str = ", ".join(set(c.theme for c in theme_companies))
        
        if opportunity_type == "multi_theme_winner":
            return f"{ticker} benefits from multiple converging trends: {themes_str}. Positioned to capitalize on cross-theme synergies."
        elif opportunity_type == "multi_theme_loser":
            return f"{ticker} faces headwinds from multiple themes: {themes_str}. Multiple disruption vectors present downside risk."
        elif opportunity_type == "theme_conflict":
            supporting = [c.theme for c in theme_companies if c.sentiment == "positive"]
            conflicting = [c.theme for c in theme_companies if c.sentiment == "negative"]
            return f"{ticker} has mixed exposure - benefits from {', '.join(supporting)} but challenged by {', '.join(conflicting)}."
        else:
            return f"{ticker} has diversified exposure across {themes_str}, providing balanced risk profile."
    
    def _generate_risk_factors(self, theme_companies: List[ThemeCompany], 
                             opportunity_type: str) -> List[str]:
        """Generate risk factors based on theme exposure."""
        risks = []
        
        if opportunity_type == "multi_theme_winner":
            risks.append("Correlation risk - multiple themes could decline simultaneously")
            risks.append("Valuation risk - may be priced for perfection across multiple themes")
        elif opportunity_type == "theme_conflict":
            risks.append("Theme conflict could create volatile performance")
            risks.append("Execution risk - company must navigate competing priorities")
        elif opportunity_type == "diversified_play":
            risks.append("Diversification may limit upside from any single theme")
        
        # Add theme-specific risks
        themes = set(c.theme for c in theme_companies)
        if len(themes) > 3:
            risks.append(f"Complexity risk - exposure to {len(themes)} different themes")
        
        return risks
    
    def _get_available_themes(self) -> List[str]:
        """Get list of available themes from research files."""
        if not self.research_dir.exists():
            return []
        
        themes = set()
        for research_file in self.research_dir.glob('*.md'):
            with open(research_file, 'r', encoding='utf-8') as f:
                content = f.read()
                theme = self._extract_theme_from_content(content, research_file.name)
                themes.add(theme)
        
        return sorted(list(themes))
    
    def _get_or_load_theme_companies(self, theme: str) -> List[ThemeCompany]:
        """Get companies for a theme, loading from cache or files as needed."""
        if theme in self._theme_companies:
            return self._theme_companies[theme]
        
        companies = []
        if self.research_dir.exists():
            for research_file in self.research_dir.glob('*.md'):
                with open(research_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    file_theme = self._extract_theme_from_content(content, research_file.name)
                    
                    if file_theme.lower() == theme.lower():
                        file_companies = self.extract_companies_from_research(content, research_file.name)
                        companies.extend(file_companies)
        
        self._theme_companies[theme] = companies
        return companies
    
    def generate_correlation_report(self) -> str:
        """Generate a markdown report of theme correlations and opportunities.
        
        Returns:
            Markdown formatted correlation report
        """
        overlaps = self.analyze_theme_correlations()
        opportunities = self.identify_cross_theme_opportunities()
        
        lines = [
            "\n---",
            "\n## Multi-Theme Correlation Analysis",
            f"*Analysis of {len(self._get_available_themes())} investment themes*\n"
        ]
        
        if overlaps:
            lines.extend([
                "### Theme Correlations",
                "| Theme 1 | Theme 2 | Overlap | Type | Common Tickers |",
                "|---------|---------|---------|------|----------------|"
            ])
            
            for overlap in overlaps[:10]:  # Top 10
                common_str = ", ".join(overlap.common_tickers[:5])
                if len(overlap.common_tickers) > 5:
                    common_str += f" (+{len(overlap.common_tickers) - 5} more)"
                
                correlation_emoji = {
                    "complementary": "🤝",
                    "conflicting": "⚡",
                    "independent": "➖"
                }.get(overlap.correlation_type, "")
                
                lines.append(f"| {overlap.theme1} | {overlap.theme2} | {overlap.overlap_score:.2f} | {correlation_emoji} {overlap.correlation_type.title()} | {common_str} |")
        
        if opportunities:
            lines.extend([
                "\n### Cross-Theme Investment Opportunities",
                "| Ticker | Company | Themes | Type | Confidence |",
                "|--------|---------|---------|------|-----------|"
            ])
            
            for opp in opportunities[:15]:  # Top 15
                themes_str = ", ".join(opp.themes[:3])
                if len(opp.themes) > 3:
                    themes_str += f" (+{len(opp.themes) - 3})"
                
                type_emoji = {
                    "multi_theme_winner": "🚀",
                    "multi_theme_loser": "⚠️",
                    "theme_conflict": "⚡",
                    "diversified_play": "🎯"
                }.get(opp.opportunity_type, "")
                
                confidence_pct = f"{opp.confidence_score*100:.0f}%"
                
                lines.append(f"| {opp.ticker} | {opp.company_name[:25]}{'...' if len(opp.company_name) > 25 else ''} | {themes_str} | {type_emoji} {opp.opportunity_type.replace('_', ' ').title()} | {confidence_pct} |")
        
        # Key insights
        if overlaps:
            most_correlated = overlaps[0]
            lines.extend([
                "\n### Key Insights",
                f"- **Highest Correlation**: {most_correlated.theme1} ↔ {most_correlated.theme2} ({most_correlated.overlap_score:.2f})",
            ])
            
            if most_correlated.insights:
                for insight in most_correlated.insights[:2]:
                    lines.append(f"  - {insight}")
        
        if opportunities:
            multi_winners = [o for o in opportunities if o.opportunity_type == "multi_theme_winner"]
            conflicts = [o for o in opportunities if o.opportunity_type == "theme_conflict"]
            
            if multi_winners:
                lines.append(f"- **Multi-Theme Winners**: {len(multi_winners)} companies benefit from multiple themes")
                top_winner = multi_winners[0]
                lines.append(f"  - Top pick: {top_winner.ticker} ({len(top_winner.themes)} themes, {top_winner.confidence_score*100:.0f}% confidence)")
            
            if conflicts:
                lines.append(f"- **Theme Conflicts**: {len(conflicts)} companies face mixed theme exposure")
        
        lines.append("\n*Cross-theme analysis helps identify overlooked connections and conflicts between investment themes.*")
        
        return "\n".join(lines)
    
    def save_correlation_data(self, output_filename: str = None) -> Path:
        """Save correlation analysis to JSON file.
        
        Args:
            output_filename: Output filename, auto-generated if None
            
        Returns:
            Path to saved file
        """
        if not output_filename:
            output_filename = f"theme_correlations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_path = self.correlation_dir / output_filename
        
        overlaps = self.analyze_theme_correlations()
        opportunities = self.identify_cross_theme_opportunities()
        
        correlation_data = {
            'generated_at': datetime.now().isoformat(),
            'themes_analyzed': self._get_available_themes(),
            'theme_overlaps': [o.to_dict() for o in overlaps],
            'cross_theme_opportunities': [o.to_dict() for o in opportunities],
            'summary_stats': {
                'total_themes': len(self._get_available_themes()),
                'theme_pairs_analyzed': len(overlaps),
                'cross_theme_opportunities_found': len(opportunities),
                'multi_theme_winners': len([o for o in opportunities if o.opportunity_type == "multi_theme_winner"]),
                'theme_conflicts': len([o for o in opportunities if o.opportunity_type == "theme_conflict"])
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(correlation_data, f, indent=2, ensure_ascii=False)
        
        return output_path