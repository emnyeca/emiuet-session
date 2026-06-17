"""Relative Melodic Resolver v0 (Solo Mode) の resolver 単体テスト。"""

from emiuet_session.core.solo import (
    PhraseDirection,
    SoloGesture,
    resolve_solo_note,
)

# Dm7: core = D F A C, LPC = D Dorian
CORE = (2, 5, 9, 0)
LPC = (2, 4, 5, 7, 9, 11, 0)


def note(gesture, last, **kw):
    return resolve_solo_note(gesture, last, LPC, CORE, **kw).note


def test_initial_repeat_returns_nearest_core_to_anchor():
    assert note(SoloGesture.REPEAT, None) == 60  # C4


def test_core_up_returns_nearest_core_above():
    assert note(SoloGesture.CORE_UP, 60) == 62  # D above C


def test_core_down_returns_nearest_core_below():
    assert note(SoloGesture.CORE_DOWN, 60) == 57  # A below C


def test_lpc_up_returns_nearest_lpc_above():
    assert note(SoloGesture.LPC_UP, 62) == 64  # E above D


def test_lpc_down_returns_nearest_lpc_below():
    assert note(SoloGesture.LPC_DOWN, 60) == 59  # B below C


def test_chromatic_up_is_last_plus_one():
    assert note(SoloGesture.CHROMATIC_UP, 60) == 61


def test_chromatic_down_is_last_minus_one():
    assert note(SoloGesture.CHROMATIC_DOWN, 60) == 59


def test_resolve_moves_to_nearest_core():
    assert note(SoloGesture.RESOLVE, 64) == 65  # E -> F (nearest core)


def test_resolve_on_core_repeats():
    res = resolve_solo_note(SoloGesture.RESOLVE, 60, LPC, CORE)  # C is a core tone
    assert res.note == 60
    assert "repeat" in res.reason


def test_skip_count_picks_second_candidate():
    # From C: core above = [D, F, A, ...]; skip=1 -> F (65).
    assert note(SoloGesture.CORE_UP, 60, pending_skip_count=1) == 65


def test_octave_shift_up_adds_twelve():
    assert note(SoloGesture.CORE_UP, 60, pending_octave_shift=1) == 74  # D + 12


def test_octave_shift_down_subtracts_twelve():
    assert note(SoloGesture.CORE_UP, 60, pending_octave_shift=-1) == 50  # D - 12


def test_skip_and_octave_combine():
    # skip=2 -> A(69); +12 -> 81.
    assert note(SoloGesture.CORE_UP, 60, pending_skip_count=2, pending_octave_shift=1) == 81


def test_chromatic_ignores_skip_but_applies_octave():
    assert note(SoloGesture.CHROMATIC_UP, 60, pending_skip_count=3) == 61  # skip ignored
    assert note(SoloGesture.CHROMATIC_UP, 60, pending_octave_shift=1) == 73  # +12


def test_resolve_tie_break_prefers_down_without_direction():
    # last sits exactly between two core tones equidistant; default tie -> down.
    # Cmaj7 core C E G B; from D (62): up=E(64,+2), down=C(60,-2) -> tie -> down(60).
    cmaj_core = (0, 4, 7, 11)
    res = resolve_solo_note(SoloGesture.RESOLVE, 62, LPC, cmaj_core,
                            phrase_direction=PhraseDirection.NONE)
    assert res.note == 60


def test_resolve_tie_break_follows_phrase_direction_up():
    cmaj_core = (0, 4, 7, 11)
    res = resolve_solo_note(SoloGesture.RESOLVE, 62, LPC, cmaj_core,
                            phrase_direction=PhraseDirection.UP)
    assert res.note == 64
