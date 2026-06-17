"""Solo Mode -- 相対メロディ解決 (Relative Melodic Resolver v0).

Solo Mode では、各キーは固定音ではなく「旋律ジェスチャー (SoloGesture)」として
扱う。次に出す音は、直前の出力音 (last_output_note)・現在の LPC・現在のコードの
core 構成音・pending modifier から相対的に決まる。

ここは pure な演奏ロジックであり、GUI / MIDI library / platform I/O に依存しない。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

DEFAULT_ANCHOR_MIDI = 60  # last_output_note が無いときの基準 (C4)


class SoloGesture(Enum):
    REPEAT = "repeat"
    CORE_DOWN = "core_down"
    LPC_DOWN = "lpc_down"
    CHROMATIC_DOWN = "chromatic_down"
    RESOLVE = "resolve"
    CORE_UP = "core_up"
    LPC_UP = "lpc_up"
    CHROMATIC_UP = "chromatic_up"


# 方向（phrase_direction / 解決の向き）
class PhraseDirection(Enum):
    NONE = "none"
    UP = "up"
    DOWN = "down"


_UP_GESTURES = {SoloGesture.CORE_UP, SoloGesture.LPC_UP, SoloGesture.CHROMATIC_UP}
_DOWN_GESTURES = {SoloGesture.CORE_DOWN, SoloGesture.LPC_DOWN, SoloGesture.CHROMATIC_DOWN}
# skip_count を適用するジェスチャー（Chromatic / Repeat / Resolve には適用しない）
_SKIP_GESTURES = {
    SoloGesture.CORE_UP,
    SoloGesture.CORE_DOWN,
    SoloGesture.LPC_UP,
    SoloGesture.LPC_DOWN,
}


@dataclass
class SoloCursor:
    """直前の出力音と方向を保持する。"""

    last_output_note: int | None = None
    last_output_pitch_class: int | None = None
    last_gesture: SoloGesture | None = None
    phrase_direction: PhraseDirection = PhraseDirection.NONE

    def reset(self) -> None:
        self.last_output_note = None
        self.last_output_pitch_class = None
        self.last_gesture = None
        self.phrase_direction = PhraseDirection.NONE

    def update(self, gesture: SoloGesture, note: int) -> None:
        self.last_output_note = note
        self.last_output_pitch_class = note % 12
        self.last_gesture = gesture
        if gesture in _UP_GESTURES:
            self.phrase_direction = PhraseDirection.UP
        elif gesture in _DOWN_GESTURES:
            self.phrase_direction = PhraseDirection.DOWN
        # REPEAT / RESOLVE は phrase_direction を維持する。


@dataclass
class PendingNoteModifiers:
    """次の 1 発音にだけ適用される modifier。発音後に reset される。"""

    octave_shift: int = 0
    skip_count: int = 0

    def reset(self) -> None:
        self.octave_shift = 0
        self.skip_count = 0


@dataclass(frozen=True)
class SoloResolution:
    note: int
    pitch_class: int
    reason: str  # DisplayState / ログ用の trace


def _candidates(pcs: tuple[int, ...], ref: int, direction: int, inclusive: bool) -> list[int]:
    """``ref`` から ``direction`` 方向に、pitch class が ``pcs`` に含まれる MIDI note を
    近い順に並べて返す（0..127 内）。``inclusive`` のとき ``ref`` 自身も候補に含む。"""
    pc_set = set(pc % 12 for pc in pcs)
    start = ref if inclusive else ref + direction
    stop = 128 if direction > 0 else -1
    return [n for n in range(start, stop, direction) if 0 <= n <= 127 and n % 12 in pc_set]


def _nearest(pcs: tuple[int, ...], anchor: int) -> int | None:
    """``anchor`` に最も近い（同距離なら低い）pitch class 一致 note。"""
    pc_set = set(pc % 12 for pc in pcs)
    notes = [n for n in range(128) if n % 12 in pc_set]
    if not notes:
        return None
    return min(notes, key=lambda n: (abs(n - anchor), n))


def _pick(candidates: list[int], skip: int) -> int | None:
    if not candidates:
        return None
    return candidates[min(skip, len(candidates) - 1)]


def resolve_solo_note(
    gesture: SoloGesture,
    last_output_note: int | None,
    current_lpc: tuple[int, ...],
    current_core: tuple[int, ...],
    *,
    pending_octave_shift: int = 0,
    pending_skip_count: int = 0,
    anchor_midi: int = DEFAULT_ANCHOR_MIDI,
    phrase_direction: PhraseDirection = PhraseDirection.NONE,
) -> SoloResolution:
    """ジェスチャーから次の MIDI note を決定する（決定的）。

    初回（last_output_note is None）は anchor を基準にし、方向系は anchor 自身も
    含めて (>= / <=) 選ぶ。2 回目以降は直前音より strictly 上 / 下から選ぶ。
    skip_count は CORE/LPC の上下にのみ適用し、Chromatic/Repeat/Resolve には適用しない。
    octave_shift は解決後に ``*12`` 加算する。
    """
    initial = last_output_note is None
    ref = anchor_midi if initial else last_output_note
    skip = pending_skip_count if gesture in _SKIP_GESTURES else 0

    base, detail = _resolve_base(
        gesture, ref, initial, current_lpc, current_core, skip, anchor_midi, phrase_direction
    )

    note = max(0, min(127, base + pending_octave_shift * 12))
    octave_note = note
    reason = f"{gesture.name} {detail}"
    if pending_octave_shift:
        reason += f" -> {base} {pending_octave_shift:+d}*12 = {octave_note}"
    return SoloResolution(note=octave_note, pitch_class=octave_note % 12, reason=reason)


def _resolve_base(
    gesture: SoloGesture,
    ref: int,
    initial: bool,
    lpc: tuple[int, ...],
    core: tuple[int, ...],
    skip: int,
    anchor: int,
    phrase_direction: PhraseDirection,
) -> tuple[int, str]:
    if gesture is SoloGesture.REPEAT:
        if initial:
            note = _nearest(core, anchor)
            note = anchor if note is None else note
            return note, f"initial nearest core to {anchor} -> {note}"
        return ref, f"repeat last={ref} -> {ref}"

    if gesture is SoloGesture.CHROMATIC_UP:
        note = max(0, min(127, ref + 1))
        return note, f"last={ref} +1 -> {note}"
    if gesture is SoloGesture.CHROMATIC_DOWN:
        note = max(0, min(127, ref - 1))
        return note, f"last={ref} -1 -> {note}"

    # Directional gestures always move strictly up/down from the reference
    # (the anchor when initial). So initial Core/LPC Up -> the core/lpc above C4,
    # initial Core/LPC Down -> the one below. Repeat/Resolve cover the anchor itself.
    if gesture in (SoloGesture.CORE_UP, SoloGesture.LPC_UP):
        pcs = core if gesture is SoloGesture.CORE_UP else lpc
        cands = _candidates(pcs, ref, +1, inclusive=False)
        note = _pick(cands, skip)
        note = ref if note is None else note
        return note, f"last={ref} candidates={cands} skip={skip} -> {note}"
    if gesture in (SoloGesture.CORE_DOWN, SoloGesture.LPC_DOWN):
        pcs = core if gesture is SoloGesture.CORE_DOWN else lpc
        cands = _candidates(pcs, ref, -1, inclusive=False)
        note = _pick(cands, skip)
        note = ref if note is None else note
        return note, f"last={ref} candidates={cands} skip={skip} -> {note}"

    # RESOLVE
    if initial:
        note = _nearest(core, anchor)
        note = anchor if note is None else note
        return note, f"initial nearest core to {anchor} -> {note}"
    if ref % 12 in {pc % 12 for pc in core}:
        return ref, f"already on core last={ref} -> repeat {ref}"
    up = _candidates(core, ref, +1, inclusive=False)
    down = _candidates(core, ref, -1, inclusive=False)
    note = _resolve_nearest_core(ref, up, down, anchor, phrase_direction)
    return note, f"resolve last={ref} up={up[:1]} down={down[:1]} dir={phrase_direction.value} -> {note}"


def _resolve_nearest_core(
    ref: int,
    up: list[int],
    down: list[int],
    anchor: int,
    phrase_direction: PhraseDirection,
) -> int:
    if up and not down:
        return up[0]
    if down and not up:
        return down[0]
    if not up and not down:
        return ref
    dist_up = up[0] - ref
    dist_down = ref - down[0]
    if dist_up < dist_down:
        return up[0]
    if dist_down < dist_up:
        return down[0]
    # tie-break: 1) phrase_direction, 2) 下方向, 3) anchor に近い方
    if phrase_direction is PhraseDirection.UP:
        return up[0]
    if phrase_direction is PhraseDirection.DOWN:
        return down[0]
    return down[0]
