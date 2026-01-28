"""Markdown generation utilities."""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import frontmatter


class MarkdownGenerator:
    """Generates markdown documents for research output."""

    def __init__(self, output_dir: Optional[Path] = None):
        if output_dir is None:
            self.output_dir = Path(__file__).parent.parent.parent / "data"
        else:
            self.output_dir = output_dir

    def generate_research_doc(
        self,
        theme: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> Path:
        """Generate a research document from exploration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_theme = theme.lower().replace(" ", "_").replace("/", "_")[:50]
        filename = f"{safe_theme}_{timestamp}.md"

        output_path = self.output_dir / "research" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc_metadata = {
            "theme": theme,
            "generated": datetime.now().isoformat(),
            "type": "research"
        }
        if metadata:
            doc_metadata.update(metadata)

        post = frontmatter.Post(content, **doc_metadata)

        with open(output_path, "w") as f:
            f.write(frontmatter.dumps(post))

        return output_path

    def generate_thesis_doc(
        self,
        thesis_id: str,
        content: str,
        metadata: dict[str, Any]
    ) -> Path:
        """Generate a thesis document."""
        filename = f"{thesis_id}.md"

        status = metadata.get("status", "active")
        output_path = self.output_dir / "theses" / status / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        post = frontmatter.Post(content, **metadata)

        with open(output_path, "w") as f:
            f.write(frontmatter.dumps(post))

        return output_path

    def generate_digest(self, content: str, metadata: Optional[dict[str, Any]] = None) -> Path:
        """Generate a monitoring digest."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_digest.md"

        output_path = self.output_dir / "digests" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc_metadata = {
            "generated": datetime.now().isoformat(),
            "type": "digest"
        }
        if metadata:
            doc_metadata.update(metadata)

        post = frontmatter.Post(content, **doc_metadata)

        with open(output_path, "w") as f:
            f.write(frontmatter.dumps(post))

        return output_path

    def load_thesis(self, thesis_id: str) -> Optional[tuple[dict[str, Any], str]]:
        """Load a thesis document by ID, searching all status directories."""
        for status in ["active", "confirmed", "refuted", "archived"]:
            filepath = self.output_dir / "theses" / status / f"{thesis_id}.md"
            if filepath.exists():
                post = frontmatter.load(filepath)
                return dict(post.metadata), post.content
        return None

    def list_theses(self, status: Optional[str] = None) -> list[Path]:
        """List thesis files, optionally filtered by status."""
        theses_dir = self.output_dir / "theses"
        if not theses_dir.exists():
            return []

        if status:
            status_dir = theses_dir / status
            if status_dir.exists():
                return list(status_dir.glob("*.md"))
            return []

        all_theses = []
        for status_dir in theses_dir.iterdir():
            if status_dir.is_dir():
                all_theses.extend(status_dir.glob("*.md"))
        return all_theses

    def list_research(self) -> list[Path]:
        """List all research documents."""
        research_dir = self.output_dir / "research"
        if not research_dir.exists():
            return []
        return list(research_dir.glob("*.md"))

    def list_digests(self) -> list[Path]:
        """List all digest documents."""
        digests_dir = self.output_dir / "digests"
        if not digests_dir.exists():
            return []
        return sorted(digests_dir.glob("*.md"), reverse=True)
