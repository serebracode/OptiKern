# -*- coding: utf-8 -*-
"""
Calibration layer based on the M-method.

This module inspects a Latin font in Glyphs, finds key reference glyphs
(M, H, O, V, T), and derives basic spacing calibration data.

Phase 1: metrics-based calibration (no raster yet).
Later this will be extended with silhouette / zone analysis.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# --- Data structures --------------------------------------------------------


@dataclass
class ReferenceGlyphMetrics:
    name: str
    width: float
    lsb: float
    rsb: float

    @property
    def total_sidebearings(self) -> float:
        return self.lsb + self.rsb

    @property
    def avg_sidebearing(self) -> float:
        return (self.lsb + self.rsb) / 2.0 if (self.lsb + self.rsb) != 0 else 0.0


@dataclass
class CalibrationData:
    """
    Result of the M-method based calibration.

    All values are in font units and derived from Latin reference glyphs.
    """

    # Raw metrics for reference glyphs (if found)
    refs: Dict[str, ReferenceGlyphMetrics]

    # Aggregated reference spacing values
    vertical_spacing: float      # H, M (vertical stems)
    round_spacing: float         # O (round forms)
    diagonal_spacing: float      # V (diagonals)
    topheavy_spacing: float      # T (strong top bar)
    global_avg_spacing: float    # averaged across all refs

    # Convenience scale factors (relative to vertical)
    round_scale: float           # round_spacing / vertical_spacing
    diagonal_scale: float        # diagonal_spacing / vertical_spacing
    topheavy_scale: float        # topheavy_spacing / vertical_spacing

    def get_fallback_spacing(self) -> float:
        """
        Generic spacing to use when we have no better information.
        """
        return self.global_avg_spacing or self.vertical_spacing or 0.0


# --- Internal helpers -------------------------------------------------------


# Primary Latin reference glyphs for calibration
PRIMARY_REFS = {
    "M": "M",   # max width + vertical structure
    "H": "H",   # pure vertical
    "O": "O",   # round
    "V": "V",   # diagonal
    "T": "T",   # top-heavy
}

# Simple fallbacks in case some primary glyphs are missing
FALLBACK_REFS = {
    "M": ["M", "N", "H"],
    "H": ["H", "I", "N"],
    "O": ["O", "C", "Q"],
    "V": ["V", "W", "Y"],
    "T": ["T", "F"],
}


def _find_glyph(font, names: List[str]):
    """
    Try to find the first existing glyph by list of names.
    Returns Glyph object or None.
    """
    for n in names:
        g = font.glyphs[n]
        if g is not None:
            return g
    return None


def _get_metrics_for_glyph(glyph, master_id: str) -> Optional[ReferenceGlyphMetrics]:
    """
    Extract basic metrics for a glyph in a given master.
    """
    if glyph is None:
        return None

    layer = glyph.layers[master_id]
    if layer is None:
        return None

    width = layer.width
    lsb = layer.LSB
    rsb = layer.RSB

    return ReferenceGlyphMetrics(
        name=glyph.name,
        width=float(width),
        lsb=float(lsb),
        rsb=float(rsb),
    )


def _safe_mean(values: List[float]) -> float:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else 0.0


# --- Public API -------------------------------------------------------------


def calibrate_reference_metrics(font, master) -> CalibrationData:
    """
    Perform M-method style calibration for the given font + master.

    Returns CalibrationData, which can be used by:
      - edge_features
      - raster_features
      - optical_engine
      - clustering

    This is metric-based only (Phase 1). Raster/zone information will be
    layered on top later.
    """
    master_id = master.id

    refs: Dict[str, ReferenceGlyphMetrics] = {}

    # 1. Collect metrics for each reference role (M, H, O, V, T)
    for role, primary in PRIMARY_REFS.items():
        # Try primary first, then fallbacks
        candidates = [primary] + FALLBACK_REFS.get(role, [])
        glyph = _find_glyph(font, candidates)
        if not glyph:
            print(f"[OptiKern][Calibration] Warning: no glyph found for role '{role}' (tried: {candidates})")
            continue

        metrics = _get_metrics_for_glyph(glyph, master_id)
        if metrics is None:
            print(f"[OptiKern][Calibration] Warning: no metrics for glyph '{glyph.name}' in master '{master.name}'")
            continue

        refs[role] = metrics

    if not refs:
        # Catastrophic case: nothing found. Return zeros to avoid crashes.
        print("[OptiKern][Calibration] Error: no reference glyphs found, calibration will be zeroed.")
        return CalibrationData(
            refs={},
            vertical_spacing=0.0,
            round_spacing=0.0,
            diagonal_spacing=0.0,
            topheavy_spacing=0.0,
            global_avg_spacing=0.0,
            round_scale=1.0,
            diagonal_scale=1.0,
            topheavy_scale=1.0,
        )

    # 2. Derive aggregated spacing values
    # Vertical spacing: H and M as primary vertical references
    vertical_candidates = []
    for r in ("H", "M"):
        if r in refs:
            vertical_candidates.append(refs[r].avg_sidebearing)
    vertical_spacing = _safe_mean(vertical_candidates)

    # Round spacing: O (maybe C/Q)
    round_candidates = []
    if "O" in refs:
        round_candidates.append(refs["O"].avg_sidebearing)
    round_spacing = _safe_mean(round_candidates) if round_candidates else vertical_spacing

    # Diagonal spacing: V, maybe also weight from W/Y later
    diagonal_candidates = []
    if "V" in refs:
        diagonal_candidates.append(refs["V"].avg_sidebearing)
    diagonal_spacing = _safe_mean(diagonal_candidates) if diagonal_candidates else vertical_spacing

    # Top-heavy spacing: T
    topheavy_candidates = []
    if "T" in refs:
        topheavy_candidates.append(refs["T"].avg_sidebearing)
    topheavy_spacing = _safe_mean(topheavy_candidates) if topheavy_candidates else vertical_spacing

    # Global average across all reference glyphs
    all_spacings = [m.avg_sidebearing for m in refs.values()]
    global_avg_spacing = _safe_mean(all_spacings)

    # 3. Derive scale factors relative to vertical spacing
    base = vertical_spacing or global_avg_spacing or 1.0  # avoid division by zero
    round_scale = (round_spacing / base) if base else 1.0
    diagonal_scale = (diagonal_spacing / base) if base else 1.0
    topheavy_scale = (topheavy_spacing / base) if base else 1.0

    print(
        f"[OptiKern][Calibration] vertical={vertical_spacing:.2f}, "
        f"round={round_spacing:.2f}, diagonal={diagonal_spacing:.2f}, "
        f"topheavy={topheavy_spacing:.2f}, global={global_avg_spacing:.2f}"
    )

    return CalibrationData(
        refs=refs,
        vertical_spacing=vertical_spacing,
        round_spacing=round_spacing,
        diagonal_spacing=diagonal_spacing,
        topheavy_spacing=topheavy_spacing,
        global_avg_spacing=global_avg_spacing,
        round_scale=round_scale,
        diagonal_scale=diagonal_scale,
        topheavy_scale=topheavy_scale,
    )
