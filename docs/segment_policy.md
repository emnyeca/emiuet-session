# Segment & Meter Policy

手動セグメント送り（manual segment advance）を基本演奏モデルとします。速いテンポで
全コードを毎回手動送りさせません。Next 1 回で 1 segment 進み、segment 内部の複数 step は
tempo に従って自動進行します。目安は **1.0〜2.0 秒に 1 回**の手動操作で、**800ms 未満
ごと**の操作が必要になる設計は避けます。

よく使う拍子（4/4, 3/4, 5/4, 6/8）は preset を持ち、それ以外は**明示的な segment map
override** と fallback で対応します。**全ての変拍子を自動推測することは目的にしません。**

## なぜ manual advance か

速いテンポで、コードごとに Next を押させるのは音楽的ではありません。Next 1 回は妥当な
音楽的スパン（*segment*）をカバーし、その内部の chord change（*step*）は tempo に従って
自動進行すべきです。目標の手動操作間隔は **1.0〜2.0 秒**、~800ms より頻繁な操作を要する
設計は避けます。

## MeterPolicy (`model/meter.py`)

許可される manual-advance length（単位は quarter-note beat = 共通単位）。

| Meter | Allowed | Avoided (default) |
|-------|---------|-------------------|
| 4/4 | 1, 2, 4 | 3 |
| 3/4 | 1, 3 | 2 |
| 5/4 | 1, 2, 3, 5 | — (2 と 3 が 2+3 / 3+2 の grouping になる) |
| 6/8 | 1.5 (dotted quarter), 3 (full bar) | — |
| その他 / 変拍子 | full bar, 1 (safety net) | — |

> このシステムは、よく使う拍子の preset と明示的な segment map override をサポートする。
> 全ての拍子について grouping を自動推測することは**しない**。

## SegmentPolicy (`model/meter.py`)

`SegmentPolicy` は、収まる中で最大の length を取るのではなく、心地よい手動操作間隔に
近づくように advance length を選びます。

既定値: `ideal_manual_interval_s = 1.0`, `min_manual_interval_s = 0.8`,
`max_manual_interval_s = 2.0`。

`choose_advance_beats(meter, tempo)`:

1. その meter の allowed length のうち、このテンポでの長さが `[min, max]` window に
   入るものを集める。
2. その中で **`ideal_manual_interval_s` に最も近い**ものを選ぶ。
3. tie のときは**短い方**を優先する。
4. window 内に候補がない場合、より遅い選択肢があるなら過速（min 未満）を避ける。なければ
   ideal に最も近い allowed length に fallback する。

advance は tempo に追従します。

| Meter / tempo | 1 beat | 2 beats | 4 beats | 選択 |
|---|---|---|---|---|
| 4/4 @ 120 | 0.5 s | 1.0 s | 2.0 s | **2 beats** |
| 4/4 @ 240 | 0.25 s | 0.5 s | 1.0 s | **4 beats** |
| 4/4 @ 60 | 1.0 s | 2.0 s | 4.0 s | **1 beat** |
| 3/4 @ 120 | 0.5 s | — | 3 beats = 1.5 s | **3 beats** |
| 5/4 @ 120 | 0.5 s | 1.0 s | 3 beats = 1.5 s, 5 = 2.5 s | **2 beats** |

5/4 では 2-beat と 3-beat の advance が 2+3 / 3+2 の grouping を表します。policy は ideal に
最も近いもの（120 BPM では 2 beats）を選びます。

`group_indices(...)` は chord の duration を辿り、累積長が選んだ advance に達したところで
segment を区切ります。長い 1 つの chord はそれ単独で 1 segment になり、短い chord が複数
あればまとまります。

`group_indices(..., override=[[...], ...])` は明示的な grouping をそのまま使います —
変拍子や手書きの phrasing 用の逃げ道です。

## tempo と timing の再計算

曲のテンポはセッションでの曲コール時に決まることが多いです。runtime は tempo 更新を
受け取り、**step timing**（各 step の ms 長、つまり segment 内部の自動進行ポイント）を
再計算します。segment 境界 — manual advance の構造 — は一度構築したら固定で、その timing
だけが tempo に応じて伸縮します。これで phrasing を安定させつつ、同じ model を任意の速度で
演奏できます。（`tests/test_runtime.py` で担保。）
