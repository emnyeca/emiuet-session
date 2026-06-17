"""Compiled timeline importer（schema v2, progression/contrast）。"""

from pathlib import Path

import pytest

from emiuet_session.core.timeline import TimelineBasis
from emiuet_session.core.timeline_io import (
    TimelineSchemaError,
    load_compiled_timeline,
    parse_compiled_timeline,
)

FIXTURE = Path(__file__).parent / "fixtures" / "dm7_g7_cmaj7_a7_contrast_timeline.json"


def test_loads_fixture_v2():
    tl = load_compiled_timeline(FIXTURE)
    assert tl.basis is TimelineBasis.DIGITONE_STEP
    assert [s.source_label for s in tl.steps] == ["Dm7", "G7", "Cmaj7", "A7"]
    assert tl.total_ticks == 96


def test_chord_context_core_is_resolver_core():
    tl = load_compiled_timeline(FIXTURE)
    dm7 = tl.steps[0].context_for("progression")
    assert dm7.core_pcs == (2, 5, 9, 0)  # D F A C


def test_contrast_contexts_present():
    tl = load_compiled_timeline(FIXTURE)
    assert tl.steps[0].context_for("contrast").scale_collection == "Half-Whole Diminished"
    assert tl.steps[2].context_for("contrast").scale_collection == "Lydian"  # Cmaj7
    assert tl.steps[0].context_for("contrast").display == "Dm7 HW"


def test_hard_context_imported_but_separate_from_resolver_core():
    # A Dm11-style step: hard_context (D F A C E G) differs from resolver_core (D F A C).
    data = _timeline_with_step(
        progression={
            "role": "progression",
            "display": "Dm11",
            "scale_name": "Dorian",
            "scale_root": "D",
            "hard_context": ["D", "F", "A", "C", "E", "G"],
            "resolver_core": ["D", "F", "A", "C"],
            "lpc": ["D", "E", "F", "G", "A", "B", "C"],
        }
    )
    step = parse_compiled_timeline(data).steps[0]
    ctx = step.context_for("progression")
    assert ctx.core_pcs == (2, 5, 9, 0)  # resolver_core, NOT hard_context
    assert set(ctx.hard_context) == {2, 5, 9, 0, 4, 7}  # hard_context retained separately


def test_resolver_core_must_be_subset_of_lpc():
    data = _timeline_with_step(
        progression={
            "role": "progression",
            "display": "X",
            "scale_name": "S",
            "scale_root": "C",
            "resolver_core": ["C", "F#"],  # F# not in lpc
            "lpc": ["C", "E", "G"],
        }
    )
    with pytest.raises(TimelineSchemaError, match="subset"):
        parse_compiled_timeline(data)


def test_missing_contrast_is_allowed():
    data = _timeline_with_step(
        progression={
            "role": "progression", "display": "C", "scale_name": "Ionian", "scale_root": "C",
            "resolver_core": ["C", "E", "G"], "lpc": ["C", "D", "E", "F", "G", "A", "B"],
        },
        contrast=None,
    )
    step = parse_compiled_timeline(data).steps[0]
    assert step.has_context("progression")
    assert not step.has_context("contrast")


def test_rejects_wrong_schema():
    with pytest.raises(TimelineSchemaError, match="schema"):
        parse_compiled_timeline({"schema": "nope", "schema_version": 2})


def test_rejects_non_digitone_basis():
    data = _timeline_with_step(progression=_simple_ctx())
    data["timeline_basis"] = "original_song"
    with pytest.raises(TimelineSchemaError, match="digitone_step"):
        parse_compiled_timeline(data)


def test_rejects_non_monotonic_ticks():
    data = {
        "schema": "emnyeca.emiuet_session.compiled_timeline",
        "schema_version": 2,
        "timeline_basis": "digitone_step",
        "steps": [
            _step("a", 0, 48, _simple_ctx()),
            _step("b", 24, 72, _simple_ctx()),  # overlaps previous
        ],
    }
    with pytest.raises(TimelineSchemaError, match="monotonic"):
        parse_compiled_timeline(data)


# --- helpers -------------------------------------------------------------


def _simple_ctx():
    return {
        "role": "progression", "display": "C", "scale_name": "Ionian", "scale_root": "C",
        "resolver_core": ["C", "E", "G"], "lpc": ["C", "D", "E", "F", "G", "A", "B"],
    }


def _step(step_id, start, end, progression, contrast="__omit__"):
    contexts = {"progression": progression}
    if contrast != "__omit__":
        contexts["contrast"] = contrast
    return {
        "id": step_id, "source_step_index": 0, "start_tick": start, "end_tick": end,
        "chord": progression["display"], "default_context_role": "progression",
        "mod_context_role": "contrast", "contexts": contexts,
    }


def _timeline_with_step(progression, contrast="__omit__"):
    return {
        "schema": "emnyeca.emiuet_session.compiled_timeline",
        "schema_version": 2,
        "timeline_basis": "digitone_step",
        "steps": [_step("step_000", 0, 24, progression, contrast)],
    }
