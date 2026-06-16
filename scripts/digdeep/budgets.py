"""Soft research-effort profiles.

These mirror the Quick / Standard / Deep profiles the dig-deep orchestrator
uses to scale how wide and how many rounds a research run goes. They are
*advisory* — an orchestrator (or the AGENTS.md spec) reads them to decide how
hard to dig. The lanes themselves don't enforce them; the caller does.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Profile:
    name: str
    soft_minutes: Optional[int]   # rough wall-clock budget; None = take your time
    extra_lanes: int              # how many lanes beyond the initial web sweep
    rounds_per_lane: int          # iterative fan-out rounds per lane
    search_breadth: int           # search queries per lane pass
    fetch_breadth: int            # pages/threads to read per lane pass
    blurb: str


PROFILES = {
    "quick": Profile(
        name="quick", soft_minutes=5, extra_lanes=1, rounds_per_lane=1,
        search_breadth=4, fetch_breadth=6,
        blurb="Fast skim — web sweep plus at most one extra lane, single round.",
    ),
    "standard": Profile(
        name="standard", soft_minutes=12, extra_lanes=2, rounds_per_lane=2,
        search_breadth=6, fetch_breadth=10,
        blurb="Balanced dig — web sweep plus up to two lanes, a follow-up round each.",
    ),
    "deep": Profile(
        name="deep", soft_minutes=None, extra_lanes=4, rounds_per_lane=3,
        search_breadth=8, fetch_breadth=15,
        blurb="Exhaustive — every relevant lane, multiple rounds, until leads run dry.",
    ),
}

DEFAULT_PROFILE = "deep"

# Phrases an orchestrator can scan for in a user's question to pick a profile.
_HINTS = {
    "quick": ("quick", "fast", "skim", "tldr", "just a", "briefly", "5 min", "five min"),
    "standard": ("standard", "balanced", "10 min", "ten min", "decent", "moderate"),
    "deep": ("deep", "thorough", "exhaustive", "comprehensive", "take your time", "full picture"),
}


def get_profile(name: str) -> Profile:
    return PROFILES.get((name or "").strip().lower(), PROFILES[DEFAULT_PROFILE])


def classify(question: str) -> Profile:
    """Best-effort profile pick from a question's wording. Defaults to deep."""
    low = (question or "").lower()
    for key in ("quick", "standard", "deep"):
        if any(h in low for h in _HINTS[key]):
            return PROFILES[key]
    return PROFILES[DEFAULT_PROFILE]
