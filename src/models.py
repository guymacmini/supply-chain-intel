"""Data models for Supply Chain Intel."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json


class ThesisStatus(Enum):
    """Status of an investment thesis."""
    ACTIVE = "active"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    ARCHIVED = "archived"


class ConfidenceLevel(Enum):
    """Confidence level for claims."""
    VERIFIED = "verified"
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"


@dataclass
class WatchlistEntity:
    """Entity being monitored in the watchlist."""
    ticker: str
    name: str
    themes: list[str]
    added_date: str
    source_research: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "themes": self.themes,
            "added_date": self.added_date,
            "source_research": self.source_research
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WatchlistEntity":
        return cls(
            ticker=data["ticker"],
            name=data["name"],
            themes=data.get("themes", []),
            added_date=data["added_date"],
            source_research=data.get("source_research")
        )


@dataclass
class Claim:
    """A testable claim extracted from a thesis."""
    statement: str
    confidence: ConfidenceLevel
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "statement": self.statement,
            "confidence": self.confidence.value,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence
        }


@dataclass
class ThesisTrigger:
    """A monitoring trigger for a thesis."""
    keyword: str
    description: str
    last_fired: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "keyword": self.keyword,
            "description": self.description,
            "last_fired": self.last_fired
        }


@dataclass
class Thesis:
    """Investment thesis with validation data."""
    id: str
    statement: str
    status: ThesisStatus
    confidence: int
    created: str
    updated: str
    claims: list[Claim] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    key_assumptions: list[str] = field(default_factory=list)
    risks: list[dict] = field(default_factory=list)
    counter_thesis: Optional[str] = None

    def to_frontmatter(self) -> dict:
        return {
            "id": self.id,
            "status": self.status.value,
            "confidence": self.confidence,
            "created": self.created,
            "updated": self.updated,
            "triggers": self.triggers,
            "entities": self.entities
        }


@dataclass
class ResearchOpportunity:
    """An investment opportunity discovered during research."""
    ticker: str
    name: str
    relationship: str
    order: int  # 1st, 2nd, or 3rd order
    exposure_level: str  # high, medium, low
    rationale: str
    risks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "relationship": self.relationship,
            "order": self.order,
            "exposure_level": self.exposure_level,
            "rationale": self.rationale,
            "risks": self.risks
        }


@dataclass
class NewsItem:
    """A news item from monitoring."""
    title: str
    source: str
    url: str
    published_date: str
    relevance_score: int
    summary: str
    matched_entities: list[str] = field(default_factory=list)
    matched_triggers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "published_date": self.published_date,
            "relevance_score": self.relevance_score,
            "summary": self.summary,
            "matched_entities": self.matched_entities,
            "matched_triggers": self.matched_triggers
        }
