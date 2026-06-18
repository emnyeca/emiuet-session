"""Song payload and library index models for Emiuet Session.

These models describe the lightweight shape the device reads. Changes remains
responsible for chord analysis and context generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.timeline import (
    CompiledTimeline,
    RuntimeTransposePolicy,
    TimelineAdvanceMode,
    TimelineBasis,
    default_runtime_transpose_policy,
)


@dataclass(frozen=True)
class SessionTimeline:
    id: str
    advance_mode: TimelineAdvanceMode
    timeline_basis: TimelineBasis
    compiled_timeline: CompiledTimeline
    runtime_transpose_policy: RuntimeTransposePolicy | None = None
    device: str | None = None

    def __post_init__(self) -> None:
        if self.runtime_transpose_policy is None:
            object.__setattr__(
                self,
                "runtime_transpose_policy",
                default_runtime_transpose_policy(self.advance_mode, self.timeline_basis),
            )


@dataclass(frozen=True)
class SongPayload:
    song_id: str
    title: str
    default_key: str
    default_tempo: float
    meter: str
    timelines: tuple[SessionTimeline, ...] = ()

    def timeline_by_id(self, timeline_id: str) -> SessionTimeline:
        for timeline in self.timelines:
            if timeline.id == timeline_id:
                return timeline
        raise KeyError(f"timeline not found: {timeline_id}")


@dataclass(frozen=True)
class SongIndexEntry:
    song_id: str
    title: str
    default_key: str
    default_tempo: float
    meter: str
    available_timelines: tuple[str, ...]
    favorite: bool = False
    recent_order: int | None = None
    payload_ref: str | None = None


@dataclass
class SongLibraryIndex:
    songs: list[SongIndexEntry] = field(default_factory=list)

    def entry_by_id(self, song_id: str) -> SongIndexEntry:
        for entry in self.songs:
            if entry.song_id == song_id:
                return entry
        raise KeyError(f"song not found: {song_id}")

