"""Compiled timeline importer（EUB Changes export JSON を読む）。

EUB Changes が出した digitone_step basis の compiled timeline JSON を読み、
``CompiledTimeline``（progression / contrast context つき）に変換する。Emiuet Session 側
で SPEED / LENGTH / tempo を再解釈しない。検証は docs/compiled_timeline_schema.md 準拠。

pure（mido / platform 非依存）。
"""

from __future__ import annotations

import json
from pathlib import Path

from .pitch import NOTE_NAMES_FLAT, NOTE_NAMES_SHARP
from .timeline import (
    ChordContext,
    CompiledHarmonicStep,
    CompiledTimeline,
    TimelineBasis,
)

SCHEMA_NAME = "emnyeca.emiuet_session.compiled_timeline"
SUPPORTED_SCHEMA_VERSIONS = (2,)

_NAME_TO_PC = {name: pc for pc, name in enumerate(NOTE_NAMES_SHARP)}
_NAME_TO_PC.update({name: pc for pc, name in enumerate(NOTE_NAMES_FLAT)})


class TimelineSchemaError(ValueError):
    """compiled timeline JSON が schema 違反のときに送出。"""


def _pc(name: str) -> int:
    base = name.strip()
    if base in _NAME_TO_PC:
        return _NAME_TO_PC[base]
    raise TimelineSchemaError(f"unknown note name: {name!r}")


def _pcs(names) -> tuple[int, ...]:
    if not isinstance(names, list):
        raise TimelineSchemaError(f"expected a list of note names, got {names!r}")
    return tuple(_pc(n) for n in names)


def _parse_context(raw: dict, where: str) -> ChordContext:
    if not isinstance(raw, dict):
        raise TimelineSchemaError(f"{where}: context must be an object")
    core = _pcs(raw.get("resolver_core", []))
    lpc = _pcs(raw.get("lpc", []))
    if not core:
        raise TimelineSchemaError(f"{where}: resolver_core must not be empty")
    if not lpc:
        raise TimelineSchemaError(f"{where}: lpc must not be empty")
    if not set(core).issubset(set(lpc)):
        raise TimelineSchemaError(f"{where}: resolver_core must be a subset of lpc")
    return ChordContext(
        chord=raw.get("display", ""),
        core_pcs=core,
        lpc=lpc,
        scale_collection=raw.get("scale_name", ""),
        role=raw.get("role", ""),
        display=raw.get("display", ""),
        scale_root=raw.get("scale_root", ""),
        hard_context=_pcs(raw.get("hard_context", [])),
    )


def _parse_step(raw: dict, index: int) -> CompiledHarmonicStep:
    where = f"steps[{index}]"
    for key in ("id", "start_tick", "end_tick", "chord"):
        if key not in raw:
            raise TimelineSchemaError(f"{where}: missing '{key}'")
    start, end = raw["start_tick"], raw["end_tick"]
    if not (isinstance(start, int) and isinstance(end, int) and start < end):
        raise TimelineSchemaError(f"{where}: require integer start_tick < end_tick")

    default_role = raw.get("default_context_role", "progression")
    mod_role = raw.get("mod_context_role", "contrast")

    raw_contexts = raw.get("contexts", {})
    if default_role not in raw_contexts:
        raise TimelineSchemaError(f"{where}: missing default context role {default_role!r}")

    contexts: dict[str, ChordContext] = {}
    for role, raw_ctx in raw_contexts.items():
        if raw_ctx is None:
            continue  # contrast: null -> omitted; falls back to progression
        ctx = _parse_context(raw_ctx, f"{where}.contexts.{role}")
        # carry the chord symbol for NOW display even if context.display differs
        contexts[role] = ChordContext(
            chord=raw["chord"] if role == default_role else ctx.chord or raw["chord"],
            core_pcs=ctx.core_pcs,
            lpc=ctx.lpc,
            scale_collection=ctx.scale_collection,
            role=role,
            display=ctx.display or raw["chord"],
            scale_root=ctx.scale_root,
            hard_context=ctx.hard_context,
        )

    return CompiledHarmonicStep(
        id=raw["id"],
        start_tick=start,
        end_tick=end,
        chord_context=contexts[default_role],
        source_step_index=raw.get("source_step_index"),
        source_label=raw.get("chord"),
        contexts=contexts,
        default_context_role=default_role,
        mod_context_role=mod_role,
    )


def parse_compiled_timeline(
    data: dict,
    *,
    expected_basis: str | None = "digitone_step",
) -> CompiledTimeline:
    if not isinstance(data, dict):
        raise TimelineSchemaError("compiled timeline must be a JSON object")
    if data.get("schema") != SCHEMA_NAME:
        raise TimelineSchemaError(f"unexpected schema {data.get('schema')!r}; expected {SCHEMA_NAME}")
    if data.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
        raise TimelineSchemaError(
            f"unsupported schema_version {data.get('schema_version')!r}; "
            f"supported: {SUPPORTED_SCHEMA_VERSIONS}"
        )
    raw_basis = data.get("timeline_basis")
    if expected_basis is not None and raw_basis != expected_basis:
        raise TimelineSchemaError(
            f"timeline_basis must be {expected_basis!r}, got {raw_basis!r}"
        )
    try:
        basis = TimelineBasis(raw_basis)
    except ValueError as exc:
        raise TimelineSchemaError(f"unsupported timeline_basis {raw_basis!r}") from exc

    raw_steps = data.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise TimelineSchemaError("steps must be a non-empty list")

    steps = [_parse_step(raw, i) for i, raw in enumerate(raw_steps)]
    prev_end = None
    for step in steps:
        if prev_end is not None and step.start_tick < prev_end:
            raise TimelineSchemaError(f"step ticks must be monotonic; {step.id} overlaps previous")
        prev_end = step.end_tick

    clock = data.get("clock", {})
    return CompiledTimeline(
        basis=basis,
        steps=steps,
        original_tempo=clock.get("original_tempo"),
        digitone_tempo=clock.get("digitone_tempo"),
    )


def load_compiled_timeline(path: str | Path) -> CompiledTimeline:
    p = Path(path)
    if not p.exists():
        raise TimelineSchemaError(f"compiled timeline not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TimelineSchemaError(f"{p} is not valid JSON: {exc}") from exc
    return parse_compiled_timeline(data)
