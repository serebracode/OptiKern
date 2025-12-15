# -*- coding: utf-8 -*-
"""
Export kerning classes into Glyphs.

Creates/updates Glyphs classes:
  @L_...
  @R_...

Phase 1:
- deterministic overwrite mode (safe for testing)
- optional prefix to avoid trashing existing classes
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ExportConfig:
    prefix: str = "OK_"          # to avoid messing with existing classes
    overwrite: bool = True       # overwrite existing class definition
    clear_missing: bool = False  # if True, delete classes that are not in current run


def _normalize_class_name(name: str, cfg: ExportConfig) -> str:
    """
    Ensure class name has prefix and no leading '@' (Glyphs stores without '@').
    """
    n = name[1:] if name.startswith("@") else name
    if cfg.prefix and not n.startswith(cfg.prefix):
        n = cfg.prefix + n
    return n


def _ensure_class(font, class_name: str):
    """
    Find existing GSClass by name or create a new one.
    """
    for c in font.classes:
        if c.name == class_name:
            return c

    # Create new class
    new_class = font.classes.appendNewClass(class_name)
    return new_class


def write_classes_to_glyphs(
    font,
    left_classes: Dict[str, List[str]],
    right_classes: Dict[str, List[str]],
    cfg: Optional[ExportConfig] = None,
):
    """
    Create/update Glyphs classes based on dictionaries:
      left_classes["L_round"] = ["O", "Q", ...]
      right_classes["R_diag"] = ["V", "W", ...]

    Writes:
      class name: OK_L_round, OK_R_diag
      class code: "O Q ..." (space-separated)
    """
    if cfg is None:
        cfg = ExportConfig()

    desired_names = set()

    def write_one(class_key: str, glyph_names: List[str]):
        class_name = _normalize_class_name(class_key, cfg)
        desired_names.add(class_name)

        c = _ensure_class(font, class_name)
        code = " ".join(glyph_names)

        if (not cfg.overwrite) and c.code:
            # keep existing
            return

        c.code = code
        c.automatic = False  # we manage it
        return

    # Write LEFT
    for key, glyphs in left_classes.items():
        write_one(key, glyphs)

    # Write RIGHT
    for key, glyphs in right_classes.items():
        write_one(key, glyphs)

    # Optionally clear old classes from previous runs
    if cfg.clear_missing:
        to_delete = []
        for c in font.classes:
            if cfg.prefix and c.name.startswith(cfg.prefix):
                if c.name not in desired_names:
                    to_delete.append(c)
        for c in to_delete:
            font.classes.remove(c)

    print(
        f"[OptiKern][Export] Wrote {len(left_classes)} left + {len(right_classes)} right classes "
        f"(prefix='{cfg.prefix}')"
    )

    return {
        "left_count": len(left_classes),
        "right_count": len(right_classes),
        "prefix": cfg.prefix,
    }
