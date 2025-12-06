from dataclasses import dataclass

@dataclass
class EdgeFeatures:
    vertical_mass: float
    diagonal_mass: float
    roundness: float
    openness: float
    xheight_distribution: float
    top_distribution: float
    baseline_distribution: float

def build_edge_features(font, glyph_list, master):
    return {}
