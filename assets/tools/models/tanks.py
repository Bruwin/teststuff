"""Storage: bulk tanks, horizontal pressure vessels, silo and drums."""

from voxelgen.model import Model
from voxelgen import details as D


def _nozzle_bolts(m, axis, c0, u, v, r, t=0.5):
    """Bolt ring around a flange facing `axis`."""
    import math
    for i in range(8):
        a = i * math.pi / 4
        du, dv = (r + 0.6) * math.cos(a), (r + 0.6) * math.sin(a)
        if axis == 0:
            m.box(c0 + t, u + du - 0.25, v + dv - 0.25, c0 + t + 0.5,
                  u + du + 0.25, v + dv + 0.25, "brass")
        elif axis == 1:
            m.box(u + du - 0.25, c0 + t, v + dv - 0.25, u + du + 0.25,
                  c0 + t + 0.5, v + dv + 0.25, "brass")
        else:
            m.box(u + du - 0.25, v + dv - 0.25, c0 + t, u + du + 0.25,
                  v + dv + 0.25, c0 + t + 0.5, "brass")
    return m


def water_tank():
    m = Model("water_tank")
    m.box(0, 0, 0, 32, 32, 2, "concrete_dark")
    D.hazard_plinth(m, 0, 0, 32, 32, 0, 2, period=3.0)
    # support skirt with bolt pads
    m.tube(2, 2, 16, 16, 8, 13, 2, "steel_dark")
    m.cyl(2, 9, 16, 16, 0.5, 13.2, "steel_light")
    for x, y in ((3, 3), (25, 25), (3, 25), (25, 3)):
        m.box(x, y, 0, x + 4, y + 4, 3, "concrete")
        m.box(x + 0.5, y + 0.5, 3, x + 3.5, y + 3.5, 4, "steel_dark")
        m.bolts((x + 1.0, y + 0.5, 3.5), (x + 3.0, y + 0.5, 3.5), 2, size=0.4)
    # shell
    m.cyl(2, 8, 16, 16, 32, 14, "galv", noise=0.012, seed=23)
    for z in (14, 22, 30, 37):
        m.cyl(2, z, 16, 16, 1, 14.4, "steel_dark")
        m.cyl(2, z + 0.5, 16, 16, 0.5, 14.1, "steel_light")
    D.panel_seams(m, 2, 2, 30, 30, 8, 40, step=7.0, axis="x", col="steel_dark")
    # domed roof
    for i, r in enumerate((13.2, 11.6, 9.4, 6.6, 3.4)):
        m.cyl(2, 40 + i, 16, 16, 1, r, "steel_light")
    m.cyl(2, 40, 16, 16, 2, 14, "steel")
    m.box(14, 14, 45, 18, 18, 47, "steel_dark")     # manway
    m.cyl(2, 45, 16, 16, 1, 3, "galv")
    m.cyl(2, 46, 16, 16, 2, 2, "iron")
    _nozzle_bolts(m, 2, 46, 16, 16, 2.4)
    # vent + safety valve
    m.cyl(2, 44, 10, 16, 4, 1.4, "brass")
    m.cyl(2, 47, 10, 16, 1, 1.9, "steel_dark")
    m.cyl(2, 43, 22, 22, 5, 1.8, "steel_dark")
    m.cyl(2, 47, 22, 22, 1, 2.4, "brass")
    # ladder up the front with a cage
    D.ladder(m, 13.0, 19.0, 0.0, 2.0, 44.0, rungs=4.0)
    for z in range(10, 44, 8):
        m.box(11, 0, z, 21, 0.5, z + 0.5, "steel_dark")   # cage hoops
        m.box(11, 0, z, 11.5, 2, z + 0.5, "steel_dark")
        m.box(20.5, 0, z, 21, 2, z + 0.5, "steel_dark")
    # level gauge on the front face
    m.box(6, 0, 12, 8, 2, 34, "steel_dark")
    m.box(6.25, 0, 14, 7.75, 1, 32, "glass")
    m.box(6.25, 0, 18, 7.75, 1, 22, "water_light")
    m.bolts((6.0, 0.5, 12.5), (7.5, 0.5, 12.5), 2, size=0.25)
    m.bolts((6.0, 0.5, 33.0), (7.5, 0.5, 33.0), 2, size=0.25)
    # inlet / outlet nozzles with bolted flanges
    m.cyl(0, 0, 16, 10, 6, 3, "galv")
    m.cyl(0, 0, 16, 10, 1, 4, "steel_dark")
    _nozzle_bolts(m, 0, 0, 16, 10, 3.2, t=0.0)
    m.cyl(2, 12, 24, 24, 4, 3, "galv")
    m.cyl(2, 12, 24, 24, 0.5, 4, "steel_dark")
    # instrument pod
    D.control_pod(m, 24.0, 0.0, 20.0, w=5.0, h=6.0, depth=1.5)
    D.gauge_cluster(m, 24.0, 0.0, 27.5, n=2, gap=3.0, size=1.5)
    D.nameplate(m, 10.0, 0.0, 5.0, w=5.0, h=1.2)
    m.port("in", (0, 16, 10), (-1, 0, 0), "fluid", "fill nozzle")
    m.port("out", (24, 24, 12), (0, 0, -1), "fluid", "drain")
    m.port("vent", (10, 16, 48), (0, 0, 1), "gas")
    m.info(category="storage", tile="2x2", capacity_l=24000)
    return m


def gas_tank():
    """Horizontal LPG/bullet tank with saddle supports and a valve cluster."""
    m = Model("gas_tank")
    import math
    m.box(0, 2, 0, 48, 26, 2, "concrete_dark")
    D.hazard_plinth(m, 0, 2, 48, 26, 0, 2, period=3.0)
    # shell along x with domed ends
    m.cyl(0, 8, 14, 13, 32, 10, "galv", noise=0.012, seed=29)
    for i in range(1, 6):
        r = 10 * math.sqrt(max(0.0, 1 - (i / 6.2) ** 2))
        m.cyl(0, 8 - i, 14, 13, 1, r, "galv")
        m.cyl(0, 40 + i - 1, 14, 13, 1, r, "galv")
    # bands + hazard stripe
    for x in (10, 36):
        m.cyl(0, x, 14, 13, 1, 10.4, "steel_dark")
    for x in (20, 26):
        m.cyl(0, x, 14, 13, 1, 10.3, "hazard_yellow")
    D.panel_seams(m, 4, 4, 44, 24, 8, 24, step=8.0, axis="x", col="steel_dark")
    # saddles
    for x in (12, 34):
        m.box(x, 4, 0, x + 4, 24, 6, "steel_dark")
        m.box(x - 1, 3, 0, x + 5, 25, 2, "concrete_dark")
        m.box(x - 0.5, 4, 2, x + 4.5, 24, 3.5, "steel")
        m.bolts((x - 0.5, 3.5, 2.5), (x + 4.0, 3.5, 2.5), 4, size=0.4)
    # valve cluster on top
    m.box(21, 11, 22, 27, 17, 25, "steel_dark")
    m.box(22, 12, 25, 26, 16, 26, "steel_light")
    m.cyl(2, 25, 23, 14, 6, 1.8, "brass")
    m.tube(2, 30, 23, 14, 1, 4.4, 2.4, "red")
    m.cyl(2, 30, 23, 14, 2, 1.4, "steel_dark")
    m.cyl(2, 26, 24, 13, 4, 1.2, "galv")
    m.cyl(2, 26, 24, 13, 1, 2, "steel_dark")
    D.gauge(m, 21.0, 10.5, 21.5, size=2.0)
    D.nameplate(m, 8.0, 4.0, 4.0, w=6.0, h=1.5)
    # end manway + drain
    m.cyl(0, 43, 14, 13, 2, 5, "steel_dark")
    m.cyl(0, 45, 14, 13, 1, 3.4, "galv")
    _nozzle_bolts(m, 0, 45, 14, 13, 3.6, t=0.0)
    m.cyl(2, 3, 20, 13, 5, 1.6, "galv")
    m.cyl(2, 3, 20, 13, 1, 2.2, "steel_dark")
    # sun shade slats over the top
    for x in range(12, 38, 4):
        m.box(x, 9, 21, x + 2, 19, 22, "steel_light")
        m.box(x + 0.5, 9, 22, x + 1.5, 19, 22.5, "steel_dark")
    # access ladder at the right end
    D.ladder(m, 44.0, 47.5, 4.0, 2.0, 24.0, rungs=4.0)
    m.port("in", (0, 14, 13), (-1, 0, 0), "gas", "fill point")
    m.port("out", (24, 14, 31), (0, 0, 1), "gas", "vapour take-off")
    m.port("drain", (20, 14, 6), (0, 0, -1), "fluid")
    m.info(category="storage", tile="3x2", capacity_l=18000)
    return m


def silo():
    m = Model("silo")
    m.box(0, 0, 0, 32, 32, 2, "concrete_dark")
    D.hazard_plinth(m, 0, 0, 32, 32, 0, 2, period=3.0)
    # four legs with bolt pads and gussets
    for x, y in ((1, 1), (27, 27), (1, 27), (27, 1)):
        m.box(x, y, 0, x + 4, y + 4, 18, "steel_dark")
        m.box(x + 0.5, y + 0.5, 18, x + 3.5, y + 3.5, 19, "steel_light")
        m.box(x - 1, y - 1, 0, x + 5, y + 5, 2, "concrete")
        m.bolts((x - 0.5, y - 0.5, 1.0), (x + 3.5, y - 0.5, 1.0), 3, size=0.4)
        # gusset plate up to the barrel
        m.box(x + 1.0, y + 1.0, 4, x + 3.0, y + 3.0, 12, "steel")
    # slim ring bracing
    for z in (8, 14):
        m.box(4, 1, z, 28, 2, z + 1, "steel")
        m.box(4, 30, z, 28, 31, z + 1, "steel")
        m.box(1, 4, z, 2, 28, z + 1, "steel")
        m.box(30, 4, z, 31, 28, z + 1, "steel")
        m.bolts((5.0, 1.0, z + 0.5), (27.0, 1.0, z + 0.5), 4, size=0.4)
    # discharge cone: narrow at the bottom, wide where the barrel starts
    for z in range(4, 18):
        r = 3 + (z - 4) * (9.0 / 14.0)
        m.cyl(2, z, 16, 16, 1, r, "steel", noise=0.012, seed=31)
    m.cyl(2, 2, 16, 16, 2, 3.6, "galv")
    m.box(13, 12, 2, 19, 20, 4, "steel_dark")       # knife gate valve
    m.box(14, 13, 2, 18, 19, 2.5, "steel_light")
    m.tube(2, 1, 16, 16, 2, 4.4, 2, "red")
    m.box(19, 14, 3, 22, 18, 4, "yellow")
    # barrel + top cone
    m.cyl(2, 18, 16, 16, 28, 12, "galv", noise=0.012, seed=37)
    for z in (24, 32, 40):
        m.cyl(2, z, 16, 16, 1, 12.4, "steel_dark")
        m.cyl(2, z + 0.5, 16, 16, 0.5, 12.1, "steel_light")
    D.panel_seams(m, 4, 4, 28, 28, 20, 44, step=9.0, axis="x", col="steel_dark")
    for i, r in enumerate((11.4, 9.8, 7.6, 4.8)):
        m.cyl(2, 46 + i, 16, 16, 1, r, "steel_light")
    m.cyl(2, 50, 16, 16, 2, 3.4, "steel_dark")
    m.cyl(2, 52, 16, 16, 1, 2, "iron")
    m.cyl(2, 48, 9, 16, 3, 1.4, "brass")            # pressure relief
    m.cyl(2, 51, 9, 16, 1, 1.9, "steel_dark")
    # ladder + cage
    D.ladder(m, 28.0, 32.0, 14.0, 18.0, 48.0, rungs=4.0)
    for z in range(24, 48, 8):
        m.box(26, 13, z, 32, 14, z + 0.5, "steel_dark")
        m.box(26, 13, z, 26.5, 16, z + 0.5, "steel_dark")
    # level indicator window on the front of the barrel
    m.box(15, 5, 22, 17, 6, 44, "glass_dark")
    m.box(15, 5, 22, 17, 6, 34, "grain")
    m.box(14, 5, 21, 18, 6, 22, "steel_dark")
    m.box(14, 5, 44, 18, 6, 45, "steel_dark")
    m.bolts((14.5, 5.0, 21.5), (17.0, 5.0, 21.5), 2, size=0.25)
    # control pod + gauges + tag
    D.control_pod(m, 4.0, 0.0, 6.0, w=5.0, h=6.0, depth=1.5)
    D.gauge_cluster(m, 4.0, 0.0, 14.0, n=2, gap=3.0, size=1.5)
    D.nameplate(m, 20.0, 14.0, 20.0, w=6.0, h=1.5)
    m.port("in", (16, 32, 40), (0, 1, 0), "item", "pneumatic fill line")
    m.port("out", (16, 16, 0), (0, 0, -1), "item", "gravity discharge")
    m.info(category="storage", tile="2x2", capacity_l=30000)
    return m


def air_receiver():
    m = Model("air_receiver")
    m.box(0, 0, 0, 18, 18, 2, "concrete_dark")
    D.hazard_plinth(m, 0, 0, 18, 18, 0, 2, period=2.0)
    for x, y in ((2, 2), (14, 14), (2, 14), (14, 2)):
        m.box(x, y, 0, x + 2, y + 2, 6, "steel_dark")
        m.box(x + 0.25, y + 0.25, 6, x + 1.75, y + 1.75, 6.5, "steel_light")
        m.bolts((x + 0.25, y + 0.25, 0.5), (x + 1.5, y + 0.25, 0.5), 1, size=0.4)
    m.cyl(2, 5, 9, 9, 26, 7, "galv", noise=0.012, seed=41)
    for z in (11, 19, 26):
        m.cyl(2, z, 9, 9, 1, 7.4, "steel_dark")
    for i, r in enumerate((6.4, 4.8, 2.4)):
        m.cyl(2, 31 + i, 9, 9, 1, r, "steel_light")
        m.cyl(2, 4 - i, 9, 9, 1, r, "steel_light")
    m.cyl(2, 34, 9, 9, 2, 2, "steel_dark")
    m.cyl(2, 3, 9, 9, 1, 2, "steel_dark")
    _nozzle_bolts(m, 2, 34, 9, 9, 2.4)
    # gauge + relief valve
    m.cyl(0, 12, 2, 9, 3, 2, "steel_dark")
    D.gauge(m, 12.0, 0.0, 17.0, size=1.8)
    m.box(12.0, 0, 0.5, 17.0, 1, 17.0, "steel_dark")
    m.cyl(2, 30, 13, 13, 4, 1.2, "brass")
    m.cyl(2, 34, 13, 13, 1, 1.7, "steel_dark")
    # drain and tag
    m.cyl(2, 3, 5, 5, 3, 1.0, "galv")
    m.cyl(2, 2, 5, 5, 1, 1.4, "steel_dark")
    D.nameplate(m, 6.0, 0.0, 3.0, w=4.0, h=1.2)
    m.port("in", (0, 9, 9), (-1, 0, 0), "gas")
    m.port("out", (18, 9, 9), (1, 0, 0), "gas")
    m.info(category="fluids", tile="1x1", capacity_l=900)
    return m


def barrel():
    m = Model("barrel")
    m.cyl(2, 0, 5, 5, 17, 4.4, "teal", noise=0.05, seed=43)
    for z in (3, 12):
        m.cyl(2, z, 5, 5, 2, 4.8, "teal_dark")
        m.cyl(2, z + 1.5, 5, 5, 0.5, 4.7, "teal")
    m.cyl(2, 0, 5, 5, 1, 4.6, "steel_dark")
    m.cyl(2, 16, 5, 5, 1, 4.4, "teal_dark")
    m.cyl(2, 17, 5, 5, 1, 3.6, "teal")
    m.cyl(2, 17, 3, 5, 1, 1.2, "steel_dark")        # bungs
    m.cyl(2, 17, 7, 7, 1, 1, "steel_dark")
    m.box(1, 1, 8, 2, 4, 11, "hazard_yellow")        # hazard label
    m.box(1, 1, 9, 2, 4, 10, "hazard_black")
    m.box(4, 0, 5, 6, 1, 7, "white_panel")           # drum label
    m.port("in", (5, 5, 18), (0, 0, 1), "fluid")
    m.info(category="props", tile="1x1", capacity_l=200)
    return m


BUILDERS = [water_tank, gas_tank, silo, air_receiver, barrel]
