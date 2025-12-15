from dataclasses import dataclass

@dataclass
class CalibrationData:
    vertical_spacing: float
    diagonal_scale: float
    round_scale: float
    topheavy_scale: float


def calibrate_reference_metrics(font, master):
    M = font.glyphs["M"]
    layer = M.layers[master.id]
    bounds = layer.bounds

    data = CalibrationData(
        vertical_spacing=bounds.size.height,
        diagonal_scale=1.0,
        round_scale=1.0,
        topheavy_scale=1.0,
    )

    print("[OptiKern][Calibration] OK")
    return data
