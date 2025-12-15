def get_kernable_glyphs(font):
    return [
        g for g in font.glyphs
        if g.export and g.layers and not g.name.startswith("_")
    ]
