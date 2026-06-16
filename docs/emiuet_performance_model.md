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

## 8-slot layout algorithm (`model/layout.py`)

Surface: `■ □ ■ □ ■ □ ■ □` — `■` core (even indices), `□` colour/tension (odd).

1. Drop excluded roles (approach) and, in NORMAL, suppressed roles (avoid).
2. Sort core-eligible and colour-eligible candidates by weight (stability, then
   pitch class as deterministic tie-breaks).
3. Fill 4 core slots from the core pool, 4 colour slots from the colour pool.
   Colour slots are reserved for colour; a group borrows from the other pool
   only when it is short (so we don't fill every key with chord tones when
   useful tensions exist).
4. Assign pitch classes to specific slots and pick each note's octave:
   - With a previous layout, choose the assignment that **minimises total
     per-slot register jump** (brute force over ≤24 permutations) so ii-V-I and
     similar progressions voice-lead smoothly.
   - Without one, lay notes out in ascending pitch order around the anchor.
5. **Slot voicing de-duplication** (see below).

All weights/policy live in `LayoutPolicy` — no magic numbers scattered around.
The builder is deterministic, so layouts are testable.

### Slot voicing de-duplication

A 7-note scale has only 3 non-chord tones, so the 4th colour slot necessarily
borrows a chord tone and can land on the **exact same MIDI note** as its core
slot — a dead duplicate key. The de-dup pass (enabled by
`LayoutPolicy.dedupe_voicing`, default on):

- keeps the **higher-priority** slot's note (core position first, then higher
  weight, then lower index);
- nudges the **lower-priority / colour** slot by whole octaves to a free,
  in-range note;
- moves an octave **only when it frees a playable note**, otherwise leaves it;
- never changes a pitch class or a role.

It is a voicing/playability adjustment, **not** a harmonic-analysis change.
Example (Dm7): without de-dup two keys sound MIDI 62; with it, the colour slot
moves to 74 while the core D stays at 62.

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
