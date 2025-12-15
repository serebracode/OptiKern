from dataclasses import dataclass

@dataclass
class ClassifyConfig:
    use_raster: bool = True


def build_classes(edge, raster, cfg):
    L, R = {}, {}

    for name in edge.keys():
        L.setdefault("L_default", []).append(name)
        R.setdefault("R_default", []).append(name)

    print("[OptiKern][Clustering] OK")
    return L, R, {}, {}
