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

`SegmentPolicy` chooses the advance length by aiming for a comfortable manual
operation interval, **not** by taking the largest length that fits.

Defaults: `ideal_manual_interval_s = 1.0`, `min_manual_interval_s = 0.8`,
`max_manual_interval_s = 2.0`.

`choose_advance_beats(meter, tempo)`:

1. Collect the meter's allowed lengths whose duration at this tempo lands in the
   `[min, max]` window.
2. Among those, pick the one **closest to `ideal_manual_interval_s`**.
3. On a tie, prefer the **shorter** advance.
4. If none land in the window, avoid the too-fast (below-min) lengths when any
   slower option exists; otherwise fall back to the allowed length closest to
   the ideal.

So advance tracks tempo:

| Meter / tempo | 1 beat | 2 beats | 4 beats | chosen |
|---|---|---|---|---|
| 4/4 @ 120 | 0.5 s | 1.0 s | 2.0 s | **2 beats** |
| 4/4 @ 240 | 0.25 s | 0.5 s | 1.0 s | **4 beats** |
| 4/4 @ 60 | 1.0 s | 2.0 s | 4.0 s | **1 beat** |
| 3/4 @ 120 | 0.5 s | — | 3 beats = 1.5 s | **3 beats** |
| 5/4 @ 120 | 0.5 s | 1.0 s | 3 beats = 1.5 s, 5 = 2.5 s | **2 beats** |

For 5/4 the 2-beat and 3-beat advances express the 2+3 / 3+2 groupings; the
policy chooses the one nearest the ideal interval (2 beats at 120 BPM).

`group_indices(...)` then walks the chord durations, closing a segment once the
accumulated length reaches the chosen advance. A single long chord becomes its
own segment; several short chords combine.

`group_indices(..., override=[[...], ...])` uses an explicit grouping verbatim —
the escape hatch for irregular meters or hand-authored phrasing.

## Tempo and timing recalculation

A tune's tempo is often set when it is called in a session. The runtime accepts
a tempo update and recomputes **step timing** (each step's duration in ms, and
thus the auto-advance points inside a segment). Segment boundaries — the manual
advance structure — are built once and stay fixed; only their timing scales with
tempo. This keeps the phrasing stable while letting the same model play at any
speed. (Guarded by `tests/test_runtime.py`.)
