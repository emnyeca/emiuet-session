"""Data models: Song reference, Harmonic Analysis, and Performance Model.

These three are deliberately distinct (see docs/emiuet_performance_model.md):

- Song            : structure + chord symbols (what EUB Changes imports).
- HarmonicAnalysis: per-chord theory result (what EUB Changes computes).
- PerformanceModel: Emiuet-Session-specific playable layout (what we build here).
"""
