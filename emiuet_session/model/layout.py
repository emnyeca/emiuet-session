"""8-slot layout builder.

The playing surface is 8 keys with alternating importance::

    ■ □ ■ □ ■ □ ■ □     ■ = core (high importance)   □ = colour/tension

Goals (all tunable in one place via ``LayoutPolicy`` -- no scattered magic
numbers):

- Put the highest-weight chord/core notes in the core slots (even indices).
- Put useful tension/colour notes in the colour slots (odd indices).
- In the NORMAL profile, suppress strong avoid notes.
- Keep the core/colour alternation.
- Minimise per-slot pitch/register jump from the previous step's layout so
  common progressions (ii-V-I) voice-lead smoothly.
- Don't fill every slot with chord tones when useful tensions exist -- colour
  slots are reserved for colour and only borrow chord tones as a fallback.
- Slot voicing de-duplication (LayoutPolicy.dedupe_voicing): if two slots resolve
  to the exact same MIDI note, nudge the lower-priority slot by whole octaves so
  every key sounds a distinct, usable note. This is a voicing/playability pass --
  it never changes a pitch class, a role, or anything harmonic.

The builder is deterministic (stable sorts + lexicographic permutation
tie-breaks) so it is easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import permutations

from ..core.pitch import nearest_midi_note, note_name
from .analysis import HarmonicStep, PitchCandidate, PitchRole
from .performance import Layout, Slot, SlotKind

_ROLE_TO_KIND = {
    PitchRole.CORE: SlotKind.CORE,
    PitchRole.TENSION: SlotKind.TENSION,
    PitchRole.ALTERED_TENSION: SlotKind.ALTERED,
    PitchRole.COLOR: SlotKind.COLOR,
    PitchRole.APPROACH: SlotKind.APPROACH,
    PitchRole.AVOID: SlotKind.COLOR,
}


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

    # Slot voicing de-duplication: split exact duplicate MIDI notes by octave.
    dedupe_voicing: bool = True
    voicing_low: int = 36  # nudges stay within a playable register window
    voicing_high: int = 96


def _sort_candidates(cands: list[PitchCandidate]) -> list[PitchCandidate]:
    # Highest weight first; stability then pitch class as deterministic tie-breaks.
    return sorted(cands, key=lambda c: (-c.weight, -c.stability, c.pitch_class))


def _fill(primary: list[PitchCandidate], fallback: list[PitchCandidate], n: int) -> list[PitchCandidate]:
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


def _assign(
    cands: list[PitchCandidate],
    prev_slots: list[Slot] | None,
    anchor: int,
) -> list[tuple[PitchCandidate, int]]:
    """Map candidates to a group's slots and pick each one's MIDI octave.

    With a previous layout, choose the candidate->slot assignment that minimises
    total per-slot register jump (brute force over <=24 permutations). Without
    one, lay candidates out in ascending pitch order around the anchor.
    """
    n = len(cands)
    if prev_slots and len(prev_slots) == n:
        anchors = [s.preferred_midi for s in prev_slots]
        best: tuple[int, tuple[int, ...], list[int]] | None = None
        for perm in permutations(range(n)):
            midis = [nearest_midi_note(cands[perm[i]].pitch_class, anchors[i]) for i in range(n)]
            total = sum(abs(midis[i] - anchors[i]) for i in range(n))
            if best is None or total < best[0]:
                best = (total, perm, midis)
        perm, midis = best[1], best[2]
        return [(cands[perm[i]], midis[i]) for i in range(n)]

    order = sorted(range(n), key=lambda i: cands[i].pitch_class)
    return [(cands[i], nearest_midi_note(cands[i].pitch_class, anchor)) for i in order]


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

    # Reserve colour slots for colour: core borrows from colour only if short,
    # and colour borrows from core only if short.
    n_core = len(policy.core_slot_indices)
    n_color = len(policy.color_slot_indices)
    core_sel = _fill(core_pool, color_pool, n_core)
    color_sel = _fill(color_pool, core_pool, n_color)

    prev_core = (
        [previous_layout.slots[i] for i in policy.core_slot_indices] if previous_layout else None
    )
    prev_color = (
        [previous_layout.slots[i] for i in policy.color_slot_indices] if previous_layout else None
    )

    core_assigned = _assign(core_sel, prev_core, policy.anchor_midi)
    color_assigned = _assign(color_sel, prev_color, policy.anchor_midi)

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

    return Layout(slots=tuple(slots))  # type: ignore[arg-type]


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
