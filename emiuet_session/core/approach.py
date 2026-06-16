"""Approach +/- modifiers.

Two immediate-control modifiers bend the *next/affected* triggered note by a
semitone, giving the player chromatic approach motion without leaving the
8-key layout. This is an immediate performance gesture and is kept separate
from scale/profile switching (which may produce similar colour later).

Policies:
- MOMENTARY     : offset applies while the modifier is held (default).
- NEXT_NOTE_ONLY: offset applies to the next single trigger, then clears.
- HELD_TRANSFORM: reserved -- transform held notes too (future, not default).

Default is MOMENTARY. Full chromatic mode is never the default.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ApproachDirection(Enum):
    PLUS = 1
    MINUS = -1


class ApproachPolicy(Enum):
    MOMENTARY = "momentary"
    NEXT_NOTE_ONLY = "next_note_only"
    HELD_TRANSFORM = "held_transform"  # reserved / future


@dataclass
class ApproachState:
    policy: ApproachPolicy = ApproachPolicy.MOMENTARY
    direction: ApproachDirection | None = None  # currently engaged direction
    _armed_next: ApproachDirection | None = None  # for NEXT_NOTE_ONLY

    def press(self, direction: ApproachDirection) -> None:
        if self.policy is ApproachPolicy.NEXT_NOTE_ONLY:
            self._armed_next = direction
        else:
            self.direction = direction

    def release(self, direction: ApproachDirection) -> None:
        # Releasing only clears if it matches the active direction (ignores a
        # stale release for the opposite modifier).
        if self.policy is not ApproachPolicy.NEXT_NOTE_ONLY and self.direction is direction:
            self.direction = None

    def offset_for_trigger(self) -> int:
        """Semitone offset to apply to a note being triggered now.

        For NEXT_NOTE_ONLY the armed offset is consumed by this call.
        """
        if self.policy is ApproachPolicy.NEXT_NOTE_ONLY:
            armed = self._armed_next
            self._armed_next = None
            return armed.value if armed else 0
        return self.direction.value if self.direction else 0

    def label(self) -> str:
        active = self.direction or self._armed_next
        if active is ApproachDirection.PLUS:
            return "APP+"
        if active is ApproachDirection.MINUS:
            return "APP-"
        return "APP."
