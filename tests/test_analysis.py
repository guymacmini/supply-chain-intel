"""Tests for analysis modules."""

import pytest
from src.analysis.shortage_analyzer import ShortageAnalyzer, ShortageSeverity
from src.analysis.valuation_checker import ValuationChecker, ValuationVerdict
from src.analysis.demand_analyzer import DemandAnalyzer, PricingPower


class TestShortageAnalyzer:
    """Tests for ShortageAnalyzer."""

    def test_critical_lead_time(self):
        """Long lead time should be CRITICAL."""
        analyzer = ShortageAnalyzer()
        result = analyzer.assess_component(
            component="Test Component",
            lead_time_months=9
        )
        assert result.severity == ShortageSeverity.CRITICAL

    def test_critical_single_source(self):
        """Single source should be CRITICAL."""
        analyzer = ShortageAnalyzer()
        result = analyzer.assess_component(
            component="Test Component",
            source_concentration="single-source"
        )
        assert result.severity == ShortageSeverity.CRITICAL

    def test_critical_high_utilization(self):
        """95% utilization should be CRITICAL."""
        analyzer = ShortageAnalyzer()
        result = analyzer.assess_component(
            component="Test Component",
            capacity_utilization=95
        )
        assert result.severity == ShortageSeverity.CRITICAL

    def test_watch_medium_lead_time(self):
        """3-6 month lead time should be WATCH."""
        analyzer = ShortageAnalyzer()
        result = analyzer.assess_component(
            component="Test Component",
            lead_time_months=4
        )
        assert result.severity == ShortageSeverity.WATCH

    def test_adequate_low_risk(self):
        """Low risk factors should be ADEQUATE."""
        analyzer = ShortageAnalyzer()
        result = analyzer.assess_component(
            component="Test Component",
            lead_time_months=1,
            capacity_utilization=60,
            source_concentration="diversified"
        )
        assert result.severity == ShortageSeverity.ADEQUATE

    def test_markdown_output(self):
        """Should generate valid markdown."""
        analyzer = ShortageAnalyzer()
        components = [
            {"component": "Critical Part", "lead_time_months": 9, "source_concentration": "single-source"},
            {"component": "Watch Part", "capacity_utilization": 85},
            {"component": "OK Part", "capacity_utilization": 50}
        ]
        _, markdown = analyzer.analyze_supply_chain(components)
        assert "🔴" in markdown
        assert "🟡" in markdown
        assert "🟢" in markdown
        assert "Critical Part" in markdown


class TestValuationChecker:
    """Tests for ValuationChecker."""

    def test_priced_in_high_premium(self):
        """High premium to history should be PRICED IN."""
        checker = ValuationChecker()
        result = checker.assess(
            ticker="TEST",
            company="Test Co",
            current_pe=50,
            pe_5y_avg=30,
            pe_sector_avg=25
        )
        assert result.verdict == ValuationVerdict.PRICED_IN

    def test_underappreciated_discount(self):
        """Discount to history with growth should be UNDERAPPRECIATED."""
        checker = ValuationChecker()
        result = checker.assess(
            ticker="TEST",
            company="Test Co",
            current_pe=15,
            pe_5y_avg=25,
            revenue_growth=30
        )
        assert result.verdict == ValuationVerdict.UNDERAPPRECIATED

    def test_speculative_no_earnings(self):
        """No earnings should be SPECULATIVE."""
        checker = ValuationChecker()
        result = checker.assess(
            ticker="TEST",
            company="Test Co",
            current_pe=None,
            revenue_growth=100
        )
        assert result.verdict == ValuationVerdict.SPECULATIVE

    def test_markdown_output(self):
        """Should generate valid markdown."""
        checker = ValuationChecker()
        stocks = [
            {"ticker": "NVDA", "company": "NVIDIA", "current_pe": 45, "pe_5y_avg": 35},
            {"ticker": "INTC", "company": "Intel", "current_pe": 12, "pe_5y_avg": 15, "revenue_growth": 20}
        ]
        _, markdown = checker.analyze_portfolio(stocks)
        assert "Valuation Reality Check" in markdown
        assert "NVDA" in markdown


class TestDemandAnalyzer:
    """Tests for DemandAnalyzer."""

    def test_high_demand_multiplier(self):
        """High multiplier should have high investment score."""
        analyzer = DemandAnalyzer()
        result = analyzer.assess_tier(
            tier_name="Test Tier",
            tier_level=1,
            demand_multiplier=2.5,
            scale_lead_time_months=24,
            current_utilization=95,
            pricing_power="high"
        )
        assert result.investment_score >= 70

    def test_low_investment_score(self):
        """Low multiplier and utilization should have low score."""
        analyzer = DemandAnalyzer()
        result = analyzer.assess_tier(
            tier_name="Commodity Tier",
            tier_level=3,
            demand_multiplier=0.5,
            scale_lead_time_months=3,
            current_utilization=50,
            pricing_power="low"
        )
        assert result.investment_score < 60

    def test_markdown_output(self):
        """Should generate valid markdown."""
        analyzer = DemandAnalyzer()
        tiers = [
            {
                "tier_name": "Advanced Packaging",
                "tier_level": 1,
                "demand_multiplier": 2.0,
                "current_utilization": 90,
                "pricing_power": "high"
            }
        ]
        _, markdown = analyzer.analyze_supply_chain(tiers)
        assert "Demand Acceleration" in markdown
        assert "Advanced Packaging" in markdown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
