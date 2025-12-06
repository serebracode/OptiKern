# -*- coding: utf-8 -*-
"""
Contour-based feature extraction for optical kerning.

Phase 1:
- Compute simple geometric/optical features from outlines.
- Normalize everything using CalibrationData.
- Prepare for clustering and raster-enhanced scoring.

Later we will refine diagonal mass, zone profiles,
and curvature analysis.
"""

from dataclasses import dataclass
from typing import Dict
from .calibration import CalibrationData


@dataclass
class EdgeFeatures:
    """
    Basic contour-based features for a glyph.

    All values normalized using CalibrationData.
    """
    vertical_mass: float
    diagonal_mass: float
    roundness: float
    openness: float
    baseline_distribution: float
    xheight_distribution: float
    top_distribution: float


def _estimate_vertical_mass(layer):
    """
    Rough measurement:
    Count vertical segments vs total segments.
    """
    total = 0
    vertical = 0

    for path in layer.paths:
        for seg in path.segments:
            if len(seg) == 2:  # straight line
                x1, y1 = seg[0].x, seg[0].y
                x2, y2 = seg[1].x, seg[1].y
                total += 1
                if abs(x2 - x1) < abs(y2 - y1):  # near-vertical
                    vertical += 1

    return (vertical / total) if total > 0 else 0.0


def _estimate_diagonal_mass(layer):
    """
    Portion of diagonal segments (non-vertical, non-horizontal).
    """
    total = 0
    diag = 0

    for path in layer.paths:
        for seg in path.segments:
            if len(seg) == 2:
                x1, y1 = seg[0].x, seg[0].y
                x2, y2 = seg[1].x, seg[1].y
                dx, dy = abs(x2 - x1), abs(y2 - y1)
                total += 1
                if dx > 5 and dy > 5:  # heuristic threshold
                    diag += 1

    return (diag / total) if total > 0 else 0.0


def _estimate_roundness(layer):
    """
    Very rough estimate:
    Count curve segments vs total.
    """
    total = 0
    curves = 0

    for path in layer.paths:
        for node in path.nodes:
            if node.type == "curve":
                curves += 1
            total += 1

    return (curves / total) if total > 0 else 0.0


def _estimate_openness(layer):
    """
    Detect open forms by looking at large internal gaps.
    Phase 1: simple bounding box → should refine later.
    """
    bounds = layer.bounds
    if not bounds:
        return 0.0

    width = bounds.size.width
    height = bounds.size.height

    # Heuristic: open shapes tend to have large horizontal gaps
    openness = (width / height) if height > 0 else 0.0
    return openness


def _estimate_vertical_distribution(layer, calib: CalibrationData):
    """
    Placeholder for zone-based mass distribution.
    Phase 1: use ratio of glyph height to M-reference height.
    """
    b = layer.bounds
    if not b:
        return 0.0

    height = b.size.height
    # Normalize relative to global spacing reference (approximation)
    return height / (calib.vertical_spacing + 1.0)


def build_edge_features(font, glyph_list, master) -> Dict[str, EdgeFeatures]:
    """
    Main public function.

    Returns:
        dict[glyph_name] = EdgeFeatures(...)
    """
    master_id = master.id
    features = {}

    # Calibration is needed for normalization
    from .calibration import calibrate_reference_metrics
    calib = calibrate_reference_metrics(font, master)

    for glyph in glyph_list:
        layer = glyph.layers[master_id]
        if not layer:
            continue

        vertical_mass = _estimate_vertical_mass(layer)
        diagonal_mass = _estimate_diagonal_mass(layer)
        roundness = _estimate_roundness(layer)
        openness = _estimate_openness(layer)

        baseline_dist = _estimate_vertical_distribution(layer, calib)
        xheight_dist = baseline_dist * calib.round_scale  # placeholder
        top_dist = baseline_dist * calib.topheavy_scale   # placeholder

        # Normalize everything
        vertical_mass *= calib.vertical_spacing or 1
        diagonal_mass *= calib.diagonal_scale
        roundness *= calib.round_scale
        openness *= 1.0  # no calibration yet

        features[glyph.name] = EdgeFeatures(
            vertical_mass=vertical_mass,
            diagonal_mass=diagonal_mass,
            roundness=roundness,
            openness=openness,
            baseline_distribution=baseline_dist,
            xheight_distribution=xheight_dist,
            top_distribution=top_dist,
        )

    print(f"[OptiKern][EdgeFeatures] Extracted features for {len(features)} glyphs.")
    return features
