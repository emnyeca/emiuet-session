"""Session library, timeline descriptors, and runtime transpose."""

from pathlib import Path

import pytest

from emiuet_session.core.frames import InputFrame
from emiuet_session.core.midi import MidiEventType
from emiuet_session.core.mode import PerformanceMode
from emiuet_session.core.solo import SoloGesture
from emiuet_session.core.timeline import (
    RuntimeTransposePolicy,
    TimelineAdvanceMode,
    TimelineBasis,
    transpose_context,
)
from emiuet_session.core.timeline_io import (
    load_compiled_timeline,
)
from emiuet_session.core.transport import AdvanceMode, TransportEvent
from emiuet_session.fixtures import sample_performance_model
from emiuet_session.model.library import (
    SessionTimeline,
    SongIndexEntry,
    SongLibraryIndex,
    SongPayload,
)
from emiuet_session.model.library_io import parse_library_index, parse_song_payload
from emiuet_session.runtime import EmiuetCore

FIXTURE = Path(__file__).parent / "fixtures" / "dm7_g7_cmaj7_a7_contrast_timeline.json"


def test_advance_mode_timeline_basis_and_default_policies():
    tl = load_compiled_timeline(FIXTURE)
    clock = SessionTimeline(
        "clock_song",
        TimelineAdvanceMode.CLOCK_SONG,
        TimelineBasis.ORIGINAL_SONG,
        tl,
    )
    manual = SessionTimeline(
        "manual",
        TimelineAdvanceMode.MANUAL,
        TimelineBasis.SEGMENT_MAP,
        tl,
    )
    device = SessionTimeline(
        "digitone_ii_a01",
        TimelineAdvanceMode.DEVICE_STEP,
        TimelineBasis.DIGITONE_STEP,
        tl,
    )
    assert clock.runtime_transpose_policy is RuntimeTransposePolicy.ALLOWED
    assert manual.runtime_transpose_policy is RuntimeTransposePolicy.ALLOWED
    assert device.runtime_transpose_policy is RuntimeTransposePolicy.LOCKED


def test_song_payload_can_hold_multiple_timelines():
    tl = load_compiled_timeline(FIXTURE)
    payload = SongPayload(
        "contrast_demo",
        "Contrast Demo",
        "C",
        120.0,
        "4/4",
        (
            SessionTimeline("clock_song", TimelineAdvanceMode.CLOCK_SONG, TimelineBasis.ORIGINAL_SONG, tl),
            SessionTimeline("digitone", TimelineAdvanceMode.DEVICE_STEP, TimelineBasis.DIGITONE_STEP, tl),
        ),
    )
    assert [timeline.id for timeline in payload.timelines] == ["clock_song", "digitone"]
    assert payload.timeline_by_id("digitone").runtime_transpose_policy is RuntimeTransposePolicy.LOCKED


def test_library_index_keeps_metadata_without_payloads():
    index = SongLibraryIndex(
        [
            SongIndexEntry(
                song_id=f"song_{i:04d}",
                title=f"Song {i}",
                default_key="C",
                default_tempo=120.0,
                meter="4/4",
                available_timelines=("clock_song",),
                payload_ref=f"songs/song_{i:04d}.json",
            )
            for i in range(2000)
        ]
    )
    assert len(index.songs) == 2000
    assert index.entry_by_id("song_1999").payload_ref == "songs/song_1999.json"


def test_runtime_transpose_moves_resolver_core_lpc_and_scale_root():
    tl = load_compiled_timeline(FIXTURE)
    dm7 = tl.steps[0].context_for("progression")
    moved = transpose_context(dm7, 2)
    assert moved.core_pcs == (4, 7, 11, 2)  # E G B D
    assert set(moved.lpc) == {(pc + 2) % 12 for pc in dm7.lpc}
    assert moved.scale_root == "E"
    assert moved.display == "Dm7 +2"


def test_runtime_transpose_is_applied_before_solo_resolver():
    core = EmiuetCore(
        sample_performance_model(),
        mode=PerformanceMode.SOLO,
        transpose_offset_semitones=2,
    )
    core.process(InputFrame(solo_gesture=SoloGesture.REPEAT))  # C4 anchor
    out = core.process(InputFrame(solo_gesture=SoloGesture.LPC_UP))
    note = [event.note for event in out.midi_events if event.type is MidiEventType.NOTE_ON][0]
    assert note % 12 == 1  # D Dorian +2 has C# above C4


def test_locked_transpose_policy_prevents_context_transpose_and_warns():
    core = EmiuetCore(
        sample_performance_model(),
        mode=PerformanceMode.SOLO,
        transpose_offset_semitones=2,
        runtime_transpose_policy=RuntimeTransposePolicy.LOCKED,
    )
    out = core.process(InputFrame(solo_gesture=SoloGesture.CORE_UP))
    assert core.active_notes()[0] % 12 == 2  # Dm7 core stays D
    assert "locked" in out.display.warning


def test_harmonic_ahead_contrast_then_transpose_order():
    tl = load_compiled_timeline(FIXTURE)
    core = EmiuetCore(
        sample_performance_model(),
        mode=PerformanceMode.SOLO,
        advance_mode=AdvanceMode.AUTO_FOLLOW,
        timeline=tl,
        transpose_offset_semitones=2,
    )
    core.process(InputFrame(transport_event=TransportEvent.START))
    core.process(InputFrame(harmonic_ahead=True))
    core.process(InputFrame(contrast_mod_press=True))
    aim = core.effective_context()
    assert aim.display == "G7 HW +2"
    assert aim.core_pcs == (9, 1, 4, 7)  # G B D F -> A C# E G


def test_parse_song_payload_with_clock_and_device_timelines():
    fixture = load_compiled_timeline(FIXTURE)
    raw_timeline = {
        "schema": "emnyeca.emiuet_session.compiled_timeline",
        "schema_version": 2,
        "timeline_basis": "original_song",
        "steps": [
            {
                "id": "bar_001",
                "start_tick": 0,
                "end_tick": 96,
                "chord": "Dm7",
                "default_context_role": "progression",
                "mod_context_role": "contrast",
                "contexts": {
                    "progression": {
                        "role": "progression",
                        "display": "Dm7",
                        "scale_name": "Dorian",
                        "scale_root": "D",
                        "resolver_core": ["D", "F", "A", "C"],
                        "lpc": ["D", "E", "F", "G", "A", "B", "C"],
                    }
                },
            }
        ],
    }
    payload = parse_song_payload(
        {
            "schema": "emnyeca.emiuet_session.song_payload",
            "schema_version": 1,
            "song_id": "contrast_demo",
            "title": "Contrast Demo",
            "default_key": "C",
            "default_tempo": 120,
            "meter": "4/4",
            "timelines": [
                {
                    "id": "clock_song",
                    "advance_mode": "clock_song",
                    "timeline_basis": "original_song",
                    "runtime_transpose_policy": "allowed",
                    "compiled_timeline": raw_timeline,
                },
                {
                    "id": "digitone",
                    "advance_mode": "device_step",
                    "timeline_basis": "digitone_step",
                    "compiled_timeline": {
                        "schema": "emnyeca.emiuet_session.compiled_timeline",
                        "schema_version": 2,
                        "timeline_basis": "digitone_step",
                        "steps": [
                            {
                                "id": "step_000",
                                "start_tick": 0,
                                "end_tick": 24,
                                "chord": "Dm7",
                                "default_context_role": "progression",
                                "mod_context_role": "contrast",
                                "contexts": {
                                    "progression": {
                                        "role": "progression",
                                        "display": "Dm7",
                                        "scale_name": "Dorian",
                                        "scale_root": "D",
                                        "resolver_core": ["D", "F", "A", "C"],
                                        "lpc": ["D", "E", "F", "G", "A", "B", "C"],
                                    }
                                },
                            }
                        ],
                    },
                },
            ],
        }
    )
    assert payload.timeline_by_id("clock_song").compiled_timeline.basis is TimelineBasis.ORIGINAL_SONG
    assert payload.timeline_by_id("digitone").runtime_transpose_policy is RuntimeTransposePolicy.LOCKED
    assert fixture.basis is TimelineBasis.DIGITONE_STEP


def test_parse_library_index():
    index = parse_library_index(
        {
            "schema": "emnyeca.emiuet_session.library_index",
            "schema_version": 1,
            "songs": [
                {
                    "song_id": "contrast_demo",
                    "title": "Contrast Demo",
                    "default_key": "C",
                    "default_tempo": 120,
                    "meter": "4/4",
                    "available_timelines": ["clock_song", "digitone"],
                    "payload_ref": "songs/contrast_demo.json",
                }
            ],
        }
    )
    assert index.entry_by_id("contrast_demo").available_timelines == ("clock_song", "digitone")


def test_transpose_offset_range_is_validated():
    with pytest.raises(ValueError, match="-12"):
        EmiuetCore(sample_performance_model(), transpose_offset_semitones=13)
