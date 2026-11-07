"""Articulated robot arm (rigged), AGV and safety fencing."""

from voxelgen.model import Model, Rig
from voxelgen import details as D

# Joint pivots in shared world voxel space (see Rig in voxelgen.model).
SHOULDER = (12, 12, 18)
ELBOW = (12, 12, 29)
WRIST = (12, 12, 36)
FLANGE = (12, 12, 40)


def robot_arm():
    rig = Rig("robot_arm")

    base = Model("base")
    base.box(0, 0, 0, 24, 24, 1, "concrete_dark")
    D.hazard_plinth(base, 0, 0, 24, 24, 0, 1, period=2.0)
    base.box(1, 1, 1, 23, 23, 2, "steel_dark")
    for x, y in ((2, 2), (19, 19), (2, 19), (19, 2)):
        base.box(x, y, 2, x + 3, y + 3, 4, "iron")
        base.box(x + 0.25, y + 0.25, 4, x + 2.75, y + 2.75, 4.5, "steel_light")
        base.cyl(2, 4, x + 1, y + 1, 1, 1, "brass")
    base.cyl(2, 2, 12, 12, 6, 9, "steel")
    base.cyl(2, 7, 12, 12, 1, 9.4, "steel_dark")
    base.cyl(2, 8, 12, 12, 0.5, 8.6, "steel_light")
    # motor cover with fins and a connector box at the back
    base.box(17, 3, 4, 23, 9, 9, "steel_dark")
    base.grate(18, 3, 5, 22, 9, 8, "steel_light", step=1.5, axis=2)
    base.box(19, 1, 4, 23, 3, 8, "steel_light")
    D.cable_gland(base, 20.0, 1.0, 8.0)
    D.nameplate(base, 1.0, 0.0, 2.0, w=5.0, h=1.2)
    rig.part("base", base, (12, 12, 0), None, axis=None,
             note="bolted to the floor, never moves")

    turret = Model("turret")
    turret.cyl(2, 8, 12, 12, 3, 8.8, "steel_light")
    turret.cyl(2, 11, 12, 12, 1, 9.2, "steel_dark")
    turret.cyl(2, 12, 12, 12, 0.5, 8.4, "galv")
    # shoulder yoke: two upright plates carrying the arm
    for x0 in (4, 17):
        turret.box(x0, 9, 12, x0 + 3, 15, 17, "steel")
        turret.box(x0, 10, 12, x0 + 3, 14, 13, "steel_light")
        turret.bolts((x0, 9, 15.5), (x0 + 2.5, 9, 15.5), 2, size=0.3)
    turret.box(7, 9, 12, 17, 15, 14, "steel_dark")
    turret.box(8, 10, 14, 16, 14, 15, "iron")
    turret.box(20, 9, 12, 22, 15, 15, "steel")       # cable gland
    turret.stroke([(21, 14, 13), (22, 19, 9), (17, 20, 5)], 0.5, "rubber")
    turret.box(4, 9, 13, 5, 15, 14, "hazard_yellow")  # hazard sticker
    turret.box(4, 9.5, 13, 5, 10, 14, "hazard_black")
    rig.part("turret", turret, (12, 12, 8), "base", axis="z", limits=(-170, 170),
             note="base rotation")

    shoulder = Model("shoulder")
    shoulder.cyl(0, 8, 12, 18, 8, 4.6, "steel_dark")   # joint barrel
    shoulder.cyl(0, 8, 12, 18, 0.5, 5.2, "galv")
    shoulder.cyl(0, 15.5, 12, 18, 0.5, 5.2, "galv")
    shoulder.box(8, 9, 18, 16, 15, 29, "steel")        # upper arm
    shoulder.box(8, 9, 18, 9, 15, 29, "steel_light")
    shoulder.box(15, 9, 18, 16, 15, 29, "steel_light")
    shoulder.box(8, 9, 25, 16, 15, 26, "hazard_yellow")  # safety band
    shoulder.box(8, 9, 25, 16, 10, 26, "hazard_black")
    shoulder.box(8, 15, 19, 16, 19, 27, "steel_dark")  # counterweight
    shoulder.box(9, 16, 21, 15, 19, 25, "iron")
    shoulder.bolts((9, 15.5, 26.5), (14, 15.5, 26.5), 3, size=0.3)
    shoulder.cyl(2, 26, 16, 12, 3, 1.6, "galv")        # lift eye
    shoulder.stroke([(15, 12, 26), (17, 18, 23), (16, 18, 15)], 0.45, "rubber")
    rig.part("shoulder", shoulder, SHOULDER, "turret", axis="x", limits=(-60, 85),
             note="upper arm pitch")

    elbow = Model("elbow")
    elbow.cyl(0, 8, 12, 29, 8, 4.1, "steel_light")     # elbow barrel
    elbow.cyl(0, 8, 12, 29, 0.5, 4.6, "galv")
    elbow.cyl(0, 15.5, 12, 29, 0.5, 4.6, "galv")
    elbow.box(9, 10, 30, 15, 15, 36, "steel")          # forearm
    elbow.box(9, 10, 34, 15, 15, 35, "orange")         # accent band
    elbow.box(10, 9, 30, 14, 10, 35, "steel_dark")
    elbow.box(10, 15, 30, 14, 16, 35, "steel_dark")
    elbow.bolts((9.5, 9.5, 32.0), (14.0, 9.5, 32.0), 2, size=0.3)
    rig.part("elbow", elbow, ELBOW, "shoulder", axis="x", limits=(-120, 70),
             note="forearm pitch")

    wrist = Model("wrist")
    wrist.cyl(2, 36, 12, 12, 2, 3.8, "steel_dark")
    wrist.cyl(2, 36, 12, 12, 0.5, 4.3, "galv")
    wrist.box(9, 9, 38, 15, 15, 39, "galv")
    wrist.box(10, 10, 39, 14, 14, 40, "steel")
    wrist.bolts((9.5, 9.5, 38.5), (14, 9.5, 38.5), 2, size=0.3)
    rig.part("wrist", wrist, WRIST, "elbow", axis="x", limits=(-180, 180),
             note="wrist roll")

    gripper = Model("gripper")
    gripper.box(8, 9, 40, 16, 15, 41, "steel_dark")    # tool flange
    gripper.box(9, 10, 41, 15, 14, 42, "steel")
    gripper.box(9.5, 10.5, 42, 14.5, 13.5, 42.5, "galv")
    for x0 in (8, 13):                                  # two fingers, 2 voxel gap
        gripper.box(x0, 10, 41, x0 + 3, 14, 45, "galv")
        gripper.box(x0 + 1, 9, 42, x0 + 2, 15, 44, "rubber")
    gripper.box(10, 10, 41, 11, 14, 42, "lamp_green")
    # part-present sensor on the jaw
    gripper.box(14.5, 11, 43, 16, 13, 44, "steel_dark")
    gripper.box(14.75, 11, 43, 15.75, 13, 43.5, "lamp_blue")
    rig.part("gripper", gripper, FLANGE, "wrist", axis="x", limits=(0, 40),
             note="parallel two-finger gripper, 40 mm travel")

    rig.port("grasp", (12, 12, 44), (0, 0, -1), "grasp", "tool centre point")
    rig.port("power", (20, 20, 2), (0, 0, -1), "power")
    rig.info(category="robotics", tile="1x1", reach_m=1.4, payload_kg=12,
             preview_pose={"turret": -40, "shoulder": 58, "elbow": 14,
                           "wrist": -58, "gripper": 15})
    return rig


def agv():
    m = Model("agv")
    # chassis
    m.box(2, 2, 1, 22, 14, 5, "steel")
    m.box(1, 1, 4, 23, 15, 5, "steel_dark")
    m.box(2, 2, 5, 22, 14, 6, "hazard_yellow")
    for x in range(3, 22, 3):
        m.box(x, 2, 5, x + 1, 3, 6, "hazard_black")
        m.box(x + 1.5, 2, 5, x + 2.5, 3, 6, "hazard_black")
    # wheels with hub bolts
    for cx in (5, 19):
        for y0 in (0.5, 13.5):
            m.cyl(1, y0, cx, 3, 2.5, 3, "rubber")
            m.cyl(1, y0 + 0.5, cx, 3, 1, 1.4, "steel_light")
            m.cyl(1, y0 + 1.0, cx, 3, 0.5, 2.6, "steel_dark")
            for dz in (-1, 1):
                m.box(cx - 0.25, y0 + 1.0, 3 + dz - 0.25, cx + 0.25, y0 + 1.5,
                      3 + dz + 0.25, "brass")
    # castor + bumper skirts with hazard chevrons
    for y in (0.5, 14.0):
        m.box(2, y, 2, 22, y + 1.5, 4, "rubber_dark")
        for x in range(3, 21, 4):
            m.box(x, y, 2.25, x + 1.5, y + 1.5, 3.75, "hazard_yellow")
    m.box(2, 0.5, 4, 22, 2.0, 4.5, "hazard_black")
    # lidar mast and sensor band
    m.cyl(2, 6, 4, 8, 3, 2.2, "steel_dark")
    m.cyl(2, 9, 4, 8, 2, 2.4, "glass_dark")
    m.cyl(2, 11, 4, 8, 1, 2, "steel")
    m.cyl(2, 9.5, 4, 8, 0.5, 2.6, "lamp_blue")
    # antenna + warning beacon
    m.cyl(2, 6, 20, 12, 4, 0.5, "steel_light")
    m.box(19.5, 11.5, 10, 20.5, 12.5, 11.5, "lamp_amber")
    # led strips
    m.box(3, 2.5, 4.5, 21, 3.0, 5.0, "lamp_blue")
    m.box(3, 13.0, 4.5, 21, 13.5, 5.0, "lamp_blue")
    # roller deck detail
    for x in range(3, 22, 3):
        m.cyl(1, 3.5, x, 6.5, 9.0, 0.9, "roller")
        m.box(x - 0.25, 3.0, 6.25, x + 0.25, 3.5, 6.75, "roller_dark")
        m.box(x - 0.25, 12.5, 6.25, x + 0.25, 13.0, 6.75, "roller_dark")
    m.box(2, 2, 6, 3, 14, 7, "steel_dark")
    m.box(21, 2, 6, 22, 14, 7, "steel_dark")
    # charging contacts underneath
    for x in (8, 14):
        m.box(x, 6, 0.5, x + 2, 10, 1, "brass")
    D.nameplate(m, 4.0, 2.0, 4.0, w=4.0, h=1.0)
    m.port("deck", (12, 8, 7), (0, 0, 1), "item", "load deck")
    m.port("power", (12, 8, 0), (0, 0, -1), "power", "inductive charging pad")
    m.info(category="robotics", tile="2x1", speed_mps=1.2)
    return m


def safety_fence():
    m = Model("safety_fence")
    m.box(0, 0, 0, 32, 2, 28, "yellow")
    # panels are mostly open mesh
    m.clear(2, 0, 3, 30, 2, 26)
    m.box(0, 0, 26, 32, 2, 28, "yellow")
    m.box(0, 0, 26, 32, 2, 27, "hazard_black")
    m.box(0, 0, 2, 32, 2, 3, "yellow_dark")
    # posts with cast feet and bolts
    for x in (0, 30):
        m.box(x, 0, 0, x + 2, 2, 28, "yellow")
        m.box(x - 1, 0, 0, x + 3, 3, 2, "concrete_dark")
        m.box(x - 0.5, 0, 2, x + 2.5, 2, 3, "steel_dark")
        m.bolts((x - 0.5, 0.0, 1.0), (x + 2.0, 0.0, 1.0), 2, size=0.4)
        m.box(x, 0, 27, x + 2, 2, 28, "orange")
        m.box(x, 0, 24, x + 2, 2, 25, "steel_dark")
    # wire mesh: vertical then horizontal wires
    for x in range(3, 30, 3):
        m.box(x, 0, 3, x + 0.5, 1, 26, "steel_light")
    for z in range(3, 26, 3):
        m.box(2, 0, z, 30, 1, z + 0.5, "steel_light")
    # mid rail, hazard kick plate and warning sign
    m.box(2, 0, 13, 30, 2, 14, "yellow_dark")
    m.box(2, 0, 3, 30, 1, 4, "hazard_yellow")
    for x in range(2, 30, 2):
        m.box(x, 0, 3, x + 1, 1, 4, "hazard_black")
    m.box(14, 0, 19, 18, 1, 24, "red")
    m.box(14.5, 0, 19.5, 17.5, 1, 23.5, "white_panel")
    m.box(15, 0, 21, 17, 1, 22, "red_dark")
    # gate hinge pin and latch
    m.cyl(2, 14, 32, 0.5, 4, 1.0, "galv")
    m.box(30, 0, 13, 32, 2, 14, "steel_dark")
    m.box(30.5, 0, 12, 31.5, 2, 15, "steel_light")
    m.port("hinge", (32, 1, 14), (1, 0, 0), "mechanical", "gate hinge point")
    m.info(category="safety", tile="2x1")
    return m


BUILDERS = [robot_arm, agv, safety_fence]
