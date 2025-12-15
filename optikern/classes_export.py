from dataclasses import dataclass

@dataclass
class ExportConfig:
    prefix: str = "OK_"
    overwrite: bool = True


def write_classes_to_glyphs(font, L, R, cfg):
    for cname, glyphs in {**L, **R}.items():
        name = cfg.prefix + cname
        c = font.classes[name] if name in font.classes else font.classes.appendNewClass(name)
        c.code = " ".join(sorted(glyphs))
        c.automatic = False

    print("[OptiKern][Export] OK")
