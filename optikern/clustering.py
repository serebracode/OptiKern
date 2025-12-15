# -*- coding: utf-8 -*-
"""
Class building (clustering) for optical kerning.

Phase 1:
- No external ML deps.
- Deterministic heuristic clustering into a small set of classes
  based on EdgeFeatures (and optionally RasterEdgeProfile).

We create separate LEFT and RIGHT classes because left/right edges
often behave differently.

Later we can replace heuristics with K-means/DBSCAN if needed,
but this baseline is stable and debuggable.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .edge_features import EdgeFeatures
from .raster_features import RasterEdgeProfile


@dataclass
class ClassifyConfig:
    """
    Thresholds for heuristic clustering.
    Tune later per style preset.
    """
    roundness_hi: float = 0.35
    diagonal_hi: float = 0.22
    vertical_hi: float = 0.30
    openness_hi: float = 1.10  # from edge_features openness (rough)

    # raster-based emphasis (optional)
    use_raster: bool = True
    raster_edge_bias: float = 0.60  # how much we trust edge "emptiness"
    raster_edge_columns: int = 6    # columns from the very edge


def _edge_emptiness(profile: RasterEdgeProfile, side: str, edge_cols: int) -> float:
    """
    Returns average emptiness (0..1) near the chosen edge.
    emptiness = 1 - ink_density.

    We use all bands top/middle/bottom.
    """
    if not profile or not profile.top:
        return 0.0

    n = len(profile.top)
    k = min(edge_cols, n)
    if k <= 0:
        return 0.0

    if side == "L":
        idxs = range(0, k)
    else:
        idxs = range(n - k, n)

    ink = 0.0
    cnt = 0
    for i in idxs:
        ink += profile.top[i] + profile.middle[i] + profile.bottom[i]
        cnt += 3
    avg_ink = ink / cnt if cnt else 0.0
    emptiness = max(0.0, min(1.0, 1.0 - avg_ink))
    return emptiness


def _pick_bucket(
    ef: EdgeFeatures,
    emptiness: Optional[float],
    cfg: ClassifyConfig,
) -> str:
    """
    Decide class bucket name based on features + optional raster emptiness.
    Returns a bucket id (without L_/R_ prefix).
    """

    # Primary shape buckets from contour features
    is_round = ef.roundness >= cfg.roundness_hi
    is_diag = ef.diagonal_mass >= cfg.diagonal_hi
    is_vert = ef.vertical_mass >= cfg.vertical_hi
    is_open = ef.openness >= cfg.openness_hi

    # Optional: use raster to detect very open edges (emptiness close to 1)
    edge_open = False
    if cfg.use_raster and emptiness is not None:
        edge_open = emptiness >= cfg.raster_edge_bias

    # Bucket selection rules (ordered)
    # 1) Strong diagonals first (V, A, W-ish)
    if is_diag and not is_round:
        if edge_open:
            return "diag_open"
        return "diag"

    # 2) Strong rounds (O, C, G)
    if is_round and not is_diag:
        if edge_open:
            return "round_open"
        return "round"

    # 3) Vertical stem shapes (H, I, N)
    if is_vert and not is_round and not is_diag:
        if edge_open:
            return "vert_open"
        return "vert"

    # 4) Open shapes (T, F, P right side often open; C open)
    if is_open or edge_open:
        return "open"

    # 5) Mixed / complex
    if is_round and is_diag:
        return "round_diag"
    if is_vert and is_diag:
        return "vert_diag"
    if is_vert and is_round:
        return "vert_round"

    return "mixed"


def build_classes(
    edge_features: Dict[str, EdgeFeatures],
    raster_profiles: Optional[Dict[str, RasterEdgeProfile]] = None,
    cfg: Optional[ClassifyConfig] = None,
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], Dict[str, str], Dict[str, str]]:
    """
    Build LEFT and RIGHT kerning classes.

    Returns:
      left_classes:  dict[className] = [glyphNames]
      right_classes: dict[className] = [glyphNames]
      glyph_to_L:    dict[glyphName] = className
      glyph_to_R:    dict[glyphName] = className

    Class names are returned WITHOUT '@' prefix.
    Suggested usage in Glyphs: '@' + className
    """
    if cfg is None:
        cfg = ClassifyConfig()

    left_classes: Dict[str, List[str]] = {}
    right_classes: Dict[str, List[str]] = {}
    glyph_to_L: Dict[str, str] = {}
    glyph_to_R: Dict[str, str] = {}

    for gname, ef in edge_features.items():
        prof = raster_profiles.get(gname) if raster_profiles else None

        # LEFT
        empt_L = _edge_emptiness(prof, "L", cfg.raster_edge_columns) if prof else None
        bucket_L = _pick_bucket(ef, empt_L, cfg)
        cname_L = f"L_{bucket_L}"
        left_classes.setdefault(cname_L, []).append(gname)
        glyph_to_L[gname] = cname_L

        # RIGHT
        empt_R = _edge_emptiness(prof, "R", cfg.raster_edge_columns) if prof else None
        bucket_R = _pick_bucket(ef, empt_R, cfg)
        cname_R = f"R_{bucket_R}"
        right_classes.setdefault(cname_R, []).append(gname)
        glyph_to_R[gname] = cname_R

    # Sort glyph lists for stable output
    for k in left_classes:
        left_classes[k] = sorted(left_classes[k])
    for k in right_classes:
        right_classes[k] = sorted(right_classes[k])

    print(
        f"[OptiKern][Clustering] Left classes: {len(left_classes)}, "
        f"Right classes: {len(right_classes)}"
    )

    return left_classes, right_classes, glyph_to_L, glyph_to_R
