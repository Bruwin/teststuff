"""Pipe network modules on the same 2 m / 32 voxel grid as the belts."""

from voxelgen.model import Model
from voxelgen import details as D

PIPE_Z = 16          # pipe centreline height (1 m)
PIPE_R = 4           # 0.5 m outer diameter


def _pipe(m, pts, zc=PIPE_Z, r=PIPE_R, col="galv", clip=None):
    m.pipe_path(pts, zc, r, col, clip=clip)


def _flange(m, axis, c0, u, v, r=PIPE_R + 1.6, t=2, bolts=True):
    m.cyl(axis, c0, u, v, t, r, "steel_dark")
    m.cyl(axis, c0 + (0 if t < 2 else 0), u, v, 1, r + 0.6, "iron")
    if bolts:
        import math
        for i in range(8):
            a = i * math.pi / 4
            du, dv = (r + 1.2) * math.cos(a), (r + 1.2) * math.sin(a)
            if axis == 0:
                m.box(c0, u + du - 0.4, v + dv - 0.4, c0 + 1, u + du + 0.4,
                      v + dv + 0.4, "brass")
            else:
                m.box(u + du - 0.4, c0, v + dv - 0.4, u + du + 0.4, c0 + 1,
                      v + dv + 0.4, "brass")


def _insulation_rings(m, pts, count, zc=PIPE_Z, r=PIPE_R + 0.6, clip=None):
    """Clamp rings perpendicular to the run, evenly spaced along it."""
    n = len(pts)
    for i in range(count):
        t = (i + 0.5) / count
        idx = min(int(t * (n - 1)), n - 2)
        a, b = pts[idx], pts[idx + 1]
        f = t * (n - 1) - idx
        px = a[0] + (b[0] - a[0]) * f
        py = a[1] + (b[1] - a[1]) * f
        if clip is not None:
            cx0, cy0, cx1, cy1 = clip
            if not (cx0 <= px <= cx1 and cy0 <= py <= cy1):
                continue
        along_x = abs(b[0] - a[0]) >= abs(b[1] - a[1])
        if along_x:
            m.tube(0, px - 0.25, py, zc, 0.5, r + 0.3, 0.6, "steel_dark")
        else:
            m.tube(1, py - 0.25, px, zc, 0.5, r + 0.3, 0.6, "steel_dark")


def _tag(m, x, y, z):
    m.box(x, y, z, x + 3.0, y + 0.5, z + 2.0, "white_panel")
    m.box(x + 0.5, y, z + 0.5, x + 2.5, y + 0.5, z + 1.0, "steel_dark")


def pipe_straight():
    m = Model("pipe_straight")
    _pipe(m, [(0, 8), (32, 8)], clip=(0, 0, 32, 16))
    m.pipe_path([(2, 8), (30, 8)], PIPE_Z + 1.5, 3.4, "steel_light",
                clip=(0, 0, 32, 16))
    _insulation_rings(m, [(0, 8), (32, 8)], 7)
    for x in (0, 30):
        _flange(m, 0, x, 8, PIPE_Z)
    # mid-span support: foot, post, saddle clamp and gussets
    m.box(13, 4, 0, 19, 12, 2, "concrete_dark")
    D.hazard_plinth(m, 13, 4, 19, 12, 0, 2, period=1.5)
    m.box(15, 6, 2, 17, 10, PIPE_Z - 4, "steel_dark")
    m.box(15.5, 6.5, 2, 16.5, 9.5, PIPE_Z - 4, "steel_light")
    m.box(13, 4, PIPE_Z - 5, 19, 12, PIPE_Z - 4, "steel")
    m.box(13, 4, PIPE_Z - 4, 14, 12, PIPE_Z - 3, "steel_light")
    m.box(18, 4, PIPE_Z - 4, 19, 12, PIPE_Z - 3, "steel_light")
    for y in (4.0, 10.0):
        m.box(15, y, 2, 17, y + 1, 5, "frame_dark")
    _tag(m, 20.0, 4.0, PIPE_Z - 2)
    m.port("a", (0, 8, PIPE_Z), (-1, 0, 0), "fluid")
    m.port("b", (32, 8, PIPE_Z), (1, 0, 0), "fluid")
    m.info(category="logistics", tile="2x1", snap=32, inner_radius=0.0937,
           tile_voxels=(32, 16))
    return m


def pipe_elbow():
    """90 degree bend on the same path as the conveyor corner module."""
    import math
    m = Model("pipe_elbow")
    pts = [(0, 8), (8, 8)]
    for i in range(1, 13):
        a = -math.pi / 2 + (math.pi / 2) * i / 12
        pts.append((8 + 8 * math.cos(a), 16 + 8 * math.sin(a)))
    pts += [(16, 16), (16, 32)]
    _pipe(m, pts, clip=(0, 0, 32, 32))
    m.pipe_path(pts, PIPE_Z + 1.5, 3.4, "steel_light", clip=(0, 0, 32, 32))
    _insulation_rings(m, pts, 8, clip=(0, 0, 32, 32))
    _flange(m, 0, 0, 8, PIPE_Z)
    _flange(m, 1, 30, 16, PIPE_Z)
    # support under the straight run
    m.box(1, 4, 0, 7, 12, 2, "concrete_dark")
    D.hazard_plinth(m, 1, 4, 7, 12, 0, 2, period=1.5)
    m.box(3, 6, 2, 5, 10, PIPE_Z - 4, "steel_dark")
    m.box(1, 4, PIPE_Z - 5, 7, 12, PIPE_Z - 4, "steel")
    m.port("a", (0, 8, PIPE_Z), (-1, 0, 0), "fluid")
    m.port("b", (16, 32, PIPE_Z), (0, 1, 0), "fluid")
    m.info(category="logistics", tile="2x2", snap=32, kind="elbow",
           tile_voxels=(32, 32))
    return m


def pipe_tee():
    m = Model("pipe_tee")
    _pipe(m, [(0, 8), (32, 8)], clip=(0, 0, 32, 32))
    m.cyl(2, PIPE_Z - 4, 16, 8, 16, PIPE_R, "galv")      # branch up
    m.cyl(2, PIPE_Z + 11, 16, 8, 2, PIPE_R + 1.6, "steel_dark")
    m.cyl(2, PIPE_Z + 13, 16, 8, 1, PIPE_R + 2.4, "iron")
    _flange(m, 0, 0, 8, PIPE_Z)
    _flange(m, 0, 30, 8, PIPE_Z)
    m.box(14, 2, PIPE_Z - 6, 18, 14, PIPE_Z - 5, "steel")   # saddle clamps
    m.box(13, 4, PIPE_Z - 3, 19, 12, PIPE_Z - 2, "steel_dark")
    m.bolts((13.5, 4.0, PIPE_Z - 2.5), (18.0, 4.0, PIPE_Z - 2.5), 2, size=0.4)
    m.cyl(2, 0, 16, 8, PIPE_Z - 5, 2.2, "steel_dark")       # branch support leg
    m.box(13.5, 4, 0, 18.5, 12, 2, "concrete_dark")
    D.hazard_plinth(m, 13.5, 4, 18.5, 12, 0, 2, period=1.5)
    _tag(m, 20.0, 4.0, PIPE_Z - 2)
    m.port("a", (0, 8, PIPE_Z), (-1, 0, 0), "fluid")
    m.port("b", (32, 8, PIPE_Z), (1, 0, 0), "fluid")
    m.port("branch", (16, 8, PIPE_Z + 14), (0, 0, 1), "fluid")
    m.info(category="logistics", tile="2x1", snap=32, kind="tee",
           tile_voxels=(32, 16))
    return m


def valve():
    m = Model("valve")
    _pipe(m, [(0, 8), (32, 8)], clip=(0, 0, 32, 16))
    _insulation_rings(m, [(0, 8), (32, 8)], 6)
    # valve body
    m.cyl(2, PIPE_Z - 6, 16, 8, 12, 6, "red")
    m.cyl(2, PIPE_Z - 7, 16, 8, 2, 5, "red_dark")
    m.cyl(2, PIPE_Z + 5, 16, 8, 3, 3, "steel_dark")
    m.cyl(2, PIPE_Z + 5, 16, 8, 0.5, 3.6, "steel_light")
    # handwheel: hollow ring with spokes
    m.tube(2, PIPE_Z + 8, 16, 8, 2, 7, 2, "red_dark")
    m.cyl(2, PIPE_Z + 8, 16, 8, 0.5, 6.4, "red")
    for dx, dy in ((5, 0), (-5, 0), (0, 5), (0, -5)):
        m.box(16 + dx - 0.5, 8 + dy - 0.5, PIPE_Z + 8, 16 + dx + 0.5,
              8 + dy + 0.5, PIPE_Z + 9, "steel_light")
    m.cyl(2, PIPE_Z + 8, 16, 8, 2, 2, "steel_dark")
    # position indicator: green open / red closed
    m.box(19.5, 8.5, PIPE_Z + 6, 21.5, 10.5, PIPE_Z + 7, "steel_dark")
    m.box(20, 9, PIPE_Z + 6, 21, 10, PIPE_Z + 7, "lamp_green")
    # flanges + stem
    _flange(m, 0, 0, 8, PIPE_Z)
    _flange(m, 0, 30, 8, PIPE_Z)
    m.box(15, 7, PIPE_Z + 4, 17, 9, PIPE_Z + 9, "galv")
    # label plate and actuator junction box
    m.box(12, 4, PIPE_Z - 9, 20, 5, PIPE_Z - 7, "hazard_yellow")
    m.box(12, 4, PIPE_Z - 9, 20, 5, PIPE_Z - 8.5, "hazard_black")
    m.box(19, 4, PIPE_Z - 4, 22, 7, PIPE_Z - 1, "steel_dark")
    m.box(19.5, 4, PIPE_Z - 3.5, 21.5, 7, PIPE_Z - 1.5, "screen")
    m.port("a", (0, 8, PIPE_Z), (-1, 0, 0), "fluid")
    m.port("b", (32, 8, PIPE_Z), (1, 0, 0), "fluid")
    m.info(category="logistics", tile="2x1", snap=32, kind="valve",
           tile_voxels=(32, 16))
    return m


BUILDERS = [pipe_straight, pipe_elbow, pipe_tee, valve]
