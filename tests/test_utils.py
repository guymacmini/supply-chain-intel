"""Tests for utility modules."""

import json
import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from src.utils.config_loader import ConfigLoader
from src.utils.watchlist_manager import WatchlistManager
from src.utils.markdown_generator import MarkdownGenerator
from src.models import WatchlistEntity


class TestConfigLoader:
    """Tests for ConfigLoader."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_load_json_missing_file(self, temp_config_dir):
        """Test loading a missing JSON file returns empty dict."""
        loader = ConfigLoader(config_dir=temp_config_dir)
        result = loader.load_json("nonexistent.json")
        assert result == {}

    def test_load_json_existing_file(self, temp_config_dir):
        """Test loading an existing JSON file."""
        test_data = {"key": "value", "list": [1, 2, 3]}
        filepath = temp_config_dir / "test.json"
        with open(filepath, "w") as f:
            json.dump(test_data, f)

        loader = ConfigLoader(config_dir=temp_config_dir)
        result = loader.load_json("test.json")
        assert result == test_data

    def test_save_json(self, temp_config_dir):
        """Test saving JSON data."""
        loader = ConfigLoader(config_dir=temp_config_dir)
        test_data = {"test": "data"}
        loader.save_json("output.json", test_data)

        filepath = temp_config_dir / "output.json"
        assert filepath.exists()
        with open(filepath) as f:
            loaded = json.load(f)
        assert loaded == test_data

    def test_get_api_config_defaults(self, temp_config_dir):
        """Test API config returns defaults when no file exists."""
        loader = ConfigLoader(config_dir=temp_config_dir)
        config = loader.get_api_config()
        assert config["model"] == "claude-opus-4-5-20251101"
        assert config["max_tokens"] == 16000
        assert config["temperature"] == 0.7


class TestWatchlistManager:
    """Tests for WatchlistManager."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_add_entity(self, temp_data_dir):
        """Test adding an entity to watchlist."""
        manager = WatchlistManager(data_dir=temp_data_dir)
        entity = WatchlistEntity(
            ticker="NVDA",
            name="NVIDIA",
            themes=["AI"],
            added_date="2026-01-28"
        )
        result = manager.add(entity)
        assert result is True

        # Verify it was added
        entities = manager.get_all()
        assert len(entities) == 1
        assert entities[0].ticker == "NVDA"

    def test_add_duplicate_entity(self, temp_data_dir):
        """Test adding a duplicate entity returns False."""
        manager = WatchlistManager(data_dir=temp_data_dir)
        entity = WatchlistEntity(
            ticker="NVDA",
            name="NVIDIA",
            themes=["AI"],
            added_date="2026-01-28"
        )
        manager.add(entity)
        result = manager.add(entity)
        assert result is False

    def test_remove_entity(self, temp_data_dir):
        """Test removing an entity."""
        manager = WatchlistManager(data_dir=temp_data_dir)
        entity = WatchlistEntity(
            ticker="NVDA",
            name="NVIDIA",
            themes=["AI"],
            added_date="2026-01-28"
        )
        manager.add(entity)
        result = manager.remove("NVDA")
        assert result is True
        assert len(manager.get_all()) == 0

    def test_get_by_ticker(self, temp_data_dir):
        """Test getting entity by ticker."""
        manager = WatchlistManager(data_dir=temp_data_dir)
        entity = WatchlistEntity(
            ticker="ASML",
            name="ASML Holding",
            themes=["semiconductors"],
            added_date="2026-01-28"
        )
        manager.add(entity)

        result = manager.get_by_ticker("asml")  # Test case insensitivity
        assert result is not None
        assert result.name == "ASML Holding"

    def test_get_by_theme(self, temp_data_dir):
        """Test filtering by theme."""
        manager = WatchlistManager(data_dir=temp_data_dir)

        manager.add(WatchlistEntity(
            ticker="NVDA", name="NVIDIA", themes=["AI", "semiconductors"],
            added_date="2026-01-28"
        ))
        manager.add(WatchlistEntity(
            ticker="TSLA", name="Tesla", themes=["EV", "energy"],
            added_date="2026-01-28"
        ))

        ai_entities = manager.get_by_theme("AI")
        assert len(ai_entities) == 1
        assert ai_entities[0].ticker == "NVDA"

    def test_add_many(self, temp_data_dir):
        """Test adding multiple entities at once."""
        manager = WatchlistManager(data_dir=temp_data_dir)
        entities = [
            WatchlistEntity(ticker="A", name="A Corp", themes=[], added_date="2026-01-28"),
            WatchlistEntity(ticker="B", name="B Corp", themes=[], added_date="2026-01-28"),
            WatchlistEntity(ticker="C", name="C Corp", themes=[], added_date="2026-01-28"),
        ]
        count = manager.add_many(entities)
        assert count == 3
        assert len(manager.get_all()) == 3

    def test_remove_by_theme(self, temp_data_dir):
        """Test removing entities by theme."""
        manager = WatchlistManager(data_dir=temp_data_dir)

        manager.add(WatchlistEntity(
            ticker="NVDA", name="NVIDIA", themes=["AI"],
            added_date="2026-01-28"
        ))
        manager.add(WatchlistEntity(
            ticker="AMD", name="AMD", themes=["AI"],
            added_date="2026-01-28"
        ))
        manager.add(WatchlistEntity(
            ticker="TSLA", name="Tesla", themes=["EV"],
            added_date="2026-01-28"
        ))

        removed = manager.remove_by_theme("AI")
        assert removed == 2
        assert len(manager.get_all()) == 1


class TestMarkdownGenerator:
    """Tests for MarkdownGenerator."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_generate_research_doc(self, temp_output_dir):
        """Test generating a research document."""
        generator = MarkdownGenerator(output_dir=temp_output_dir)
        content = "# Research\n\nThis is research content."
        path = generator.generate_research_doc(
            theme="AI Infrastructure",
            content=content,
            metadata={"depth": 2}
        )
        assert path.exists()
        assert "ai_infrastructure" in path.name

    def test_generate_thesis_doc(self, temp_output_dir):
        """Test generating a thesis document."""
        generator = MarkdownGenerator(output_dir=temp_output_dir)
        content = "# Thesis\n\nThis is thesis content."
        metadata = {
            "id": "test_thesis",
            "status": "active",
            "confidence": 72
        }
        path = generator.generate_thesis_doc(
            thesis_id="test_thesis",
            content=content,
            metadata=metadata
        )
        assert path.exists()
        assert "active" in str(path)

    def test_generate_digest(self, temp_output_dir):
        """Test generating a monitoring digest."""
        generator = MarkdownGenerator(output_dir=temp_output_dir)
        content = "# Digest\n\nMonitoring results."
        path = generator.generate_digest(content)
        assert path.exists()
        assert "digest" in path.name

    def test_list_theses(self, temp_output_dir):
        """Test listing thesis files."""
        generator = MarkdownGenerator(output_dir=temp_output_dir)

        # Create some thesis files
        generator.generate_thesis_doc("thesis1", "Content 1", {"status": "active"})
        generator.generate_thesis_doc("thesis2", "Content 2", {"status": "active"})
        generator.generate_thesis_doc("thesis3", "Content 3", {"status": "confirmed"})

        active = generator.list_theses(status="active")
        assert len(active) == 2

        all_theses = generator.list_theses()
        assert len(all_theses) == 3
