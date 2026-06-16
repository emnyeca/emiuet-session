"""8-slot layout builder behaviour (spec tests 1-5)."""

from emiuet_session.fixtures.sample import sample_analysis
from emiuet_session.model.layout import LayoutPolicy, build_layout
from emiuet_session.model.performance import Layout, SlotKind

STEPS = sample_analysis().steps  # Dm7, G7, Cmaj7, A7alt
CORE_INDICES = (0, 2, 4, 6)
COLOR_INDICES = (1, 3, 5, 7)


def total_jump(prev: Layout, cur: Layout) -> int:
    return sum(abs(cur.slots[i].preferred_midi - prev.slots[i].preferred_midi) for i in range(8))


def test_layout_has_eight_slots():
    layout = build_layout(STEPS[0])
    assert len(layout.slots) == 8
    assert tuple(s.index for s in layout.slots) == tuple(range(8))


def test_core_color_alternation():
    # Every chord here has >= 4 chord tones, so the core positions must hold
    # core-importance notes and the colour positions are the in-between keys.
    for step in STEPS:
        layout = build_layout(step)
        for i in CORE_INDICES:
            assert layout.slots[i].kind is SlotKind.CORE
        for i in COLOR_INDICES:
            assert layout.slots[i].index % 2 == 1


def test_high_weight_chord_tones_go_to_core_slots():
    step = STEPS[0]  # Dm7: chord tones D F A C
    layout = build_layout(step)
    core_pcs = {layout.slots[i].pitch_class for i in CORE_INDICES}
    assert core_pcs == {2, 5, 9, 0}


def test_useful_tensions_go_to_color_slots():
    step = STEPS[0]  # Dm7 tensions/colour: E(9) B(13) G(11)
    layout = build_layout(step)
    color_pcs = {layout.slots[i].pitch_class for i in COLOR_INDICES}
    assert {4, 11, 7}.issubset(color_pcs)


def test_avoid_note_suppressed_in_normal():
    # G7's 11 (C, pc 0) is an avoid note and must not appear in the NORMAL layout.
    layout = build_layout(STEPS[1])
    assert all(s.pitch_class != 0 for s in layout.slots)


def test_ii_v_i_minimises_same_slot_jump():
    dm7, g7, _cmaj7, _ = STEPS
    l0 = build_layout(dm7)
    chained = build_layout(g7, previous_layout=l0)
    independent = build_layout(g7)  # placed around the anchor, ignoring l0
    assert total_jump(l0, chained) <= total_jump(l0, independent)


def test_no_duplicate_midi_notes_in_layout():
    for step in STEPS:
        layout = build_layout(step)
        notes = [s.preferred_midi for s in layout.slots]
        assert len(set(notes)) == 8


# --- slot voicing de-duplication ----------------------------------------


def test_dm7_does_not_map_same_midi_note_to_two_keys():
    # Without de-dup the borrowed chord tone collides (e.g. 62 on two keys);
    # with the default policy every key sounds a distinct note.
    off = build_layout(STEPS[0], policy=LayoutPolicy(dedupe_voicing=False))
    on = build_layout(STEPS[0])
    off_notes = [s.preferred_midi for s in off.slots]
    on_notes = [s.preferred_midi for s in on.slots]
    assert len(set(off_notes)) < 8  # the collision the pass exists to fix
    assert len(set(on_notes)) == 8


def test_voicing_dedup_preserves_pitch_classes():
    for step in STEPS:
        off = build_layout(step, policy=LayoutPolicy(dedupe_voicing=False))
        on = build_layout(step)
        assert [s.pitch_class for s in on.slots] == [s.pitch_class for s in off.slots]


def test_voicing_dedup_preserves_alternation_and_roles():
    on = build_layout(STEPS[0])
    off = build_layout(STEPS[0], policy=LayoutPolicy(dedupe_voicing=False))
    assert [s.kind for s in on.slots] == [s.kind for s in off.slots]
    for i in CORE_INDICES:
        assert on.slots[i].kind is SlotKind.CORE


def test_voicing_dedup_nudges_colour_not_core():
    # Core slots keep their preferred note; the lower-priority colour slot moves.
    off = build_layout(STEPS[0], policy=LayoutPolicy(dedupe_voicing=False))
    on = build_layout(STEPS[0])
    for i in CORE_INDICES:
        assert on.slots[i].preferred_midi == off.slots[i].preferred_midi
    moved = [i for i in COLOR_INDICES if on.slots[i].preferred_midi != off.slots[i].preferred_midi]
    assert moved  # at least one colour slot was nudged
    # A nudge is whole octaves only (pitch class unchanged).
    for i in moved:
        assert (on.slots[i].preferred_midi - off.slots[i].preferred_midi) % 12 == 0
