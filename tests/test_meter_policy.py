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


def test_advance_targets_ideal_manual_interval():
    # SegmentPolicy aims for ~1 manual press/second, not the largest length that
    # fits the window.
    policy = SegmentPolicy()
    assert policy.choose_advance_beats(MeterPolicy(4, 4), 120) == 2.0  # 2 beats = 1.0 s
    assert policy.choose_advance_beats(MeterPolicy(4, 4), 240) == 4.0  # 4 beats = 1.0 s
    assert policy.choose_advance_beats(MeterPolicy(4, 4), 60) == 1.0  # 1 beat = 1.0 s


def test_advance_three_four_120():
    policy = SegmentPolicy()
    # allowed 1 (0.5 s) and 3 (1.5 s); 3 beats is closest to the 1.0 s ideal.
    assert policy.choose_advance_beats(MeterPolicy(3, 4), 120) == 3.0


def test_advance_tie_breaks_to_shorter():
    # 5/4 @ 150 BPM: 2 beats = 0.8 s and 3 beats = 1.2 s are equidistant from the
    # 1.0 s ideal; the shorter advance wins.
    policy = SegmentPolicy()
    assert policy.choose_advance_beats(MeterPolicy(5, 4), 150) == 2.0


def test_advance_unknown_meter_does_not_break():
    policy = SegmentPolicy()
    choice = policy.choose_advance_beats(MeterPolicy(7, 8), 120)
    assert choice in MeterPolicy(7, 8).allowed_advance_beats()
