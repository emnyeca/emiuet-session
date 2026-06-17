"""Performance mode -- 演奏面の解釈方法。

- ChordMode : 既存の固定 slot / 2 段 4 列コード配置。コード確認・比較用に維持。
- SoloMode  : キーを旋律ジェスチャーとして扱う（Relative Melodic Resolver）。今後の主軸。
- BassistMode: 予約のみ（Root/Fifth/walking など将来モード）。v0 では未実装。
"""

from __future__ import annotations

from enum import Enum


class PerformanceMode(Enum):
    CHORD = "chord"
    SOLO = "solo"
    BASSIST = "bassist"  # 予約。runtime は未実装。
