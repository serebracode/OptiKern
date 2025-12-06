# -*- coding: utf-8 -*-
"""
Raster-based silhouette analysis for optical kerning.

Phase 1:
- Sample each glyph layer on a simple grid.
- For each vertical column, compute ink density in
  three vertical zones: top / middle / bottom.
- Result is a RasterEdgeProfile with three arrays.

Later we can refine:
- resolution
- zone splitting (baseline/x-height/etc.)
- weighting per zone
"""

from dataclasses import dataclass
from typing import Dict, List
from AppKit import NSPoint


@dataclass
class RasterEdgeProfile:
    top: List[float]
    middle: List[float]
    bottom: List[float]


def _sample_density_in_band(path, x: float, y_min: float, y_max: float, samples: int) -> float:
    """
    Return ink density (0..1) for a vertical band [y_min, y_max]
    at given x, by uniform sampling.
    """
    if y_max <= y_min or samples <= 0:
        return 0.0

    step = (y_max - y_min) / float(samples)
    inside = 0
    total = 0

    y = y_min + step * 0.5
    for _ in range(samples):
        p = NSPoint(x, y)
        if path.containsPoint_(p):
            inside += 1
        total += 1
        y += step

    return inside / float(total) if total > 0 else 0.0


def _build_profile_for_layer(layer, columns: int = 32, samples_per_band: int = 12) -> RasterEdgeProfile:
    """
    Build top/middle/bottom density arrays for one layer.
    """
    bounds = layer.bounds
    if not bounds:
        # empty layer
        return RasterEdgeProfile(top=[], middle=[], bottom=[])

    path = layer.bezierPath or layer.completeBezierPath()
    if not path:
        return RasterEdgeProfile(top=[], middle=[], bottom=[])

    x_min = bounds.origin.x
    x_max = bounds.origin.x + bounds.size.width
    y_min = bounds.origin.y
    y_max = bounds.origin.y + bounds.size.height

    if x_max <= x_min or y_max <= y_min:
        return RasterEdgeProfile(top=[], middle=[], bottom=[])

    # Simple 3-band split: bottom / middle / top
    # Later можно заменить на baseline/x-height/ascender zones
    full_height = y_max - y_min
    band_height = full_height / 3.0

    bottom_min = y_min
    bottom_max = y_min + band_height

    middle_min = bottom_max
    middle_max = middle_min + band_height

    top_min = middle_max
    top_max = y_max

    top_profile: List[float] = []
    middle_profile: List[float] = []
    bottom_profile: List[float] = []

    # Берём колонки примерно по центру каждой полосы по X
    step_x = (x_max - x_min) / float(columns)
    x = x_min + step_x * 0.5

    for _ in range(columns):
        # bottom band
        bottom_density = _sample_density_in_band(
            path, x, bottom_min, bottom_max, samples_per_band
        )

        # middle band
        middle_density = _sample_density_in_band(
            path, x, middle_min, middle_max, samples_per_band
        )

        # top band
        top_density = _sample_density_in_band(
            path, x, top_min, top_max, samples_per_band
        )

        bottom_profile.append(bottom_density)
        middle_profile.append(middle_density)
        top_profile.append(top_density)

        x += step_x

    return RasterEdgeProfile(
        top=top_profile,
        middle=middle_profile,
        bottom=bottom_profile,
    )


def build_raster_profiles(font, glyph_list, master, columns: int = 32, samples_per_band: int = 12) -> Dict[str, RasterEdgeProfile]:
    """
    Main public function.

    Returns:
        dict[glyph_name] = RasterEdgeProfile(top[], middle[], bottom[])
    """
    master_id = master.id
    profiles: Dict[str, RasterEdgeProfile] = {}

    for glyph in glyph_list:
        layer = glyph.layers[master_id]
        if not layer:
            continue

        profile = _build_profile_for_layer(
            layer,
            columns=columns,
            samples_per_band=samples_per_band,
        )
        profiles[glyph.name] = profile

    print(f"[OptiKern][Raster] Built raster profiles for {len(profiles)} glyphs.")
    return profiles
