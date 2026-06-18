"""JSON import helpers for Emiuet Session song payloads and library indexes."""

from __future__ import annotations

import json
from pathlib import Path

from ..core.timeline import RuntimeTransposePolicy, TimelineAdvanceMode, TimelineBasis
from ..core.timeline_io import TimelineSchemaError, parse_compiled_timeline
from .library import SessionTimeline, SongIndexEntry, SongLibraryIndex, SongPayload

SONG_PAYLOAD_SCHEMA_NAME = "emnyeca.emiuet_session.song_payload"
LIBRARY_INDEX_SCHEMA_NAME = "emnyeca.emiuet_session.library_index"
SUPPORTED_SONG_PAYLOAD_VERSIONS = (1,)
SUPPORTED_LIBRARY_INDEX_VERSIONS = (1,)


def _enum(enum_type, raw, where: str):
    try:
        return enum_type(raw)
    except ValueError as exc:
        raise TimelineSchemaError(f"{where}: unsupported value {raw!r}") from exc


def parse_song_payload(data: dict) -> SongPayload:
    if not isinstance(data, dict):
        raise TimelineSchemaError("song payload must be a JSON object")
    if data.get("schema") != SONG_PAYLOAD_SCHEMA_NAME:
        raise TimelineSchemaError(
            f"unexpected schema {data.get('schema')!r}; expected {SONG_PAYLOAD_SCHEMA_NAME}"
        )
    if data.get("schema_version") not in SUPPORTED_SONG_PAYLOAD_VERSIONS:
        raise TimelineSchemaError(
            f"unsupported song payload schema_version {data.get('schema_version')!r}"
        )

    raw_timelines = data.get("timelines", [])
    if not isinstance(raw_timelines, list) or not raw_timelines:
        raise TimelineSchemaError("song payload timelines must be a non-empty list")

    timelines: list[SessionTimeline] = []
    for index, raw in enumerate(raw_timelines):
        where = f"timelines[{index}]"
        if not isinstance(raw, dict):
            raise TimelineSchemaError(f"{where}: timeline must be an object")
        compiled_data = raw.get("compiled_timeline", raw)
        compiled = parse_compiled_timeline(compiled_data, expected_basis=None)
        advance_mode = _enum(TimelineAdvanceMode, raw.get("advance_mode"), f"{where}.advance_mode")
        timeline_basis = _enum(TimelineBasis, raw.get("timeline_basis"), f"{where}.timeline_basis")
        if compiled.basis is not timeline_basis:
            raise TimelineSchemaError(
                f"{where}: compiled timeline_basis {compiled.basis.value!r} "
                f"does not match descriptor {timeline_basis.value!r}"
            )
        raw_policy = raw.get("runtime_transpose_policy")
        policy = (
            None
            if raw_policy is None
            else _enum(RuntimeTransposePolicy, raw_policy, f"{where}.runtime_transpose_policy")
        )
        timelines.append(
            SessionTimeline(
                id=str(raw.get("id") or f"timeline_{index:03d}"),
                advance_mode=advance_mode,
                timeline_basis=timeline_basis,
                runtime_transpose_policy=policy,
                device=(None if raw.get("device") is None else str(raw.get("device"))),
                compiled_timeline=compiled,
            )
        )

    return SongPayload(
        song_id=str(data["song_id"]),
        title=str(data.get("title") or data["song_id"]),
        default_key=str(data.get("default_key") or "C"),
        default_tempo=float(data.get("default_tempo", 120.0)),
        meter=str(data.get("meter") or "4/4"),
        timelines=tuple(timelines),
        default_timeline_id=(
            None if data.get("default_timeline_id") is None else str(data.get("default_timeline_id"))
        ),
    )


def load_song_payload(path: str | Path) -> SongPayload:
    p = Path(path)
    if not p.exists():
        raise TimelineSchemaError(f"song payload not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TimelineSchemaError(f"{p} is not valid JSON: {exc}") from exc
    return parse_song_payload(data)


def parse_library_index(data: dict) -> SongLibraryIndex:
    if not isinstance(data, dict):
        raise TimelineSchemaError("library index must be a JSON object")
    if data.get("schema") != LIBRARY_INDEX_SCHEMA_NAME:
        raise TimelineSchemaError(
            f"unexpected schema {data.get('schema')!r}; expected {LIBRARY_INDEX_SCHEMA_NAME}"
        )
    if data.get("schema_version") not in SUPPORTED_LIBRARY_INDEX_VERSIONS:
        raise TimelineSchemaError(
            f"unsupported library index schema_version {data.get('schema_version')!r}"
        )

    entries: list[SongIndexEntry] = []
    for index, raw in enumerate(data.get("songs", [])):
        if not isinstance(raw, dict):
            raise TimelineSchemaError(f"songs[{index}]: entry must be an object")
        timelines = raw.get("available_timelines", [])
        if not isinstance(timelines, list):
            raise TimelineSchemaError(f"songs[{index}].available_timelines must be a list")
        entries.append(
            SongIndexEntry(
                song_id=str(raw["song_id"]),
                title=str(raw.get("title") or raw["song_id"]),
                default_key=str(raw.get("default_key") or "C"),
                default_tempo=float(raw.get("default_tempo", 120.0)),
                meter=str(raw.get("meter") or "4/4"),
                available_timelines=tuple(str(t) for t in timelines),
                favorite=bool(raw.get("favorite", False)),
                recent_order=(
                    None if raw.get("recent_order") is None else int(raw.get("recent_order"))
                ),
                payload_ref=(None if raw.get("payload_ref") is None else str(raw.get("payload_ref"))),
            )
        )
    return SongLibraryIndex(entries)
