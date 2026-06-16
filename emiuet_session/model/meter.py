"""Meter and segment policy.

Manual segment advance is the default performance model: one Next press moves
the player forward by a musically sensible amount, and any chord changes inside
that span auto-advance by tempo. The aim is roughly one manual action every
1.0-2.0 s; we avoid designs that demand a Next press more often than ~800 ms.

This module does NOT try to infer groupings for every possible meter. It ships
presets for common meters plus a safe fallback, and supports explicit overrides
at the song level. All advance lengths are expressed in quarter-note beats (the
universal unit) so tempo math is uniform.
"""

from __future__ import annotations

from dataclasses import dataclass

# (numerator, denominator) -> (allowed_advance_beats, avoided_advance_beats)
# Lengths are in quarter-note beats.
_METER_TABLE: dict[tuple[int, int], tuple[tuple[float, ...], tuple[float, ...]]] = {
    (4, 4): ((1.0, 2.0, 4.0), (3.0,)),
    (3, 4): ((1.0, 3.0), (2.0,)),
    # 5/4 supports 2+3 and 3+2 groupings: advances of 2 and 3 are both allowed.
    (5, 4): ((1.0, 2.0, 3.0, 5.0), ()),
    # 6/8 is compound: dotted-quarter (1.5 quarter-beats) groupings or full bar.
    (6, 8): ((1.5, 3.0), ()),
}


@dataclass(frozen=True)
class MeterPolicy:
    numerator: int = 4
    denominator: int = 4

    @property
    def beats_per_bar(self) -> float:
        return self.numerator * (4.0 / self.denominator)

    def is_known(self) -> bool:
        return (self.numerator, self.denominator) in _METER_TABLE

    def allowed_advance_beats(self) -> tuple[float, ...]:
        if self.is_known():
            return _METER_TABLE[(self.numerator, self.denominator)][0]
        # Irregular/unknown: fall back to full bar, with single-beat as a safety
        # net. Explicit song-level overrides are handled by SegmentPolicy.
        full = self.beats_per_bar
        return tuple(sorted({full, 1.0}))

    def avoided_advance_beats(self) -> tuple[float, ...]:
        if self.is_known():
            return _METER_TABLE[(self.numerator, self.denominator)][1]
        return ()


@dataclass(frozen=True)
class SegmentPolicy:
    """Chooses how many beats one Next press covers, then groups chords.

    The choice targets a comfortable *manual operation interval*: roughly one
    Next press per second. Among the meter's allowed advance lengths, we pick the
    one whose duration at the current tempo is closest to ``ideal_manual_interval_s``
    (not simply the largest that fits). This gives the expected feel, e.g. 4/4 at
    120 BPM -> 2 beats, at 240 BPM -> 4 beats, at 60 BPM -> 1 beat.
    """

    ideal_manual_interval_s: float = 1.0
    min_manual_interval_s: float = 0.8
    max_manual_interval_s: float = 2.0

    def choose_advance_beats(self, meter: MeterPolicy, tempo_bpm: float) -> float:
        spb = 60.0 / tempo_bpm  # seconds per quarter-beat
        allowed = meter.allowed_advance_beats()

        def seconds(beats: float) -> float:
            return beats * spb

        def closest_to_ideal(options: list[float]) -> float:
            # Closest to the ideal interval; on a tie prefer the shorter advance.
            return min(options, key=lambda b: (abs(seconds(b) - self.ideal_manual_interval_s), b))

        in_window = [
            b
            for b in allowed
            if self.min_manual_interval_s - 1e-9 <= seconds(b) <= self.max_manual_interval_s + 1e-9
        ]
        if in_window:
            return closest_to_ideal(in_window)

        # No allowed length lands in the comfortable window. Avoid the too-fast
        # advances (below min) when any slower option exists; otherwise fall back
        # to whatever allowed length is closest to the ideal.
        not_too_fast = [b for b in allowed if seconds(b) >= self.min_manual_interval_s - 1e-9]
        return closest_to_ideal(not_too_fast or list(allowed))

    def group_indices(
        self,
        durations: list[float],
        meter: MeterPolicy,
        tempo_bpm: float,
        override: list[list[int]] | None = None,
    ) -> list[list[int]]:
        """Group chord indices into segments.

        ``durations`` are per-chord lengths in quarter-beats. An explicit
        ``override`` (list of index groups) is used verbatim when supplied --
        the escape hatch for irregular meters.
        """
        if override is not None:
            return override

        advance = self.choose_advance_beats(meter, tempo_bpm)
        groups: list[list[int]] = []
        current: list[int] = []
        acc = 0.0
        for i, dur in enumerate(durations):
            current.append(i)
            acc += dur
            if acc >= advance - 1e-9:
                groups.append(current)
                current = []
                acc = 0.0
        if current:
            groups.append(current)
        return groups
