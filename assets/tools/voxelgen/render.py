"""Tiny software renderer for asset previews (ortho, z-buffered, 2x SSAA).

Pure numpy so the build has no graphics dependencies.  Used only to produce
the preview PNGs / contact sheet; it is not part of the game engine path.
"""

import numpy as np

from .model import VOXEL


def write_png(path, rgb):
    """Write an (H, W, 3) uint8 array as a PNG."""
    import struct
    import zlib
    rgb = np.ascontiguousarray(rgb)
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- camera ----
def camera_basis(azimuth_deg, elevation_deg):
    az = np.radians(azimuth_deg)
    el = np.radians(elevation_deg)
    eye_dir = np.array([np.cos(el) * np.sin(az), np.cos(el) * np.cos(az), np.sin(el)])
    eye_dir /= np.linalg.norm(eye_dir)
    fwd = -eye_dir
    right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return eye_dir, right, up


class Scene:
    """Depth-buffered triangle renderer in voxel space."""

    def __init__(self, width, height, center, extent, azimuth=35.0, elevation=26.0,
                 ssaa=2, bg=(0.93, 0.94, 0.95)):
        self.W = width * ssaa
        self.H = height * ssaa
        self.ssaa = ssaa
        self.center = np.asarray(center, float)
        self.eye_dir, self.right, self.up = camera_basis(azimuth, elevation)
        self.scale = (min(self.W, self.H) * 0.5) / (extent * 0.5) * 0.86
        self.col = np.zeros((self.H, self.W, 3), np.float32)
        self.col[:] = np.asarray(bg, np.float32)
        self.depth = np.full((self.H, self.W), np.inf, np.float32)

    def project(self, pts):
        rel = pts - self.center
        x = rel @ self.right
        y = rel @ self.up
        d = rel @ (-self.eye_dir)  # larger = farther
        sx = self.W * 0.5 + x * self.scale
        sy = self.H * 0.5 - y * self.scale
        return np.stack([sx, sy], -1), d

    def triangle(self, p2, d, rgb):
        (x0, y0), (x1, y1), (x2, y2) = p2
        minx = max(int(np.floor(min(x0, x1, x2))), 0)
        maxx = min(int(np.ceil(max(x0, x1, x2))) + 1, self.W)
        miny = max(int(np.floor(min(y0, y1, y2))), 0)
        maxy = min(int(np.ceil(max(y0, y1, y2))) + 1, self.H)
        if maxx <= minx or maxy <= miny:
            return
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-12:
            return
        xs = np.arange(minx, maxx) + 0.5
        ys = np.arange(miny, maxy) + 0.5
        X, Y = np.meshgrid(xs, ys)
        w0 = ((y1 - y2) * (X - x2) + (x2 - x1) * (Y - y2)) / den
        w1 = ((y2 - y0) * (X - x2) + (x0 - x2) * (Y - y2)) / den
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            return
        dd = w0 * d[0] + w1 * d[1] + w2 * d[2]
        sub_depth = self.depth[miny:maxy, minx:maxx]
        sub_col = self.col[miny:maxy, minx:maxx]
        mask = inside & (dd < sub_depth - 1e-6)
        sub_depth[mask] = dd[mask]
        sub_col[mask] = rgb

    def add_mesh(self, mesh, shade=True, tint=None, alpha=1.0, flat_depth=None):
        if len(mesh.positions) == 0:
            return
        p2, d = self.project(mesh.positions)
        idx = mesh.indices
        if tint is None:
            cols = mesh.colors
        else:
            cols = np.tile(np.asarray(tint, np.float32), (len(mesh.positions), 1))
        light = np.array([0.42, -0.62, 0.66])
        light /= np.linalg.norm(light)
        fill = np.array([-0.7, 0.35, 0.25])
        fill /= np.linalg.norm(fill)
        for t in idx:
            n = mesh.normals[t[0]]
            if shade:
                lam = max(0.0, float(n @ light))
                fil = max(0.0, float(n @ fill))
                # downward faces sit in their own shadow
                down = 0.72 if n[2] < -0.5 else 1.0
                k = (0.44 + 0.56 * lam + 0.16 * fil) * down
            else:
                k = 1.0
            rgb = np.clip(cols[t[0]] * k, 0, 1)
            if alpha < 1.0:
                rgb = rgb * alpha
            self.triangle(p2[t], d[t], rgb if flat_depth is None else flat_depth * k)

    def add_quad(self, a, b, c, d, rgb, shade_normal=None):
        p2, dep = self.project(np.array([a, b, c, d], float))
        n = np.array(shade_normal, float) if shade_normal is not None else np.array([0, 0, 1.0])
        k = 0.9 if shade_normal is not None else 1.0
        self.triangle([p2[0], p2[1], p2[2]], [dep[0], dep[1], dep[2]], np.array(rgb) * k)
        self.triangle([p2[0], p2[2], p2[3]], [dep[0], dep[2], dep[3]], np.array(rgb) * k)

    def add_floor(self, extent, base=(0.82, 0.83, 0.84), line=(0.74, 0.755, 0.77),
                  step=16):
        """Floor plane with a 1 m grid, in world (voxel) units."""
        e = extent
        z = 0.0
        self.add_quad((-e, -e, z), (e, -e, z), (e, e, z), (-e, e, z), base)
        # grid lines as thin quads just above the plane
        t = max(0.35, e * 0.0015)
        zz = z + 0.02
        n = int(e // step)
        for i in range(-n, n + 1):
            c = i * step
            self.add_quad((c - t, -e, zz), (c + t, -e, zz), (c + t, e, zz), (c - t, e, zz),
                          line)
            self.add_quad((-e, c - t, zz), (e, c - t, zz), (e, c + t, zz), (-e, c + t, zz),
                          line)

    def add_shadow(self, mesh, light=(0.42, -0.62, 0.66), color=(0.55, 0.56, 0.58)):
        if len(mesh.positions) == 0:
            return
        L = np.array(light, float)
        L /= np.linalg.norm(L)
        p = mesh.positions.copy()
        safe = np.where(np.abs(L[2]) < 1e-3, 1e-3, L[2])
        t = p[:, 2] / safe
        p[:, 0] -= t * L[0]
        p[:, 1] -= t * L[1]
        p[:, 2] = 0.03
        p2, d = self.project(p)
        cols = np.array(color, float)
        for tri in mesh.indices:
            self.triangle([p2[tri[0]], p2[tri[1]], p2[tri[2]]],
                          [d[tri[0]], d[tri[1]], d[tri[2]]], cols)

    def finish(self, vignette=0.0):
        img = np.clip(self.col, 0, 1)
        if self.ssaa > 1:
            s = self.ssaa
            img = img.reshape(self.H // s, s, self.W // s, s, 3).mean(axis=(1, 3))
        img = np.clip(img * 255.0, 0, 255).astype(np.uint8)
        return img


def render_model(model, width=560, height=440, azimuth=145.0, elevation=27.0,
                 floor=True, shadow=True, zoom=1.0, ssaa=2, pose=None):
    """Render a Model or Rig to an (H, W, 3) uint8 image.

    `pose` maps a rig part name to a joint angle in degrees, applied around
    that part's pivot (parents first), so a rig previews in a natural pose.
    """
    if hasattr(model, "parts"):
        size = model.size()
    else:
        mesh = model.mesh()
        size = model.size

    nx, ny, nz = size
    center = np.array([nx * 0.5, ny * 0.5, nz * 0.5], float)
    extent = max(nx, ny, nz * 1.15, 8.0)
    scene = Scene(width, height, center, extent / zoom, azimuth, elevation, ssaa=ssaa)
    if floor:
        scene.add_floor(extent * 3.0, step=int(round(1.0 / VOXEL)))

    if hasattr(model, "parts"):
        posed = _posed_part_meshes(model, pose or {})
        for m in posed:
            if shadow:
                scene.add_shadow(m)
        for m in posed:
            scene.add_mesh(m)
    else:
        if shadow:
            scene.add_shadow(mesh)
        scene.add_mesh(mesh)
    return scene.finish()


def _rot3(axis, deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    m = np.eye(3)
    if axis == "x":
        m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c
    elif axis == "y":
        m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c
    else:
        m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c
    return m


def _posed_part_meshes(rig, pose):
    """Return the rig's part meshes transformed into the requested pose."""
    from .mesh import Mesh
    by_name = {p["name"]: p for p in rig.parts}
    cache = {}

    def world(part):
        name = part["name"]
        if name in cache:
            return cache[name]
        pivot = np.array(part["pivot"], float)
        m = np.eye(4)
        if part.get("mode", "rotate") == "slide":
            # pose value is metres along the joint axis
            offset = np.zeros(3)
            offset["xyz".index(part["axis"] or "z")] = pose.get(name, 0.0) / VOXEL
            m[:3, 3] = offset
        else:
            r = _rot3(part["axis"] or "z", pose.get(name, 0.0))
            m[:3, :3] = r
            m[:3, 3] = pivot - r @ pivot
        if part["parent"] and part["parent"] in by_name:
            m = world(by_name[part["parent"]]) @ m
        cache[name] = m
        return m

    out = []
    for part in rig.parts:
        m = world(part)
        src = part["model"].mesh()
        if len(src.positions) == 0:
            continue
        dst = Mesh(
            (src.positions @ m[:3, :3].T) + m[:3, 3],
            src.normals @ m[:3, :3].T,
            src.colors.copy(),
            src.indices.copy(),
        )
        out.append(dst)
    return out


def contact_sheet(images, cols=4, pad=10, bg=(23, 26, 30), scale=1):
    """Tile (name, image) pairs into one sheet."""
    if not images:
        return np.zeros((10, 10, 3), np.uint8)
    if scale > 1:
        images = [(n, img[::scale, ::scale]) for n, img in images]
    h, w, _ = images[0][1].shape
    rows = (len(images) + cols - 1) // cols
    sheet = np.zeros((rows * (h + pad) + pad, cols * (w + pad) + pad, 3), np.uint8)
    sheet[:] = bg
    for i, (_, img) in enumerate(images):
        r, c = divmod(i, cols)
        y = pad + r * (h + pad)
        x = pad + c * (w + pad)
        sheet[y:y + h, x:x + w] = img
    return sheet
