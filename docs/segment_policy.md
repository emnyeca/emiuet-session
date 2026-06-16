# Segment & Meter Policy

## 概要 (JA)

手動セグメント送り（Manual Segment Advance）を基本演奏モデルとします。速いテンポで
全コードを毎回手動送りさせません。Next 1回で 1 セグメント進み、セグメント内部の
複数ステップはテンポに従って自動進行します。目安は **1.0〜2.0 秒に 1 回**の手動操作で、
**800ms 未満ごと**の操作が必要になる設計は避けます。

よく使う拍子（4/4, 3/4, 5/4, 6/8）はプリセットを持ち、それ以外は**明示的な segment map
override** とフォールバックで対応します。**全ての変拍子を自動推測することは目的にしません。**

## Why manual advance

At a fast tempo, asking the player to press Next on every chord is unmusical.
One Next press should cover a sensible musical span (a *segment*); chord changes
inside it (*steps*) advance automatically by tempo. Target manual interval:
**1.0–2.0 s**; avoid designs needing a press more often than ~800 ms.

## MeterPolicy (`model/meter.py`)

Allowed manual-advance lengths, in quarter-note beats (the universal unit):

| Meter | Allowed | Avoided (default) |
|-------|---------|-------------------|
| 4/4 | 1, 2, 4 | 3 |
| 3/4 | 1, 3 | 2 |
| 5/4 | 1, 2, 3, 5 | — (2 and 3 give the 2+3 / 3+2 groupings) |
| 6/8 | 1.5 (dotted quarter), 3 (full bar) | — |
| other / irregular | full bar, 1 (safety net) | — |

> This system supports presets for common meters plus an explicit segment-map
> override. It does **not** try to infer groupings for every possible meter.

## SegmentPolicy (`model/meter.py`)

`choose_advance_beats(meter, tempo)` picks the largest allowed length whose
duration fits the 1–2 s window; if none fit, the largest under the max; if all
are too long, the smallest. `group_indices(...)` then walks the chord durations,
closing a segment once the accumulated length reaches the chosen advance. A
single long chord becomes its own segment; several short chords combine.

`group_indices(..., override=[[...], ...])` uses an explicit grouping verbatim —
the escape hatch for irregular meters or hand-authored phrasing.

## Tempo and timing recalculation

A tune's tempo is often set when it is called in a session. The runtime accepts
a tempo update and recomputes **step timing** (each step's duration in ms, and
thus the auto-advance points inside a segment). Segment boundaries — the manual
advance structure — are built once and stay fixed; only their timing scales with
tempo. This keeps the phrasing stable while letting the same model play at any
speed. (Guarded by `tests/test_runtime.py`.)
