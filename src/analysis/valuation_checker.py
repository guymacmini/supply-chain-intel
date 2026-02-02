"""
Valuation Reality Check Analyzer

Determines if a stock's potential is already "priced in" based on:
- Current vs historical valuation multiples
- Implied growth rates
- Scenario analysis (bull/base/bear)

Verdicts:
- PRICED IN: Current valuation implies very high growth, limited upside
- FAIR VALUE: Reasonably priced for expected growth
- UNDERAPPRECIATED: Market underestimates the opportunity
- SPECULATIVE: No earnings, pure growth bet
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import math


class ValuationVerdict(Enum):
    """Valuation verdict with investment implications."""
    PRICED_IN = "PRICED IN"
    FAIR_VALUE = "FAIR VALUE"
    UNDERAPPRECIATED = "UNDERAPPRECIATED"
    SPECULATIVE = "SPECULATIVE"
    UNKNOWN = "UNKNOWN"

    @property
    def emoji(self) -> str:
        return {
            ValuationVerdict.PRICED_IN: "🔴",
            ValuationVerdict.FAIR_VALUE: "🟡",
            ValuationVerdict.UNDERAPPRECIATED: "🟢",
            ValuationVerdict.SPECULATIVE: "⚪",
            ValuationVerdict.UNKNOWN: "❓"
        }.get(self, "❓")
    
    @property
    def action(self) -> str:
        return {
            ValuationVerdict.PRICED_IN: "Wait for pullback",
            ValuationVerdict.FAIR_VALUE: "Size appropriately",
            ValuationVerdict.UNDERAPPRECIATED: "Consider accumulating",
            ValuationVerdict.SPECULATIVE: "Small position only",
            ValuationVerdict.UNKNOWN: "More research needed"
        }.get(self, "")


@dataclass
class ValuationAssessment:
    """Assessment of a single stock's valuation."""
    ticker: str
    company: str
    
    # Current metrics
    current_price: Optional[float] = None
    current_pe: Optional[float] = None
    current_ps: Optional[float] = None  # Price/Sales
    current_ev_ebitda: Optional[float] = None
    
    # Historical comparisons
    pe_5y_avg: Optional[float] = None
    pe_sector_avg: Optional[float] = None
    
    # Derived metrics
    pe_vs_history: Optional[float] = None  # % above/below 5Y avg
    implied_growth: Optional[float] = None  # Implied CAGR to justify valuation
    
    # Scenario analysis
    bull_upside: Optional[float] = None  # % upside in bull case
    base_return: Optional[float] = None  # % expected return in base case
    bear_downside: Optional[float] = None  # % downside in bear case
    
    # Verdict
    verdict: ValuationVerdict = ValuationVerdict.UNKNOWN
    rationale: str = ""
    
    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "company": self.company,
            "current_pe": self.current_pe,
            "pe_5y_avg": self.pe_5y_avg,
            "pe_vs_history": self.pe_vs_history,
            "implied_growth": self.implied_growth,
            "verdict": self.verdict.value,
            "rationale": self.rationale,
            "scenarios": {
                "bull_upside": self.bull_upside,
                "base_return": self.base_return,
                "bear_downside": self.bear_downside
            }
        }

    def to_markdown_row(self) -> str:
        """Generate markdown table row."""
        pe = f"{self.current_pe:.1f}x" if self.current_pe else "N/A"
        pe_avg = f"{self.pe_5y_avg:.1f}x" if self.pe_5y_avg else "-"
        
        if self.pe_vs_history is not None:
            vs_hist = f"{self.pe_vs_history:+.0f}%"
        else:
            vs_hist = "-"
            
        implied = f"{self.implied_growth:.0f}%" if self.implied_growth else "-"
        
        return f"| {self.ticker} | {self.company[:20]} | {pe} | {pe_avg} | {vs_hist} | {implied} | {self.verdict.emoji} {self.verdict.value} |"


class ValuationChecker:
    """
    Analyzes stock valuations to determine if opportunities are "priced in".
    
    Usage:
        checker = ValuationChecker()
        assessment = checker.assess(
            ticker="NVDA",
            company="NVIDIA",
            current_pe=45,
            pe_5y_avg=35,
            pe_sector_avg=25,
            revenue_growth=50  # YoY %
        )
        print(assessment.verdict)  # PRICED IN or UNDERAPPRECIATED etc.
    """
    
    # Thresholds
    PREMIUM_THRESHOLD = 30  # % above historical = expensive
    DISCOUNT_THRESHOLD = -20  # % below historical = cheap
    HIGH_IMPLIED_GROWTH = 25  # % CAGR = aggressive expectations
    
    def assess(
        self,
        ticker: str,
        company: str,
        current_pe: Optional[float] = None,
        pe_5y_avg: Optional[float] = None,
        pe_sector_avg: Optional[float] = None,
        current_ps: Optional[float] = None,
        current_ev_ebitda: Optional[float] = None,
        revenue_growth: Optional[float] = None,  # Recent YoY %
        earnings_growth: Optional[float] = None,  # Recent YoY %
        current_price: Optional[float] = None,
        target_price_bull: Optional[float] = None,
        target_price_bear: Optional[float] = None
    ) -> ValuationAssessment:
        """
        Assess a stock's valuation and determine verdict.
        """
        assessment = ValuationAssessment(
            ticker=ticker,
            company=company,
            current_price=current_price,
            current_pe=current_pe,
            current_ps=current_ps,
            current_ev_ebitda=current_ev_ebitda,
            pe_5y_avg=pe_5y_avg,
            pe_sector_avg=pe_sector_avg
        )

        rationale_parts = []

        # Handle no-earnings case
        if current_pe is None or current_pe <= 0:
            assessment.verdict = ValuationVerdict.SPECULATIVE
            rationale_parts.append("No positive earnings - pure growth play")
            if revenue_growth:
                rationale_parts.append(f"Revenue growing {revenue_growth:.0f}% YoY")
            assessment.rationale = ". ".join(rationale_parts)
            return assessment

        # Calculate PE vs historical average
        if pe_5y_avg and pe_5y_avg > 0:
            pe_vs_history = ((current_pe / pe_5y_avg) - 1) * 100
            assessment.pe_vs_history = pe_vs_history
            
            if pe_vs_history > self.PREMIUM_THRESHOLD:
                rationale_parts.append(f"Trading {pe_vs_history:.0f}% above 5Y avg P/E")
            elif pe_vs_history < self.DISCOUNT_THRESHOLD:
                rationale_parts.append(f"Trading {abs(pe_vs_history):.0f}% below 5Y avg P/E")

        # Calculate implied growth rate
        # Simple model: Implied growth ≈ (P/E - market_pe) / PEG_assumption
        # More sophisticated: Reverse DCF would be better but needs more inputs
        if current_pe and pe_sector_avg and pe_sector_avg > 0:
            pe_premium = current_pe / pe_sector_avg
            # Rough implied growth = (PE premium - 1) * base_growth_rate
            # Assume sector grows at 10% as baseline
            implied_growth = (pe_premium - 1) * 30 + 10  # Simplified
            implied_growth = max(0, min(100, implied_growth))  # Clamp
            assessment.implied_growth = implied_growth
            
            if implied_growth > self.HIGH_IMPLIED_GROWTH:
                rationale_parts.append(f"Implies {implied_growth:.0f}% growth to justify valuation")

        # Scenario analysis
        if current_price and target_price_bull:
            assessment.bull_upside = ((target_price_bull / current_price) - 1) * 100
        if current_price and target_price_bear:
            assessment.bear_downside = ((target_price_bear / current_price) - 1) * 100

        # Determine verdict
        verdict = self._determine_verdict(
            pe_vs_history=assessment.pe_vs_history,
            implied_growth=assessment.implied_growth,
            revenue_growth=revenue_growth,
            earnings_growth=earnings_growth
        )
        assessment.verdict = verdict

        # Build rationale
        if verdict == ValuationVerdict.PRICED_IN:
            rationale_parts.append("Market already pricing in significant growth")
        elif verdict == ValuationVerdict.UNDERAPPRECIATED:
            rationale_parts.append("Valuation doesn't fully reflect growth potential")
        elif verdict == ValuationVerdict.FAIR_VALUE:
            rationale_parts.append("Reasonably priced for current growth trajectory")

        assessment.rationale = ". ".join(rationale_parts) if rationale_parts else "Insufficient data for full assessment"
        
        return assessment

    def _determine_verdict(
        self,
        pe_vs_history: Optional[float],
        implied_growth: Optional[float],
        revenue_growth: Optional[float],
        earnings_growth: Optional[float]
    ) -> ValuationVerdict:
        """Determine valuation verdict based on metrics."""
        
        # High premium + high implied growth = PRICED IN
        if pe_vs_history is not None and pe_vs_history > self.PREMIUM_THRESHOLD:
            if implied_growth and implied_growth > self.HIGH_IMPLIED_GROWTH:
                return ValuationVerdict.PRICED_IN
            return ValuationVerdict.PRICED_IN  # Premium alone is concerning
        
        # Discount to history = potentially UNDERAPPRECIATED
        if pe_vs_history is not None and pe_vs_history < self.DISCOUNT_THRESHOLD:
            # But check if growth is actually there
            if revenue_growth and revenue_growth > 15:
                return ValuationVerdict.UNDERAPPRECIATED
            if earnings_growth and earnings_growth > 15:
                return ValuationVerdict.UNDERAPPRECIATED
            # Discount but no growth = could be value trap
            return ValuationVerdict.FAIR_VALUE
        
        # Growth exceeds implied expectations = UNDERAPPRECIATED
        if implied_growth and revenue_growth:
            if revenue_growth > implied_growth * 1.5:
                return ValuationVerdict.UNDERAPPRECIATED
        
        # Default to FAIR VALUE
        return ValuationVerdict.FAIR_VALUE

    def analyze_portfolio(
        self,
        stocks: list[dict]
    ) -> tuple[list[ValuationAssessment], str]:
        """
        Analyze multiple stocks and generate summary.
        
        Args:
            stocks: List of dicts with stock data
            
        Returns:
            Tuple of (assessments list, markdown summary)
        """
        assessments = []
        for stock in stocks:
            assessment = self.assess(**stock)
            assessments.append(assessment)

        # Sort: UNDERAPPRECIATED first, then FAIR_VALUE, then PRICED_IN
        verdict_order = {
            ValuationVerdict.UNDERAPPRECIATED: 0,
            ValuationVerdict.FAIR_VALUE: 1,
            ValuationVerdict.PRICED_IN: 2,
            ValuationVerdict.SPECULATIVE: 3,
            ValuationVerdict.UNKNOWN: 4
        }
        assessments.sort(key=lambda a: verdict_order[a.verdict])

        markdown = self._generate_markdown(assessments)
        return assessments, markdown

    def _generate_markdown(self, assessments: list[ValuationAssessment]) -> str:
        """Generate markdown summary of valuation analysis."""
        if not assessments:
            return ""

        # Count by verdict
        counts = {}
        for a in assessments:
            counts[a.verdict] = counts.get(a.verdict, 0) + 1

        lines = [
            "## Valuation Reality Check",
            "",
            f"**Summary**: {counts.get(ValuationVerdict.UNDERAPPRECIATED, 0)} underappreciated, "
            f"{counts.get(ValuationVerdict.FAIR_VALUE, 0)} fair value, "
            f"{counts.get(ValuationVerdict.PRICED_IN, 0)} priced in, "
            f"{counts.get(ValuationVerdict.SPECULATIVE, 0)} speculative",
            "",
        ]

        # Highlight underappreciated (buy candidates)
        underappreciated = [a for a in assessments if a.verdict == ValuationVerdict.UNDERAPPRECIATED]
        if underappreciated:
            lines.append("### 🟢 Underappreciated (Consider Accumulating)")
            lines.append("")
            for item in underappreciated:
                lines.append(f"- **{item.ticker}** ({item.company}): {item.rationale}")
            lines.append("")

        # Highlight priced in (be careful)
        priced_in = [a for a in assessments if a.verdict == ValuationVerdict.PRICED_IN]
        if priced_in:
            lines.append("### 🔴 Priced In (Wait for Pullback)")
            lines.append("")
            for item in priced_in:
                lines.append(f"- **{item.ticker}** ({item.company}): {item.rationale}")
            lines.append("")

        # Full table
        lines.extend([
            "### Detailed Valuation Table",
            "",
            "| Ticker | Company | P/E | 5Y Avg | vs History | Implied Growth | Verdict |",
            "|--------|---------|-----|--------|------------|----------------|---------|"
        ])
        
        for assessment in assessments:
            lines.append(assessment.to_markdown_row())

        lines.append("")
        lines.append("*Implied Growth = growth rate the market is pricing in based on current multiples*")
        lines.append("")
        
        return "\n".join(lines)


# Convenience function
def check_valuations(stocks: list[dict]) -> str:
    """
    Quick valuation check returning markdown.
    
    Example:
        result = check_valuations([
            {"ticker": "NVDA", "company": "NVIDIA", "current_pe": 45, "pe_5y_avg": 35, "pe_sector_avg": 25},
            {"ticker": "INTC", "company": "Intel", "current_pe": 12, "pe_5y_avg": 15, "pe_sector_avg": 25}
        ])
    """
    checker = ValuationChecker()
    _, markdown = checker.analyze_portfolio(stocks)
    return markdown
