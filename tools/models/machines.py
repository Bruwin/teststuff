"""Process machines: smelter, assembler, press, motors, pumps and support kit.

Every machine shares the same detail vocabulary (hazard plinth, control pod,
bolt flanges, gauges, panel seams) so the set reads as one product line.
"""

from voxelgen.model import Model
from voxelgen import details as D


def smelter_furnace():
    m = Model("smelter_furnace")
    m.box(0, 0, 0, 32, 32, 2, "concrete_dark")
    D.hazard_plinth(m, 0, 0, 32, 32, 0, 2, period=3.0)
    m.box(2, 2, 2, 30, 30, 30, "rust", noise=0.09, seed=3)
    D.panel_seams(m, 2, 2, 30, 30, 2, 10, step=6.0, axis="x", col="rust_dark",
                  depth=0.5)
    # corner pilasters + horizontal bands
    for x, y in ((2, 2), (27, 27), (2, 27), (27, 2)):
        m.box(x, y, 2, x + 3, y + 3, 30, "steel_dark")
    for z in (10, 19, 27):
        m.box(1, 1, z, 31, 31, z + 2, "steel_dark")
        D.bolt_frame(m, 1, 1, 31, 31, z + 1.0, count_x=6, count_y=6, size=0.4)
    # tapered crown
    m.box(4, 4, 30, 28, 28, 33, "steel")
    m.box(6, 6, 33, 26, 26, 35, "steel_dark")
    D.panel_seams(m, 4, 4, 28, 28, 31, 33, step=8.0, axis="x", col="steel_dark")
    # door surround and glowing mouth
    m.box(10, 0, 4, 24, 4, 20, "steel")
    m.clear(12, 0, 6, 22, 4, 18)
    m.box(12, 1, 6, 22, 2, 18, "orange")
    m.box(13, 1, 7, 21, 2, 17, "lamp_amber")
    m.box(14, 1, 8, 20, 2, 12, "hazard_yellow")
    m.box(10, 0, 20, 24, 3, 21, "yellow")     # lintel
    m.box(9, 0, 3, 25, 3, 4, "steel_dark")    # sill
    m.bolts((10.5, 0, 4.5), (23.0, 0, 4.5), 6, size=0.4)
    m.bolts((10.5, 0, 19.0), (23.0, 0, 19.0), 6, size=0.4)
    # slag spout front-right
    m.box(24, 0, 5, 28, 4, 9, "steel_dark")
    m.box(25, 0, 6, 27, 3, 8, "orange_dark")
    m.box(24, 0, 8, 28, 4, 9, "steel_light")
    # charge chute at the back
    m.box(18, 24, 35, 28, 31, 38, "steel_dark")
    m.box(19, 25, 34, 27, 30, 35, "iron")
    m.box(20, 26, 32, 26, 29, 34, "steel_dark")
    # chimney with cladding bands and a ladder
    m.cyl(2, 33, 9, 26, 15, 4, "steel_dark", noise=0.06, seed=7)
    for z in (36, 41, 46):
        m.cyl(2, z, 9, 26, 1, 4.3, "iron")
    m.cyl(2, 47, 9, 26, 2, 5.2, "galv")
    m.box(8, 25, 48, 10, 27, 49, "rubber_dark")
    D.ladder(m, 4.0, 8.0, 26.0, 6.0, 46.0, rungs=2.5)
    m.box(3.5, 25.5, 45.5, 8.5, 30.5, 46.0, "steel_dark")
    # control pod, gauges and nameplate
    D.control_pod(m, 25.0, 0.0, 12.0, w=6.0, h=9.0, depth=2.0)
    D.gauge_cluster(m, 26.0, 0.0, 22.0, n=2, gap=3.2, size=1.6)
    D.nameplate(m, 12.0, 0.0, 21.5, w=8.0, h=1.5)
    # gas duct to the chimney
    m.cyl(0, 24, 12, 28, 8, 1.6, "galv")
    m.box(23, 10, 26, 25, 14, 30, "steel_dark")
    m.port("charge", (23, 32, 36), (0, 1, 0), "item", "top charge chute")
    m.port("tap", (26, 0, 7), (0, -1, 0), "fluid", "molten slag/ingot tap")
    m.port("exhaust", (9, 26, 49), (0, 0, 1), "gas", "chimney outlet")
    m.info(category="process", tile="2x2", power_kw=45)
    return m


def assembler():
    m = Model("assembler")
    m.box(0, 0, 0, 32, 32, 2, "concrete_dark")
    D.hazard_plinth(m, 0, 0, 32, 32, 0, 2, period=3.0)
    m.box(2, 2, 2, 30, 30, 26, "steel", noise=0.03, seed=11)
    D.panel_seams(m, 2, 30, 30, 30, 2, 26, step=7.0, axis="x", col="steel_dark")
    # open work cell: hood, table, spindle visible through the window
    m.box(4, 0, 7, 28, 4, 26, "steel_dark")
    m.clear(5, 0, 9, 27, 4, 25)
    m.clear(6, 4, 10, 26, 11, 24)
    m.box(6, 10, 10, 26, 11, 24, "navy")          # dark cell back wall
    m.box(8, 4, 10, 24, 11, 12, "steel_dark")     # machine table
    m.grate(8, 5, 12, 24, 10, 12.5, "grille", step=2.0, axis=0)
    m.box(12, 4, 12, 20, 10, 15, "iron")          # fixture
    m.box(12.5, 4, 15, 19.5, 10, 15.5, "steel_light")
    m.box(14, 4, 15, 18, 9, 21, "orange")         # spindle body
    m.box(15, 5, 21, 17, 8, 23, "steel_light")    # spindle nose
    m.box(15.5, 5.5, 23, 16.5, 7.5, 23.5, "galv")
    m.box(9, 5, 12, 12, 9, 13, "teal")            # control valve block
    m.box(9.5, 5, 13, 11.5, 8, 14, "teal_dark")
    m.stroke([(10.5, 6, 14), (10.5, 6, 18), (13, 7, 20)], 0.5, "rubber")
    # upper glazing, mullion and sill
    m.box(6, 1, 17, 26, 2, 25, "glass")
    m.box(6, 1, 17, 26, 2, 18, "glass_dark")
    m.box(15, 1, 17, 17, 2, 25, "steel_dark")
    m.box(6, 1, 25, 26, 2, 26, "steel_light")
    m.box(4, 0, 15, 6, 2, 26, "steel")
    m.box(26, 0, 15, 28, 2, 26, "steel")
    m.box(4, 0, 26, 28, 3, 27, "yellow")           # header rail
    m.box(5, 0, 6, 27, 2, 8, "steel")              # lower sill
    m.bolts((5.5, 0, 7.0), (26.0, 0, 7.0), 8, size=0.4)
    # top cooling / extraction unit
    m.box(5, 5, 26, 27, 27, 31, "steel_light")
    m.grate(6, 6, 31, 26, 26, 32, "steel_dark", step=3, axis=2)
    m.box(5, 5, 31, 27, 27, 32, "steel")
    D.bolt_frame(m, 5, 5, 27, 27, 30.0, count_x=5, count_y=5, size=0.4)
    for x in (8, 20):
        m.cyl(2, 26, x, 12, 5, 2, "galv")
        m.cyl(2, 31, x, 12, 1, 2.6, "steel_dark")
    # stack light + operator pod
    D.stack_light(m, 26.0, 26.0, 26.0)
    D.control_pod(m, 3.0, 0.0, 3.5, w=9.0, h=6.0, depth=2.0)
    D.nameplate(m, 14.0, 0.0, 4.0, w=6.0, h=1.5)
    D.gauge(m, 21.0, 0.0, 3.5, size=2.0)
    # rear cable tray
    m.box(2, 30, 20, 30, 32, 24, "galv")
    m.box(2, 30, 24, 30, 32, 24.5, "steel_dark")
    for x in (6, 16, 26):
        m.box(x, 30, 24.5, x + 0.5, 32, 25.5, "steel_dark")
    m.port("in", (0, 16, 8), (-1, 0, 0), "item")
    m.port("out", (32, 16, 8), (1, 0, 0), "item")
    m.port("power", (16, 32, 7), (0, 1, 0), "power")
    m.port("coolant", (16, 32, 22), (0, 1, 0), "fluid")
    m.info(category="process", tile="2x2", power_kw=18)
    return m


def hydraulic_press():
    m = Model("hydraulic_press")
    # pad, plinth and hazard edge
    m.box(0, 0, 0, 24, 24, 2, "concrete_dark")
    D.hazard_plinth(m, 0, 0, 24, 24, 0, 2, period=2.5)
    m.box(1, 1, 2, 23, 23, 4, "steel_dark")
    m.bolts((2.0, 1.5, 3.0), (22.0, 1.5, 3.0), 6, size=0.4)
    # bolster + anvil + lower die
    m.box(4, 4, 4, 20, 20, 10, "steel_dark")
    m.box(5, 5, 10, 19, 19, 11, "steel_light")
    m.box(7, 7, 11, 17, 17, 14, "iron")
    m.box(8, 8, 14, 16, 16, 15, "steel_light")
    m.box(8.5, 8.5, 15, 15.5, 15.5, 15.5, "galv")
    # four tie bars at the corners, with hazard bands
    for x, y in ((0, 1), (20, 1), (0, 19), (20, 19)):
        m.box(x, y, 4, x + 4, y + 4, 36, "galv")
        m.box(x, y, 4, x + 4, y + 4, 5, "steel_dark")
        m.hazard(x, y, 30, x + 4, y + 4, 33, axis="x", period=1.5)
        m.box(x, y, 33, x + 4, y + 4, 34, "steel_dark")
        m.box(x + 0.5, y + 0.5, 5, x + 3.5, y + 3.5, 6, "steel_light")
        m.bolts((x + 0.5, y + 0.5, 34.5), (x + 3.0, y + 0.5, 34.5), 2, size=0.4)
    # crown, cylinder and ram
    m.box(0, 0, 36, 24, 24, 41, "steel")
    m.box(1, 1, 41, 23, 23, 43, "steel_light")
    D.panel_seams(m, 1, 1, 23, 23, 41, 43, step=7.0, axis="x", col="steel_dark")
    D.bolt_frame(m, 0, 0, 24, 24, 37.0, count_x=6, count_y=6, size=0.4)
    m.cyl(2, 43, 12, 12, 6, 5.4, "steel_dark")
    m.cyl(2, 49, 12, 12, 2, 4.4, "galv")
    m.stroke([(17, 12, 48), (19, 16, 44), (20, 21, 30)], 1.0, "rubber")
    m.box(6, 6, 24, 18, 18, 36, "steel_light")    # ram body
    m.box(7, 7, 25, 17, 17, 26, "steel_dark")
    m.box(7, 7, 35, 17, 17, 36, "steel")
    m.box(7, 7, 16, 17, 17, 24, "galv")           # ram rod
    m.box(6, 6, 15, 18, 18, 16, "iron")           # upper die
    m.box(6, 6, 14, 18, 18, 15, "steel_light")
    m.box(7, 7, 13, 17, 17, 14, "hazard_yellow")  # die edge marker
    # front light curtains and safety relay
    for x in (4, 19):
        m.box(x, 0, 4, x + 1, 1, 30, "yellow")
        m.box(x, 0, 30, x + 1, 1, 31, "lamp_amber")
        for z in range(6, 29, 4):
            m.box(x, 0, z, x + 1, 1, z + 0.5, "hazard_black")
    m.box(5, 0, 30, 19, 1, 31, "steel_dark")
    D.control_pod(m, 3.0, 0.0, 18.0, w=4.0, h=6.0, depth=1.5)
    D.gauge(m, 5.5, 0.0, 26.0, size=2.0)
    m.box(9.0, 0, 18, 15, 1, 22, "steel_dark")    # recessed panel
    m.box(9.5, 0, 18.5, 14.5, 1, 21.5, "white_panel")
    D.nameplate(m, 14.5, 0.0, 12.0, w=4.0, h=1.5)
    # hydraulic pack at the back
    m.box(7, 19, 4, 17, 23, 13, "steel_light")
    m.grate(7.5, 19, 4.5, 16.5, 19.5, 12.5, "steel_dark", step=1.5, axis=2)
    m.cyl(2, 13, 21, 12, 3, 2.2, "copper")
    m.cyl(0, 19, 21, 8, 5, 2, "copper")
    m.port("in", (0, 12, 8), (-1, 0, 0), "item")
    m.port("out", (24, 12, 8), (1, 0, 0), "item")
    m.port("power", (12, 24, 6), (0, 1, 0), "power")
    m.port("hydraulic", (12, 12, 48), (0, 0, 1), "fluid")
    m.info(category="process", tile="2x2", power_kw=30)
    return m


def motor():
    m = Model("motor")
    m.box(0, 2, 0, 32, 18, 2, "steel_dark")        # skid
    D.hazard_plinth(m, 0, 2, 32, 18, 0.5, 2, period=3.0)
    m.box(0, 2, 2, 32, 4, 4, "steel")
    m.box(0, 16, 2, 32, 18, 4, "steel")
    for x in (3, 24):
        D.foot_pad(m, x, 1.5, w=4.0, d=3.0)
        D.foot_pad(m, x, 17.0, w=4.0, d=3.0)
    # stator housing
    m.cyl(0, 6, 10, 11, 20, 7, "steel", noise=0.04, seed=2)
    for x in range(8, 25, 2):                      # cooling fins
        m.cyl(0, x, 10, 11, 1, 8, "steel_light")
    for x in (12, 18):                             # hazard bands
        m.cyl(0, x, 10, 11, 1, 7.4, "hazard_yellow")
        m.cyl(0, x + 0.5, 10, 11, 0.5, 7.4, "hazard_black")
    # end bells and terminal box
    m.cyl(0, 4, 10, 11, 2, 7.6, "steel_dark")
    m.cyl(0, 26, 10, 11, 2, 7.6, "steel_dark")
    for i in range(6):
        import math
        a = i * math.pi / 3
        m.box(5.4 + 0.2 * math.cos(a), 10 - 6.6 * math.sin(a), 3.5,
              5.9 + 0.2 * math.cos(a), 10.2 - 6.6 * math.sin(a), 4.0, "brass")
    m.box(11, 6, 17, 21, 14, 23, "steel_dark")
    m.box(12, 7, 23, 20, 13, 24, "steel_light")
    m.box(14, 8, 24, 18, 12, 25, "iron")
    m.bolts((12.5, 7.0, 23.5), (19.5, 7.0, 23.5), 4, size=0.4)
    m.cyl(2, 25, 16, 9, 3, 1.6, "galv")
    # junction box sits on the terminal-box lid, hose loops down to it
    m.box(11.5, 6.0, 25.0, 16.5, 10.0, 27.5, "steel_dark")
    m.box(12.0, 6.5, 27.0, 16.0, 9.5, 27.5, "steel_light")
    D.cable_gland(m, 12.5, 7.0, 27.5)
    D.cable_gland(m, 14.5, 7.0, 27.5)
    m.stroke([(16, 8, 27), (18, 8, 28), (22, 8, 28)], 0.4, "rubber")
    m.box(21.5, 7.0, 27.0, 24.0, 9.0, 28.0, "steel_dark")
    # shaft + coupling
    m.cyl(0, 28, 10, 11, 5, 2, "steel_light")
    m.cyl(0, 29, 10, 11, 2, 3.2, "brass")
    m.cyl(0, 29.5, 10, 11, 1, 1.0, "steel_dark")
    # eyebolts for lifting
    for x in (10, 22):
        m.cyl(2, 17, x, 8, 2, 1, "galv")
        m.cyl(2, 19, x, 8, 0.5, 1.4, "steel_dark")
    D.nameplate(m, 1.0, 2.0, 2.5, w=6.0, h=1.2)
    m.port("shaft", (33, 10, 11), (1, 0, 0), "shaft", "drive end")
    m.port("power", (16, 8, 25), (0, 0, 1), "power")
    m.info(category="power", tile="2x1", power_kw=22)
    return m


def pump():
    m = Model("pump")
    m.box(0, 2, 0, 30, 18, 3, "steel_dark")
    D.hazard_plinth(m, 0, 2, 30, 18, 0, 3, period=2.0)
    m.box(1, 3, 3, 29, 17, 4, "steel")
    D.foot_pad(m, 1.0, 1.5, w=3.0, d=3.0)
    D.foot_pad(m, 26.0, 1.5, w=3.0, d=3.0)
    # motor
    m.cyl(0, 18, 10, 12, 10, 6, "steel", noise=0.04, seed=5)
    for x in range(20, 28, 2):
        m.cyl(0, x, 10, 12, 1, 6.8, "steel_light")
    m.cyl(0, 28, 10, 12, 2, 6.4, "steel_dark")
    m.box(20, 8, 16, 26, 12, 20, "steel_dark")
    m.box(21, 9, 20, 25, 11, 20.5, "steel_light")
    m.bolts((20.5, 8.0, 18.5), (25.5, 8.0, 18.5), 3, size=0.4)
    # coupling guard
    m.box(15, 7, 8, 19, 13, 16, "yellow")
    m.grate(15, 7.5, 9, 19, 12.5, 15, "yellow_dark", step=2, axis=2)
    m.box(15, 7, 15.5, 19, 13, 16, "hazard_black")
    # volute casing + suction
    m.cyl(0, 4, 10, 12, 10, 8, "teal")
    m.cyl(0, 13, 10, 12, 2, 8.4, "teal_dark")
    m.cyl(0, 0, 10, 12, 4, 5, "galv")
    m.cyl(0, 0, 10, 12, 1, 6, "steel_dark")
    for i in range(8):
        import math
        a = i * math.pi / 4
        m.box(0.2, 10 - 5.4 * math.sin(a), 12 + 5.4 * math.cos(a),
              1.0, 10.2 - 5.4 * math.sin(a), 12.2 + 5.4 * math.cos(a), "brass")
    # discharge up and forward
    m.cyl(2, 17, 9, 10, 9, 4.5, "teal")
    m.cyl(2, 26, 9, 10, 2, 5.5, "steel_dark")
    m.cyl(2, 28, 9, 10, 1, 6, "galv")
    m.cyl(2, 28.5, 9, 10, 0.5, 3.5, "rubber_dark")
    # gauge, drain and control pod
    D.gauge(m, 8.0, 0.0, 14.0, size=2.0)
    m.box(7.0, 0, 12.0, 11.5, 1, 14.0, "steel_dark")
    m.cyl(2, 4, 6, 10, 6, 1.2, "galv")
    m.cyl(2, 3, 6, 10, 1, 2, "steel_dark")
    D.control_pod(m, 21.0, 0.0, 6.0, w=5.0, h=6.0, depth=1.5)
    D.nameplate(m, 12.0, 0.0, 4.5, w=5.0, h=1.5)
    m.port("suction", (0, 10, 12), (-1, 0, 0), "fluid")
    m.port("discharge", (9, 10, 29), (0, 0, 1), "fluid")
    m.port("power", (23, 10, 20), (0, 0, 1), "power")
    m.info(category="fluids", tile="2x1", power_kw=11)
    return m


def compressor():
    m = Model("compressor")
    m.box(0, 2, 0, 32, 22, 2, "steel_dark")
    D.hazard_plinth(m, 0, 2, 32, 22, 0, 2, period=2.5)
    # screw compressor block
    m.box(2, 4, 2, 18, 20, 20, "steel")
    m.box(2, 4, 2, 18, 20, 4, "steel_light")
    D.panel_seams(m, 2, 20, 18, 20, 4, 16, step=5.0, axis="x", col="steel_dark")
    m.grate(3, 5, 16, 17, 19, 20, "steel_dark", step=3, axis=0)
    m.box(4, 6, 20, 16, 18, 23, "steel_light")
    D.fan_grille(m, 10, 12, 23, r=4.0)
    m.cyl(2, 23, 6, 12, 3, 2.4, "galv")            # intake filter
    m.cyl(2, 25, 6, 12, 1, 3.0, "steel_dark")
    m.grate(2, 4, 5, 4, 20, 15, "grille", step=3, axis=2)
    # receiver tank on saddles
    m.cyl(1, 3, 25, 10, 17, 7, "galv", noise=0.03, seed=9)
    for y in (6, 16):
        m.box(21, y, 0, 29, y + 3, 4, "steel_dark")
        m.box(21.5, y + 0.5, 4, 28.5, y + 2.5, 4.5, "steel_light")
    m.cyl(2, 17, 25, 10, 2, 2.5, "steel_dark")
    m.cyl(1, 0, 25, 10, 2, 4.0, "steel_dark")
    m.cyl(1, 19, 25, 10, 1, 4.0, "steel_dark")
    m.box(23, 8, 17, 27, 12, 19, "steel_light")    # pressure switch
    D.gauge(m, 27.0, 0.0, 5.0, size=2.0)
    D.gauge(m, 27.0, 0.0, 9.0, size=2.0)
    # control panel
    D.control_pod(m, 3.0, 0.0, 8.0, w=8.0, h=8.0, depth=2.0)
    D.nameplate(m, 12.0, 0.0, 3.0, w=5.0, h=1.5)
    # discharge line to the tank
    m.stroke([(16, 12, 23), (18, 12, 23), (24, 12, 22), (26, 12, 18)], 1.4,
             "copper")
    m.box(17, 11, 22, 19, 13, 24, "steel_dark")
    m.port("in", (0, 12, 10), (-1, 0, 0), "power", "electrical feed")
    m.port("air_out", (25, 18, 17), (0, 0, 1), "gas")
    m.port("power", (9, 0, 17), (0, -1, 0), "power")
    m.info(category="fluids", tile="2x2", power_kw=15)
    return m


def generator():
    m = Model("generator")
    m.box(0, 0, 0, 40, 24, 3, "steel_dark")
    m.box(1, 1, 3, 39, 23, 21, "yellow", noise=0.04, seed=13)
    m.box(0, 0, 21, 40, 24, 23, "yellow_dark")
    m.box(1, 2, 23, 39, 22, 25, "yellow")
    D.panel_seams(m, 1, 1, 39, 23, 3, 21, step=9.0, axis="x", col="yellow_dark")
    m.bolts((2.0, 0, 20.0), (38.0, 0, 20.0), 10, size=0.4)
    # louvered doors both sides
    m.grate(4, 0, 6, 18, 2, 18, "steel_dark", step=2, axis=2)
    m.grate(22, 0, 6, 36, 2, 18, "steel_dark", step=2, axis=2)
    m.box(3, 0, 4, 19, 1, 6, "yellow_dark")
    m.box(21, 0, 4, 37, 1, 6, "yellow_dark")
    m.box(19.5, 0, 5, 20.5, 1, 19, "steel_dark")
    # control side
    D.control_pod(m, 20.0, 0.0, 6.0, w=12.0, h=11.0, depth=1.5)
    D.side_fan(m, 10.5, 0.0, 12.0, r=3.5)
    D.nameplate(m, 24.0, 0.0, 3.0, w=6.0, h=1.5)
    # exhaust stack + fuel filler
    m.cyl(2, 25, 8, 20, 11, 2.6, "steel_dark")
    m.cyl(2, 34, 8, 20, 2, 3.4, "iron")
    m.cyl(2, 33, 8, 20, 2, 2.2, "rubber_dark")
    m.cyl(2, 24, 32, 20, 4, 2, "galv")
    m.cyl(2, 27, 32, 20, 1, 2.6, "red")
    # fork pockets and lifting eyes
    m.box(4, 2, 3, 10, 5, 8, "concrete_dark")
    m.box(30, 2, 3, 36, 5, 8, "concrete_dark")
    for x in (5, 35):
        m.box(x, 22, 23, x + 2, 24, 25, "steel_dark")
    m.port("power_out", (40, 12, 10), (1, 0, 0), "power", "generator terminals")
    m.port("exhaust", (8, 20, 36), (0, 0, 1), "gas")
    m.port("fuel", (32, 20, 28), (0, 0, 1), "fluid")
    m.info(category="power", tile="3x2", power_kw=-320)
    return m


def boiler():
    m = Model("boiler")
    m.box(0, 0, 0, 28, 28, 3, "concrete_dark")
    D.hazard_plinth(m, 0, 0, 28, 28, 0, 3, period=3.0)
    m.cyl(2, 3, 14, 14, 34, 11, "galv", noise=0.04, seed=17)
    for z in (10, 18, 26, 33):
        m.cyl(2, z, 14, 14, 1, 11.6, "steel_dark")
        m.cyl(2, z + 1, 14, 14, 0.5, 11.3, "steel_light")
    m.cyl(2, 37, 14, 14, 2, 11, "steel_light")
    m.cyl(2, 39, 14, 14, 3, 8, "steel")
    m.cyl(2, 42, 14, 14, 1, 6, "steel_dark")
    # burner assembly
    m.box(10, 0, 5, 18, 4, 13, "steel_dark")
    m.grate(11, 0, 6, 17, 3, 12, "rubber_dark", step=2, axis=2)
    m.box(10, 0, 12, 18, 4, 13, "hazard_black")
    m.box(6, 0, 4, 10, 6, 16, "steel_light")
    m.box(7, 0, 8, 9, 2, 14, "red")
    m.box(7.5, 0, 14, 8.5, 2, 15, "lamp_green")
    D.control_pod(m, 18.0, 0.0, 5.0, w=6.0, h=8.0, depth=2.0)
    D.gauge_cluster(m, 6.0, 0.0, 17.5, n=3, gap=3.0, size=1.5)
    m.box(5.5, 0, 16.5, 16.5, 1, 20.0, "steel_dark")
    D.nameplate(m, 19.0, 0.0, 14.5, w=5.0, h=1.5)
    # flue at the back
    m.cyl(2, 40, 20, 24, 8, 3.4, "steel_dark")
    m.cyl(2, 48, 20, 24, 2, 4.2, "iron")
    m.cyl(2, 30, 20, 24, 1, 3.8, "steel_light")
    # water column + ladder
    m.box(24, 10, 12, 27, 14, 30, "glass_dark")
    m.box(24, 11, 14, 27, 13, 28, "glass")
    m.box(24, 10, 12, 27, 14, 13, "steel_dark")
    m.box(24, 10, 29, 27, 14, 30, "steel_dark")
    D.ladder(m, 3.0, 6.0, 26.0, 4.0, 37.0, rungs=3.0)
    D.guard_rail(m, 2.0, 26.0, 27.5, 42.0, h=3.0)
    m.port("water_in", (0, 14, 30), (-1, 0, 0), "fluid")
    m.port("steam_out", (20, 24, 50), (0, 0, 1), "gas")
    m.port("fuel", (0, 12, 8), (-1, 0, 0), "fluid")
    m.info(category="fluids", tile="2x2", power_kw=4)
    return m


def control_cabinet():
    m = Model("control_cabinet")
    m.box(0, 0, 0, 16, 10, 2, "concrete_dark")
    D.hazard_plinth(m, 0, 0, 16, 10, 0, 2, period=2.0)
    m.box(1, 1, 2, 15, 9, 26, "galv", noise=0.03, seed=19)
    m.box(1, 1, 2, 15, 9, 3, "steel_dark")
    # two doors with a seam, hinge blocks
    m.box(2, 0, 4, 14, 1, 24, "steel_light")
    m.box(7, 0, 4, 8, 1, 24, "steel_dark")
    for z in (7, 20):
        m.box(1, 0, z, 2, 1, z + 1.5, "steel_dark")
        m.box(14, 0, z, 15, 1, z + 1.5, "steel_dark")
    # louvres, HMI, E-stop
    D.vent_slots(m, 2.5, 0.0, 16.5, 6.0, z1=23.0, step=1.5)
    m.box(9, 0, 18, 13, 1, 23, "steel_dark")
    m.box(9.25, 0, 18.25, 12.75, 1, 22.75, "screen")
    m.box(9.5, 0, 20.5, 12.5, 1, 21.5, "screen_glow")
    m.box(9, 0, 14.5, 10.5, 1, 15.75, "lamp_green")
    m.box(11.5, 0, 14.5, 13, 1, 15.75, "red_dark")
    m.box(11.75, 0, 14.75, 12.75, 1, 15.5, "red")
    m.box(10.5, 0, 12.5, 12.5, 1, 13.5, "yellow")
    m.bolts((2.5, 0, 5.0), (6.5, 0, 5.0), 3, size=0.4)
    m.bolts((9.5, 0, 5.0), (13.5, 0, 5.0), 3, size=0.4)
    D.nameplate(m, 2.5, 0.0, 23.5, w=4.0, h=1.2)
    # cable entry gland on top
    m.box(4, 3, 26, 12, 7, 28, "steel_dark")
    m.box(5, 4, 28, 11, 6, 29, "iron")
    m.box(0, 0, 25, 16, 1, 26, "steel_dark")
    D.cable_gland(m, 6.0, 4.0, 29.0)
    D.cable_gland(m, 8.0, 4.0, 29.0)
    m.port("power_in", (16, 5, 12), (1, 0, 0), "power")
    m.port("signal", (8, 7, 31), (0, 0, 1), "data")
    m.info(category="control", tile="1x1")
    return m


def operator_console():
    m = Model("operator_console")
    m.box(0, 0, 0, 22, 12, 2, "concrete_dark")
    D.hazard_plinth(m, 0, 0, 22, 12, 0, 2, period=2.0)
    # pedestal desk
    m.box(1, 1, 2, 21, 11, 10, "steel_dark")
    m.box(1, 1, 10, 21, 11, 12, "galv")
    m.box(2, 1, 11, 20, 10, 12.5, "steel_light")
    m.box(3, 1.5, 3, 19, 2, 9, "steel")
    m.grate(4, 1, 4, 18, 2, 8, "steel_dark", step=2, axis=0)
    D.vent_slots(m, 4.0, 1.0, 3.0, 18.0, z1=8.0, step=2.0)
    # twin monitors on a rail
    for x0 in (2.0, 12.0):
        m.box(x0, 8, 12.5, x0 + 8, 10, 13.5, "steel_dark")
        m.box(x0 + 0.5, 7.5, 13.5, x0 + 8, 10, 22, "steel_dark")
        m.box(x0 + 1, 7.0, 14.5, x0 + 7.5, 7.6, 21.5, "screen")
        m.box(x0 + 1.5, 7.0, 17.5, x0 + 7, 7.6, 19.5, "screen_glow")
        m.box(x0 + 1.5, 7.0, 15.5, x0 + 5, 7.6, 16.5, "screen_glow")
    m.box(1, 9, 20.5, 21, 11, 21.5, "steel_light")
    # keyboard, mouse and a mug
    m.box(5, 4, 12.5, 15, 8, 13, "white_panel")
    for i in range(5):
        m.box(5.5 + i * 1.9, 4.5, 13.0, 7.0 + i * 1.9, 7.5, 13.5, "steel_dark")
    m.box(4.5, 4, 13.0, 5.5, 8, 13.5, "steel_light")
    m.box(17, 5, 12.5, 19, 7, 13.5, "steel_dark")
    m.box(17.25, 5.25, 13.5, 18.75, 6.75, 14.0, "steel_light")
    m.cyl(2, 13.0, 20.0, 4.0, 2.0, 1.0, "white_panel")
    m.cyl(2, 13.0, 20.0, 4.0, 0.5, 1.2, "red")
    D.nameplate(m, 2.0, 1.0, 9.0, w=4.0, h=1.2)
    m.port("power", (22, 6, 6), (1, 0, 0), "power")
    m.port("data", (11, 12, 4), (0, 1, 0), "data")
    m.info(category="control", tile="1x1")
    return m


BUILDERS = [
    smelter_furnace,
    assembler,
    hydraulic_press,
    motor,
    pump,
    compressor,
    generator,
    boiler,
    control_cabinet,
    operator_console,
]
