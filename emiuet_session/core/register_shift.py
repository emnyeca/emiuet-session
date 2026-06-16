"""Register shift control.

The Emiuet Session has only 8 playable keys, so a fixed +/-12 octave jump is
often too large for melodic motion. The internal concept is therefore a
*register shift* with selectable step size, never a hard-coded octave. The
physical buttons may be labelled Oct+/Oct-, but software must not assume the
step is 12 semitones.

Up/Down move by the current mode's step size and accumulate; Reset returns to
neutral (0 semitones). The accumulated offset is applied to a note *at the
moment it is triggered* -- changing the register never retunes a sounding note.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RegisterShiftMode(Enum):
    """Step size used by one Up/Down press."""

    OCTAVE = 12
    FIFTH_SLIDE = 7
    FOURTH_SLIDE = 5
    CUSTOM_SEMITONE = 0  # uses RegisterShift.custom_step

    # Reserved future modes (scale/diatonic-aware windows) are documented in
    # docs/emiuet_session_architecture.md and intentionally not implemented yet.


@dataclass
class RegisterShift:
    mode: RegisterShiftMode = RegisterShiftMode.OCTAVE
    custom_step: int = 1  # semitones per press when mode is CUSTOM_SEMITONE
    steps: int = 0  # signed accumulated steps (each step == one Up/Down press)

    @property
    def step_size(self) -> int:
        if self.mode is RegisterShiftMode.CUSTOM_SEMITONE:
            return self.custom_step
        return self.mode.value

    @property
    def offset_semitones(self) -> int:
        return self.steps * self.step_size

    def up(self) -> None:
        self.steps += 1

    def down(self) -> None:
        self.steps -= 1

    def reset(self) -> None:
        self.steps = 0

    def set_mode(self, mode: RegisterShiftMode, custom_step: int | None = None) -> None:
        """Switch step-size mode. Resets accumulation so behaviour is predictable."""
        self.mode = mode
        if custom_step is not None:
            self.custom_step = custom_step
        self.steps = 0

    def label(self) -> str:
        """Short label for DisplayState, e.g. ``REG +7`` or ``FIFTH+7``."""
        prefix = {
            RegisterShiftMode.OCTAVE: "OCT",
            RegisterShiftMode.FIFTH_SLIDE: "5TH",
            RegisterShiftMode.FOURTH_SLIDE: "4TH",
            RegisterShiftMode.CUSTOM_SEMITONE: "CUS",
        }[self.mode]
        off = self.offset_semitones
        sign = "+" if off >= 0 else ""
        return f"{prefix}{sign}{off}"
