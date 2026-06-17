"""Compiled harmonic timeline と Harmonic Ahead。

Auto Follow は、**原曲の小節・テンポではなく**、Digitone II へ送られた Pattern /
Step / SPEED / LENGTH に対応する **compiled timeline**（tick 範囲つきの harmonic
step 列）を基準に current chord を解決する。EUB Changes は原曲テンポと異なる
tempo/speed/length で Digitone 用 Syx を生成しうるため、Emiuet Session 側は compiled
timeline を信頼する。

ここは pure（MIDI library / platform 非依存）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TimelineBasis(Enum):
    ORIGINAL_SONG = "original_song"  # 参考用。Auto Follow では非推奨。
    DIGITONE_STEP = "digitone_step"  # Auto Follow が期待する基準。


class AheadTargetPolicy(Enum):
    NEXT_DISTINCT_CHORD = "next_distinct_chord"  # 既定
    NEXT_STEP = "next_step"


@dataclass(frozen=True)
class ChordContext:
    """Solo resolver が参照する和声文脈。

    ``core_pcs`` は resolver_core（Resolve / Core Up/Down が向かう安定音）、``lpc`` は
    LPC Up/Down が辿る音。``hard_context`` は EUB Changes 内部の制約で、resolver には
    使わず debug / display 用。
    """

    chord: str
    core_pcs: tuple[int, ...]  # resolver_core (安定音)
    lpc: tuple[int, ...]  # local pitch collection
    scale_collection: str = ""  # scale_name
    role: str = "progression"  # progression / contrast
    display: str = ""  # AIM 表示用（例 "G7 HW", "C Lyd"）
    scale_root: str = ""
    hard_context: tuple[int, ...] = ()  # 内部制約（resolver には使わない）


@dataclass(frozen=True)
class CompiledHarmonicStep:
    """Digitone Step 進行に合わせて compile された harmonic step（tick 範囲つき）。

    ``chord_context`` は default（progression）context。``contexts`` に role 別の
    context（progression / contrast）を持ち、Contrast MOD で切り替える。
    """

    id: str
    start_tick: int
    end_tick: int
    chord_context: ChordContext
    source_step_index: int | None = None
    source_label: str | None = None
    contexts: dict = field(default_factory=dict)  # role -> ChordContext
    default_context_role: str = "progression"
    mod_context_role: str = "contrast"

    def context_for(self, role: str) -> ChordContext | None:
        if role in self.contexts:
            return self.contexts[role]
        if role == self.default_context_role:
            return self.chord_context  # back-compat when contexts dict is empty
        return None

    def has_context(self, role: str) -> bool:
        return self.context_for(role) is not None


@dataclass
class CompiledTimeline:
    basis: TimelineBasis
    steps: list[CompiledHarmonicStep] = field(default_factory=list)
    original_tempo: float | None = None  # 表示・参考用
    digitone_tempo: float | None = None  # Digitone 側 Pattern/Syx のテンポ

    @property
    def total_ticks(self) -> int:
        return self.steps[-1].end_tick if self.steps else 0

    def find_step_by_tick(self, tick: int) -> CompiledHarmonicStep | None:
        """tick から current step を解決する（form をループ）。"""
        if not self.steps:
            return None
        total = self.total_ticks
        t = tick % total if total > 0 else 0
        for step in self.steps:
            if step.start_tick <= t < step.end_tick:
                return step
        return self.steps[-1]

    def index_of(self, step: CompiledHarmonicStep) -> int:
        return self.steps.index(step)

    def find_next_step(self, step: CompiledHarmonicStep) -> CompiledHarmonicStep | None:
        if not self.steps:
            return None
        return self.steps[(self.index_of(step) + 1) % len(self.steps)]

    def find_next_distinct_chord(
        self, step: CompiledHarmonicStep
    ) -> CompiledHarmonicStep | None:
        """``step`` 以降（form をまたいで）最初に chord が変わる step。無ければ None。"""
        return self._scan_distinct(step, +1)

    def find_prev_distinct_chord(
        self, step: CompiledHarmonicStep
    ) -> CompiledHarmonicStep | None:
        """実験用: 直前の異なる chord の step。"""
        return self._scan_distinct(step, -1)

    def _scan_distinct(self, step: CompiledHarmonicStep, direction: int) -> CompiledHarmonicStep | None:
        n = len(self.steps)
        if n == 0:
            return None
        start = self.index_of(step)
        current_chord = step.chord_context.chord
        for offset in range(1, n + 1):
            candidate = self.steps[(start + direction * offset) % n]
            if candidate.chord_context.chord != current_chord:
                return candidate
        return None  # 全 step が同じ chord


@dataclass
class HarmonicAhead:
    """次コード先取り（hold_until_arrival）の状態。

    Harmonic Ahead は「どの step を見るか」を変える（target_step）。Contrast MOD は
    「その step をどの context で見るか」を変える。両者は別物。
    """

    policy: AheadTargetPolicy = AheadTargetPolicy.NEXT_DISTINCT_CHORD
    active: bool = False
    target_step: CompiledHarmonicStep | None = None

    @property
    def target_step_id(self) -> str | None:
        return self.target_step.id if self.target_step is not None else None

    def clear(self) -> None:
        self.active = False
        self.target_step = None
