"""Small props: pallets, crates, workshop clutter."""

from voxelgen.model import Model


def pallet():
    m = Model("pallet")
    # bottom boards
    for y in (0, 7, 14):
        m.box(0, y, 0, 16, y + 2, 1, "wood_dark")
    # blocks
    for x in (1, 7, 13):
        for y in (0, 7, 14):
            m.box(x, y, 1, x + 2, y + 2, 3, "wood_dark")
            m.box(x, y, 1, x + 2, y + 0.5, 3, "wood")
    # top deck boards with nail heads
    for y in (0, 3, 6, 9, 12, 14):
        m.box(0, y, 3, 16, y + 2, 4, "wood", noise=0.03, seed=int(y))
        m.box(0, y + 1.5, 3, 16, y + 2, 3.5, "wood_dark")
        for x in (1.0, 7.0, 13.0):
            m.box(x, y + 0.5, 3, x + 0.5, y + 1.0, 4, "brass")
    # corner protectors + stencil
    for x in (0, 15):
        for y in (0, 15):
            m.box(x, y, 3, x + 1, y + 1, 4.5, "steel_light")
    m.box(5, 0, 0.25, 11, 0.5, 1, "white_panel")
    m.info(category="props", tile="1x1", mass_kg=22)
    return m


def crate():
    m = Model("crate")
    m.box(0, 0, 0, 16, 16, 13, "wood", noise=0.04, seed=53)
    m.clear(1, 1, 1, 15, 15, 12)
    # cut slat grooves one voxel deep on all four sides
    for z in (2, 5, 8, 11):
        m.clear(0, 0, z, 16, 1, z + 1)
        m.clear(0, 15, z, 16, 16, z + 1)
        m.clear(0, 0, z, 1, 16, z + 1)
        m.clear(15, 0, z, 16, 16, z + 1)
    # corner posts, top and bottom rims
    for x in (0, 14):
        for y in (0, 14):
            m.box(x, y, 0, x + 2, y + 2, 13, "wood_dark")
    m.box(0, 0, 12, 16, 16, 13, "wood_dark")
    m.box(0, 0, 12, 16, 0.5, 13, "wood")
    m.box(0, 0, 0, 16, 16, 1, "wood_dark")
    m.box(1, 1, 1, 15, 15, 2, "wood_dark")
    # steel strapping with seals
    for y in (4, 11):
        m.box(0, y, 0.5, 16, y + 0.5, 12.5, "steel")
        m.box(7, y, 0.5, 8.5, y + 0.5, 12.5, "steel_light")
    m.box(0.5, 4, 12.5, 16, 4.5, 13, "steel_dark")
    m.box(0.5, 11, 12.5, 16, 11.5, 13, "steel_dark")
    # stencil, tape and corner protectors
    m.box(5, 0, 6, 11, 1, 9, "cardboard")
    m.box(6, 0, 6.5, 10, 1, 8.5, "wood_dark")
    m.box(7, 0, 3, 9, 1, 12, "rubber_dark")
    m.box(5, 15, 6, 11, 16, 9, "cardboard")
    m.box(11, 15, 3, 13, 16, 4, "white_panel")
    m.box(1, 0, 9.5, 4, 1, 11, "hazard_yellow")
    m.box(1, 0, 9.5, 4, 1, 10, "hazard_black")
    m.box(14.5, 1, 3, 15.5, 2, 12, "steel_light")
    m.info(category="props", tile="1x1", mass_kg=40)
    return m


def cardboard_boxes():
    m = Model("cardboard_boxes")
    # pallet base
    for y in (0, 7, 14):
        m.box(0, y, 0, 16, y + 2, 1, "wood_dark")
    for x in (1, 7, 13):
        for y in (1, 7, 13):
            m.box(x, y, 1, x + 1, y + 1, 1.5, "wood_dark")
    boxes = [
        (1, 1, 1.5, 8, 8, 8, "cardboard"),
        (9, 1, 1.5, 15, 8, 6, "cardboard_dark"),
        (1, 9, 1.5, 7, 15, 10, "cardboard_dark"),
        (8, 9, 1.5, 15, 15, 7, "cardboard"),
    ]
    for x0, y0, z0, x1, y1, z1, col in boxes:
        m.box(x0, y0, z0, x1, y1, z1, col, noise=0.03, seed=int(x0 + z0))
        # tape strip down the middle of each lid
        m.box(x0, (y0 + y1) * 0.5 - 0.5, z1 - 0.5, x1, (y0 + y1) * 0.5 + 0.5, z1,
              "cardboard_dark")
        m.box(x0, y0, z1 - 0.5, x1, y0 + 0.5, z1, "cardboard_dark")
        # shipping label
        m.box(x0 + 0.5, y0, z0 + 1.5, x0 + 3.0, y0 + 0.5, z0 + 3.0, "white_panel")
        m.box(x0 + 1.0, y0, z0 + 2.0, x0 + 2.5, y0 + 0.5, z0 + 2.5,
              "steel_dark")
    m.box(4, 1, 8, 5, 8, 9, "cardboard_dark")
    m.box(9, 4, 6, 15, 5, 7, "cardboard")
    m.box(11, 15, 4, 13, 16, 5, "white_panel")
    m.info(category="props", tile="1x1")
    return m


BUILDERS = [pallet, crate, cardboard_boxes]
