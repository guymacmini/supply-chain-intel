"""Hypothesis Agent for validating investment theses."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models import Thesis, ThesisStatus, Claim, ConfidenceLevel
from ..utils.config_loader import ConfigLoader
from ..utils.markdown_generator import MarkdownGenerator
from ..utils.watchlist_manager import WatchlistManager
from .base_agent import BaseAgent


HYPOTHESIS_SYSTEM_PROMPT = """You are an expert investment analyst tasked with validating investment hypotheses.

Your role is to objectively evaluate investment theses by:

1. **Parse the Thesis**: Break down the user's thesis into discrete, testable claims.

2. **Gather Evidence**: For each claim:
   - Search for supporting evidence from credible sources
   - Search for contradicting evidence (steel-man the counter-argument)
   - Note the source and recency of each piece of evidence

3. **Score Confidence**: For each claim, assign a confidence level:
   - VERIFIED: Multiple authoritative sources confirm
   - SUPPORTED: Good evidence supports, minor gaps
   - PARTIALLY_SUPPORTED: Mixed evidence, significant uncertainty
   - UNSUPPORTED: Little or contradicting evidence

4. **Identify Assumptions**: List key assumptions that must be true for the thesis to work.

5. **Assess Risks**: Identify risks that could break the thesis, with likelihood and impact.

6. **Construct Counter-Thesis**: Build the best possible bear case (steel-man the opposition).

7. **Calculate Overall Score**: Provide a 0-100 confidence score based on:
   - Clarity of thesis (20%)
   - Strength of supporting evidence (30%)
   - Weakness of contradicting evidence (20%)
   - Verifiability of claims (15%)
   - Risk/reward profile (15%)

8. **Generate Monitoring Triggers**: Create specific events/news to watch for.

Be rigorous and objective. Your job is to find the truth, not to confirm the user's beliefs."""


class HypothesisAgent(BaseAgent):
    """Agent for validating investment hypotheses."""

    def __init__(
        self,
        config_loader: Optional[ConfigLoader] = None,
        markdown_generator: Optional[MarkdownGenerator] = None,
        watchlist_manager: Optional[WatchlistManager] = None
    ):
        super().__init__(config_loader)
        self.markdown_generator = markdown_generator or MarkdownGenerator()
        self.watchlist_manager = watchlist_manager or WatchlistManager()

    def run(self, thesis_statement: str) -> Path:
        """
        Validate an investment thesis.

        Args:
            thesis_statement: The user's investment thesis to validate

        Returns:
            Path to the generated thesis document
        """
        user_prompt = f"""Please analyze and validate the following investment thesis:

**THESIS**: {thesis_statement}

Provide your analysis in the following markdown format:

# Thesis Validation Report

## Original Thesis
> {thesis_statement}

## Parsed Claims
[Break down the thesis into discrete, testable claims]

| # | Claim | Confidence | Status |
|---|-------|------------|--------|
[Number each claim with its confidence level and brief status]

## Evidence Analysis

### Claim 1: [Claim text]
**Confidence**: [VERIFIED/SUPPORTED/PARTIALLY_SUPPORTED/UNSUPPORTED]

**Supporting Evidence**:
- [Evidence 1 with source]
- [Evidence 2 with source]

**Contradicting Evidence**:
- [Counter-evidence 1 with source]
- [Counter-evidence 2 with source]

**Assessment**: [Brief analysis of the evidence]

[Repeat for each claim]

## Key Assumptions
| Assumption | Criticality | Monitoring Trigger |
|------------|-------------|-------------------|
[List assumptions that must be true]

## Risk Factors
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
[List risks to the thesis]

## Counter-Thesis (Steel-Man Bear Case)
[Present the strongest possible argument against this thesis]

## Confidence Score
**Overall Score**: [0-100]

| Component | Weight | Score | Weighted |
|-----------|--------|-------|----------|
| Clarity | 20% | [0-100] | [score] |
| Supporting Evidence | 30% | [0-100] | [score] |
| Counter-Evidence Weakness | 20% | [0-100] | [score] |
| Verifiability | 15% | [0-100] | [score] |
| Risk/Reward | 15% | [0-100] | [score] |
| **Total** | 100% | - | **[total]** |

**Reasoning**: [Explain the score]

## Monitoring Triggers
[List specific events/news to watch that would impact this thesis]
- Trigger 1: [description]
- Trigger 2: [description]

## Entities to Monitor
[List ticker symbols and companies mentioned]

Use web search to verify claims and gather current evidence."""

        # Call Claude with the hypothesis validation prompt
        response = self._call_claude(
            system_prompt=HYPOTHESIS_SYSTEM_PROMPT,
            user_message=user_prompt,
            max_tokens=self.api_config["max_tokens"]
        )

        # Extract the content
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        # Generate thesis ID
        thesis_id = self._generate_thesis_id(thesis_statement)

        # Extract metadata from the response
        confidence = self._extract_confidence_score(content)
        triggers = self._extract_triggers(content)
        entities = self._extract_entities(content)

        # Create thesis metadata
        now = datetime.now().isoformat()
        metadata = {
            "id": thesis_id,
            "status": "active",
            "confidence": confidence,
            "created": now,
            "updated": now,
            "triggers": triggers,
            "entities": entities,
            "model": self.api_config["model"]
        }

        # Generate the thesis document
        output_path = self.markdown_generator.generate_thesis_doc(
            thesis_id=thesis_id,
            content=content,
            metadata=metadata
        )

        # Add entities to watchlist
        self._update_watchlist(thesis_id, entities)

        return output_path

    def _generate_thesis_id(self, thesis: str) -> str:
        """Generate a unique thesis ID."""
        # Extract key terms and create ID
        words = re.findall(r'\b[A-Za-z]+\b', thesis.lower())
        # Take first few meaningful words
        key_words = [w for w in words if len(w) > 3][:3]
        base_id = "_".join(key_words) if key_words else "thesis"
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"{base_id}_{timestamp}"

    def _extract_confidence_score(self, content: str) -> int:
        """Extract the overall confidence score from the content."""
        # Look for patterns like "Overall Score: 72" or "**Overall Score**: 72"
        patterns = [
            r'\*\*Overall Score\*\*:\s*(\d+)',
            r'Overall Score:\s*(\d+)',
            r'\*\*Total\*\*.*?(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return int(match.group(1))
        return 50  # Default if not found

    def _extract_triggers(self, content: str) -> list[str]:
        """Extract monitoring triggers from the content."""
        triggers = []
        # Look for the triggers section
        trigger_section = re.search(
            r'## Monitoring Triggers\s*(.*?)(?=##|\Z)',
            content,
            re.DOTALL
        )
        if trigger_section:
            # Extract bullet points
            bullets = re.findall(r'[-*]\s*(?:Trigger \d+:\s*)?(.+)', trigger_section.group(1))
            triggers = [b.strip() for b in bullets if b.strip()]
        return triggers[:10]  # Limit to 10 triggers

    def _extract_entities(self, content: str) -> list[str]:
        """Extract ticker symbols from the content."""
        # Look for ticker patterns (1-5 uppercase letters)
        tickers = set(re.findall(r'\b([A-Z]{1,5})\b', content))
        # Filter out common words that look like tickers
        common_words = {'A', 'I', 'AND', 'THE', 'FOR', 'NOT', 'BUT', 'OR', 'IF', 'ALL', 'ARE', 'WAS', 'HAS', 'HAD'}
        return [t for t in tickers if t not in common_words][:20]

    def _update_watchlist(self, thesis_id: str, entities: list[str]) -> int:
        """Add thesis entities to the watchlist."""
        from ..models import WatchlistEntity

        today = datetime.now().strftime("%Y-%m-%d")
        watchlist_entities = []

        for ticker in entities:
            entity = WatchlistEntity(
                ticker=ticker,
                name=ticker,
                themes=[f"thesis_{thesis_id}"],
                added_date=today,
                source_research=f"theses/active/{thesis_id}.md"
            )
            watchlist_entities.append(entity)

        return self.watchlist_manager.add_many(watchlist_entities)

    def update_thesis(self, thesis_id: str, new_evidence: str) -> Optional[Path]:
        """Update an existing thesis with new evidence."""
        # Load existing thesis
        result = self.markdown_generator.load_thesis(thesis_id)
        if not result:
            return None

        metadata, content = result

        # Create update prompt
        user_prompt = f"""Please update this thesis with new evidence:

**Original Thesis Document**:
{content}

**New Evidence/Information**:
{new_evidence}

Please provide an updated analysis incorporating this new information.
Update the confidence score if warranted and note what changed."""

        response = self._call_claude(
            system_prompt=HYPOTHESIS_SYSTEM_PROMPT,
            user_message=user_prompt,
            max_tokens=self.api_config["max_tokens"]
        )

        # Extract updated content
        updated_content = ""
        for block in response.content:
            if block.type == "text":
                updated_content += block.text

        # Update metadata
        metadata["updated"] = datetime.now().isoformat()
        new_confidence = self._extract_confidence_score(updated_content)
        metadata["confidence"] = new_confidence

        # Save updated thesis
        return self.markdown_generator.generate_thesis_doc(
            thesis_id=thesis_id,
            content=updated_content,
            metadata=metadata
        )

    def resolve_thesis(
        self,
        thesis_id: str,
        confirmed: bool,
        reason: Optional[str] = None
    ) -> Optional[Path]:
        """Resolve a thesis as confirmed or refuted."""
        result = self.markdown_generator.load_thesis(thesis_id)
        if not result:
            return None

        metadata, content = result

        # Update status
        new_status = "confirmed" if confirmed else "refuted"
        metadata["status"] = new_status
        metadata["resolved_date"] = datetime.now().isoformat()
        if reason:
            metadata["resolution_reason"] = reason

        # Add resolution note to content
        resolution_note = f"""

---
## Resolution

**Status**: {new_status.upper()}
**Date**: {datetime.now().strftime("%Y-%m-%d")}
**Reason**: {reason or "No reason provided"}
"""
        updated_content = content + resolution_note

        # Save to new location
        return self.markdown_generator.generate_thesis_doc(
            thesis_id=thesis_id,
            content=updated_content,
            metadata=metadata
        )
