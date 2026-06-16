"""8-slot layout builder.

The surface is 8 keys, read as two rows of four (LayoutOrientation default
``TWO_ROW_CORE_COLOR``)::

    □ □ □ □   colour / tension line (slots 1 3 5 7)
    ■ ■ ■ ■   core / high-importance line (slots 0 2 4 6)

Each line ascends left-to-right; the interleaved reading need not ascend. The
legacy single-row ``ALTERNATING_ROW`` (``■ □ ■ □ ■ □ ■ □``) is still supported.

Goals (all tunable in one place via ``LayoutPolicy`` -- no scattered magic
numbers):

- Put the highest-weight chord/core notes in the core line.
- Put useful tension/colour notes in the colour line.
- In the NORMAL profile, suppress strong avoid notes.
- Initial step (no previous layout): lay each line out low->high from a C anchor
  (InitialLayoutOrder ``ANCHOR_LOW_TO_HIGH``).
- Subsequent steps: minimise per-slot register jump from the previous layout so
  ii-V-I and similar progressions voice-lead smoothly.
- Don't fill every key with chord tones when useful tensions exist -- the colour
  line is reserved for colour and only borrows a chord tone when a 7-note scale
  leaves it a note short.
- Colour-fill voice leading: a borrowed chord tone is placed as the nearest
  ascending continuation above the colour line (an upper-octave extension, e.g.
  ``C+1``), never as a dead duplicate of the note its core slot already plays.
- Octaves: the same pitch class at different octaves is fine; an *exact* same
  MIDI note on two keys is not. The de-dup pass (``dedupe_voicing``) is the
  safety net -- it moves the lower-priority (colour) slot by whole octaves and
  never touches a pitch class, role, or anything harmonic.

The builder is deterministic (stable sorts + lexicographic permutation
tie-breaks).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import permutations

from ..core.pitch import nearest_midi_note, note_name
from .analysis import HarmonicStep, PitchCandidate, PitchRole
from .performance import Layout, LayoutOrientation, Slot, SlotKind

_ROLE_TO_KIND = {
    PitchRole.CORE: SlotKind.CORE,
    PitchRole.TENSION: SlotKind.TENSION,
    PitchRole.ALTERED_TENSION: SlotKind.ALTERED,
    PitchRole.COLOR: SlotKind.COLOR,
    PitchRole.APPROACH: SlotKind.APPROACH,
    PitchRole.AVOID: SlotKind.COLOR,
}


class InitialLayoutOrder(Enum):
    """How the very first step (no previous layout) orders each line."""

    ANCHOR_LOW_TO_HIGH = "anchor_low_to_high"  # default: rise from a C anchor
    # Reserved for future R&D; not yet implemented.
    PITCH_CLASS_ASCENDING = "pitch_class_ascending"
    ROOT_FIRST = "root_first"
    GUIDE_TONE_FIRST = "guide_tone_first"
    CUSTOM = "custom"


@dataclass(frozen=True)
class LayoutPolicy:
    core_slot_indices: tuple[int, ...] = (0, 2, 4, 6)
    color_slot_indices: tuple[int, ...] = (1, 3, 5, 7)
    core_roles: frozenset = field(default_factory=lambda: frozenset({PitchRole.CORE}))
    color_roles: frozenset = field(
        default_factory=lambda: frozenset(
            {PitchRole.TENSION, PitchRole.ALTERED_TENSION, PitchRole.COLOR}
        )
    )
    # Roles never placed in a resting layout (handled live, e.g. approach notes).
    excluded_roles: frozenset = field(default_factory=lambda: frozenset({PitchRole.APPROACH}))
    # Suppressed in NORMAL; a future COLOR/OUTSIDE profile may allow them.
    suppressed_roles_normal: frozenset = field(default_factory=lambda: frozenset({PitchRole.AVOID}))
    anchor_midi: int = 60  # register the first step centres on

    orientation: LayoutOrientation = LayoutOrientation.TWO_ROW_CORE_COLOR
    initial_order: InitialLayoutOrder = InitialLayoutOrder.ANCHOR_LOW_TO_HIGH

    # Slot voicing de-duplication: split exact duplicate MIDI notes by octave.
    dedupe_voicing: bool = True
    voicing_low: int = 36  # nudges stay within a playable register window
    voicing_high: int = 96


def _sort_candidates(cands: list[PitchCandidate]) -> list[PitchCandidate]:
    # Highest weight first; stability then pitch class as deterministic tie-breaks.
    return sorted(cands, key=lambda c: (-c.weight, -c.stability, c.pitch_class))


def _take(primary: list[PitchCandidate], n: int, fallback: list[PitchCandidate]) -> list[PitchCandidate]:
    """Return exactly ``n`` candidates: primary first, then fallback, then pad."""
    chosen: list[PitchCandidate] = list(primary[:n])
    for c in fallback:
        if len(chosen) >= n:
            break
        if c not in chosen:
            chosen.append(c)
    base = chosen or fallback or primary
    i = 0
    while len(chosen) < n:
        chosen.append(base[i % len(base)])
        i += 1
    return chosen[:n]


def _order_from_anchor(cands: list[PitchCandidate], anchor: int) -> list[PitchCandidate]:
    """Order candidates so a line rises from the anchor pitch class."""
    anchor_pc = anchor % 12
    return sorted(cands, key=lambda c: ((c.pitch_class - anchor_pc) % 12, c.pitch_class))


def _ascending_line(pitch_classes: list[int], start: int) -> list[int]:
    """Strictly ascending MIDI notes for the given pitch classes, from ``start``."""
    notes: list[int] = []
    current = start
    for pc in pitch_classes:
        note = current + ((pc - current) % 12)
        if notes and note <= notes[-1]:
            note += 12
        notes.append(note)
        current = note
    return notes


def _assign_anchor_line(cands: list[PitchCandidate], anchor: int) -> list[tuple[PitchCandidate, int]]:
    """Initial-step placement: a line rising low->high from the anchor."""
    ordered = _order_from_anchor(cands, anchor)
    notes = _ascending_line([c.pitch_class for c in ordered], anchor)
    return list(zip(ordered, notes))


def _assign_color_anchor(
    color_real: list[PitchCandidate],
    borrow_pool: list[PitchCandidate],
    n_total: int,
    anchor: int,
    used_notes: set[int],
) -> list[tuple[PitchCandidate, int]]:
    """Colour line for the initial step: real colour tones rise from the anchor,
    then any shortfall is filled by the core tone whose nearest *ascending*
    continuation sits just above the line (an upper-octave extension), avoiding
    any exact-duplicate MIDI note already in use."""
    placed = _assign_anchor_line(color_real[:n_total], anchor)
    used = set(used_notes) | {note for _c, note in placed}
    top = placed[-1][1] if placed else anchor - 1

    while len(placed) < n_total and borrow_pool:
        best: tuple[tuple[int, int], PitchCandidate, int] | None = None
        for cand in borrow_pool:
            note = top + ((cand.pitch_class - top) % 12)
            if note <= top:
                note += 12
            while note in used:
                note += 12
            key = (note - top, cand.pitch_class)
            if best is None or key < best[0]:
                best = (key, cand, note)
        _key, cand, note = best
        placed.append((cand, note))
        used.add(note)
        top = note

    while len(placed) < n_total and placed:  # degenerate: nothing to borrow
        cand, note = placed[-1]
        note += 12
        placed.append((cand, note))
    return placed


def _assign_voice_led(
    cands: list[PitchCandidate], prev_slots: list[Slot]
) -> list[tuple[PitchCandidate, int]]:
    """Subsequent-step placement: assign candidates to the line's slots so total
    per-slot register jump from the previous layout is minimised (<=24 perms)."""
    n = len(cands)
    anchors = [prev_slots[i % len(prev_slots)].preferred_midi for i in range(n)]
    best: tuple[int, tuple[int, ...], list[int]] | None = None
    for perm in permutations(range(n)):
        midis = [nearest_midi_note(cands[perm[i]].pitch_class, anchors[i]) for i in range(n)]
        total = sum(abs(midis[i] - anchors[i]) for i in range(n))
        if best is None or total < best[0]:
            best = (total, perm, midis)
    perm, midis = best[1], best[2]
    return [(cands[perm[i]], midis[i]) for i in range(n)]


def build_layout(
    step: HarmonicStep,
    previous_layout: Layout | None = None,
    policy: LayoutPolicy | None = None,
) -> Layout:
    policy = policy or LayoutPolicy()

    usable = [c for c in step.candidates if c.role not in policy.excluded_roles]
    usable = [c for c in usable if c.role not in policy.suppressed_roles_normal]

    core_pool = _sort_candidates([c for c in usable if c.role in policy.core_roles])
    color_pool = _sort_candidates([c for c in usable if c.role in policy.color_roles])

    n_core = len(policy.core_slot_indices)
    n_color = len(policy.color_slot_indices)
    core_sel = _take(core_pool, n_core, fallback=color_pool)
    color_real = color_pool[:n_color]
    n_borrow = n_color - len(color_real)

    if previous_layout is None:
        core_assigned = _assign_anchor_line(core_sel, policy.anchor_midi)
        core_notes = {note for _c, note in core_assigned}
        color_assigned = _assign_color_anchor(
            color_real, core_pool, n_color, policy.anchor_midi, core_notes
        )
    else:
        borrowed = _take(core_pool, n_borrow, fallback=color_pool) if n_borrow else []
        color_sel = _take(color_real + borrowed, n_color, fallback=core_pool)
        prev_core = [previous_layout.slots[i] for i in policy.core_slot_indices]
        prev_color = [previous_layout.slots[i] for i in policy.color_slot_indices]
        core_assigned = _assign_voice_led(core_sel, prev_core)
        color_assigned = _assign_voice_led(color_sel, prev_color)

    assigned: list[tuple[int, PitchCandidate, int]] = []
    for slot_index, (cand, midi) in zip(policy.core_slot_indices, core_assigned):
        assigned.append((slot_index, cand, midi))
    for slot_index, (cand, midi) in zip(policy.color_slot_indices, color_assigned):
        assigned.append((slot_index, cand, midi))

    midi_by_slot = {idx: midi for idx, _c, midi in assigned}
    if policy.dedupe_voicing:
        midi_by_slot = _dedupe_voicing(assigned, policy.voicing_low, policy.voicing_high)

    slots: list[Slot | None] = [None] * 8
    for slot_index, cand, _midi in assigned:
        slots[slot_index] = _make_slot(slot_index, cand, midi_by_slot[slot_index])

    return Layout(slots=tuple(slots), orientation=policy.orientation)  # type: ignore[arg-type]


def _slot_priority(slot_index: int, cand: PitchCandidate) -> tuple:
    """Higher = keeps its preferred note in a collision. Core positions win over
    colour positions; then higher weight; then lower slot index (deterministic)."""
    is_core_position = slot_index % 2 == 0
    return (is_core_position, cand.weight, -slot_index)


def _dedupe_voicing(
    assigned: list[tuple[int, PitchCandidate, int]], lo: int, hi: int
) -> dict[int, int]:
    """Slot voicing de-duplication.

    A 7-note scale has only 3 non-chord tones, so the 4th colour slot borrows a
    chord tone and can land on the exact MIDI note its core slot already uses --
    a dead key. We keep the higher-priority slot's note and nudge the
    lower-priority (colour / lower-weight) slot by whole octaves to a free,
    in-range note. Pitch class and role are preserved; an octave is moved only
    when it actually frees up a playable note, otherwise the note is left as-is.
    """
    used: set[int] = set()
    out: dict[int, int] = {}
    for slot_index, cand, midi in sorted(
        assigned, key=lambda t: _slot_priority(t[0], t[1]), reverse=True
    ):
        chosen = midi
        if chosen in used:
            for delta in (12, -12, 24, -24, 36, -36):
                candidate = midi + delta
                if lo <= candidate <= hi and candidate not in used:
                    chosen = candidate
                    break
        out[slot_index] = chosen
        used.add(chosen)
    return out


def _make_slot(index: int, cand: PitchCandidate, midi: int) -> Slot:
    return Slot(
        index=index,
        kind=_ROLE_TO_KIND[cand.role],
        pitch_class=cand.pitch_class,
        preferred_midi=midi,
        label=note_name(cand.pitch_class),
        weight=cand.weight,
        source_degree=cand.label,
    )
