"""
Demand Acceleration Analyzer

Identifies which supply chain tiers have the best demand multipliers and
ability to capture value when end markets accelerate.

Key metrics:
- Demand multiplier: If end market +10%, this tier grows X%
- Scale lead time: Months to add meaningful capacity
- Current utilization: How much headroom exists
- Pricing power: Can they raise prices in a shortage?
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json


class PricingPower(Enum):
    """Pricing power assessment."""
    HIGH = "high"      # Can raise prices, customers have no choice
    MEDIUM = "medium"  # Some pricing flexibility
    LOW = "low"        # Commodity, price taker
    UNKNOWN = "unknown"
    
    @property
    def emoji(self) -> str:
        return {
            PricingPower.HIGH: "💪",
            PricingPower.MEDIUM: "➡️",
            PricingPower.LOW: "⬇️",
            PricingPower.UNKNOWN: "❓"
        }.get(self, "❓")


class DemandAcceleration(Enum):
    """How much a tier accelerates vs end market."""
    AMPLIFIED = "amplified"      # Grows faster than end market (multiplier > 1.5)
    PROPORTIONAL = "proportional" # Grows with end market (multiplier 0.8-1.5)
    LAGGING = "lagging"          # Grows slower than end market (multiplier < 0.8)
    UNKNOWN = "unknown"


@dataclass
class DemandAssessment:
    """Assessment of demand acceleration for a supply chain tier/company."""
    tier_name: str
    tier_level: int  # 0=raw materials, 1=components, 2=subsystems, 3=integration, etc.
    
    # Core metrics
    demand_multiplier: Optional[float] = None  # 1.5 = grows 15% when end market grows 10%
    scale_lead_time_months: Optional[int] = None  # Time to add 20%+ capacity
    current_utilization: Optional[float] = None  # 0-100%
    pricing_power: PricingPower = PricingPower.UNKNOWN
    
    # Company-level details
    key_players: list[dict] = field(default_factory=list)  # [{company, ticker, share, headroom}]
    
    # Investment implications
    acceleration: DemandAcceleration = DemandAcceleration.UNKNOWN
    margin_expansion_potential: Optional[str] = None  # "high", "medium", "low"
    notes: str = ""
    
    def to_dict(self) -> dict:
        return {
            "tier_name": self.tier_name,
            "tier_level": self.tier_level,
            "demand_multiplier": self.demand_multiplier,
            "scale_lead_time_months": self.scale_lead_time_months,
            "current_utilization": self.current_utilization,
            "pricing_power": self.pricing_power.value,
            "key_players": self.key_players,
            "acceleration": self.acceleration.value,
            "margin_expansion_potential": self.margin_expansion_potential,
            "notes": self.notes
        }

    def to_markdown_row(self) -> str:
        """Generate markdown table row."""
        mult = f"{self.demand_multiplier:.1f}x" if self.demand_multiplier else "-"
        lead = f"{self.scale_lead_time_months}mo" if self.scale_lead_time_months else "-"
        util = f"{self.current_utilization:.0f}%" if self.current_utilization else "-"
        power = f"{self.pricing_power.emoji}" if self.pricing_power != PricingPower.UNKNOWN else "-"
        margin = self.margin_expansion_potential or "-"
        
        # Show top player
        top_player = "-"
        if self.key_players:
            p = self.key_players[0]
            top_player = f"{p.get('ticker', p.get('company', 'N/A'))}"
        
        return f"| T{self.tier_level} | {self.tier_name[:25]} | {mult} | {lead} | {util} | {power} | {margin} | {top_player} |"

    @property
    def investment_score(self) -> float:
        """
        Calculate investment attractiveness score (0-100).
        Higher = better risk/reward for demand acceleration play.
        """
        score = 50  # Base score
        
        # Demand multiplier (max +20)
        if self.demand_multiplier:
            if self.demand_multiplier > 2.0:
                score += 20
            elif self.demand_multiplier > 1.5:
                score += 15
            elif self.demand_multiplier > 1.0:
                score += 10
        
        # Utilization (max +15) - higher = more pricing power
        if self.current_utilization:
            if self.current_utilization > 90:
                score += 15
            elif self.current_utilization > 80:
                score += 10
            elif self.current_utilization > 70:
                score += 5
        
        # Lead time (max +15) - longer = better for incumbents
        if self.scale_lead_time_months:
            if self.scale_lead_time_months > 18:
                score += 15
            elif self.scale_lead_time_months > 12:
                score += 10
            elif self.scale_lead_time_months > 6:
                score += 5
        
        # Pricing power (max +10)
        if self.pricing_power == PricingPower.HIGH:
            score += 10
        elif self.pricing_power == PricingPower.MEDIUM:
            score += 5
        
        return min(100, max(0, score))


class DemandAnalyzer:
    """
    Analyzes demand acceleration potential across supply chain tiers.
    
    Usage:
        analyzer = DemandAnalyzer()
        assessment = analyzer.assess_tier(
            tier_name="Advanced GPU Packaging (CoWoS)",
            tier_level=1,
            demand_multiplier=2.0,
            scale_lead_time_months=24,
            current_utilization=95,
            pricing_power="high"
        )
        print(f"Investment score: {assessment.investment_score}")
    """

    def assess_tier(
        self,
        tier_name: str,
        tier_level: int,
        demand_multiplier: Optional[float] = None,
        scale_lead_time_months: Optional[int] = None,
        current_utilization: Optional[float] = None,
        pricing_power: Optional[str] = None,
        key_players: Optional[list[dict]] = None,
        notes: str = ""
    ) -> DemandAssessment:
        """
        Assess demand acceleration for a single tier.
        """
        # Parse pricing power
        pp = PricingPower.UNKNOWN
        if pricing_power:
            try:
                pp = PricingPower(pricing_power.lower())
            except ValueError:
                pass

        # Determine acceleration category
        acceleration = DemandAcceleration.UNKNOWN
        if demand_multiplier:
            if demand_multiplier > 1.5:
                acceleration = DemandAcceleration.AMPLIFIED
            elif demand_multiplier >= 0.8:
                acceleration = DemandAcceleration.PROPORTIONAL
            else:
                acceleration = DemandAcceleration.LAGGING

        # Determine margin expansion potential
        margin_potential = "low"
        if current_utilization and current_utilization > 85:
            if pp == PricingPower.HIGH:
                margin_potential = "high"
            elif pp == PricingPower.MEDIUM:
                margin_potential = "medium"
            else:
                margin_potential = "low"  # Commodity, can't raise prices
        elif current_utilization and current_utilization > 70:
            margin_potential = "medium" if pp != PricingPower.LOW else "low"

        # Auto-generate notes
        note_parts = []
        if acceleration == DemandAcceleration.AMPLIFIED:
            note_parts.append(f"Demand amplifies {demand_multiplier:.1f}x vs end market")
        if scale_lead_time_months and scale_lead_time_months > 12:
            note_parts.append(f"Long capacity lead time ({scale_lead_time_months}mo) protects incumbents")
        if current_utilization and current_utilization > 90:
            note_parts.append(f"Near full utilization ({current_utilization:.0f}%)")
        if pp == PricingPower.HIGH:
            note_parts.append("Strong pricing power")

        auto_notes = "; ".join(note_parts) if note_parts else "Standard demand characteristics"
        final_notes = f"{auto_notes}. {notes}".strip() if notes else auto_notes

        return DemandAssessment(
            tier_name=tier_name,
            tier_level=tier_level,
            demand_multiplier=demand_multiplier,
            scale_lead_time_months=scale_lead_time_months,
            current_utilization=current_utilization,
            pricing_power=pp,
            key_players=key_players or [],
            acceleration=acceleration,
            margin_expansion_potential=margin_potential,
            notes=final_notes
        )

    def analyze_supply_chain(
        self,
        tiers: list[dict]
    ) -> tuple[list[DemandAssessment], str]:
        """
        Analyze demand acceleration across multiple tiers.
        
        Args:
            tiers: List of dicts with tier data
            
        Returns:
            Tuple of (assessments list, markdown summary)
        """
        assessments = []
        for tier in tiers:
            assessment = self.assess_tier(**tier)
            assessments.append(assessment)

        # Sort by investment score (highest first)
        assessments.sort(key=lambda a: a.investment_score, reverse=True)

        markdown = self._generate_markdown(assessments)
        return assessments, markdown

    def _generate_markdown(self, assessments: list[DemandAssessment]) -> str:
        """Generate markdown summary of demand analysis."""
        if not assessments:
            return ""

        lines = [
            "## Demand Acceleration Analysis",
            "",
            "Which supply chain tiers benefit most when end-market demand accelerates?",
            "",
        ]

        # Top opportunities
        top_scores = [a for a in assessments if a.investment_score >= 70]
        if top_scores:
            lines.append("### 🎯 Best Demand Acceleration Plays")
            lines.append("")
            for item in top_scores[:5]:
                score_bar = "█" * int(item.investment_score / 10) + "░" * (10 - int(item.investment_score / 10))
                lines.append(f"- **{item.tier_name}** [{score_bar}] Score: {item.investment_score:.0f}")
                lines.append(f"  - {item.notes}")
                if item.key_players:
                    players = ", ".join([p.get('ticker', p.get('company', '?')) for p in item.key_players[:3]])
                    lines.append(f"  - Key players: {players}")
            lines.append("")

        # Full table
        lines.extend([
            "### Tier-by-Tier Analysis",
            "",
            "| Tier | Name | Demand Mult | Scale Time | Utilization | Pricing | Margin Pot | Top Player |",
            "|------|------|-------------|------------|-------------|---------|------------|------------|"
        ])
        
        for assessment in assessments:
            lines.append(assessment.to_markdown_row())

        lines.append("")
        lines.append("*Demand Mult = if end market grows 10%, this tier grows X%*")
        lines.append("*Pricing: 💪=high, ➡️=medium, ⬇️=low*")
        lines.append("")
        
        return "\n".join(lines)

    def to_json(self, assessments: list[DemandAssessment]) -> str:
        """Export assessments to JSON."""
        return json.dumps(
            [a.to_dict() for a in assessments],
            indent=2
        )


# Convenience function
def analyze_demand(tiers: list[dict]) -> str:
    """
    Quick demand analysis returning markdown.
    
    Example:
        result = analyze_demand([
            {
                "tier_name": "CoWoS Advanced Packaging",
                "tier_level": 1,
                "demand_multiplier": 2.0,
                "scale_lead_time_months": 24,
                "current_utilization": 95,
                "pricing_power": "high",
                "key_players": [{"company": "TSMC", "ticker": "TSM", "share": 90}]
            },
            {
                "tier_name": "Memory (HBM)",
                "tier_level": 1,
                "demand_multiplier": 1.8,
                "scale_lead_time_months": 18,
                "current_utilization": 85,
                "pricing_power": "medium"
            }
        ])
    """
    analyzer = DemandAnalyzer()
    _, markdown = analyzer.analyze_supply_chain(tiers)
    return markdown
