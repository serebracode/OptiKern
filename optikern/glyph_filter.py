def get_kernable_glyphs(font):
    glyphs = []
    for g in font.glyphs:
        if g.export and not g.category in ["Mark", "Separator"]:
            glyphs.append(g)
    return glyphs
