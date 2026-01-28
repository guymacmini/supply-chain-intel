"""Watchlist management utilities."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models import WatchlistEntity


class WatchlistManager:
    """Manages the entity watchlist."""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent.parent / "data"
        else:
            self.data_dir = data_dir
        self.watchlist_path = self.data_dir / "watchlist.json"

    def _load(self) -> dict:
        """Load the watchlist from disk."""
        if not self.watchlist_path.exists():
            return {"entities": [], "last_updated": None}
        with open(self.watchlist_path, "r") as f:
            return json.load(f)

    def _save(self, data: dict) -> None:
        """Save the watchlist to disk."""
        self.watchlist_path.parent.mkdir(parents=True, exist_ok=True)
        data["last_updated"] = datetime.now().isoformat()
        with open(self.watchlist_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_all(self) -> list[WatchlistEntity]:
        """Get all entities in the watchlist."""
        data = self._load()
        return [WatchlistEntity.from_dict(e) for e in data.get("entities", [])]

    def get_by_ticker(self, ticker: str) -> Optional[WatchlistEntity]:
        """Get an entity by ticker symbol."""
        entities = self.get_all()
        for entity in entities:
            if entity.ticker.upper() == ticker.upper():
                return entity
        return None

    def get_by_theme(self, theme: str) -> list[WatchlistEntity]:
        """Get entities matching a theme."""
        entities = self.get_all()
        theme_lower = theme.lower()
        return [e for e in entities if any(theme_lower in t.lower() for t in e.themes)]

    def add(self, entity: WatchlistEntity) -> bool:
        """Add an entity to the watchlist. Returns True if added, False if already exists."""
        data = self._load()
        entities = data.get("entities", [])

        # Check if already exists
        for e in entities:
            if e["ticker"].upper() == entity.ticker.upper():
                return False

        entities.append(entity.to_dict())
        data["entities"] = entities
        self._save(data)
        return True

    def add_many(self, entities: list[WatchlistEntity]) -> int:
        """Add multiple entities. Returns count of newly added entities."""
        data = self._load()
        existing = {e["ticker"].upper() for e in data.get("entities", [])}

        added = 0
        for entity in entities:
            if entity.ticker.upper() not in existing:
                data.setdefault("entities", []).append(entity.to_dict())
                existing.add(entity.ticker.upper())
                added += 1

        if added > 0:
            self._save(data)
        return added

    def remove(self, ticker: str) -> bool:
        """Remove an entity by ticker. Returns True if removed."""
        data = self._load()
        entities = data.get("entities", [])

        new_entities = [e for e in entities if e["ticker"].upper() != ticker.upper()]
        if len(new_entities) < len(entities):
            data["entities"] = new_entities
            self._save(data)
            return True
        return False

    def remove_by_theme(self, theme: str) -> int:
        """Remove all entities matching a theme. Returns count removed."""
        data = self._load()
        entities = data.get("entities", [])
        theme_lower = theme.lower()

        new_entities = [
            e for e in entities
            if not any(theme_lower in t.lower() for t in e.get("themes", []))
        ]
        removed = len(entities) - len(new_entities)

        if removed > 0:
            data["entities"] = new_entities
            self._save(data)
        return removed

    def update_themes(self, ticker: str, themes: list[str]) -> bool:
        """Update themes for an entity. Returns True if updated."""
        data = self._load()
        entities = data.get("entities", [])

        for entity in entities:
            if entity["ticker"].upper() == ticker.upper():
                entity["themes"] = themes
                self._save(data)
                return True
        return False
