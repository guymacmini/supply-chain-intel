"""Tests for data models."""

import pytest
from datetime import datetime

from src.models import (
    WatchlistEntity,
    Thesis,
    ThesisStatus,
    Claim,
    ConfidenceLevel,
    ResearchOpportunity,
    NewsItem
)


class TestWatchlistEntity:
    """Tests for WatchlistEntity model."""

    def test_create_entity(self):
        """Test creating a watchlist entity."""
        entity = WatchlistEntity(
            ticker="NVDA",
            name="NVIDIA Corporation",
            themes=["AI", "semiconductors"],
            added_date="2026-01-28"
        )
        assert entity.ticker == "NVDA"
        assert entity.name == "NVIDIA Corporation"
        assert "AI" in entity.themes
        assert entity.source_research is None

    def test_to_dict(self):
        """Test converting entity to dictionary."""
        entity = WatchlistEntity(
            ticker="ASML",
            name="ASML Holding",
            themes=["semiconductors"],
            added_date="2026-01-28",
            source_research="research_20260128.md"
        )
        data = entity.to_dict()
        assert data["ticker"] == "ASML"
        assert data["source_research"] == "research_20260128.md"

    def test_from_dict(self):
        """Test creating entity from dictionary."""
        data = {
            "ticker": "VRT",
            "name": "Vertiv Holdings",
            "themes": ["data_centers"],
            "added_date": "2026-01-28"
        }
        entity = WatchlistEntity.from_dict(data)
        assert entity.ticker == "VRT"
        assert entity.themes == ["data_centers"]


class TestClaim:
    """Tests for Claim model."""

    def test_create_claim(self):
        """Test creating a claim."""
        claim = Claim(
            statement="AI demand is accelerating",
            confidence=ConfidenceLevel.SUPPORTED,
            supporting_evidence=["Evidence 1", "Evidence 2"],
            contradicting_evidence=["Counter 1"]
        )
        assert claim.confidence == ConfidenceLevel.SUPPORTED
        assert len(claim.supporting_evidence) == 2

    def test_claim_to_dict(self):
        """Test converting claim to dictionary."""
        claim = Claim(
            statement="Test claim",
            confidence=ConfidenceLevel.VERIFIED
        )
        data = claim.to_dict()
        assert data["confidence"] == "verified"


class TestThesis:
    """Tests for Thesis model."""

    def test_create_thesis(self):
        """Test creating a thesis."""
        thesis = Thesis(
            id="vrt_thesis_20260128",
            statement="VRT is undervalued",
            status=ThesisStatus.ACTIVE,
            confidence=72,
            created="2026-01-28T10:00:00",
            updated="2026-01-28T10:00:00",
            triggers=["hyperscaler capex"],
            entities=["VRT", "MSFT"]
        )
        assert thesis.status == ThesisStatus.ACTIVE
        assert thesis.confidence == 72
        assert "VRT" in thesis.entities

    def test_thesis_frontmatter(self):
        """Test generating thesis frontmatter."""
        thesis = Thesis(
            id="test_thesis",
            statement="Test",
            status=ThesisStatus.ACTIVE,
            confidence=50,
            created="2026-01-28T10:00:00",
            updated="2026-01-28T10:00:00"
        )
        frontmatter = thesis.to_frontmatter()
        assert frontmatter["status"] == "active"
        assert frontmatter["confidence"] == 50


class TestResearchOpportunity:
    """Tests for ResearchOpportunity model."""

    def test_create_opportunity(self):
        """Test creating a research opportunity."""
        opp = ResearchOpportunity(
            ticker="AMAT",
            name="Applied Materials",
            relationship="Equipment supplier to TSMC",
            order=2,
            exposure_level="high",
            rationale="Benefits from TSMC expansion",
            risks=["Cyclical business"]
        )
        assert opp.order == 2
        assert opp.exposure_level == "high"

    def test_opportunity_to_dict(self):
        """Test converting opportunity to dictionary."""
        opp = ResearchOpportunity(
            ticker="TEST",
            name="Test Corp",
            relationship="supplier",
            order=1,
            exposure_level="medium",
            rationale="Test rationale"
        )
        data = opp.to_dict()
        assert data["ticker"] == "TEST"
        assert data["risks"] == []


class TestNewsItem:
    """Tests for NewsItem model."""

    def test_create_news_item(self):
        """Test creating a news item."""
        news = NewsItem(
            title="NVDA beats earnings",
            source="reuters.com",
            url="https://reuters.com/article/nvda",
            published_date="2026-01-28",
            relevance_score=9,
            summary="Strong AI demand drives results",
            matched_entities=["NVDA"],
            matched_triggers=["AI demand"]
        )
        assert news.relevance_score == 9
        assert "NVDA" in news.matched_entities
