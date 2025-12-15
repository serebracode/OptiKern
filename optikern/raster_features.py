from dataclasses import dataclass

@dataclass
class RasterEdgeProfile:
    top: list
    middle: list
    bottom: list


def _sample_density(path, x, y1, y2, samples):
    from AppKit import NSPoint

    inside = 0
    step = (y2 - y1) / samples
    y = y1
    for _ in range(samples):
        if path.containsPoint_(NSPoint(x, y)):
            inside += 1
        y += step
    return inside / samples


def build_raster_profiles(font, glyphs, master, columns=24):
    profiles = {}

    for g in glyphs:
        layer = g.layers[master.id]
        if not layer or not layer.bounds:
            continue

        path = layer.completeBezierPath()
        b = layer.bounds

        top, mid, bot = [], [], []

        for i in range(columns):
            x = b.origin.x + b.size.width * (i + 0.5) / columns
            y0 = b.origin.y
            y1 = y0 + b.size.height / 3
            y2 = y1 + b.size.height / 3
            y3 = b.origin.y + b.size.height

            bot.append(_sample_density(path, x, y0, y1, 8))
            mid.append(_sample_density(path, x, y1, y2, 8))
            top.append(_sample_density(path, x, y2, y3, 8))

        profiles[g.name] = RasterEdgeProfile(top, mid, bot)

    print("[OptiKern][Raster] OK")
    return profiles
