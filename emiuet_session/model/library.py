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
        if self.compiled_timeline.basis is not self.timeline_basis:
            raise ValueError(
                "SessionTimeline timeline_basis must match compiled_timeline.basis: "
                f"{self.timeline_basis.value!r} != {self.compiled_timeline.basis.value!r}"
            )
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
    default_timeline_id: str | None = None

    def get_timeline(self, timeline_id: str | None = None) -> SessionTimeline:
        selected_id = timeline_id or self.default_timeline_id
        if selected_id is None:
            if not self.timelines:
                raise KeyError(f"song has no timelines: {self.song_id}")
            return self.timelines[0]
        for timeline in self.timelines:
            if timeline.id == selected_id:
                return timeline
        raise KeyError(f"timeline not found in {self.song_id}: {selected_id}")

    def timeline_by_id(self, timeline_id: str) -> SessionTimeline:
        return self.get_timeline(timeline_id)


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

    def get_song(self, song_id: str) -> SongIndexEntry:
        for entry in self.songs:
            if entry.song_id == song_id:
                return entry
        raise KeyError(f"song not found: {song_id}")

    def entry_by_id(self, song_id: str) -> SongIndexEntry:
        return self.get_song(song_id)

    def find_by_title(self, query: str) -> list[SongIndexEntry]:
        needle = query.casefold()
        return [entry for entry in self.songs if needle in entry.title.casefold()]

    def list_titles(self) -> list[str]:
        return [entry.title for entry in self.songs]

    def available_timelines(self, song_id: str) -> tuple[str, ...]:
        return self.get_song(song_id).available_timelines
