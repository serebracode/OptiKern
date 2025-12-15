from dataclasses import dataclass

@dataclass
class EdgeFeatures:
    vertical_mass: float
    diagonal_mass: float
    roundness: float
    openness: float
    baseline_distribution: float
    xheight_distribution: float
    top_distribution: float


def build_edge_features(font, glyphs, master):
    features = {}
    for g in glyphs:
        layer = g.layers[master.id]
        if not layer or not layer.paths:
            continue

        vertical = 0
        diagonal = 0
        curves = 0
        total = 0

        for p in layer.paths:
            for n in p.nodes:
                total += 1
                if n.type == "curve":
                    curves += 1

        features[g.name] = EdgeFeatures(
            vertical_mass=0.3,
            diagonal_mass=0.3,
            roundness=curves / max(1, total),
            openness=1.0,
            baseline_distribution=1.0,
            xheight_distribution=1.0,
            top_distribution=1.0,
        )

    print("[OptiKern][EdgeFeatures] OK")
    return features
