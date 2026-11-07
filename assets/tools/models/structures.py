"""Plant structures: pallet racking, power substation, process chiller."""

from voxelgen.model import Model
from voxelgen import details as D


def storage_rack():
    """Two-bay pallet rack, 3 m tall, loaded with cartons."""
    m = Model("storage_rack")
    m.box(0, 0, 0, 32, 16, 2, "concrete_dark")
    # uprights with hazard feet
    for x in (1, 28):
        for y in (1, 12):
            m.box(x, y, 2, x + 3, y + 3, 46, "orange")
            m.box(x + 0.5, y + 0.5, 2, x + 2.5, y + 2.5, 46, "orange_dark")
            m.box(x - 1, y - 1, 0, x + 4, y + 4, 2, "steel_dark")
            m.box(x - 0.5, y - 0.5, 0.5, x + 3.5, y + 3.5, 2, "hazard_yellow")
            m.bolts((x - 0.5, y - 1.0, 0.5), (x + 2.5, y - 1.0, 0.5), 2, size=0.4)
    # diagonal bracing between the uprights
    for z in (6, 22, 38):
        for x in (1, 28):
            m.box(x, 1, z, x + 3, 2, z + 1, "orange_dark")
            m.box(x, 13, z, x + 3, 14, z + 1, "orange_dark")
            m.box(x + 0.5, 1, z, x + 2.5, 2, z + 0.5, "steel_dark")
    # beams, safety clips and shelf decks
    for z in (12, 28, 42):
        m.box(1, 1, z, 31, 3, z + 2, "blue")
        m.box(1, 13, z, 31, 15, z + 2, "blue")
        m.box(1, 1, z + 1.5, 31, 3, z + 2, "blue_dark")
        m.box(1, 13, z + 1.5, 31, 15, z + 2, "blue_dark")
        m.box(2, 3, z - 1, 30, 13, z, "steel_dark")
        m.grate(3, 3.5, z - 1, 29, 12.5, z - 0.5, "grille", step=2.0, axis=0)
        for x in (3, 12, 21, 28):
            m.box(x, 1.0, z + 1.5, x + 1, 3.0, z + 2.2, "steel_light")
    # goods: pallets with cartons on the lower and middle shelves
    for z, x0, w in ((13, 4, 11), (13, 17, 10), (29, 5, 9), (29, 17, 11), (43, 6, 8)):
        m.box(x0, 4, z, x0 + w, 12, z + 1, "wood_dark")
        m.box(x0, 5, z + 1, x0 + w - 1, 11, z + 6 + (x0 % 3), "cardboard",
              noise=0.03, seed=x0)
        m.box(x0 + 1, 5, z + 2, x0 + 2, 11, z + 5, "cardboard_dark")
        m.box(x0, 5, z + 4, x0 + w - 1, 11, z + 4.5, "cardboard_dark")
        m.box(x0 + 1, 5, z + 6, x0 + 3, 11, z + 6.5, "white_panel")
    # a barrel on the middle shelf
    m.cyl(2, 29, 22, 8, 9, 3.4, "teal")
    m.cyl(2, 32, 22, 8, 1, 3.8, "teal_dark")
    m.cyl(2, 37, 22, 8, 1, 3.6, "teal_dark")
    m.cyl(2, 29, 22, 8, 0.5, 3.7, "steel_dark")
    # load labels + aisle sign
    m.box(1, 0, 8, 4, 1, 12, "hazard_yellow")
    m.box(1, 0, 8, 4, 1, 8.5, "hazard_black")
    m.box(20, 0, 46, 28, 1, 48, "blue_dark")
    m.box(21, 0, 46.5, 27, 1, 47.5, "white_panel")
    m.box(22, 0, 46.5, 26, 1, 47.0, "blue")
    m.port("slot_a", (6, 8, 3), (0, 0, 1), "item", "floor pick face")
    m.port("slot_b", (6, 8, 19), (0, 0, 1), "item")
    m.info(category="storage", tile="2x1", bays=2, capacity_kg=2200)
    return m


def power_transformer():
    """Pad-mounted distribution transformer with HV bushings."""
    m = Model("power_transformer")
    m.box(0, 0, 0, 24, 24, 2, "concrete_dark")
    D.hazard_plinth(m, 0, 0, 24, 24, 0, 2, period=2.5)
    m.box(1, 1, 2, 23, 23, 3, "concrete")
    # radiator banks with tie rods
    for z in range(5, 19, 2):
        m.box(0, 4, z, 2, 20, z + 1, "steel")
        m.box(22, 4, z, 24, 20, z + 1, "steel")
        m.box(0.5, 4, z + 0.5, 2, 20, z + 1, "steel_light")
    for y in (5, 19):
        m.box(0, y, 4, 24, y + 1, 19, "steel_dark")
    m.bolts((0.0, 5.5, 4.5), (0.0, 18.0, 4.5), 4, size=0.4)
    # tank body
    m.box(2, 2, 3, 22, 22, 20, "teal", noise=0.03, seed=73)
    m.box(2, 2, 19, 22, 22, 21, "steel_light")
    m.box(3, 3, 21, 21, 21, 22, "steel_dark")
    D.panel_seams(m, 2, 22, 22, 22, 4, 18, step=6.0, axis="x", col="teal_dark")
    D.bolt_frame(m, 2, 2, 22, 22, 4.0, count_x=5, count_y=5, size=0.4)
    # HV bushings with bolt rings
    for x, y in ((6, 7), (6, 17), (12, 12)):
        m.box(x, y, 22, x + 2, y + 2, 24, "steel_light")
        m.cyl(2, 24, x + 1, y + 1, 4, 1.6, "white_panel")
        m.cyl(2, 26, x + 1, y + 1, 0.5, 2.1, "steel_dark")
        m.cyl(2, 28, x + 1, y + 1, 1, 2.1, "steel_dark")
        m.cyl(2, 28, x + 1, y + 1, 1, 1.7, "white_panel")
    # front control pod, gauges and warning labels
    D.control_pod(m, 8.0, 0.0, 5.0, w=9.0, h=11.0, depth=1.5,
                  lamp="lamp_green")
    D.gauge(m, 5.0, 0.0, 6.0, size=2.0)
    D.gauge(m, 5.0, 0.0, 11.0, size=2.0)
    m.box(4.0, 0, 4.0, 8.0, 1, 16.0, "steel_dark")
    m.box(3.0, 0, 2.5, 21.0, 1, 4.0, "hazard_yellow")
    for x in range(3, 21, 2):
        m.box(x, 0, 2.5, x + 1, 1, 4.0, "hazard_black")
    m.box(6, 0, 17, 18, 1, 19, "red")
    m.box(7, 0, 18, 17, 1, 19, "white_panel")
    m.box(8, 0, 17.5, 16, 1, 18.5, "red_dark")
    D.nameplate(m, 18.0, 0.0, 5.0, w=3.5, h=1.0)
    # earthing strap
    m.box(11, 22, 3, 13, 23, 12, "copper")
    m.box(11.5, 22, 12, 12.5, 23, 12.5, "brass")
    m.port("hv_in", (6, 7, 30), (0, 0, 1), "power", "high voltage feed")
    m.port("lv_out", (18, 22, 6), (0, 1, 0), "power", "400 V distribution")
    m.info(category="power", tile="1x1", rating_kva=630)
    return m


def cooling_chiller():
    m = Model("cooling_chiller")
    m.box(0, 0, 0, 32, 24, 2, "concrete_dark")
    D.hazard_plinth(m, 0, 0, 32, 24, 0, 2, period=2.5)
    m.box(1, 1, 2, 31, 23, 17, "steel", noise=0.03, seed=79)
    m.box(1, 1, 2, 31, 23, 4, "steel_dark")
    D.panel_seams(m, 1, 23, 31, 23, 4, 17, step=6.0, axis="x", col="steel_dark")
    # side louvres with frames
    m.grate(3, 0, 6, 15, 2, 15, "steel_dark", step=2, axis=2)
    m.grate(17, 0, 6, 29, 2, 15, "steel_dark", step=2, axis=2)
    m.grate(3, 22, 6, 29, 24, 15, "steel_dark", step=2, axis=2)
    m.box(2, 0, 5, 16, 1, 6, "steel_light")
    m.box(2, 0, 15, 16, 1, 16, "steel_light")
    m.box(16, 0, 5, 30, 1, 6, "steel_light")
    m.box(16, 0, 15, 30, 1, 16, "steel_light")
    # fan deck with two grilles
    m.box(1, 1, 17, 31, 23, 19, "steel_light")
    m.clear(7, 4, 17, 25, 20, 19)
    m.tube(2, 18, 16, 12, 3, 9.4, 2, "steel_dark")
    m.tube(2, 18, 10, 12, 3, 5.2, 1.2, "steel_dark")
    m.tube(2, 18, 22, 12, 3, 5.2, 1.2, "steel_dark")
    D.fan_grille(m, 10, 12, 18.5, r=4.4)
    D.fan_grille(m, 22, 12, 18.5, r=4.4)
    # refrigerant lines, insulation rings and a control pod
    m.cyl(0, 24, 8, 9, 8, 2, "copper")
    m.cyl(0, 24, 8, 9, 0.5, 2.6, "brass")
    m.cyl(2, 4, 26, 6, 6, 1.6, "copper")
    m.cyl(2, 9, 26, 6, 1, 2.2, "brass")
    D.control_pod(m, 20.0, 0.0, 6.0, w=8.0, h=8.0, depth=1.5)
    m.box(3, 0, 4.5, 10, 0.5, 5.5, "hazard_yellow")
    m.box(3, 0, 4.5, 10, 0.5, 5.0, "hazard_black")
    D.nameplate(m, 3.0, 0.0, 12.0, w=4.0, h=1.2)
    m.port("water_in", (0, 20, 10), (-1, 0, 0), "fluid")
    m.port("water_out", (32, 20, 10), (1, 0, 0), "fluid")
    m.port("power", (16, 24, 8), (0, 1, 0), "power")
    m.info(category="fluids", tile="2x2", power_kw=22, cooling_kw=120)
    return m


BUILDERS = [storage_rack, power_transformer, cooling_chiller]
