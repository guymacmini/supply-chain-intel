"""Advanced research analytics for tracking patterns, themes, and quality metrics."""

import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, field
import statistics


@dataclass
class ResearchMetrics:
    """Analytics metrics for a research document."""
    filename: str
    theme: str
    generated_date: str
    word_count: int
    ticker_count: int
    table_count: int
    section_count: int
    tldr_length: int
    sources_count: int
    thesis_count: int
    confidence_keywords: int
    sentiment_score: float
    complexity_score: float
    quality_score: float
    
    def to_dict(self) -> Dict:
        return {
            'filename': self.filename,
            'theme': self.theme,
            'generated_date': self.generated_date,
            'word_count': self.word_count,
            'ticker_count': self.ticker_count,
            'table_count': self.table_count,
            'section_count': self.section_count,
            'tldr_length': self.tldr_length,
            'sources_count': self.sources_count,
            'thesis_count': self.thesis_count,
            'confidence_keywords': self.confidence_keywords,
            'sentiment_score': self.sentiment_score,
            'complexity_score': self.complexity_score,
            'quality_score': self.quality_score
        }


@dataclass
class ThemeAnalytics:
    """Analytics for a specific research theme."""
    theme: str
    document_count: int
    avg_quality_score: float
    avg_ticker_count: float
    avg_word_count: float
    total_tickers: int
    unique_tickers: int
    common_tickers: List[str]
    sentiment_distribution: Dict[str, int]
    date_range: Tuple[str, str]
    
    def to_dict(self) -> Dict:
        return {
            'theme': self.theme,
            'document_count': self.document_count,
            'avg_quality_score': self.avg_quality_score,
            'avg_ticker_count': self.avg_ticker_count,
            'avg_word_count': self.avg_word_count,
            'total_tickers': self.total_tickers,
            'unique_tickers': self.unique_tickers,
            'common_tickers': self.common_tickers,
            'sentiment_distribution': self.sentiment_distribution,
            'date_range': list(self.date_range)
        }


class ResearchAnalyticsEngine:
    """Advanced analytics engine for research quality and pattern analysis."""
    
    def __init__(self, data_dir: Path):
        """Initialize the analytics engine.
        
        Args:
            data_dir: Directory containing research files
        """
        self.data_dir = data_dir
        self.research_dir = data_dir / 'research'
        self.analytics_dir = data_dir / 'analytics'
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for computed analytics
        self._metrics_cache: Dict[str, ResearchMetrics] = {}
        self._cache_timestamp: Optional[datetime] = None
    
    def analyze_document_metrics(self, research_content: str, filename: str) -> ResearchMetrics:
        """Analyze a single research document and compute quality metrics.
        
        Args:
            research_content: Full research document content
            filename: Name of the research file
            
        Returns:
            ResearchMetrics object with computed metrics
        """
        # Basic text metrics
        word_count = len(research_content.split())
        
        # Extract metadata
        metadata = self._extract_metadata(research_content)
        theme = metadata.get('theme', 'Unknown')
        generated_date = metadata.get('generated', datetime.now().isoformat())
        
        # Count structural elements
        ticker_count = len(self._extract_tickers(research_content))
        table_count = research_content.count('|---')  # Markdown table separators
        section_count = len(re.findall(r'^#{1,3}\s', research_content, re.MULTILINE))
        
        # Analyze TLDR
        tldr_length = self._get_tldr_length(research_content)
        
        # Count sources
        sources_count = self._count_sources(research_content)
        
        # Count investment theses
        thesis_count = self._count_theses(research_content)
        
        # Analyze confidence indicators
        confidence_keywords = self._count_confidence_keywords(research_content)
        
        # Calculate sentiment score
        sentiment_score = self._calculate_sentiment_score(research_content)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(research_content)
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(
            word_count, ticker_count, table_count, section_count,
            tldr_length, sources_count, confidence_keywords, sentiment_score
        )
        
        return ResearchMetrics(
            filename=filename,
            theme=theme,
            generated_date=generated_date,
            word_count=word_count,
            ticker_count=ticker_count,
            table_count=table_count,
            section_count=section_count,
            tldr_length=tldr_length,
            sources_count=sources_count,
            thesis_count=thesis_count,
            confidence_keywords=confidence_keywords,
            sentiment_score=sentiment_score,
            complexity_score=complexity_score,
            quality_score=quality_score
        )
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from research document."""
        metadata = {}
        
        if content.startswith('---'):
            end_marker = content.find('---', 3)
            if end_marker != -1:
                frontmatter = content[3:end_marker]
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip().strip("'\"")
        
        # Extract theme from title if not in metadata
        if 'theme' not in metadata:
            title_match = re.search(r'# Investment Research:\s*([^\n]+)', content)
            if title_match:
                metadata['theme'] = title_match.group(1).strip()
        
        return metadata
    
    def _extract_tickers(self, content: str) -> List[str]:
        """Extract ticker symbols from content."""
        # Look for tickers in tables and text
        ticker_pattern = r'\b([A-Z]{1,5})\b'
        potential_tickers = re.findall(ticker_pattern, content)
        
        # Filter out common false positives
        excluded = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'CEO', 'USD', 'API', 'ETF', 'IPO', 'ESG'}
        
        return [t for t in set(potential_tickers) if len(t) >= 2 and t not in excluded]
    
    def _get_tldr_length(self, content: str) -> int:
        """Get length of TLDR section."""
        tldr_match = re.search(r'\*\*TLDR:\*\*\s*([^*]+)', content)
        return len(tldr_match.group(1).strip()) if tldr_match else 0
    
    def _count_sources(self, content: str) -> int:
        """Count number of sources cited."""
        # Look for sources section
        sources_section = re.search(r'## Sources.*?(?=##|\Z)', content, re.DOTALL)
        if sources_section:
            # Count URLs and citations
            urls = len(re.findall(r'https?://[^\s\)]+', sources_section.group(0)))
            citations = len(re.findall(r'^\d+\.', sources_section.group(0), re.MULTILINE))
            return max(urls, citations)
        return 0
    
    def _count_theses(self, content: str) -> int:
        """Count investment theses in the document."""
        thesis_indicators = [
            'investment thesis', 'thesis', 'opportunity', 'recommendation',
            'buy', 'sell', 'hold', 'target price', 'price target'
        ]
        
        count = 0
        content_lower = content.lower()
        for indicator in thesis_indicators:
            count += content_lower.count(indicator)
        
        return min(count, 20)  # Cap at reasonable maximum
    
    def _count_confidence_keywords(self, content: str) -> int:
        """Count confidence-indicating keywords."""
        confidence_words = [
            'confident', 'certain', 'likely', 'probable', 'expect',
            'believe', 'anticipate', 'forecast', 'predict', 'estimate'
        ]
        
        content_lower = content.lower()
        return sum(content_lower.count(word) for word in confidence_words)
    
    def _calculate_sentiment_score(self, content: str) -> float:
        """Calculate overall sentiment score (-1.0 to 1.0)."""
        positive_words = [
            'opportunity', 'growth', 'bullish', 'strong', 'outperform',
            'undervalued', 'compelling', 'attractive', 'upside', 'benefit'
        ]
        
        negative_words = [
            'risk', 'decline', 'bearish', 'weak', 'underperform',
            'overvalued', 'concern', 'downside', 'threat', 'challenge'
        ]
        
        content_lower = content.lower()
        positive_count = sum(content_lower.count(word) for word in positive_words)
        negative_count = sum(content_lower.count(word) for word in negative_words)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        return (positive_count - negative_count) / total
    
    def _calculate_complexity_score(self, content: str) -> float:
        """Calculate document complexity score (0.0 to 1.0)."""
        # Factors: sentence length, vocabulary diversity, technical terms
        sentences = re.split(r'[.!?]+', content)
        avg_sentence_length = statistics.mean(len(s.split()) for s in sentences if s.strip())
        
        # Vocabulary diversity (unique words / total words)
        words = re.findall(r'\b\w+\b', content.lower())
        vocab_diversity = len(set(words)) / len(words) if words else 0
        
        # Technical terms count
        technical_terms = [
            'analysis', 'valuation', 'fundamentals', 'metrics', 'correlation',
            'revenue', 'margin', 'profitability', 'competitive', 'strategy'
        ]
        tech_density = sum(content.lower().count(term) for term in technical_terms) / len(words) * 1000
        
        # Combine factors (normalize to 0-1 range)
        length_score = min(avg_sentence_length / 25, 1.0)  # 25 words = high complexity
        diversity_score = min(vocab_diversity * 2, 1.0)
        tech_score = min(tech_density / 10, 1.0)
        
        return (length_score + diversity_score + tech_score) / 3
    
    def _calculate_quality_score(self, word_count: int, ticker_count: int, 
                                table_count: int, section_count: int,
                                tldr_length: int, sources_count: int, 
                                confidence_keywords: int, sentiment_score: float) -> float:
        """Calculate overall research quality score (0.0 to 1.0)."""
        # Quality factors with weights
        factors = {
            'length': min(word_count / 10000, 1.0) * 0.15,  # 10k words = optimal
            'tickers': min(ticker_count / 20, 1.0) * 0.15,  # 20 tickers = good coverage
            'structure': min(table_count / 5 + section_count / 15, 1.0) * 0.2,
            'tldr': min(tldr_length / 500, 1.0) * 0.1,  # 500 chars = good TLDR
            'sources': min(sources_count / 10, 1.0) * 0.2,  # 10 sources = well-researched
            'confidence': min(confidence_keywords / 10, 1.0) * 0.1,
            'objectivity': (1.0 - abs(sentiment_score)) * 0.1  # Balanced sentiment = higher quality
        }
        
        return sum(factors.values())
    
    def analyze_all_documents(self, force_refresh: bool = False) -> List[ResearchMetrics]:
        """Analyze all research documents and return metrics.
        
        Args:
            force_refresh: Whether to force recomputation of metrics
            
        Returns:
            List of ResearchMetrics for all documents
        """
        # Check if cache is valid
        if not force_refresh and self._cache_timestamp and self._metrics_cache:
            # Cache is valid if less than 1 hour old
            if datetime.now() - self._cache_timestamp < timedelta(hours=1):
                return list(self._metrics_cache.values())
        
        # Clear cache and recompute
        self._metrics_cache.clear()
        metrics_list = []
        
        if not self.research_dir.exists():
            return metrics_list
        
        for research_file in self.research_dir.glob('*.md'):
            try:
                with open(research_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                metrics = self.analyze_document_metrics(content, research_file.name)
                self._metrics_cache[research_file.name] = metrics
                metrics_list.append(metrics)
                
            except Exception as e:
                print(f"Error analyzing {research_file.name}: {e}")
                continue
        
        self._cache_timestamp = datetime.now()
        return metrics_list
    
    def analyze_themes(self) -> List[ThemeAnalytics]:
        """Analyze research patterns by theme.
        
        Returns:
            List of ThemeAnalytics objects
        """
        all_metrics = self.analyze_all_documents()
        
        # Group by theme
        themes_data = defaultdict(list)
        for metrics in all_metrics:
            themes_data[metrics.theme].append(metrics)
        
        theme_analytics = []
        
        for theme, theme_metrics in themes_data.items():
            if not theme_metrics:
                continue
            
            # Calculate theme statistics
            quality_scores = [m.quality_score for m in theme_metrics]
            ticker_counts = [m.ticker_count for m in theme_metrics]
            word_counts = [m.word_count for m in theme_metrics]
            
            # Collect all tickers for this theme
            all_tickers = []
            for m in theme_metrics:
                all_tickers.extend(self._extract_tickers(f"dummy content with metrics ticker_count={m.ticker_count}"))
            
            ticker_counter = Counter(all_tickers)
            common_tickers = [ticker for ticker, count in ticker_counter.most_common(10)]
            
            # Calculate sentiment distribution
            sentiment_dist = {'positive': 0, 'neutral': 0, 'negative': 0}
            for m in theme_metrics:
                if m.sentiment_score > 0.2:
                    sentiment_dist['positive'] += 1
                elif m.sentiment_score < -0.2:
                    sentiment_dist['negative'] += 1
                else:
                    sentiment_dist['neutral'] += 1
            
            # Date range
            dates = [m.generated_date for m in theme_metrics if m.generated_date]
            date_range = (min(dates), max(dates)) if dates else ("", "")
            
            analytics = ThemeAnalytics(
                theme=theme,
                document_count=len(theme_metrics),
                avg_quality_score=statistics.mean(quality_scores),
                avg_ticker_count=statistics.mean(ticker_counts),
                avg_word_count=statistics.mean(word_counts),
                total_tickers=len(all_tickers),
                unique_tickers=len(set(all_tickers)),
                common_tickers=common_tickers,
                sentiment_distribution=sentiment_dist,
                date_range=date_range
            )
            
            theme_analytics.append(analytics)
        
        # Sort by document count (most researched themes first)
        return sorted(theme_analytics, key=lambda x: x.document_count, reverse=True)
    
    def get_quality_trends(self, days: int = 30) -> Dict[str, List[float]]:
        """Get research quality trends over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with daily quality metrics
        """
        all_metrics = self.analyze_all_documents()
        
        # Filter recent documents
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_metrics = [
            m for m in all_metrics 
            if m.generated_date and datetime.fromisoformat(m.generated_date[:19]) > cutoff_date
        ]
        
        # Group by date
        daily_metrics = defaultdict(list)
        for m in recent_metrics:
            if m.generated_date:
                date_key = m.generated_date[:10]  # YYYY-MM-DD
                daily_metrics[date_key].append(m)
        
        # Calculate daily averages
        trends = {
            'dates': [],
            'quality_scores': [],
            'word_counts': [],
            'ticker_counts': [],
            'sources_counts': []
        }
        
        for date in sorted(daily_metrics.keys()):
            day_metrics = daily_metrics[date]
            
            trends['dates'].append(date)
            trends['quality_scores'].append(statistics.mean(m.quality_score for m in day_metrics))
            trends['word_counts'].append(statistics.mean(m.word_count for m in day_metrics))
            trends['ticker_counts'].append(statistics.mean(m.ticker_count for m in day_metrics))
            trends['sources_counts'].append(statistics.mean(m.sources_count for m in day_metrics))
        
        return trends
    
    def generate_analytics_report(self) -> str:
        """Generate a comprehensive analytics report in markdown format.
        
        Returns:
            Markdown formatted analytics report
        """
        all_metrics = self.analyze_all_documents()
        theme_analytics = self.analyze_themes()
        
        if not all_metrics:
            return "\n## Research Analytics\n\nNo research documents found for analysis."
        
        # Overall statistics
        total_docs = len(all_metrics)
        avg_quality = statistics.mean(m.quality_score for m in all_metrics)
        avg_word_count = statistics.mean(m.word_count for m in all_metrics)
        total_tickers = len(set().union(*[self._extract_tickers(f"dummy {m.ticker_count}") for m in all_metrics]))
        
        lines = [
            "\n---",
            "\n## Research Analytics Dashboard",
            f"*Comprehensive analysis of {total_docs} research documents*\n",
            "### Overall Statistics",
            f"- **Average Quality Score**: {avg_quality:.2f}/1.00",
            f"- **Average Document Length**: {avg_word_count:,.0f} words",
            f"- **Total Unique Tickers Analyzed**: {total_tickers}",
            f"- **Research Themes Covered**: {len(theme_analytics)}",
            ""
        ]
        
        # Quality distribution
        quality_ranges = {
            'Excellent (0.8+)': len([m for m in all_metrics if m.quality_score >= 0.8]),
            'Good (0.6-0.8)': len([m for m in all_metrics if 0.6 <= m.quality_score < 0.8]),
            'Fair (0.4-0.6)': len([m for m in all_metrics if 0.4 <= m.quality_score < 0.6]),
            'Needs Improvement (<0.4)': len([m for m in all_metrics if m.quality_score < 0.4])
        }
        
        lines.extend([
            "### Quality Distribution",
            "| Quality Range | Documents | Percentage |",
            "|---------------|-----------|------------|"
        ])
        
        for range_name, count in quality_ranges.items():
            percentage = (count / total_docs * 100) if total_docs > 0 else 0
            lines.append(f"| {range_name} | {count} | {percentage:.1f}% |")
        
        # Top themes
        if theme_analytics:
            lines.extend([
                "",
                "### Research Themes Analysis",
                "| Theme | Documents | Avg Quality | Avg Tickers | Unique Tickers |",
                "|-------|-----------|-------------|-------------|----------------|"
            ])
            
            for theme in theme_analytics[:8]:  # Top 8 themes
                lines.append(
                    f"| {theme.theme} | {theme.document_count} | {theme.avg_quality_score:.2f} | "
                    f"{theme.avg_ticker_count:.1f} | {theme.unique_tickers} |"
                )
        
        # Research quality insights
        high_quality_docs = [m for m in all_metrics if m.quality_score >= 0.8]
        if high_quality_docs:
            lines.extend([
                "",
                "### Quality Insights",
                f"- **Top Research Themes**: {', '.join([ta.theme for ta in theme_analytics[:3]])}",
                f"- **Most Comprehensive Documents**: {statistics.mean(m.word_count for m in high_quality_docs):,.0f} avg words",
                f"- **Best Sourced Research**: {statistics.mean(m.sources_count for m in high_quality_docs):.1f} avg sources",
            ])
        
        lines.append("\n*Research analytics help improve documentation quality and identify successful patterns.*")
        
        return "\n".join(lines)
    
    def save_analytics_data(self, output_filename: str = None) -> Path:
        """Save analytics data to JSON file.
        
        Args:
            output_filename: Output filename, auto-generated if None
            
        Returns:
            Path to saved file
        """
        if not output_filename:
            output_filename = f"research_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_path = self.analytics_dir / output_filename
        
        all_metrics = self.analyze_all_documents()
        theme_analytics = self.analyze_themes()
        quality_trends = self.get_quality_trends()
        
        analytics_data = {
            'generated_at': datetime.now().isoformat(),
            'total_documents': len(all_metrics),
            'document_metrics': [m.to_dict() for m in all_metrics],
            'theme_analytics': [t.to_dict() for t in theme_analytics],
            'quality_trends': quality_trends,
            'summary_stats': {
                'avg_quality_score': statistics.mean(m.quality_score for m in all_metrics) if all_metrics else 0,
                'avg_word_count': statistics.mean(m.word_count for m in all_metrics) if all_metrics else 0,
                'total_themes': len(theme_analytics),
                'quality_distribution': {
                    'excellent': len([m for m in all_metrics if m.quality_score >= 0.8]),
                    'good': len([m for m in all_metrics if 0.6 <= m.quality_score < 0.8]),
                    'fair': len([m for m in all_metrics if 0.4 <= m.quality_score < 0.6]),
                    'poor': len([m for m in all_metrics if m.quality_score < 0.4])
                }
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analytics_data, f, indent=2, ensure_ascii=False)
        
        return output_path