"""Reusable industrial details, authored in 1/16 m units (0.5 steps allowed).

Everything here writes *inside* the model bounds: a face detail is a 0.5-unit
thick decal sitting on the front plane (y >= 0), never a box hanging off it.
"""


def control_pod(m, x, y, z, w=4.0, h=4.0, depth=1.5, screen=True,
                estop=True, lamp="lamp_green"):
    """Wall-mounted control box with a recessed panel, screen, E-stop and lamp."""
    m.box(x, y, z, x + w, y + depth, z + h, "steel_light")
    m.box(x + 0.25, y, z + 0.25, x + w - 0.25, y + 0.5, z + h - 0.25, "frame_dark")
    if screen:
        m.box(x + 0.75, y, z + h - 2.5, x + w - 0.75, y + 0.5, z + h - 1.0,
              "screen")
        m.box(x + 1.25, y, z + h - 2.0, x + w - 1.5, y + 0.5, z + h - 1.5,
              "screen_glow")
    if estop:
        m.box(x + 0.5, y, z + 0.5, x + 1.75, y + 0.5, z + 1.75, "red_dark")
        m.box(x + 0.75, y, z + 0.75, x + 1.5, y + 0.5, z + 1.5, "red")
    if lamp:
        m.box(x + w - 1.75, y, z + 0.75, x + w - 0.75, y + 0.5, z + 1.75, lamp)
    m.bolts((x + 0.5, y, z + 0.25), (x + w - 1.0, y, z + 0.25), 3, size=0.25)
    return m


def hazard_plinth(m, x0, y0, x1, y1, z0, z1, period=3.0, inset=0.0):
    """Hazard-striped band around the base of a machine."""
    x0, y0, x1, y1 = x0 + inset, y0 + inset, x1 - inset, y1 - inset
    m.hazard(x0, y0, z0, x1, y0 + 0.5, z1, axis="y", period=period)
    m.hazard(x0, y1 - 0.5, z0, x1, y1, z1, axis="y", period=period)
    m.hazard(x0, y0, z0, x0 + 0.5, y1, z1, axis="x", period=period)
    m.hazard(x1 - 0.5, y0, z0, x1, y1, z1, axis="x", period=period)
    return m


def bolt_frame(m, x0, y0, x1, y1, z, count_x=4, count_y=4, size=0.4,
               col="brass"):
    """Bolt heads around a rectangular flange at height z (decal, in-plane)."""
    for i in range(count_x):
        t = (i + 0.5) / count_x
        x = x0 + (x1 - x0) * t
        m.box(x - size * 0.5, y0 + 0.5, z, x + size * 0.5, y0 + 1.0, z + 0.5, col)
        m.box(x - size * 0.5, y1 - 1.0, z, x + size * 0.5, y1 - 0.5, z + 0.5, col)
    for i in range(count_y):
        t = (i + 0.5) / count_y
        y = y0 + (y1 - y0) * t
        m.box(x0 + 0.5, y - size * 0.5, z, x0 + 1.0, y + size * 0.5, z + 0.5, col)
        m.box(x1 - 1.0, y - size * 0.5, z, x1 - 0.5, y + size * 0.5, z + 0.5, col)
    return m


def panel_seams(m, x0, y0, x1, y1, z0, z1, step=6.0, axis="x",
                col="steel_dark", depth=0.5):
    """Shallow grooves that break up a large flat panel."""
    if axis == "x":
        x = x0 + step
        while x < x1 - 0.5:
            m.box(x, y0, z0, x + depth, y1, z1, col)
            x += step
    else:
        y = y0 + step
        while y < y1 - 0.5:
            m.box(x0, y, z0, x1, y + depth, z1, col)
            y += step
    return m


def gauge(m, x, y, z, size=2.0, dial="white_panel", needle="red"):
    """Round dial gauge drawn as a decal on the front plane at y."""
    m.box(x, y, z, x + size + 0.5, y + 0.5, z + size + 0.5, "steel_dark")
    m.box(x + 0.5, y, z + 0.5, x + size, y + 0.5, z + size, dial)
    m.box(x + size * 0.5, y, z + 0.75, x + size * 0.75, y + 0.5, z + size - 0.5,
          needle)
    m.box(x + 0.5, y, z + size * 0.5, x + size - 0.5, y + 0.5, z + size * 0.75,
          "steel_dark")
    return m


def gauge_cluster(m, x, y, z, n=3, gap=3.0, size=1.5):
    for i in range(n):
        gauge(m, x + i * gap, y, z, size=size)
    return m


def cable_gland(m, x, y, z, col="galv"):
    m.box(x, y, z, x + 1.0, y + 1.0, z + 0.5, col)
    m.box(x + 0.25, y + 0.25, z + 0.5, x + 0.75, y + 0.75, z + 1.0, "rubber")
    return m


def fan_grille(m, cx, cy, z, r=4.0, col="steel_dark", ring="steel_light"):
    """Recessed fan opening with a slatted grille, drawn on a horizontal face."""
    m.cyl(2, z, cx, cy, 0.5, r, ring)
    m.cyl(2, z + 0.5, cx, cy, 0.5, r - 0.75, "rubber_dark")
    for i in range(-2, 3):
        m.box(cx - r + 1.0, cy + i * 1.4 - 0.35, z + 0.5, cx + r - 1.0,
              cy + i * 1.4 + 0.35, z + 1.0, col)
    m.cyl(2, z + 0.5, cx, cy, 1.0, 1.2, "galv")
    return m


def side_fan(m, x, y, z, r=3.5, col="steel_dark"):
    """Fan opening on a vertical front face (decal)."""
    m.cyl(1, y, x, z, 0.5, r, "steel_light")
    m.cyl(1, y, x, z, 0.5, r - 0.75, "rubber_dark")
    for i in range(-2, 3):
        m.box(x + i * 1.4 - 0.35, y, z - r + 1.0, x + i * 1.4 + 0.35, y + 0.5,
              z + r - 1.0, col)
    m.box(x - 0.35, y, z - r + 1.0, x + 0.35, y + 0.5, z + r - 1.0, col)
    return m


def nameplate(m, x, y, z, w=4.0, h=1.5, col="white_panel"):
    m.box(x, y, z, x + w, y + 0.5, z + h, col)
    m.box(x + 0.5, y, z + 0.5, x + w - 0.5, y + 0.5, z + h - 0.5, "steel_dark")
    return m


def ladder(m, x0, x1, y, z0, z1, rail="steel_light", rungs=2.0, side=0.5):
    """Vertical ladder against a face at y, with safety hoops."""
    m.box(x0, y, z0, x0 + side, y + 0.5, z1, rail)
    m.box(x1 - side, y, z0, x1, y + 0.5, z1, rail)
    z = z0 + 1.0
    while z < z1 - 1.0:
        m.box(x0 + side, y, z, x1 - side, y + 0.5, z + 0.4, rail)
        z += rungs
    return m


def guard_rail(m, x0, x1, y, z, h=3.0, col="hazard_yellow", post_col="frame_dark"):
    """Top guard rail with posts, as seen around mezzanines and platforms."""
    m.box(x0, y, z + h, x1, y + 0.5, z + h + 0.5, col)
    m.box(x0, y, z + h * 0.5, x1, y + 0.5, z + h * 0.5 + 0.4, col)
    x = x0
    while x <= x1 - 0.5:
        m.box(x, y, z, x + 0.5, y + 0.5, z + h, post_col)
        x += 8.0
    return m


def foot_pad(m, x, y, w=3.0, d=3.0, col="steel_dark"):
    m.box(x, y, 0, x + w, y + d, 0.5, col)
    m.box(x + 0.25, y + 0.25, 0.5, x + w - 0.25, y + d - 0.25, 0.75,
          "concrete_dark")
    m.bolts((x + 0.25, y, 0.5), (x + w - 1.0, y, 0.5), 2, size=0.25)
    return m


def stack_light(m, x, y, z, w=2.0, lamps=("lamp_red", "lamp_amber", "lamp_green")):
    """Stack light on a small post."""
    m.box(x, y, z, x + w, y + w, z + 1.0, "frame_dark")
    for i, col in enumerate(lamps):
        m.box(x + 0.25, y + 0.25, z + 1.0 + i * 1.5, x + w - 0.25, y + w - 0.25,
              z + 2.5 + i * 1.5, col)
    return m


def vent_slots(m, x0, y0, z0, x1, z1, step=1.5, col="rubber_dark"):
    """Horizontal ventilation slots on a front face."""
    z = z0
    while z < z1 - 0.5:
        m.box(x0, y0, z, x1, y0 + 0.5, z + 0.75, col)
        z += step
    return m


def pipe_run(m, x0, y, z, x1, colour="galv", r=0.9, brackets=True):
    """Straight horizontal pipe along x with wall brackets."""
    m.cyl(0, x0, y, z, x1 - x0, r, colour)
    if brackets:
        x = x0 + 2.0
        while x < x1 - 1.0:
            m.box(x, y - r - 0.5, z - r - 0.5, x + 0.5, y + r + 0.5, z + r + 0.5,
                  "steel_dark")
            x += 8.0
    return m
