# Performance Model & 8-Slot Layout

## 概要 (JA)

ここでは 3 つのモデル（Song / Harmonic Analysis / Performance Model）の違いと、
8キーへの配置アルゴリズム、そして「スロット・ボイシング重複除去（slot voicing
de-duplication）」を説明します。重複除去は**ボイシング上の調整**であり、和声解析を
書き換えるものではありません。

## Three distinct models

| Model | What it is | Who produces it |
|-------|------------|-----------------|
| `Song` (`model/song.py`) | structure, meter, tempo, chord symbols in bars | EUB Changes import |
| `HarmonicAnalysis` (`model/analysis.py`) | per-chord theory: chord tones, LPC, scale, per-pitch role/weight | EUB Changes analysis |
| `PerformanceModel` (`model/performance.py`) | the playable 8-slot layout, grouped into segments/steps | Emiuet Session Model Builder |

They are deliberately separate. The Song says *what the tune is*; the Analysis
says *what notes mean*; the Performance Model says *how to play it on 8 keys*.

### Segment vs Step

- **Segment** — the unit advanced by one **Next** press.
- **Step** — a chord change *inside* a segment; steps auto-advance by tempo.

So at a fast tempo a segment may hold several steps that walk by themselves,
while the player presses Next at a comfortable rate.

## Harmonic Analysis: the Changes export contract

`HarmonicStep` is the shape we want a Changes exporter to fill: chord symbol,
root, quality, chord tones, LPC, selected scale + priority, retry/fallback
level, and a list of `PitchCandidate`s. Each candidate carries `pitch_class`,
`label` (degree), `role`, `weight`, `stability`, `tension`.

`PitchRole` ∈ {core, tension, altered_tension, approach, avoid, color}. Role and
weight drive slot placement.

## 8-slot layout: two rows of four (`model/layout.py`)

The surface is read as two rows (`LayoutOrientation.TWO_ROW_CORE_COLOR`, the R&D
default):

```
□ □ □ □   colour / tension line  (slots 1 3 5 7)
■ ■ ■ ■   core / high-importance line  (slots 0 2 4 6)
```

- Each **line ascends** left-to-right (`■` ascending, `□` ascending).
- The interleaved single-row reading **need not** ascend.
- The legacy single-row `ALTERNATING_ROW` (`■ □ ■ □ ■ □ ■ □`) is still supported;
  the slot indices and note assignment are identical, only the display differs.

### Algorithm

1. Drop excluded roles (approach) and, in NORMAL, suppressed roles (avoid).
2. Sort core-eligible and colour-eligible candidates by weight (stability, then
   pitch class as deterministic tie-breaks).
3. Take 4 core notes for the core line and up to 4 colour notes for the colour
   line. The colour line is reserved for colour; it only borrows a chord tone
   when a 7-note scale leaves it short (see colour fill).
4. Place notes and pick octaves:
   - **Initial step** (no previous layout, `InitialLayoutOrder.ANCHOR_LOW_TO_HIGH`):
     each line rises low→high from a C anchor (MIDI 60).
   - **Subsequent steps**: choose the assignment that **minimises total per-slot
     register jump** from the previous layout (≤24 permutations) so ii-V-I and
     similar progressions voice-lead smoothly. (Strict per-line ascent is a
     property of the initial layout; subsequent steps prioritise voice leading.)
5. **Slot voicing de-duplication** safety net (below).

All weights/policy live in `LayoutPolicy` — no magic numbers scattered around.
The builder is deterministic, so layouts are testable.

### Colour fill (when a scale leaves the colour line short)

A 7-note scale has only 3 non-chord tones, so the 4th colour slot must borrow a
chord tone. Instead of duplicating a note the core line already plays, the
borrowed tone is placed as the **nearest ascending continuation above the colour
line** — an upper-octave extension. The same pitch class at a different octave is
allowed (and musically useful on an 8-key surface); fill notes may exceed the
nominal register span.

Example (Dm7), produced deterministically:

```
□ E   G   B   C+1      colour line  (64 67 71 72)
■ C   D   F   A        core line    (60 62 65 69)
```

The spec illustration writes the colour line as `B E G C+1`; the implementation
emits `E G B C+1` — the same pitch-class set `{B, E, G, C}`, each line strictly
ascending, with `C+1` the borrowed upper-octave extension (not a dead duplicate).

### Slot voicing de-duplication

Where placement still yields an **exact same MIDI note** on two keys (mainly on
voice-led subsequent steps), the de-dup pass (`LayoutPolicy.dedupe_voicing`,
default on):

- keeps the **higher-priority** slot's note (core position first, then higher
  weight, then lower index);
- nudges the **lower-priority / colour** slot by whole octaves to a free,
  in-range note, **only when** that frees a playable note;
- never changes a pitch class or a role.

It is a voicing/playability adjustment, **not** a harmonic-analysis change. The
same pitch class at different octaves is fine; only exact duplicate MIDI notes
are removed.

## Assumptions in the sample fixture

The built-in `Dm7 | G7 | Cmaj7 | A7alt` fixture (`fixtures/sample.py`) is a
placeholder until a real Changes export is wired in. Documented assumptions:

- Weights/stability/tension values are hand-set, not Changes output.
- LPCs are the obvious parent scales (Dorian / Mixolydian / Ionian / Altered).
- The 11 is marked `avoid` on G7 and Cmaj7 (suppressed in NORMAL).
- **A7alt** core is taken as the underlying A7 chord tones (A C# E G), with the
  altered notes modelled as `altered_tension`/`color`. The natural 5th is kept
  as a core tone for the 8-key surface even though a strict altered scale omits
  it. If this diverges from the Changes theory spec, the exporter is the source
  of truth and this fixture should be regenerated.
