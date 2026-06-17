"""Transport / clock の型。

MIDI Realtime (F8/FA/FB/FC) の受信そのものは desktop adapter 側に置き、core へは
抽象 ``TransportEvent`` として渡す（core は mido / platform に依存しない）。
"""

from __future__ import annotations

from enum import Enum

PPQN = 24  # MIDI Clock: 1 quarter note = 24 clocks


class TransportEvent(Enum):
    CLOCK = "clock"  # F8
    START = "start"  # FA  -- 頭から再生
    CONTINUE = "continue"  # FB  -- 続きから再生（Start 扱いにしない）
    STOP = "stop"  # FC


class TransportState(Enum):
    STOPPED = "stopped"
    RUNNING = "running"


class StopPolicy(Enum):
    RESET_TO_HEAD = "reset_to_head"  # 既定
    KEEP_POSITION = "keep_position"


class AdvanceMode(Enum):
    MANUAL = "manual"
    AUTO_FOLLOW = "auto_follow"


class ClockSource(Enum):
    INTERNAL = "internal"
    MIDI_CLOCK = "midi_clock"


class TransportSource(Enum):
    MANUAL = "manual"
    MIDI_TRANSPORT = "midi_transport"
