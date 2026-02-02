import json
from pathlib import Path
from typing import List, Optional
from src.models import SavedResearch, SavedResearchStatus

class SavedResearchStore:
    def __init__(self, data_dir: Path):
        self.file_path = data_dir / "saved_research.json"
    
    def _load(self) -> List[dict]:
        if self.file_path.exists():
            return json.loads(self.file_path.read_text())
        return []
    
    def _save(self, data: List[dict]):
        self.file_path.write_text(json.dumps(data, indent=2))
    
    def get_all(self) -> List[SavedResearch]:
        return [SavedResearch.from_dict(d) for d in self._load()]
    
    def add(self, item: SavedResearch) -> bool:
        data = self._load()
        if any(d["filename"] == item.filename for d in data):
            return False
        data.append(item.to_dict())
        self._save(data)
        return True
    
    def update(self, filename: str, updates: dict) -> bool:
        data = self._load()
        for d in data:
            if d["filename"] == filename:
                d.update(updates)
                d["last_updated"] = __import__("datetime").datetime.now().isoformat()
                self._save(data)
                return True
        return False
    
    def remove(self, filename: str) -> bool:
        data = self._load()
        new_data = [d for d in data if d["filename"] != filename]
        if len(new_data) < len(data):
            self._save(new_data)
            return True
        return False