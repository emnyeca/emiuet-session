"""Build a PerformanceModel from a Song + HarmonicAnalysis.

This is the Emiuet Session Model Builder: it consumes Changes-style data and
produces the playable layout. It chains layouts so each step voice-leads from
the previous one, then groups chord changes into manual-advance segments.
"""

from __future__ import annotations

from .analysis import HarmonicAnalysis
from .layout import LayoutPolicy, build_layout
from .meter import MeterPolicy, SegmentPolicy
from .performance import PerformanceModel, Segment, Step
from .song import Song


def build_performance_model(
    song: Song,
    analysis: HarmonicAnalysis,
    *,
    layout_policy: LayoutPolicy | None = None,
    segment_policy: SegmentPolicy | None = None,
    segment_override: list[list[int]] | None = None,
) -> PerformanceModel:
    chords = song.chords()
    if len(chords) != len(analysis.steps):
        raise ValueError(
            f"Song has {len(chords)} chords but analysis has {len(analysis.steps)} steps; "
            "they must align one-to-one."
        )

    segment_policy = segment_policy or SegmentPolicy()
    meter = MeterPolicy(song.meter.numerator, song.meter.denominator)

    # Build each step's layout, chaining previous->current for smooth voice leading.
    layouts = []
    previous = None
    for hstep in analysis.steps:
        layout = build_layout(hstep, previous, layout_policy)
        layouts.append(layout)
        previous = layout

    durations = [c.beats for c in chords]
    groups = segment_policy.group_indices(durations, meter, song.default_tempo, segment_override)

    segments: list[Segment] = []
    for gi, group in enumerate(groups):
        steps: list[Step] = []
        beat_offset = 0.0
        for idx in group:
            hstep = analysis.steps[idx]
            chord = chords[idx]
            next_chord = chords[idx + 1].symbol if idx + 1 < len(chords) else ""
            steps.append(
                Step(
                    step_id=f"step{idx}",
                    beat_offset=beat_offset,
                    duration_beats=chord.beats,
                    chord=chord.symbol,
                    next_chord=next_chord,
                    analysis_summary=(
                        f"{hstep.scale_collection} "
                        f"(prio {hstep.scale_priority}, retry {hstep.retry_level})"
                    ),
                    layout=layouts[idx],
                    scale_collection=hstep.scale_collection,
                    scale_priority=hstep.scale_priority,
                    retry_level=hstep.retry_level,
                    lpc=tuple(hstep.local_pitch_collection),
                    core_pcs=tuple(hstep.chord_tones),
                )
            )
            beat_offset += chord.beats
        seg_beats = sum(s.duration_beats for s in steps)
        label = steps[0].chord if len(steps) == 1 else f"{steps[0].chord}..{steps[-1].chord}"
        segments.append(
            Segment(
                segment_id=f"seg{gi}",
                label=label,
                manual_advance_length=seg_beats,
                duration_beats=seg_beats,
                steps=steps,
            )
        )

    return PerformanceModel(
        version=1,
        source_title=song.title,
        default_tempo=song.default_tempo,
        meter=str(song.meter),
        segments=segments,
    )
