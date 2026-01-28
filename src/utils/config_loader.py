"""Configuration loading utilities."""

import json
import os
from pathlib import Path
from typing import Any, Optional

import yaml


class ConfigLoader:
    """Loads and manages configuration files."""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent.parent / "config"
        else:
            self.config_dir = config_dir

    def load_json(self, filename: str) -> dict[str, Any]:
        """Load a JSON configuration file."""
        filepath = self.config_dir / filename
        if not filepath.exists():
            return {}
        with open(filepath, "r") as f:
            return json.load(f)

    def load_yaml(self, filename: str) -> dict[str, Any]:
        """Load a YAML configuration file."""
        filepath = self.config_dir / filename
        if not filepath.exists():
            return {}
        with open(filepath, "r") as f:
            return yaml.safe_load(f)

    def save_json(self, filename: str, data: dict[str, Any]) -> None:
        """Save data to a JSON configuration file."""
        filepath = self.config_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def get_sources(self) -> dict[str, list[str]]:
        """Get the news sources configuration."""
        return self.load_json("sources.json")

    def get_api_config(self) -> dict[str, Any]:
        """Get API configuration with defaults."""
        config = self.load_json("api.json")
        return {
            "model": config.get("model", "claude-opus-4-5-20251101"),
            "max_tokens": config.get("max_tokens", 16000),
            "temperature": config.get("temperature", 0.7)
        }

    def get_optional_api_keys(self) -> dict[str, Optional[str]]:
        """Get optional API keys from environment variables.

        Returns:
            dict with 'finnhub' and 'tavily' keys, values are None if not set
        """
        return {
            "finnhub": os.getenv("FINNHUB_API_KEY"),
            "tavily": os.getenv("TAVILY_API_KEY")
        }
