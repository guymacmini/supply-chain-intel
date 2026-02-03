"""Historical analysis tracking for investment thesis performance."""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from .finnhub_client import FinnhubClient


class ThesisOutcome(Enum):
    """Possible outcomes for investment theses."""
    PENDING = "pending"  # Still being tracked
    SUCCESS = "success"  # Thesis proved correct
    FAILURE = "failure"  # Thesis proved incorrect  
    MIXED = "mixed"      # Partially correct
    EXPIRED = "expired"  # Time horizon passed, neutral outcome


class PriceTarget(Enum):
    """Types of price expectations."""
    OUTPERFORM = "outperform"  # Expected to outperform market/sector
    UNDERPERFORM = "underperform"  # Expected to underperform
    STABLE = "stable"  # Expected to remain relatively stable
    VOLATILE = "volatile"  # Expected high volatility


@dataclass
class InvestmentThesis:
    """An investment thesis extracted from research."""
    thesis_id: str
    ticker: str
    company_name: str
    thesis_statement: str
    prediction_type: PriceTarget
    confidence_level: str  # "high", "medium", "low"
    time_horizon_months: int
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    catalyst: Optional[str] = None
    risks: List[str] = field(default_factory=list)
    
    # Metadata
    research_file: Optional[str] = None
    created_date: Optional[str] = None
    analyst_notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'thesis_id': self.thesis_id,
            'ticker': self.ticker,
            'company_name': self.company_name,
            'thesis_statement': self.thesis_statement,
            'prediction_type': self.prediction_type.value,
            'confidence_level': self.confidence_level,
            'time_horizon_months': self.time_horizon_months,
            'entry_price': self.entry_price,
            'target_price': self.target_price,
            'stop_loss': self.stop_loss,
            'catalyst': self.catalyst,
            'risks': self.risks,
            'research_file': self.research_file,
            'created_date': self.created_date,
            'analyst_notes': self.analyst_notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InvestmentThesis':
        """Create from dictionary."""
        data = data.copy()
        if 'prediction_type' in data:
            data['prediction_type'] = PriceTarget(data['prediction_type'])
        return cls(**data)


@dataclass
class ThesisPerformance:
    """Performance tracking for an investment thesis."""
    thesis_id: str
    
    # Price tracking
    initial_price: Optional[float] = None
    current_price: Optional[float] = None
    peak_price: Optional[float] = None
    trough_price: Optional[float] = None
    
    # Performance metrics
    return_pct: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    max_gain_pct: Optional[float] = None
    volatility: Optional[float] = None
    
    # Benchmark comparison
    sp500_return_pct: Optional[float] = None  # For comparison
    sector_return_pct: Optional[float] = None
    alpha: Optional[float] = None  # Excess return vs benchmark
    
    # Outcome tracking
    outcome: ThesisOutcome = ThesisOutcome.PENDING
    outcome_date: Optional[str] = None
    outcome_notes: Optional[str] = None
    
    # Timeline
    tracking_start_date: Optional[str] = None
    last_updated: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'thesis_id': self.thesis_id,
            'initial_price': self.initial_price,
            'current_price': self.current_price,
            'peak_price': self.peak_price,
            'trough_price': self.trough_price,
            'return_pct': self.return_pct,
            'max_drawdown_pct': self.max_drawdown_pct,
            'max_gain_pct': self.max_gain_pct,
            'volatility': self.volatility,
            'sp500_return_pct': self.sp500_return_pct,
            'sector_return_pct': self.sector_return_pct,
            'alpha': self.alpha,
            'outcome': self.outcome.value,
            'outcome_date': self.outcome_date,
            'outcome_notes': self.outcome_notes,
            'tracking_start_date': self.tracking_start_date,
            'last_updated': self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ThesisPerformance':
        """Create from dictionary."""
        data = data.copy()
        if 'outcome' in data:
            data['outcome'] = ThesisOutcome(data['outcome'])
        return cls(**data)


class HistoricalTracker:
    """Tracks investment thesis performance over time."""
    
    def __init__(self, data_dir: Path, finnhub_client: Optional[FinnhubClient] = None):
        """Initialize historical tracker.
        
        Args:
            data_dir: Directory to store tracking data
            finnhub_client: Optional Finnhub client for price data
        """
        self.data_dir = data_dir
        self.tracking_dir = data_dir / 'historical_tracking'
        self.tracking_dir.mkdir(parents=True, exist_ok=True)
        
        self.theses_file = self.tracking_dir / 'investment_theses.json'
        self.performance_file = self.tracking_dir / 'thesis_performance.json'
        
        self.finnhub_client = finnhub_client or FinnhubClient()
        
        # Load existing data
        self.theses: Dict[str, InvestmentThesis] = self._load_theses()
        self.performance: Dict[str, ThesisPerformance] = self._load_performance()
    
    def _load_theses(self) -> Dict[str, InvestmentThesis]:
        """Load investment theses from file."""
        if not self.theses_file.exists():
            return {}
        
        try:
            with open(self.theses_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: InvestmentThesis.from_dict(v) for k, v in data.items()}
        except Exception as e:
            print(f"Error loading theses: {e}")
            return {}
    
    def _load_performance(self) -> Dict[str, ThesisPerformance]:
        """Load thesis performance from file."""
        if not self.performance_file.exists():
            return {}
        
        try:
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: ThesisPerformance.from_dict(v) for k, v in data.items()}
        except Exception as e:
            print(f"Error loading performance: {e}")
            return {}
    
    def _save_theses(self) -> None:
        """Save investment theses to file."""
        try:
            data = {k: v.to_dict() for k, v in self.theses.items()}
            with open(self.theses_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving theses: {e}")
    
    def _save_performance(self) -> None:
        """Save thesis performance to file."""
        try:
            data = {k: v.to_dict() for k, v in self.performance.items()}
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving performance: {e}")
    
    def extract_theses_from_research(self, research_content: str, research_filename: str) -> List[InvestmentThesis]:
        """Extract investment theses from research content.
        
        Args:
            research_content: Full research document content
            research_filename: Name of research file
            
        Returns:
            List of extracted investment theses
        """
        theses = []
        
        # Look for investment opportunity tables
        opportunity_pattern = r'\|\s*([A-Z]+)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|[^|]*?\|\s*([^|]*?)\s*\|'
        matches = re.findall(opportunity_pattern, research_content)
        
        # Extract thesis statements from various sections
        thesis_patterns = [
            r'\*\*([A-Z]+)\*\*[^.]*?(outperform|underperform|overvalued|undervalued|bullish|bearish)[^.]*?\.',
            r'([A-Z]+)\s+(?:is|appears|looks|seems)\s+(?:undervalued|overvalued|attractive|compelling)',
            r'(?:Buy|Sell|Hold)\s+([A-Z]+).*?(?:target|price|upside)',
        ]
        
        # Look for specific investment recommendations
        recommendation_sections = [
            'Investment Opportunities',
            'Top Picks', 
            'Recommendations',
            'Key Plays',
            'Actionable Trades'
        ]
        
        for section in recommendation_sections:
            section_match = re.search(f'#{2,3}\\s*{section}.*?(?=#{2,3}|$)', research_content, re.DOTALL | re.IGNORECASE)
            if section_match:
                section_content = section_match.group(0)
                
                # Extract ticker mentions with context
                ticker_context_pattern = r'\b([A-Z]{1,5})\b[^.]*?(?:(undervalued|overvalued|outperform|target|upside|downside|bullish|bearish|buy|sell)[^.]*?\.)'
                context_matches = re.findall(ticker_context_pattern, section_content, re.IGNORECASE)
                
                for ticker, context in context_matches:
                    if len(ticker) >= 2:  # Valid ticker length
                        thesis_id = f"{research_filename.split('.')[0]}_{ticker}_{datetime.now().strftime('%Y%m%d')}"
                        
                        # Determine prediction type from context
                        context_lower = context.lower()
                        if any(word in context_lower for word in ['undervalued', 'upside', 'outperform', 'bullish', 'buy']):
                            prediction_type = PriceTarget.OUTPERFORM
                        elif any(word in context_lower for word in ['overvalued', 'downside', 'underperform', 'bearish', 'sell']):
                            prediction_type = PriceTarget.UNDERPERFORM
                        else:
                            prediction_type = PriceTarget.STABLE
                        
                        thesis = InvestmentThesis(
                            thesis_id=thesis_id,
                            ticker=ticker,
                            company_name=self._extract_company_name(research_content, ticker),
                            thesis_statement=context,
                            prediction_type=prediction_type,
                            confidence_level="medium",  # Default confidence
                            time_horizon_months=12,  # Default time horizon
                            research_file=research_filename,
                            created_date=datetime.now().isoformat(),
                            analyst_notes=f"Extracted from {section} section"
                        )
                        theses.append(thesis)
        
        return theses
    
    def _extract_company_name(self, content: str, ticker: str) -> str:
        """Try to extract company name for a ticker from research content."""
        # Look for patterns like "Apple (AAPL)" or "AAPL (Apple Inc)"
        patterns = [
            rf'([^|(),\n]+?)\s*\(\s*{ticker}\s*\)',
            rf'{ticker}\s*\(([^)]+)\)',
            rf'\|\s*{ticker}\s*\|\s*([^|]+?)\s*\|'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                company_name = match.group(1).strip()
                if company_name and len(company_name) > 2:
                    return company_name
        
        return f"Unknown ({ticker})"
    
    def add_thesis(self, thesis: InvestmentThesis) -> bool:
        """Add a new investment thesis.
        
        Args:
            thesis: Investment thesis to add
            
        Returns:
            True if added successfully
        """
        try:
            self.theses[thesis.thesis_id] = thesis
            
            # Initialize performance tracking
            performance = ThesisPerformance(
                thesis_id=thesis.thesis_id,
                tracking_start_date=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat()
            )
            
            # Get initial price if possible
            if self.finnhub_client.is_available():
                quote = self.finnhub_client.get_quote(thesis.ticker)
                if quote and 'c' in quote:
                    performance.initial_price = quote['c']
                    performance.current_price = quote['c']
                    performance.peak_price = quote['c']
                    performance.trough_price = quote['c']
            
            self.performance[thesis.thesis_id] = performance
            
            self._save_theses()
            self._save_performance()
            return True
            
        except Exception as e:
            print(f"Error adding thesis: {e}")
            return False
    
    def update_performance(self, thesis_id: str = None) -> bool:
        """Update performance for one or all theses.
        
        Args:
            thesis_id: Specific thesis to update, or None for all
            
        Returns:
            True if updated successfully
        """
        if not self.finnhub_client.is_available():
            return False
        
        theses_to_update = [thesis_id] if thesis_id else list(self.theses.keys())
        updated_count = 0
        
        for t_id in theses_to_update:
            if t_id not in self.theses or t_id not in self.performance:
                continue
            
            thesis = self.theses[t_id]
            perf = self.performance[t_id]
            
            # Skip if already concluded
            if perf.outcome != ThesisOutcome.PENDING:
                continue
            
            try:
                # Get current quote
                quote = self.finnhub_client.get_quote(thesis.ticker)
                if not quote or 'c' not in quote:
                    continue
                
                current_price = quote['c']
                perf.current_price = current_price
                
                # Update peak and trough
                if perf.peak_price is None or current_price > perf.peak_price:
                    perf.peak_price = current_price
                if perf.trough_price is None or current_price < perf.trough_price:
                    perf.trough_price = current_price
                
                # Calculate returns if we have initial price
                if perf.initial_price:
                    perf.return_pct = ((current_price - perf.initial_price) / perf.initial_price) * 100
                    perf.max_gain_pct = ((perf.peak_price - perf.initial_price) / perf.initial_price) * 100
                    perf.max_drawdown_pct = ((perf.trough_price - perf.initial_price) / perf.initial_price) * 100
                
                # Check if time horizon expired
                if thesis.created_date:
                    created_date = datetime.fromisoformat(thesis.created_date)
                    expiry_date = created_date + timedelta(days=thesis.time_horizon_months * 30)
                    if datetime.now() > expiry_date:
                        self._evaluate_thesis_outcome(thesis, perf)
                
                perf.last_updated = datetime.now().isoformat()
                updated_count += 1
                
            except Exception as e:
                print(f"Error updating performance for {thesis.ticker}: {e}")
                continue
        
        if updated_count > 0:
            self._save_performance()
        
        return updated_count > 0
    
    def _evaluate_thesis_outcome(self, thesis: InvestmentThesis, perf: ThesisPerformance) -> None:
        """Evaluate the outcome of a thesis based on performance."""
        if not perf.return_pct:
            perf.outcome = ThesisOutcome.EXPIRED
            perf.outcome_notes = "Insufficient data to evaluate"
            return
        
        # Define success thresholds based on prediction type
        if thesis.prediction_type == PriceTarget.OUTPERFORM:
            if perf.return_pct > 10:  # Beat market expectation
                perf.outcome = ThesisOutcome.SUCCESS
                perf.outcome_notes = f"Outperformed with {perf.return_pct:.1f}% return"
            elif perf.return_pct < -5:  # Underperformed significantly
                perf.outcome = ThesisOutcome.FAILURE
                perf.outcome_notes = f"Underperformed with {perf.return_pct:.1f}% return"
            else:
                perf.outcome = ThesisOutcome.MIXED
                perf.outcome_notes = f"Mixed results with {perf.return_pct:.1f}% return"
        
        elif thesis.prediction_type == PriceTarget.UNDERPERFORM:
            if perf.return_pct < -5:  # Successfully predicted underperformance
                perf.outcome = ThesisOutcome.SUCCESS
                perf.outcome_notes = f"Correctly predicted decline: {perf.return_pct:.1f}%"
            elif perf.return_pct > 10:  # Failed to predict underperformance
                perf.outcome = ThesisOutcome.FAILURE
                perf.outcome_notes = f"Failed to predict rise: {perf.return_pct:.1f}%"
            else:
                perf.outcome = ThesisOutcome.MIXED
                perf.outcome_notes = f"Mixed results: {perf.return_pct:.1f}%"
        
        else:  # STABLE or VOLATILE
            if abs(perf.return_pct) < 10:
                perf.outcome = ThesisOutcome.SUCCESS
                perf.outcome_notes = f"Stable as predicted: {perf.return_pct:.1f}%"
            else:
                perf.outcome = ThesisOutcome.MIXED
                perf.outcome_notes = f"More volatile than expected: {perf.return_pct:.1f}%"
        
        perf.outcome_date = datetime.now().isoformat()
    
    def get_hit_rate_stats(self) -> Dict[str, Any]:
        """Calculate hit rate and performance statistics.
        
        Returns:
            Dictionary with performance statistics
        """
        total_theses = len(self.theses)
        if total_theses == 0:
            return {
                'total_theses': 0,
                'hit_rate_pct': 0.0,
                'success_count': 0,
                'failure_count': 0,
                'mixed_count': 0,
                'pending_count': 0,
                'expired_count': 0,
                'avg_return_pct': 0.0,
                'concluded_count': 0
            }
        
        # Count outcomes
        outcomes = {'success': 0, 'failure': 0, 'mixed': 0, 'pending': 0, 'expired': 0}
        total_return = 0
        concluded_count = 0
        
        for perf in self.performance.values():
            outcomes[perf.outcome.value] += 1
            if perf.outcome != ThesisOutcome.PENDING and perf.return_pct:
                total_return += perf.return_pct
                concluded_count += 1
        
        # Calculate rates
        hit_rate = (outcomes['success'] / total_theses) * 100 if total_theses > 0 else 0
        avg_return = total_return / concluded_count if concluded_count > 0 else 0
        
        return {
            'total_theses': total_theses,
            'hit_rate_pct': round(hit_rate, 1),
            'success_count': outcomes['success'],
            'failure_count': outcomes['failure'],
            'mixed_count': outcomes['mixed'],
            'pending_count': outcomes['pending'],
            'expired_count': outcomes['expired'],
            'avg_return_pct': round(avg_return, 1),
            'concluded_count': concluded_count
        }
    
    def generate_performance_report(self) -> str:
        """Generate a markdown performance report.
        
        Returns:
            Markdown formatted performance report
        """
        stats = self.get_hit_rate_stats()
        
        if stats['total_theses'] == 0:
            return "## Historical Performance\n\nNo investment theses tracked yet."
        
        lines = [
            "\n---",
            "\n## Historical Investment Thesis Performance",
            f"*Performance tracking for {stats['total_theses']} investment theses*\n",
            "### Overall Statistics",
            f"- **Hit Rate**: {stats['hit_rate_pct']}% ({stats['success_count']}/{stats['total_theses']} successful)",
            f"- **Average Return**: {stats['avg_return_pct']}%",
            f"- **Active Tracking**: {stats['pending_count']} theses",
            f"- **Completed**: {stats['concluded_count']} theses\n"
        ]
        
        # Top performers
        if self.performance:
            lines.append("### Recent Performance")
            lines.append("| Ticker | Thesis | Return | Status | Notes |")
            lines.append("|--------|--------|--------|--------|-------|")
            
            # Sort by return percentage
            perf_items = [(thesis_id, perf) for thesis_id, perf in self.performance.items() 
                         if perf.return_pct is not None]
            perf_items.sort(key=lambda x: x[1].return_pct, reverse=True)
            
            for thesis_id, perf in perf_items[:10]:  # Top 10
                if thesis_id in self.theses:
                    thesis = self.theses[thesis_id]
                    status_emoji = {
                        ThesisOutcome.SUCCESS: "✅",
                        ThesisOutcome.FAILURE: "❌", 
                        ThesisOutcome.MIXED: "⚠️",
                        ThesisOutcome.PENDING: "🔄",
                        ThesisOutcome.EXPIRED: "⏰"
                    }.get(perf.outcome, "")
                    
                    return_str = f"{perf.return_pct:+.1f}%" if perf.return_pct else "N/A"
                    notes = perf.outcome_notes[:30] + "..." if perf.outcome_notes and len(perf.outcome_notes) > 30 else perf.outcome_notes or ""
                    
                    lines.append(f"| {thesis.ticker} | {thesis.thesis_statement[:30]}... | {return_str} | {status_emoji} {perf.outcome.value.title()} | {notes} |")
        
        lines.append("\n*Historical tracking helps improve research accuracy over time.*")
        
        return "\n".join(lines)
    
    def process_research_file(self, research_file_path: Path) -> int:
        """Process a research file and extract/track theses.
        
        Args:
            research_file_path: Path to research file
            
        Returns:
            Number of theses extracted and added
        """
        try:
            with open(research_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            theses = self.extract_theses_from_research(content, research_file_path.name)
            added_count = 0
            
            for thesis in theses:
                if self.add_thesis(thesis):
                    added_count += 1
            
            return added_count
            
        except Exception as e:
            print(f"Error processing research file {research_file_path}: {e}")
            return 0