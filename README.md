# OptiKern

**OptiKern** is an optical kerning engine for Glyphs App, combining contour analysis, raster silhouette evaluation, and M-method calibration.

The goal:
- automate kerning classes generation
- compute optical kerning between classes (similar to Adobe Optical)
- provide stable results across weights (Light → Heavy)
- support Latin first, Cyrillic later

## Architecture
font → glyph filtering → M-calibration →
edge features → raster features → clustering →
optical engine → kerning cleanup → export to Glyphs

## Status
Development: Phase 1 (Latin-only engine, calibration layer).
