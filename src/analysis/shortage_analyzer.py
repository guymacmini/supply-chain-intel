"""
Shortage and Bottleneck Analyzer

Identifies supply chain chokepoints and scores severity for investment research.
Severity levels:
- 🔴 CRITICAL: 6+ month lead times, single-source, high impact
- 🟡 WATCH: Tightening supply, concentrated but not critical
- 🟢 ADEQUATE: Sufficient capacity, diversified supply
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json


class ShortageSeverity(Enum):
    """Shortage severity levels with emoji indicators."""
    CRITICAL = "🔴"
    WATCH = "🟡"
    ADEQUATE = "🟢"
    UNKNOWN = "⚪"

    def __str__(self):
        return f"{self.value} {self.name}"


@dataclass
class BottleneckAssessment:
    """Assessment of a single supply chain bottleneck."""
    component: str
    severity: ShortageSeverity
    lead_time_months: Optional[float] = None
    source_concentration: Optional[str] = None  # e.g., "single-source", "dual-source", "diversified"
    geographic_risk: Optional[str] = None  # e.g., "Taiwan", "China", "diversified"
    capacity_utilization: Optional[float] = None  # 0-100%
    new_capacity_date: Optional[str] = None  # When new supply comes online
    affected_companies: list[str] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> dict:
        return {
            "component": self.component,
            "severity": self.severity.name,
            "severity_emoji": self.severity.value,
            "lead_time_months": self.lead_time_months,
            "source_concentration": self.source_concentration,
            "geographic_risk": self.geographic_risk,
            "capacity_utilization": self.capacity_utilization,
            "new_capacity_date": self.new_capacity_date,
            "affected_companies": self.affected_companies,
            "notes": self.notes
        }

    def to_markdown_row(self) -> str:
        """Generate markdown table row."""
        lead = f"{self.lead_time_months}mo" if self.lead_time_months else "-"
        util = f"{self.capacity_utilization:.0f}%" if self.capacity_utilization else "-"
        geo = self.geographic_risk or "-"
        affected = ", ".join(self.affected_companies[:3]) if self.affected_companies else "-"
        if len(self.affected_companies) > 3:
            affected += f" +{len(self.affected_companies)-3}"
        
        return f"| {self.severity.value} | {self.component} | {lead} | {util} | {geo} | {affected} |"


class ShortageAnalyzer:
    """
    Analyzes supply chain data to identify and score bottlenecks.
    
    Usage:
        analyzer = ShortageAnalyzer()
        assessment = analyzer.assess_component(
            component="Advanced GPU chips",
            lead_time_months=9,
            source_concentration="dual-source",
            geographic_risk="Taiwan",
            capacity_utilization=95
        )
        print(assessment.severity)  # 🔴 CRITICAL
    """

    # Thresholds for severity scoring
    CRITICAL_LEAD_TIME = 6  # months
    WATCH_LEAD_TIME = 3
    
    CRITICAL_UTILIZATION = 90  # %
    WATCH_UTILIZATION = 80
    
    HIGH_RISK_GEOS = {"Taiwan", "China", "South Korea"}
    CRITICAL_CONCENTRATION = {"single-source", "single source", "monopoly"}
    WATCH_CONCENTRATION = {"dual-source", "dual source", "duopoly", "concentrated"}

    def assess_component(
        self,
        component: str,
        lead_time_months: Optional[float] = None,
        source_concentration: Optional[str] = None,
        geographic_risk: Optional[str] = None,
        capacity_utilization: Optional[float] = None,
        new_capacity_date: Optional[str] = None,
        affected_companies: Optional[list[str]] = None,
        notes: str = ""
    ) -> BottleneckAssessment:
        """
        Assess a single component for shortage severity.
        
        Scoring logic:
        - CRITICAL if ANY: lead_time >= 6mo, single-source, utilization >= 90%
        - WATCH if ANY: lead_time >= 3mo, dual-source, utilization >= 80%, high-risk geo
        - ADEQUATE otherwise
        """
        severity = ShortageSeverity.ADEQUATE
        risk_factors = []

        # Lead time scoring
        if lead_time_months is not None:
            if lead_time_months >= self.CRITICAL_LEAD_TIME:
                severity = ShortageSeverity.CRITICAL
                risk_factors.append(f"Long lead time ({lead_time_months}mo)")
            elif lead_time_months >= self.WATCH_LEAD_TIME:
                if severity != ShortageSeverity.CRITICAL:
                    severity = ShortageSeverity.WATCH
                risk_factors.append(f"Extended lead time ({lead_time_months}mo)")

        # Source concentration scoring
        if source_concentration:
            conc_lower = source_concentration.lower()
            if any(c in conc_lower for c in self.CRITICAL_CONCENTRATION):
                severity = ShortageSeverity.CRITICAL
                risk_factors.append(f"Single-source dependency")
            elif any(c in conc_lower for c in self.WATCH_CONCENTRATION):
                if severity != ShortageSeverity.CRITICAL:
                    severity = ShortageSeverity.WATCH
                risk_factors.append(f"Concentrated supply")

        # Capacity utilization scoring
        if capacity_utilization is not None:
            if capacity_utilization >= self.CRITICAL_UTILIZATION:
                severity = ShortageSeverity.CRITICAL
                risk_factors.append(f"Near-full utilization ({capacity_utilization:.0f}%)")
            elif capacity_utilization >= self.WATCH_UTILIZATION:
                if severity != ShortageSeverity.CRITICAL:
                    severity = ShortageSeverity.WATCH
                risk_factors.append(f"High utilization ({capacity_utilization:.0f}%)")

        # Geographic risk scoring (only elevates to WATCH, not CRITICAL alone)
        if geographic_risk and geographic_risk in self.HIGH_RISK_GEOS:
            if severity == ShortageSeverity.ADEQUATE:
                severity = ShortageSeverity.WATCH
            risk_factors.append(f"Geographic concentration ({geographic_risk})")

        # Build notes from risk factors
        auto_notes = "; ".join(risk_factors) if risk_factors else "No significant constraints"
        final_notes = f"{auto_notes}. {notes}".strip() if notes else auto_notes

        return BottleneckAssessment(
            component=component,
            severity=severity,
            lead_time_months=lead_time_months,
            source_concentration=source_concentration,
            geographic_risk=geographic_risk,
            capacity_utilization=capacity_utilization,
            new_capacity_date=new_capacity_date,
            affected_companies=affected_companies or [],
            notes=final_notes
        )

    def analyze_supply_chain(
        self,
        components: list[dict]
    ) -> tuple[list[BottleneckAssessment], str]:
        """
        Analyze multiple components and generate summary.
        
        Args:
            components: List of dicts with component data
            
        Returns:
            Tuple of (assessments list, markdown summary)
        """
        assessments = []
        for comp in components:
            assessment = self.assess_component(**comp)
            assessments.append(assessment)

        # Sort by severity (CRITICAL first)
        severity_order = {
            ShortageSeverity.CRITICAL: 0,
            ShortageSeverity.WATCH: 1,
            ShortageSeverity.ADEQUATE: 2,
            ShortageSeverity.UNKNOWN: 3
        }
        assessments.sort(key=lambda a: severity_order[a.severity])

        # Generate markdown
        markdown = self._generate_markdown(assessments)
        
        return assessments, markdown

    def _generate_markdown(self, assessments: list[BottleneckAssessment]) -> str:
        """Generate markdown summary of bottleneck analysis."""
        if not assessments:
            return ""

        # Count by severity
        critical = sum(1 for a in assessments if a.severity == ShortageSeverity.CRITICAL)
        watch = sum(1 for a in assessments if a.severity == ShortageSeverity.WATCH)
        adequate = sum(1 for a in assessments if a.severity == ShortageSeverity.ADEQUATE)

        lines = [
            "## Supply Chain Bottleneck Analysis",
            "",
            f"**Summary**: {critical} critical, {watch} watch, {adequate} adequate",
            "",
        ]

        # Critical alerts at top
        critical_items = [a for a in assessments if a.severity == ShortageSeverity.CRITICAL]
        if critical_items:
            lines.append("### 🔴 Critical Bottlenecks")
            lines.append("")
            for item in critical_items:
                lines.append(f"- **{item.component}**: {item.notes}")
            lines.append("")

        # Watch items
        watch_items = [a for a in assessments if a.severity == ShortageSeverity.WATCH]
        if watch_items:
            lines.append("### 🟡 Watch List")
            lines.append("")
            for item in watch_items:
                lines.append(f"- **{item.component}**: {item.notes}")
            lines.append("")

        # Full table
        lines.extend([
            "### Detailed Assessment",
            "",
            "| Status | Component | Lead Time | Utilization | Geo Risk | Affected |",
            "|--------|-----------|-----------|-------------|----------|----------|"
        ])
        
        for assessment in assessments:
            lines.append(assessment.to_markdown_row())

        lines.append("")
        
        return "\n".join(lines)

    def to_json(self, assessments: list[BottleneckAssessment]) -> str:
        """Export assessments to JSON."""
        return json.dumps(
            [a.to_dict() for a in assessments],
            indent=2
        )


# Convenience function for quick analysis
def analyze_bottlenecks(components: list[dict]) -> str:
    """
    Quick bottleneck analysis returning markdown.
    
    Example:
        result = analyze_bottlenecks([
            {"component": "HBM3 Memory", "lead_time_months": 9, "source_concentration": "dual-source"},
            {"component": "CoWoS Packaging", "capacity_utilization": 95, "geographic_risk": "Taiwan"}
        ])
    """
    analyzer = ShortageAnalyzer()
    _, markdown = analyzer.analyze_supply_chain(components)
    return markdown
