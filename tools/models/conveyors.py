"""Belt and roller conveyor modules.  Every module tiles on the 2 m grid.

Authored in 1/16 m units (32 x 16 units per 2 x 1 m tile); the raster is twice
as fine, so rollers, hazard chevrons and bolts read at 3 cm.
"""

from voxelgen.model import Model, Rig

BELT_TOP = 14.5        # roller crown height: 0.9 m
BED_Y0, BED_Y1 = 2.5, 13.5
FRAME_Z0, FRAME_Z1 = 11.0, 14.5
ROLLER_R = 0.75
ROLLER_PITCH = 2.0


def _side_frame(m, x0, x1, y0, inner_dir):
    """Orange side beam: dark under-frame, orange beam, dark cap, hazard skirt."""
    m.box(x0, y0, FRAME_Z0, x1, y0 + 2.0, FRAME_Z0 + 1.5, "frame_dark")
    m.box(x0, y0, FRAME_Z0 + 1.5, x1, y0 + 2.0, FRAME_Z1, "orange_frame")
    m.box(x0, y0, FRAME_Z1, x1, y0 + 2.0, FRAME_Z1 + 0.5, "frame_dark")
    # bold hazard chevrons on the OUTER slab of the beam, like the reference
    if inner_dir > 0:
        m.hazard(x0, y0, FRAME_Z0 + 1.5, x1, y0 + 0.5, FRAME_Z1, axis="y",
                 period=2.0)
    else:
        m.hazard(x0, y0 + 1.5, FRAME_Z0 + 1.5, x1, y0 + 2.0, FRAME_Z1, axis="y",
                 period=2.0)
    # bolt row on the inner face, plus end plates
    yi = y0 + 2.0 if inner_dir > 0 else y0
    m.bolts((x0 + 1.0, yi - 0.5, FRAME_Z0 + 2.5), (x1 - 1.0, yi - 0.5, FRAME_Z0 + 2.5),
            max(2, int((x1 - x0) / 6)), col="brass", size=0.4)
    return m


def _rollers(m, x0, x1, y0, y1, z_centre):
    n = int(round((x1 - x0) / ROLLER_PITCH))
    for i in range(n):
        x = x0 + ROLLER_PITCH * (i + 0.5)
        m.cyl(1, y0, x, z_centre, y1 - y0, ROLLER_R, "roller")
        # shaft ends
        m.box(x - 0.25, y0 - 0.25, z_centre - 0.25, x + 0.25, y0 + 0.25,
              z_centre + 0.25, "roller_dark")
        m.box(x - 0.25, y1 - 0.25, z_centre - 0.25, x + 0.25, y1 + 0.25,
              z_centre + 0.25, "roller_dark")
    # longitudinal bed rails under the rollers
    for yy in (y0 + 1.0, y1 - 2.0):
        m.box(x0, yy, z_centre - 1.6, x1, yy + 1.0, z_centre - 1.0, "frame_dark")
    return m


def _legs(m, xs, y0, y1):
    for x in xs:
        for y in (y0 + 0.5, y1 - 2.5):
            m.box(x, y, 0.75, x + 2.0, y + 2.0, FRAME_Z0, "frame_dark")
            m.box(x + 0.25, y + 0.25, 0.75, x + 1.75, y + 1.75, 2.0,
                  "steel_dark")
            m.box(x - 0.75, y - 0.75, 0, x + 2.75, y + 2.75, 0.75, "steel_dark")
            m.box(x - 0.5, y - 0.5, 0.75, x + 2.5, y + 2.5, 1.25,
                  "orange_frame_dark")
            m.bolts((x - 0.5, y - 0.5, 0.5), (x + 2.0, y - 0.5, 0.5), 2, size=0.4)
    # gussets and diagonal braces to the feet
    for x in xs:
        m.box(x, 2.0, FRAME_Z0 - 2.0, x + 2.0, 3.5, FRAME_Z0, "orange_frame")
        m.stroke([(x + 0.75, 2.5, 2.0), (x + 0.75, 3.2, 5.5),
                  (x + 0.75, 3.2, FRAME_Z0 - 1.0)], 0.5, "frame_dark")
    return m


def _drive_unit(m, x, y, z):
    m.box(x, y, z, x + 5.0, y + 6.0, z + 4.5, "steel")
    m.grate(x + 0.5, y - 0.5, z + 1.0, x + 4.5, y, z + 4.0, "frame_dark",
            step=1.0, axis=2)
    m.box(x + 1.0, y + 6.0, z + 0.5, x + 4.0, y + 7.0, z + 3.5, "steel_dark")
    m.cyl(2, z + 4.5, x + 2.5, y + 3.0, 1.0, 1.4, "galv")
    m.stroke([(x + 2.5, y + 3.0, z + 5.5), (x + 2.5, y + 1.0, z + 7.5),
              (x + 2.5, y + 1.0, z + 9.5)], 0.6, "rubber")
    m.bolts((x + 0.5, y + 0.5, z + 4.5), (x + 4.5, y + 0.5, z + 4.5), 4, size=0.5)
    return m


def _control_pod(m, x, y, z):
    """Orange control box with an E-stop and a status lamp (reference style)."""
    m.box(x, y, z, x + 4.0, y + 1.5, z + 4.0, "orange_frame")
    m.box(x + 0.5, y - 0.5, z + 0.5, x + 3.5, y, z + 3.0, "frame_dark")
    m.box(x + 0.75, y - 1.0, z + 2.0, x + 1.75, y - 0.5, z + 2.75, "red")
    m.box(x + 2.25, y - 1.0, z + 2.0, x + 3.0, y - 0.5, z + 2.75, "lamp_green")
    m.box(x + 1.25, y - 1.0, z + 0.75, x + 2.75, y - 0.5, z + 1.25, "screen")
    m.bolts((x + 0.25, y - 0.5, z + 0.25), (x + 3.75, y - 0.5, z + 0.25), 3,
            col="brass", size=0.4)
    return m


def _base_conveyor(m, x0, x1, clip=None):
    """Roller bed plus frames, legs, bracing and cable tray."""
    _side_frame(m, x0, x1, 0.0, +1)
    _side_frame(m, x0, x1, 14.0, -1)
    _rollers(m, x0, x1, BED_Y0, BED_Y1, BELT_TOP - ROLLER_R)
    # cross members under the bed
    for x in (x0 + 6.0, x0 + 14.0, x0 + 22.0, x1 - 2.0):
        m.box(x, BED_Y0, BELT_TOP - 2.4, x + 1.0, BED_Y1, BELT_TOP - 1.6,
              "frame_dark")
    _legs(m, (x0 + 2.0, x1 - 4.0), BED_Y0, BED_Y1)
    # lower bracing rails
    m.box(x0 + 2.0, 1.5, 4.0, x1 - 2.0, 2.5, 4.75, "frame_dark")
    m.box(x0 + 2.0, 13.5, 4.0, x1 - 2.0, 14.5, 4.75, "frame_dark")
    # cable tray with two hoses
    m.box(x0 + 1.0, 6.0, 7.5, x1 - 1.0, 10.0, 8.5, "grille")
    m.stroke([(x0 + 1.5, 7.0, 8.0), (x1 - 1.5, 7.0, 8.0)], 0.55, "rubber")
    m.stroke([(x0 + 1.5, 9.0, 8.0), (x1 - 1.5, 9.0, 8.0)], 0.55, "rubber")
    # end caps
    m.box(x0, 1.0, FRAME_Z0, x0 + 0.75, 15.0, FRAME_Z1 + 0.5, "orange_frame_dark")
    m.box(x1 - 0.75, 1.0, FRAME_Z0, x1, 15.0, FRAME_Z1 + 0.5, "orange_frame_dark")
    return m


def conveyor_straight():
    m = Model("conveyor_straight")
    _base_conveyor(m, 0.0, 32.0)
    _drive_unit(m, 23.0, 4.0, 4.5)
    _control_pod(m, 5.0, 0.0, 11.0)
    m.box(0.0, 0.0, FRAME_Z0 + 0.5, 32.0, 2.0, FRAME_Z0 + 1.0, "orange_frame")
    m.port("in", (0, 8, BELT_TOP), (-1, 0, 0), "item", "belt inlet")
    m.port("out", (32, 8, BELT_TOP), (1, 0, 0), "item", "belt outlet")
    m.port("power", (7, 0, 12), (0, -1, 0), "power")
    m.info(category="logistics", tile="2x1", snap=32, tile_voxels=(32, 16),
           kind="roller")
    return m


def conveyor_scanner():
    """Roller module under a sensor gantry (inspection station)."""
    m = Model("conveyor_scanner")
    _base_conveyor(m, 0.0, 32.0)
    _drive_unit(m, 23.0, 4.0, 4.5)
    # gantry posts on both sides, with hazard bands
    for x in (5.0, 23.0):
        for y in (0.0, 14.0):
            m.box(x, y, FRAME_Z1, x + 3.0, y + 2.0, 44.0, "orange_frame")
            m.box(x, y, FRAME_Z1, x + 3.0, y + 2.0, FRAME_Z1 + 1.0,
                  "orange_frame_dark")
            m.box(x - 0.5, y - 0.5, FRAME_Z1, x + 3.5, y + 2.5, FRAME_Z1 + 0.5,
                  "steel_dark")
            m.box(x + 3.0, y, 15.0, x + 3.5, y + 2.0, 20.0, "orange_frame_dark")
            m.bolts((x + 0.75, y - 0.5, 16.0), (x + 0.75, y - 0.5, 40.0), 6,
                    size=0.4)
    # top beams: cross members and one longitudinal rail
    m.box(5.0, 0.0, 41.0, 8.0, 16.0, 44.0, "orange_frame")
    m.box(23.0, 0.0, 41.0, 26.0, 16.0, 44.0, "orange_frame")
    m.box(5.0, 13.0, 40.0, 26.0, 16.0, 41.0, "orange_frame_dark")
    m.box(5.0, 0.0, 44.0, 26.0, 2.0, 45.0, "frame_dark")
    # sensor heads hanging over the belt
    for x0 in (5.75, 23.75):
        m.box(x0, 4.0, 36.5, x0 + 1.5, 8.0, 41.0, "frame_dark")
        m.box(x0 + 0.25, 4.5, 35.5, x0 + 1.25, 7.5, 36.5, "steel_dark")
        m.box(x0 + 0.4, 5.0, 34.75, x0 + 1.1, 7.0, 35.5, "lamp_blue")
        m.stroke([(x0 + 0.75, 8.0, 40.0), (x0 + 0.75, 9.5, 41.5),
                  (x0 + 0.75, 9.5, 43.5)], 0.5, "rubber")
    # stack lights on the gantry
    m.box(6.25, 1.5, 45.0, 7.75, 3.0, 46.5, "lamp_green")
    m.box(24.25, 1.5, 45.0, 25.75, 3.0, 46.5, "lamp_red")
    m.box(6.0, 1.25, 44.75, 8.0, 3.25, 45.0, "frame_dark")
    m.box(24.0, 1.25, 44.75, 26.0, 3.25, 45.0, "frame_dark")
    # inspection camera box on the near side
    _control_pod(m, 11.0, 0.0, 10.5)
    m.box(12.0, 1.0, FRAME_Z1, 14.0, 1.5, FRAME_Z1 + 3.0, "frame_dark")
    m.box(12.25, 0.5, FRAME_Z1 + 0.75, 13.75, 1.0, FRAME_Z1 + 2.5, "screen")
    m.port("in", (0, 8, BELT_TOP), (-1, 0, 0), "item")
    m.port("out", (32, 8, BELT_TOP), (1, 0, 0), "item")
    m.port("scan", (14, 8, 40), (0, 0, 1), "data", "inspection data")
    m.port("power", (13, 0, 12), (0, -1, 0), "power")
    m.info(category="logistics", tile="2x1", snap=32, tile_voxels=(32, 16),
           kind="scanner")
    return m


def _corner_path():
    import math
    pts = [(0, 8), (8, 8)]
    for i in range(1, 17):
        a = -math.pi / 2 + (math.pi / 2) * i / 16
        pts.append((8 + 8 * math.cos(a), 16 + 8 * math.sin(a)))
    pts += [(16, 16), (16, 32)]
    return pts


def _walk(pts, step):
    """Sample points and tangents along a polyline at roughly `step` spacing."""
    import math
    out = []
    acc = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if seg < 1e-6:
            continue
        ux, uy = (b[0] - a[0]) / seg, (b[1] - a[1]) / seg
        t = step - acc
        while t <= seg:
            out.append((a[0] + ux * t, a[1] + uy * t, ux, uy))
            t += step
        acc = (acc + seg) % step
    return out


def conveyor_corner():
    """90 degree roller bend on a 2 x 2 m tile.

    Runs in along +x at y = 8 so it lines up with a straight module to the west,
    turns through a 0.5 m radius and leaves along +y centred at x = 16.
    """
    m = Model("conveyor_corner")
    pts = _corner_path()
    clip = (0, 0, 32, 32)
    # frame: full 16-unit band, middle cleared, dark cap on both rails
    m.path_fill(pts, 8.0, FRAME_Z0, FRAME_Z1, "orange_frame", clip=clip)
    m.path_fill(pts, 6.0, FRAME_Z0, FRAME_Z1, "steel", mode="clear", clip=clip)
    m.path_fill(pts, 8.0, FRAME_Z1, FRAME_Z1 + 0.5, "frame_dark", clip=clip)
    m.path_fill(pts, 6.0, FRAME_Z1, FRAME_Z1 + 0.5, "steel", mode="clear",
                clip=clip)
    m.path_fill(pts, 8.0, FRAME_Z0, FRAME_Z0 + 1.5, "frame_dark", clip=clip)
    m.path_fill(pts, 6.0, FRAME_Z0, FRAME_Z0 + 1.5, "steel", mode="clear",
                clip=clip)
    # hazard chevrons on the two square end faces of the L
    # roller bed: round bars perpendicular to the path, straight or on the arc
    for px, py, ux, uy in _walk(pts, ROLLER_PITCH):
        nx, ny = -uy, ux
        z = BELT_TOP - ROLLER_R
        m.stroke([(px - nx * 5.6, py - ny * 5.6, z),
                  (px + nx * 5.6, py + ny * 5.6, z)], 0.7, "roller")
        m.stroke([(px - nx * 5.9, py - ny * 5.9, z),
                  (px - nx * 4.9, py - ny * 4.9, z)], 0.75, "roller_dark")
        m.stroke([(px + nx * 4.9, py + ny * 4.9, z),
                  (px + nx * 5.9, py + ny * 5.9, z)], 0.75, "roller_dark")
    # legs with feet on the straight runs
    for lx, ly in ((3.0, 1.0), (25.0, 27.0), (3.0, 12.0), (24.0, 27.0)):
        m.box(lx, ly, 2.0, lx + 2.0, ly + 2.0, FRAME_Z0, "frame_dark")
        m.box(lx - 0.75, ly - 0.75, 0, lx + 2.75, ly + 2.75, 0.75, "steel_dark")
        m.box(lx - 0.5, ly - 0.5, 0.75, lx + 2.5, ly + 2.5, 1.25,
              "orange_frame_dark")
    # centre bearing plate under the bend
    m.box(10.0, 10.0, 4.0, 18.0, 18.0, FRAME_Z0, "frame_dark")
    m.cyl(2, 4.0, 14.0, 14.0, 2.0, 4.0, "steel_dark")
    # cable tray and a small junction box
    m.stroke([(1.0, 9.0, 8.5), (7.0, 9.0, 8.5), (10.0, 12.0, 8.5),
              (12.0, 20.0, 8.5)], 0.6, "grille")
    m.box(2.0, 6.0, 6.0, 5.5, 10.5, 9.0, "steel_light")
    m.box(2.5, 6.0, 6.5, 5.0, 10.0, 8.5, "screen")
    # end caps: only across the 16-unit rail band, never across the whole tile
    m.box(0, 0, FRAME_Z0, 1.0, 16, FRAME_Z1, "orange_frame_dark")
    m.box(0, 0, FRAME_Z1, 1.0, 16, FRAME_Z1 + 0.5, "frame_dark")
    m.box(8, 31, FRAME_Z0, 24, 32, FRAME_Z1, "orange_frame_dark")
    m.box(8, 31, FRAME_Z1, 24, 32, FRAME_Z1 + 0.5, "frame_dark")
    m.hazard(0.0, 1.0, FRAME_Z0 + 1.5, 0.5, 15.0, FRAME_Z1, axis="x", period=2.0)
    m.hazard(9.0, 31.5, FRAME_Z0 + 1.5, 23.0, 32.0, FRAME_Z1, axis="y",
             period=2.0)
    m.port("in", (0, 8, BELT_TOP), (-1, 0, 0), "item")
    m.port("out", (16, 32, BELT_TOP), (0, 1, 0), "item")
    m.info(category="logistics", tile="2x2", snap=32, kind="curve",
           tile_voxels=(32, 32))
    return m


def conveyor_endstop():
    """Short 1 m end module: roller bed with a stop plate and drop chute."""
    m = Model("conveyor_endstop")
    _base_conveyor(m, 0.0, 16.0)
    # stop plate with a hazard cap
    m.box(14.5, 1.0, FRAME_Z0, 16.0, 15.0, FRAME_Z1, "orange_frame")
    m.hazard(14.5, 1.0, FRAME_Z1, 16.0, 15.0, FRAME_Z1 + 1.0, axis="z", period=2.0)
    m.box(15.0, 3.0, FRAME_Z0 + 1.0, 16.0, 13.0, FRAME_Z1 - 1.0, "orange_frame_dark")
    m.bolts((14.5, 1.5, FRAME_Z0 + 1.5), (14.5, 13.0, FRAME_Z0 + 1.5), 4,
            size=0.4)
    # chute through the frame
    m.box(15.0, 3.0, 3.0, 19.0, 13.0, 9.0, "frame_dark")
    m.box(16.0, 5.0, 3.0, 19.0, 11.0, 8.0, "belt_dark")
    m.box(15.0, 2.0, 8.0, 19.0, 14.0, 9.0, "steel_light")
    # photo-eye on a bracket with a reflector across the bed
    m.box(9.0, 0.0, 16.0, 10.0, 1.5, 16.5, "frame_dark")
    m.box(9.25, 0.0, 15.0, 10.0, 1.0, 16.0, "red")
    m.box(9.0, 14.5, 15.0, 10.0, 16.0, 16.5, "white_panel")
    m.port("in", (0, 8, BELT_TOP), (-1, 0, 0), "item")
    m.port("chute", (19, 8, 4), (1, 0, 0), "item", "gravity drop")
    m.info(category="logistics", tile="1x1", snap=16, tile_voxels=(16, 16))
    return m


def conveyor_hopper():
    """Dump hopper that loads a belt from above."""
    m = Model("conveyor_hopper")
    m.box(0, 0, 0, 24, 24, 1.5, "steel_dark")
    # flared body
    for i in range(26):
        z = 9.0 + i * 0.5
        h = 5.0 + i * 0.22
        m.box(12 - h, 12 - h, z, 12 + h, 12 + h, z + 0.5, "orange_frame")
    m.box(1.5, 1.5, 22.0, 22.5, 22.5, 25.0, "orange_frame_dark")
    m.clear(4.0, 4.0, 22.5, 20.0, 20.0, 25.0)
    m.box(4.0, 4.0, 22.0, 20.0, 20.0, 22.5, "frame_dark")
    m.hazard(1.5, 1.5, 22.0, 22.5, 2.0, 25.0, axis="y", period=2.5)
    m.hazard(1.5, 1.5, 22.0, 2.0, 22.5, 25.0, axis="x", period=2.5)
    # legs and feet
    for x in (1.0, 19.5):
        for y in (1.0, 19.5):
            m.box(x, y, 1.5, x + 3.0, y + 3.0, 9.0, "frame_dark")
            m.box(x - 0.5, y - 0.5, 1.5, x + 3.5, y + 3.5, 2.5, "steel_dark")
            m.bolts((x + 0.5, y - 0.5, 2.0), (x + 2.5, y - 0.5, 2.0), 2, size=0.4)
    # vibrator motor, ladder and outlet
    m.box(5.0, 0.0, 14.0, 8.0, 2.0, 17.0, "steel")
    m.grate(5.0, -0.5, 14.5, 8.0, 0.0, 16.5, "frame_dark", step=1.0, axis=2)
    m.box(6.0, -0.5, 15.5, 7.0, 0.0, 16.5, "lamp_amber")
    for z in range(11, 22, 2):
        m.box(9.5, 0.0, z, 13.5, 1.0, z + 0.5, "steel_light")
    m.box(9.5, 0.0, 9.5, 10.0, 1.0, 22.0, "steel_light")
    m.box(13.0, 0.0, 9.5, 13.5, 1.0, 22.0, "steel_light")
    m.cyl(0, 22.0, 12.0, 12.0, 5.0, 2.5, "galv")
    m.cyl(0, 27.0, 12.0, 12.0, 1.5, 3.2, "steel_dark")
    m.port("in", (12, 12, 30), (0, 0, 1), "item", "loaded from above")
    m.port("out", (28, 12, 12), (1, 0, 0), "item")
    m.info(category="logistics", tile="2x2", snap=32, tile_voxels=(32, 32))
    return m


def _lane_y(m, x0, x1, y0, y1):
    """Roller lane running along +y, for side infeed lanes."""
    for x in (x0 - 2.0, x1):
        m.box(x, y0, FRAME_Z0, x + 2.0, y1, FRAME_Z1, "orange_frame")
        m.box(x, y0, FRAME_Z1, x + 2.0, y1, FRAME_Z1 + 0.5, "frame_dark")
        m.box(x, y0, FRAME_Z0, x + 2.0, y1, FRAME_Z0 + 1.5, "frame_dark")
    # hazard on the outer faces of both rails
    m.hazard(x0 - 2.0, y0, FRAME_Z0 + 1.5, x0 - 1.5, y1, FRAME_Z1, axis="x",
             period=2.0)
    m.hazard(x1 + 1.5, y0, FRAME_Z0 + 1.5, x1 + 2.0, y1, FRAME_Z1, axis="x",
             period=2.0)
    # roller bars
    x = x0
    while x < x1 - 0.5:
        m.cyl(1, y0, x + 1.0, BELT_TOP - ROLLER_R, y1 - y0, ROLLER_R, "roller")
        m.box(x + 0.75, y0, BELT_TOP - ROLLER_R - 0.25, x + 1.25, y0 + 0.5,
              BELT_TOP - ROLLER_R + 0.25, "roller_dark")
        m.box(x + 0.75, y1 - 0.5, BELT_TOP - ROLLER_R - 0.25, x + 1.25, y1,
              BELT_TOP - ROLLER_R + 0.25, "roller_dark")
        x += ROLLER_PITCH
    # legs under the lane
    for y in (y0 + 1.0, y1 - 3.0):
        for xx in (x0 - 1.5, x1 + 0.5):
            m.box(xx, y, 1.5, xx + 1.5, y + 1.5, FRAME_Z0, "frame_dark")
            m.box(xx - 0.5, y - 0.5, 0, xx + 2.0, y + 2.0, 0.75, "steel_dark")
    return m


def conveyor_diverter():
    """Roller module with a pneumatic pusher that ejects to the far side.

    Rigged: the `pusher` part slides along +y. 0 m = retracted (authored),
    0.30 m = full stroke across the bed and out through the reject opening.
    """
    rig = Rig("conveyor_diverter")

    frame = Model("frame")
    _base_conveyor(frame, 0.0, 32.0)
    _drive_unit(frame, 23.0, 4.0, 4.5)
    # reject opening in the far rail
    frame.clear(12.0, 14.0, FRAME_Z0, 19.0, 16.0, FRAME_Z1 + 0.5)
    for x in (12.0, 18.0):
        frame.box(x, 14.0, FRAME_Z0, x + 1.0, 16.0, FRAME_Z1 + 0.5,
                  "orange_frame_dark")
        frame.box(x + 0.25, 14.0, FRAME_Z0 + 1.5, x + 0.75, 15.0, FRAME_Z1,
                  "hazard_yellow")
    # bracket, cylinder body and gland are static
    frame.box(11.5, 0.0, 15.0, 20.5, 3.0, 16.5, "frame_dark")
    for x in (12.0, 19.5):
        frame.box(x, 0.0, FRAME_Z0, x + 1.0, 3.0, 15.0, "frame_dark")
    frame.box(13.0, 1.0, 15.5, 19.0, 4.5, 17.5, "galv")
    frame.box(13.5, 1.0, 15.5, 18.5, 2.0, 17.5, "steel_dark")
    frame.cyl(1, 1.0, 16.0, 16.5, 3.0, 1.0, "brass")
    # air valve block and hoses on the near rail
    frame.box(20.0, 0.0, 15.0, 24.0, 2.0, 18.5, "steel_dark")
    frame.box(20.5, 0.0, 15.5, 23.5, 2.0, 17.5, "steel_light")
    frame.box(21.0, 0.0, 16.0, 22.0, 2.0, 17.0, "lamp_green")
    frame.stroke([(22.0, 0.75, 18.0), (19.0, 0.75, 18.0), (17.0, 0.75, 17.4),
                  (16.2, 1.2, 17.0)], 0.4, "rubber")
    frame.stroke([(13.2, 0.75, 18.0), (11.5, 0.75, 17.6), (11.0, 1.2, 17.0)],
                 0.4, "rubber")
    # photo-eye upstream so the pusher knows when to fire
    frame.box(7.5, 0.0, 15.0, 9.0, 1.5, 20.0, "frame_dark")
    frame.box(8.0, 0.0, 18.0, 8.75, 1.5, 19.0, "red")
    frame.box(7.5, 14.5, 15.0, 9.0, 16.0, 20.0, "frame_dark")
    frame.box(8.0, 14.5, 18.0, 8.75, 16.0, 19.0, "white_panel")
    _control_pod(frame, 2.0, 0.0, 11.0)
    rig.part("frame", frame, (16.0, 8.0, 0.0), None, axis=None,
             note="static: roller bed, frames, drive unit, valve block")

    # the moving pusher: face plate plus the two piston rods
    pusher = Model("pusher")
    pusher.box(15.5, 4.5, 16.0, 16.5, 7.5, 17.0, "steel_light")
    pusher.box(17.0, 4.5, 16.0, 18.0, 7.5, 17.0, "steel_light")
    pusher.box(13.0, 7.5, 14.5, 19.0, 8.5, 20.0, "steel_light")
    pusher.box(13.0, 7.0, 18.0, 19.0, 7.5, 19.5, "hazard_yellow")
    pusher.box(13.0, 7.0, 18.5, 19.0, 7.5, 19.0, "hazard_black")
    pusher.box(13.0, 7.5, 14.5, 19.0, 8.5, 15.0, "steel_dark")
    pusher.bolts((13.5, 7.0, 15.0), (18.5, 7.0, 15.0), 4, size=0.4)
    rig.part("pusher", pusher, (16.0, 8.0, 17.25), "frame", axis="y",
             limits=(0.0, 0.30), mode="slide",
             note="0 m = retracted, 0.30 m = full stroke across the bed")

    rig.port("in", (0, 8, BELT_TOP), (-1, 0, 0), "item")
    rig.port("out", (32, 8, BELT_TOP), (1, 0, 0), "item")
    rig.port("reject", (15.5, 16, BELT_TOP), (0, 1, 0), "item", "pusher ejection")
    rig.port("air", (22.0, 0.0, 17.0), (0, -1, 0), "gas")
    rig.port("power", (4.0, 0.0, 12.0), (0, -1, 0), "power")
    rig.info(category="logistics", tile="2x1", snap=32, kind="diverter",
             tile_voxels=(32, 16), pusher_stroke_m=0.30,
             preview_pose={"pusher": 0.15})
    return rig


def conveyor_merge():
    """2:1 merge: a side roller lane joins the main run through a chamfer.

    The throat carries a pop-up chain transfer in the far half of the bed.
    Rigged: the `transfer` part slides along +z.  0 m = chain deck retracted
    below the roller crown (items roll straight over it), 0.10 m = links raised
    to grab the merged item and pull it into the main flow.  The transfer's
    strip has no full-width rollers, so the bed rollers stop at its near wall.
    """
    rig = Rig("conveyor_merge")

    frame = Model("frame")
    _base_conveyor(frame, 0.0, 32.0)
    # open the far rail where the side lane joins
    frame.clear(6.0, 14.0, FRAME_Z0, 18.0, 16.0, FRAME_Z1 + 0.5)
    _lane_y(frame, 6.0, 18.0, 14.0, 32.0)
    frame.box(4.0, 31.0, FRAME_Z0, 20.0, 32.0, FRAME_Z1 + 0.5,
              "orange_frame_dark")
    frame.hazard(5.0, 31.5, FRAME_Z0 + 1.5, 19.0, 32.0, FRAME_Z1, axis="y",
                 period=2.0)
    # merge chamfer guides the side lane into +x flow
    for i in range(5):
        frame.box(18.0 + i, 13.5 - i * 0.8, FRAME_Z0 + 1.5, 19.0 + i,
                  14.5 - i * 0.8, FRAME_Z1, "orange_frame")
        frame.box(18.0 + i, 13.5 - i * 0.8, FRAME_Z1, 19.0 + i,
                  14.5 - i * 0.8, FRAME_Z1 + 0.5, "frame_dark")
    frame.box(23.0, 9.5, FRAME_Z1, 24.0, 11.5, FRAME_Z1 + 0.5, "frame_dark")
    # merge-entry photo-eye: sees main-line items while they are still upstream
    # of the side lane's chamfer, so a controller can arm the transfer from a
    # short closed-loop clearance instead of dead-reckoning from the far end of
    # the diverter module.  Sits between the side lane (x 6..14) and the chamfer
    # (x 18..23), clear of both.
    frame.box(15.0, 2.0, 15.0, 16.5, 3.5, 20.0, "frame_dark")
    frame.box(15.25, 2.0, 18.0, 16.25, 3.5, 19.0, "lamp_amber")
    frame.box(15.0, 11.0, 15.0, 16.5, 12.5, 20.0, "frame_dark")
    frame.box(15.25, 11.0, 18.0, 16.25, 12.5, 19.0, "white_panel")
    # photo-eye across the merge throat
    frame.box(20.0, 2.0, 15.0, 21.5, 3.5, 20.0, "frame_dark")
    frame.box(20.25, 2.0, 18.0, 21.25, 3.5, 19.0, "lamp_blue")
    frame.box(20.0, 11.0, 15.0, 21.5, 12.5, 20.0, "frame_dark")
    frame.box(20.25, 11.0, 18.0, 21.25, 12.5, 19.0, "white_panel")
    _control_pod(frame, 2.0, 0.0, 11.0)
    frame.box(26.0, 15.0, FRAME_Z0, 29.0, 17.0, FRAME_Z1 + 0.5, "steel_dark")
    frame.box(26.5, 15.0, FRAME_Z0 + 1.0, 28.5, 17.0, FRAME_Z1, "screen")

    # -- pop-up chain transfer: well, guide walls, lift cylinder -------------
    frame.clear(24.0, 9.5, 10.5, 30.5, 13.5, 15.0)   # cut the bed for the well
    frame.box(24.0, 9.5, 10.5, 30.5, 13.5, 11.0, "frame_dark")   # well floor
    # slots so the two lift rods can pass up through the floor
    frame.clear(26.55, 11.35, 10.5, 26.9, 11.75, 11.0)
    frame.clear(27.35, 11.35, 10.5, 27.7, 11.75, 11.0)
    frame.box(24.0, 9.5, 11.0, 30.5, 10.0, 14.5, "steel_dark")    # near wall
    frame.box(24.0, 13.0, 11.0, 30.5, 13.5, 14.5, "steel_dark")   # far wall
    frame.box(24.0, 10.0, 11.0, 24.5, 13.0, 14.5, "steel_dark")   # upstream end
    frame.box(30.0, 10.0, 11.0, 30.5, 13.0, 14.5, "steel_dark")   # downstream end
    frame.hazard(24.5, 9.5, 14.0, 30.0, 10.0, 14.5, axis="z", period=2.0)
    frame.bolts((24.75, 9.75, 14.5), (29.75, 9.75, 14.5), 4, size=0.4)
    # lift cylinder under the well, bolted to a base plate on the frame rails
    frame.box(25.9, 10.6, 4.0, 28.35, 12.5, 5.0, "steel_dark")
    frame.box(26.2, 10.9, 5.0, 28.05, 12.2, 10.0, "galv")
    frame.box(25.9, 10.6, 10.0, 28.35, 12.5, 10.5, "steel_dark")
    frame.bolts((26.1, 10.75, 4.5), (28.15, 10.75, 4.5), 3, size=0.35)
    # air valve on the near rail, hose down to the cylinder
    frame.box(26.5, 0.0, FRAME_Z0, 29.5, 2.0, 13.5, "steel_dark")
    frame.box(27.0, 0.0, 12.6, 29.0, 1.5, 13.2, "steel_light")
    frame.box(27.5, 0.0, 12.2, 28.5, 1.0, 12.6, "lamp_green")
    frame.stroke([(27.5, 0.75, 11.9), (27.5, 4.5, 8.2), (27.2, 9.0, 6.2),
                  (27.1, 10.6, 5.4)], 0.45, "rubber")
    rig.part("frame", frame, (16.0, 8.0, 0.0), None, axis=None,
             note="static: roller bed, side lane, chamfer, photo-eyes, housing, lift cylinder")

    # the moving chain deck: carriage, chain links, sprockets and lift rods
    deck = Model("transfer")
    deck.box(24.6, 10.1, 12.0, 29.9, 12.9, 12.5, "steel_dark")
    deck.box(24.6, 10.1, 12.5, 29.9, 10.6, 13.5, "steel_dark")
    deck.box(24.6, 12.4, 12.5, 29.9, 12.9, 13.5, "steel_dark")
    deck.box(24.6, 10.6, 13.0, 29.9, 12.4, 13.5, "frame_dark")
    # the chain itself: bright links over the dark guide, top face just under
    # the roller crown, so the links only clear the walls once the deck rises
    deck.grate(24.6, 11.0, 13.5, 29.9, 12.0, 14.0, "galv", step=0.5, axis=0)
    for x in (25.0, 29.5):
        deck.cyl(1, 11.0, x, 13.5, 1.0, 0.5, "steel_dark")
    deck.box(29.55, 10.1, 12.5, 29.9, 12.9, 13.5, "hazard_yellow")
    for x in (26.55, 27.35):
        deck.box(x, 11.35, 8.0, x + 0.35, 11.75, 12.0, "galv")
    rig.part("transfer", deck, (27.25, 11.5, 12.0), "frame", axis="z",
             limits=(0.0, 0.10), mode="slide",
             note="0 m = links below the roller crown, 0.10 m = links raised")

    rig.port("in_main", (0, 8, BELT_TOP), (-1, 0, 0), "item")
    rig.port("in_side", (12, 32, BELT_TOP), (0, 1, 0), "item")
    rig.port("out", (32, 8, BELT_TOP), (1, 0, 0), "item")
    rig.port("air", (28.0, 0.0, 12.4), (0, -1, 0), "gas")
    rig.port("power", (4.0, 0.0, 12.0), (0, -1, 0), "power")
    rig.info(category="logistics", tile="2x2", snap=32, kind="merge",
             tile_voxels=(32, 32), transfer_stroke_m=0.10,
             preview_pose={"transfer": 0.10})
    return rig


def conveyor_gate():
    """Single-tile roller gate: a rising blade that holds items back.

    Rigged: the `blade` part slides along +z. 0 m = closed (raised, authored),
    -0.14 m = open, with the blade sunk into the frame below the rollers.
    """
    rig = Rig("conveyor_gate")

    frame = Model("frame")
    _base_conveyor(frame, 0.0, 16.0)
    # blade guides on both rails
    for y in (1.0, 13.5):
        frame.box(6.5, y, FRAME_Z1 - 1.0, 8.5, y + 1.5, 19.5, "frame_dark")
        frame.box(7.0, y, 19.0, 8.0, y + 1.5, 20.0, "steel_light")
        frame.bolts((6.5, y, 19.25), (8.0, y, 19.25), 2, size=0.4)
    # lift cylinder under the bed with a guide rod
    frame.box(5.5, 5.0, 6.0, 9.5, 11.0, 10.0, "galv")
    frame.box(6.0, 5.5, 6.0, 9.0, 10.5, 7.0, "steel_dark")
    frame.cyl(2, 10.0, 7.5, 8.0, 4.5, 1.0, "steel_dark")
    frame.box(5.0, 4.0, 4.0, 10.0, 12.0, 6.0, "frame_dark")
    # photo-eyes on both sides of the gate
    for x, col in ((3.0, "lamp_amber"), (12.5, "lamp_red")):
        frame.box(x, 0.0, 15.0, x + 1.5, 1.5, 19.5, "frame_dark")
        frame.box(x + 0.25, 0.0, 17.5, x + 1.25, 1.5, 18.5, col)
        frame.box(x, 14.5, 15.0, x + 1.5, 16.0, 19.5, "frame_dark")
        frame.box(x + 0.25, 14.5, 17.5, x + 1.25, 16.0, 18.5, "white_panel")
    # cylinder mounting legs down to the floor
    for x, y in ((5.5, 5.0), (8.0, 9.0)):
        frame.box(x, y, 0, x + 1.5, y + 2.0, 4.0, "frame_dark")
        frame.box(x - 0.5, y - 0.5, 0, x + 2.0, y + 2.5, 0.75, "steel_dark")
    # air valve and control pod on the near rail, hose down to the cylinder
    frame.box(9.5, 0.0, FRAME_Z0, 13.0, 1.5, 14.0, "steel_dark")
    frame.box(10.0, 0.0, FRAME_Z0 + 0.5, 12.5, 1.5, 13.5, "lamp_green")
    _control_pod(frame, 0.5, 0.0, FRAME_Z0)
    frame.stroke([(4.0, 0.75, FRAME_Z0 + 1.0), (7.0, 0.75, FRAME_Z0 + 0.5),
                  (9.5, 0.75, FRAME_Z0 + 0.5)], 0.45, "rubber")
    frame.stroke([(10.0, 0.75, FRAME_Z0), (7.0, 2.0, 8.0), (7.5, 5.5, 10.0)],
                 0.45, "rubber")
    rig.part("frame", frame, (8.0, 8.0, 0.0), None, axis=None,
             note="static: roller bed, guides, lift cylinder, photo-eyes")

    # the moving blade plus its header bar
    blade = Model("blade")
    blade.box(7.0, 2.5, 14.5, 8.0, 13.5, 18.0, "steel_light")
    blade.hazard(7.0, 3.0, 15.0, 7.5, 13.0, 17.5, axis="x", period=2.0)
    blade.box(6.5, 2.0, 18.0, 8.5, 14.0, 19.0, "frame_dark")
    blade.box(6.75, 2.0, 18.0, 8.25, 14.0, 18.5, "hazard_yellow")
    # -0.29 m puts the blade top level with the roller crown, so a fully open
    # gate really does clear the bed instead of still tripping items
    rig.part("blade", blade, (7.5, 8.0, 14.5), "frame", axis="z",
             limits=(-0.29, 0.0), mode="slide",
             note="0 m = closed (raised), -0.29 m = open (blade top at roller height)")

    rig.port("in", (0, 8, BELT_TOP), (-1, 0, 0), "item")
    rig.port("out", (16, 8, BELT_TOP), (1, 0, 0), "item")
    rig.port("air", (12.0, 0.0, 13.0), (0, -1, 0), "gas")
    rig.info(category="logistics", tile="1x1", snap=16, kind="gate",
             tile_voxels=(16, 16), blade_travel_m=0.29,
             preview_pose={"blade": -0.145})
    return rig


BUILDERS = [conveyor_straight, conveyor_scanner, conveyor_corner,
            conveyor_endstop, conveyor_hopper, conveyor_diverter,
            conveyor_merge, conveyor_gate]
