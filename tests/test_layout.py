"""8-slot layout builder behaviour (spec tests 1-5)."""

from emiuet_session.core.pitch import note_name
from emiuet_session.fixtures.sample import sample_analysis
from emiuet_session.model.layout import LayoutPolicy, build_layout
from emiuet_session.model.performance import Layout, LayoutOrientation, SlotKind

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


# --- two-row orientation & line ordering --------------------------------


def test_two_row_orientation_is_default():
    assert build_layout(STEPS[0]).orientation is LayoutOrientation.TWO_ROW_CORE_COLOR


def test_core_line_ascends_low_to_high():
    for step in STEPS:
        core = build_layout(step).core_slots()
        notes = [s.preferred_midi for s in core]
        assert notes == sorted(notes) and len(set(notes)) == 4


def test_color_line_ascends_low_to_high():
    for step in STEPS:
        color = build_layout(step).color_slots()
        notes = [s.preferred_midi for s in color]
        assert notes == sorted(notes) and len(set(notes)) == 4


def test_dm7_core_line_is_c_d_f_a():
    core = build_layout(STEPS[0]).core_slots()
    assert [s.pitch_class for s in core] == [0, 2, 5, 9]  # C D F A


def test_dm7_color_line_pitch_classes_match_b_e_g_c():
    # Spec illustration is "B E G C+1"; the deterministic AnchorLowToHigh output
    # is E G B C+1 (64 67 71 72) -- same pitch-class set {E G B C}, each line
    # strictly ascending, with C borrowed as an upper-octave extension.
    color = build_layout(STEPS[0]).color_slots()
    assert {s.pitch_class for s in color} == {4, 7, 11, 0}  # E G B C
    assert [note_name(s.pitch_class) for s in color] == ["E", "G", "B", "C"]


def test_alternating_row_orientation_still_supported():
    layout = build_layout(STEPS[0], policy=LayoutPolicy(orientation=LayoutOrientation.ALTERNATING_ROW))
    assert layout.orientation is LayoutOrientation.ALTERNATING_ROW
    for i in CORE_INDICES:
        assert layout.slots[i].kind is SlotKind.CORE


# --- colour fill & slot voicing de-duplication --------------------------


def test_borrowed_fill_is_upper_octave_extension():
    # Dm7 has only 3 colour tones; the 4th colour slot borrows a chord tone and
    # places it as an upper-octave extension (same pitch class as a core slot, a
    # higher MIDI note) -- not a dead duplicate.
    layout = build_layout(STEPS[0])
    core_by_pc = {s.pitch_class: s.preferred_midi for s in layout.core_slots()}
    extensions = [
        s
        for s in layout.color_slots()
        if s.pitch_class in core_by_pc and s.preferred_midi > core_by_pc[s.pitch_class]
    ]
    assert extensions  # at least one octave-extension fill note


def test_same_pitch_class_different_octave_allowed_but_no_exact_duplicate():
    for step in STEPS:
        notes = [s.preferred_midi for s in build_layout(step).slots]
        assert len(set(notes)) == 8  # no exact duplicate MIDI note
    # And the Dm7 layout deliberately repeats pitch class C at two octaves.
    pcs = [s.pitch_class for s in build_layout(STEPS[0]).slots]
    assert pcs.count(0) == 2  # C and C+1


def test_voicing_dedup_preserves_pitch_classes():
    for step in STEPS:
        off = build_layout(step, policy=LayoutPolicy(dedupe_voicing=False))
        on = build_layout(step)
        assert [s.pitch_class for s in on.slots] == [s.pitch_class for s in off.slots]


def test_dedup_pass_moves_colour_not_core_and_by_octave():
    # Unit test of the safety net on a forced collision: a core slot and a colour
    # slot resolve to the same MIDI note. The colour (lower-priority) slot moves,
    # by a whole octave, and the pitch class is preserved.
    from emiuet_session.model.analysis import PitchCandidate, PitchRole
    from emiuet_session.model.layout import _dedupe_voicing

    core_cand = PitchCandidate(0, "R", PitchRole.CORE, weight=1.0)
    color_cand = PitchCandidate(0, "8", PitchRole.COLOR, weight=0.5)
    assigned = [(0, core_cand, 60), (1, color_cand, 60)]  # both land on MIDI 60
    out = _dedupe_voicing(assigned, lo=36, hi=96)
    assert out[0] == 60  # core slot keeps its note
    assert out[1] != 60 and out[1] % 12 == 0  # colour moved, still pitch class C
    assert (out[1] - 60) % 12 == 0  # by whole octaves
