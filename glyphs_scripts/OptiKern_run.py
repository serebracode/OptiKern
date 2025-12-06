# -*- coding: utf-8 -*-
# OptiKern entry point for Glyphs

from optikern.glyphs_integration import get_current_font
from optikern.glyph_filter import get_kernable_glyphs
from optikern.calibration import calibrate_reference_metrics
from optikern.edge_features import build_edge_features
from optikern.raster_features import build_raster_profiles
from optikern.clustering import build_classes
from optikern.optical_engine import compute_all_class_pairs
from optikern.kerning_cleanup import cleanup_pairs

def run():
    font = get_current_font()
    if not font:
        print("No font open.")
        return

    master = font.selectedFontMaster

    glyphs = get_kernable_glyphs(font)
    refs = calibrate_reference_metrics(font, master)
    edge = build_edge_features(font, glyphs, master)
    raster = build_raster_profiles(font, glyphs, master)
    L, R = build_classes(edge)
    raw = compute_all_class_pairs(L, R, config={})
    cleaned = cleanup_pairs(raw)

    print("OptiKern finished.")

run()
