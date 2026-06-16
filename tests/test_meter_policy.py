"""Meter and segment policy (spec tests 9-12)."""

from emiuet_session.model.meter import MeterPolicy, SegmentPolicy


def test_four_four_allowed_lengths():
    m = MeterPolicy(4, 4)
    assert m.allowed_advance_beats() == (1.0, 2.0, 4.0)
    assert m.avoided_advance_beats() == (3.0,)


def test_three_four_allowed_lengths():
    m = MeterPolicy(3, 4)
    assert m.allowed_advance_beats() == (1.0, 3.0)
    assert m.avoided_advance_beats() == (2.0,)


def test_five_four_supports_two_plus_three_groupings():
    m = MeterPolicy(5, 4)
    allowed = m.allowed_advance_beats()
    assert 2.0 in allowed and 3.0 in allowed  # 2+3 and 3+2
    assert 5.0 in allowed  # full bar


def test_unknown_meter_falls_back_safely():
    m = MeterPolicy(7, 8)
    assert not m.is_known()
    allowed = m.allowed_advance_beats()
    assert allowed  # never empty
    assert 1.0 in allowed  # single-beat safety net
    assert m.beats_per_bar in allowed  # full bar fallback


def test_segment_override_is_used_verbatim():
    policy = SegmentPolicy()
    override = [[0, 1], [2], [3]]
    groups = policy.group_indices([1, 1, 1, 1], MeterPolicy(7, 8), 120, override=override)
    assert groups == override


def test_advance_choice_respects_target_window():
    # At 120 BPM a quarter-beat is 0.5 s; the 4-beat advance (2.0 s) fits best.
    policy = SegmentPolicy()
    assert policy.choose_advance_beats(MeterPolicy(4, 4), 120) == 4.0
    # At a very fast tempo, larger groupings keep manual actions comfortable.
    assert policy.choose_advance_beats(MeterPolicy(4, 4), 240) == 4.0
