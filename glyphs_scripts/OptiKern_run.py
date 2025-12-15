# -*- coding: utf-8 -*-

import os
import sys

# Ensure script directory is on sys.path (Glyphs-safe)
SCRIPT_DIR = os.path.dirname(__file__)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


from optikern.glyphs_integration import get_current_font
from optikern.glyph_filter import get_kernable_glyphs
from optikern.calibration import calibrate_reference_metrics
from optikern.edge_features import build_edge_features
from optikern.raster_features import build_raster_profiles
from optikern.clustering import build_classes, ClassifyConfig
from optikern.classes_export import write_classes_to_glyphs, ExportConfig

def run():
    font = get_current_font()
    if not font:
        print("No font open.")
        return

    master = font.selectedFontMaster
    if not master:
        print("No master selected.")
        return

    glyphs = get_kernable_glyphs(font)
    print(f"[OptiKern] Kernable glyphs: {len(glyphs)}")

    # Calibration (M-method baseline)
    calib = calibrate_reference_metrics(font, master)

    # Feature extraction
    edge = build_edge_features(font, glyphs, master)
    raster = build_raster_profiles(font, glyphs, master, columns=32, samples_per_band=12)

    # Build classes
    cfg = ClassifyConfig(use_raster=True)
    L, R, glyph_to_L, glyph_to_R = build_classes(edge, raster, cfg=cfg)

    # Export to Glyphs (safe prefix)
    export_cfg = ExportConfig(prefix="OK_", overwrite=True, clear_missing=False)
    write_classes_to_glyphs(font, L, R, cfg=export_cfg)

    print("[OptiKern] Done. Check Glyphs > Font Info > Classes for OK_* classes.")

run()
