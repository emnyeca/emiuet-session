"""Performance profiles (selected scale / colour hooks).

Profile switching is intentionally *not* the beginner main workflow -- it is a
model hook for later expansion. The runtime currently honours NORMAL fully and
treats the others as defined-but-reserved states so the data model and display
are ready without committing beginner UX to scale switching.
"""

from __future__ import annotations

from enum import Enum


class PerformanceProfile(Enum):
    NORMAL = "Normal"
    COLOR = "Color"
    OUTSIDE_UP = "OutsideUp"
    OUTSIDE_DOWN = "OutsideDown"
    DOMINANT_MOTION = "DominantMotion"

    def next(self) -> "PerformanceProfile":
        members = list(PerformanceProfile)
        return members[(members.index(self) + 1) % len(members)]
