# MenuTitle: Run: Optical Kerning Classes
# Description: Build OK_* kerning classes using optical analysis
# Version: 0.1
# Author: Denis Serebryakov

# -*- coding: utf-8 -*-

import os, sys
import GlyphsApp

SCRIPT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

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
        print("[OptiKern] No font open.")
        return

    master = font.selectedFontMaster
    glyphs = get_kernable_glyphs(font)

    print(f"[OptiKern] Glyphs: {len(glyphs)}")

    calibrate_reference_metrics(font, master)

    edge = build_edge_features(font, glyphs, master)
    raster = build_raster_profiles(font, glyphs, master)

    cfg = ClassifyConfig(use_raster=True)
    L, R, _, _ = build_classes(edge, raster, cfg)

    export_cfg = ExportConfig(prefix="OK_", overwrite=True)
    write_classes_to_glyphs(font, L, R, export_cfg)

    print("[OptiKern] DONE")


run()
