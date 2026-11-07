"""Voxel model authoring helpers.

Coordinate convention inside the generator (Z-up, right handed):

    +x  -> right
    +y  -> back   (the front face of every machine is authored at y = 0)
    +z  -> up

Authoring units: one unit is 1/16 m = 6.25 cm, so the 2 m tile is 32 x 16
units.  The raster is `RES` (2) times finer than that, i.e. one *fine voxel* is
1/32 m = 3.125 cm, which is what lets details like bolts, individual conveyor
rollers and 3 cm hazard stripes read.  All public helpers take **authored
units** and may be fractional at 0.5 steps; positions are multiplied by RES
internally, so the exported world size is unchanged from the coarse grid.

Export rotates into glTF's Y-up space (x, z, -y), so a model's front becomes +Z.
See README.md.
"""

import numpy as np

from .palette import PALETTE, hex_to_rgb

VOXEL = 1.0 / 32.0  # metres per fine voxel
RES = 2             # fine voxels per authored unit (6.25 cm)

_RGB_LOOKUP = {k: hex_to_rgb(v) for k, v in PALETTE.items()}
_NAMES = sorted(PALETTE)
_INDEX = {n: i + 1 for i, n in enumerate(_NAMES)}  # 0 reserved for empty
_EXTRA_RGB = []
_DARK_OF = {}


def _r(v):
    """Authored units -> fine voxel index."""
    return int(round(float(v) * RES))


def palette_array():
    rgb = np.zeros((len(_NAMES) + len(_EXTRA_RGB) + 1, 3), np.float32)
    for n, i in _INDEX.items():
        rgb[i] = _RGB_LOOKUP[n]
    for j, c in enumerate(_EXTRA_RGB):
        rgb[len(_NAMES) + 1 + j] = c
    return rgb


def palette_index():
    return dict(_INDEX)


def _cid(name):
    try:
        return _INDEX[name]
    except KeyError:
        raise KeyError(f"unknown palette colour {name!r}")


def _darker(name):
    """A slightly darker sibling, for noise patches and shading detail."""
    if name in _DARK_OF:
        return _DARK_OF[name]
    sib = name + "_dark"
    if sib in _INDEX:
        _DARK_OF[name] = _INDEX[sib]
        return _DARK_OF[name]
    if name.endswith("_dark"):
        return _cid(name)
    r, g, b = _RGB_LOOKUP[name]
    _EXTRA_RGB.append((r * 0.76, g * 0.76, b * 0.77))
    _DARK_OF[name] = len(_NAMES) + len(_EXTRA_RGB)
    return _DARK_OF[name]


def _hash01(x, y, z, salt):
    """Deterministic 0..1 noise, vectorised over numpy arrays."""
    h = (x * 73856093) ^ (y * 19349663) ^ (z * 83492791) ^ (int(salt) * 2654435761)
    return (h & 0x7FFFFFFF) % 1000 / 1000.0


def _distance_field(pts, shape):
    """Min distance from each cell centre in a 2D grid to a polyline."""
    pts = np.asarray(pts, float)
    nx, ny = shape
    X, Y = np.meshgrid(np.arange(nx) + 0.5, np.arange(ny) + 0.5, indexing="ij")
    best = np.full((nx, ny), 1e9, np.float32)
    for a, b in zip(pts[:-1], pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        seg2 = dx * dx + dy * dy
        if seg2 < 1e-9:
            d = (X - a[0]) ** 2 + (Y - a[1]) ** 2
        else:
            t = np.clip(((X - a[0]) * dx + (Y - a[1]) * dy) / seg2, 0.0, 1.0)
            d = (X - (a[0] + t * dx)) ** 2 + (Y - (a[1] + t * dy)) ** 2
        best = np.minimum(best, d)
    return np.sqrt(best)


def _norm_meta(kw):
    """Keep tile sizes in fine voxels so downstream code has one unit."""
    out = dict(kw)
    if "tile_voxels" in out:
        out["tile_voxels"] = tuple(int(round(v * RES)) for v in out["tile_voxels"])
    return out


class Model:
    """A single voxel model (or one articulated part of a rig)."""

    def __init__(self, name):
        self.name = name
        self.grid = np.zeros((1, 1, 1), np.int16)  # grown on demand
        self.ports = []
        self.meta = {}

    # -- grid plumbing ----------------------------------------------------
    def _reserve(self, x1, y1, z1):
        gx, gy, gz = self.grid.shape
        nx, ny, nz = max(gx, x1), max(gy, y1), max(gz, z1)
        if (nx, ny, nz) != (gx, gy, gz):
            g = np.zeros((nx, ny, nz), np.int16)
            g[:gx, :gy, :gz] = self.grid
            self.grid = g

    @property
    def size(self):
        if not self.grid.any():
            return (0, 0, 0)
        nx = int(np.argwhere(self.grid.any(axis=(1, 2))).max()) + 1
        ny = int(np.argwhere(self.grid.any(axis=(0, 2))).max()) + 1
        nz = int(np.argwhere(self.grid.any(axis=(0, 1))).max()) + 1
        return (nx, ny, nz)

    # -- raw (fine voxel) fills -------------------------------------------
    def _fill(self, x0, y0, z0, x1, y1, z1, cid, overwrite=True):
        if x1 <= x0 or y1 <= y0 or z1 <= z0:
            return
        self._reserve(x1, y1, z1)
        region = self.grid[x0:x1, y0:y1, z0:z1]
        if overwrite:
            region[:] = cid
        else:
            region[region == 0] = cid

    # -- authored-unit primitives -----------------------------------------
    def box(self, x0, y0, z0, x1, y1, z1, col, noise=0.0, seed=0):
        """Fill [x0,x1) x [y0,y1) x [z0,z1) in authored units (0.5 steps ok)."""
        cid = _cid(col)
        x0, y0, z0, x1, y1, z1 = _r(x0), _r(y0), _r(z0), _r(x1), _r(y1), _r(z1)
        if noise:
            self._fill(x0, y0, z0, x1, y1, z1, cid)
            self._speckle(x0, y0, z0, x1, y1, z1, _darker(col), noise, seed)
        else:
            self._fill(x0, y0, z0, x1, y1, z1, cid)
        return self

    def _speckle(self, x0, y0, z0, x1, y1, z1, cid, amount, seed, only=None):
        if x1 <= x0 or y1 <= y0 or z1 <= z0:
            return
        X = np.arange(x0, x1, dtype=np.int64)[:, None, None]
        Y = np.arange(y0, y1, dtype=np.int64)[None, :, None]
        Z = np.arange(z0, z1, dtype=np.int64)[None, None, :]
        region = self.grid[x0:x1, y0:y1, z0:z1]
        mask = _hash01(X, Y, Z, seed) < amount
        if only is not None:
            mask &= region == only
        region[mask] = cid

    def stamp(self, x0, y0, z0, x1, y1, z1, col):
        """Fill only where empty (decals, windows, panels)."""
        self._fill(_r(x0), _r(y0), _r(z0), _r(x1), _r(y1), _r(z1), _cid(col),
                   overwrite=False)
        return self

    def voxel(self, x, y, z, col):
        self._fill(_r(x), _r(y), _r(z), _r(x) + 1, _r(y) + 1, _r(z) + 1, _cid(col))
        return self

    def clear(self, x0, y0, z0, x1, y1, z1):
        x0, y0, z0 = max(_r(x0), 0), max(_r(y0), 0), max(_r(z0), 0)
        x1, y1, z1 = _r(x1), _r(y1), _r(z1)
        if x1 <= 0 or y1 <= 0 or z1 <= 0:
            return self
        self.grid[x0:x1, y0:y1, z0:z1] = 0
        return self

    def cyl(self, axis, c0, u0, v0, length, r, col, noise=0.0, hollow=0, seed=0):
        """Cylinder along `axis`, all dimensions in authored units.

        `c0` = start along the axis, `length` = extent, (u0, v0) = centre in the
        other two axes, `r` = radius, `hollow` = inner radius left empty.
        """
        x0 = _r(c0)
        length = _r(c0 + length) - x0
        uc, vc = _r(u0), _r(v0)
        # use the true float radius (not the rounded one) so small cylinders
        # such as conveyor rollers keep their real diameter
        rr = (float(r) * RES + 0.2) ** 2
        irr = (float(r - hollow) * RES + 0.2) ** 2 if hollow else -1.0
        n = int(np.ceil(np.sqrt(rr))) + 1
        lo, hi = x0, x0 + max(length, 0)
        if hi <= lo:
            return self

        axes = [a for a in range(3) if a != axis]
        shape = (max(self.grid.shape[axes[0]], uc + n + 1),
                 max(self.grid.shape[axes[1]], vc + n + 1))
        U, V = np.meshgrid(np.arange(shape[0]) + 0.5, np.arange(shape[1]) + 0.5,
                           indexing="ij")
        d = (U - uc) ** 2 + (V - vc) ** 2
        mask = (d <= rr) & (d > irr)
        if not mask.any():
            return self

        dims = [0, 0, 0]
        dims[axis] = hi
        dims[axes[0]] = shape[0]
        dims[axes[1]] = shape[1]
        self._reserve(*dims)
        cid = _cid(col)
        idx = [slice(None)] * 3
        for a in range(lo, hi):
            idx[axis] = a
            target = self.grid[tuple(idx)]
            full = np.zeros(target.shape, bool)
            full[:mask.shape[0], :mask.shape[1]] = mask
            target[full] = cid
        if noise:
            b0 = [0, 0, 0]
            b1 = [0, 0, 0]
            b0[axis], b1[axis] = lo, hi
            b0[axes[0]], b1[axes[0]] = uc - n, uc + n + 1
            b0[axes[1]], b1[axes[1]] = vc - n, vc + n + 1
            self._speckle(max(b0[0], 0), max(b0[1], 0), max(b0[2], 0),
                          b1[0], b1[1], b1[2], _darker(col), noise, seed, only=cid)
        return self

    def tube(self, axis, c0, u0, v0, length, r, thickness, col):
        return self.cyl(axis, c0, u0, v0, length, r, col,
                        hollow=max(0.5, r - thickness))

    def disc(self, axis, plane, u0, v0, r, col):
        return self.cyl(axis, plane, u0, v0, 0.5, r, col)

    def stroke(self, pts3, radius, col, noise=0.0, seed=0):
        """Round tube through 3D points (hoses, cables, guard rails)."""
        pts3 = np.asarray(pts3, float) * RES
        radius *= RES
        c = _cid(col)
        n = int(np.ceil(radius)) + 1
        for a, b in zip(pts3[:-1], pts3[1:]):
            steps = int(np.linalg.norm(b - a) * 2) + 1
            for s in range(steps + 1):
                p = a + (b - a) * (s / steps)
                for x in range(int(p[0]) - n, int(p[0]) + n + 1):
                    for y in range(int(p[1]) - n, int(p[1]) + n + 1):
                        for z in range(int(p[2]) - n, int(p[2]) + n + 1):
                            if (x - p[0]) ** 2 + (y - p[1]) ** 2 + (z - p[2]) ** 2 <= radius ** 2:
                                self._fill(x, y, z, x + 1, y + 1, z + 1, c)
        return self

    def path_fill(self, pts, radius, z0, z1, col, mode="fill", noise=0.0, seed=0,
                  inner=None, clip=None):
        """Fill/clear a swept ribbon along a 2D polyline (belt or pipe runs).

        `pts` are (x, y) centres in authored units; `radius` is the half width.
        `inner` clears a smaller ribbon out of the filled one in the same pass.
        `clip` is an (x0, y0, x1, y1) box that trims the ribbon so a swept
        module ends square on its tile boundary instead of with a round cap.
        """
        r = radius * RES
        pts = [(p[0] * RES, p[1] * RES) for p in pts]
        nx = int(np.ceil(max(p[0] for p in pts))) + int(r) + 2
        ny = int(np.ceil(max(p[1] for p in pts))) + int(r) + 2
        nx, ny = max(nx, 1), max(ny, 1)
        d = _distance_field(pts, (nx, ny))
        mask = d <= r
        if inner:
            mask &= d > inner * RES
        if clip is not None:
            cx0, cy0, cx1, cy1 = [_r(v) for v in clip]
            mask[:max(0, cx0), :] = False
            mask[cx1:, :] = False
            mask[:, :max(0, cy0)] = False
            mask[:, cy1:] = False
        self._reserve(nx, ny, _r(z1))
        z0, z1 = _r(z0), _r(z1)
        c = _cid(col)
        if mode == "clear":
            for x, y in np.argwhere(mask):
                self.grid[x, y, z0:z1] = 0
            return self
        for x, y in np.argwhere(mask):
            self.grid[x, y, z0:z1] = c
        if noise:
            # deterministic patchy weathering along the run
            ys, xs = np.meshgrid(np.arange(ny), np.arange(nx), indexing="xy")
            for x, y in np.argwhere(mask):
                if _hash01(x, y, 0, seed) < noise:
                    self.grid[x, y, z0:z1] = _darker(col)
        return self

    def path_clear(self, pts, radius, z0, z1, inner=None, clip=None):
        return self.path_fill(pts, radius, z0, z1, "steel", mode="clear",
                              inner=inner, clip=clip)

    def pipe_path(self, pts2, zc, r, col, noise=0.0, seed=0, clip=None):
        """Round pipe swept along a 2D polyline at height `zc`."""
        n = int(np.ceil(r * RES))
        for dz in range(-n, n + 1):
            w = np.sqrt(max((r * RES) ** 2 - dz * dz, 0.0)) / RES
            if w < 0.25:
                continue
            self.path_fill(pts2, w - 0.01, zc + dz / RES, zc + (dz + 1) / RES, col,
                           noise=noise, seed=seed + dz, clip=clip)
        return self

    def grate(self, x0, y0, z0, x1, y1, z1, col, step=1.0, axis=0):
        """Slatted panel (louvers, grilles, walkway grating)."""
        if axis == 0:
            x = x0
            while x < x1:
                self.box(x, y0, z0, min(x + step * 0.5, x1), y1, z1, col)
                x += step
        elif axis == 1:
            y = y0
            while y < y1:
                self.box(x0, y, z0, x1, min(y + step * 0.5, y1), z1, col)
                y += step
        else:
            z = z0
            while z < z1:
                self.box(x0, y0, z, x1, y1, min(z + step * 0.5, z1), col)
                z += step
        return self

    # -- detail vocabulary -------------------------------------------------
    def hazard(self, x0, y0, z0, x1, y1, z1, axis="y", period=3.0,
               col_a="hazard_yellow", col_b="hazard_black"):
        """Diagonal hazard stripes across a face (the axis names its normal)."""
        a, b = _cid(col_a), _cid(col_b)
        x0, y0, z0, x1, y1, z1 = _r(x0), _r(y0), _r(z0), _r(x1), _r(y1), _r(z1)
        if x1 <= x0 or y1 <= y0 or z1 <= z0:
            return self
        self._reserve(x1, y1, z1)
        p = max(1, int(round(period * RES)))
        X = np.arange(x0, x1, dtype=np.int64)[:, None, None]
        Y = np.arange(y0, y1, dtype=np.int64)[None, :, None]
        Z = np.arange(z0, z1, dtype=np.int64)[None, None, :]
        # add the third axis scaled to zero so the stripe field always
        # broadcasts to the full region, whatever the face thickness is
        if axis == "x":
            t = (Y + Z + X * 0) // p
        elif axis == "z":
            t = (X + Y + Z * 0) // p
        else:
            t = (X + Z + Y * 0) // p
        region = self.grid[x0:x1, y0:y1, z0:z1]
        region[(t % 2) == 0] = a
        region[(t % 2) == 1] = b
        return self

    def bolts(self, start, end, count, col="brass", size=0.5):
        """A row of bolt heads between two points (authored units)."""
        (x0, y0, z0), (x1, y1, z1) = start, end
        for i in range(count):
            t = (i + 0.5) / count if count else 0.0
            self.box(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z0 + (z1 - z0) * t,
                     x0 + (x1 - x0) * t + size, y0 + (y1 - y0) * t + size,
                     z0 + (z1 - z0) * t + size, col)
        return self

    def chamfer_box(self, x0, y0, z0, x1, y1, z1, col, chamfer=0.5, axis="z"):
        """Box with the two ends pinched in, which reads as a rounded beam."""
        self.box(x0, y0, z0, x1, y1, z1, col)
        c = chamfer
        if axis == "z":
            self.clear(x0, y0, z0, x0 + c, y1, z0 + c)
            self.clear(x1 - c, y0, z0, x1, y1, z0 + c)
            self.clear(x0, y0, z1 - c, x0 + c, y1, z1)
            self.clear(x1 - c, y0, z1 - c, x1, y1, z1)
        elif axis == "x":
            self.clear(x0, y0, z0, x1, y0 + c, z0 + c)
            self.clear(x0, y1 - c, z0, x1, y1, z0 + c)
            self.clear(x0, y0, z1 - c, x1, y0 + c, z1)
            self.clear(x0, y1 - c, z1 - c, x1, y1, z1)
        else:
            self.clear(x0, y0, z0, x0 + c, y0 + c, z1)
            self.clear(x1 - c, y0, z0, x1, y0 + c, z1)
            self.clear(x0, y1 - c, z0, x0 + c, y1, z1)
            self.clear(x1 - c, y1 - c, z0, x1, y1, z1)
        return self

    def frame(self, x0, y0, z0, x1, y1, z1, t, col):
        self.box(x0, y0, z0, x0 + t, y1, z1, col)
        self.box(x1 - t, y0, z0, x1, y1, z1, col)
        self.box(x0, y0, z0, x1, y1, z0 + t, col)
        self.box(x0, y0, z1 - t, x1, y1, z1, col)
        return self

    def rail(self, x0, y0, z0, x1, y1, z1, t, col, axis=0):
        if axis == 0:
            self.box(x0, y0, z0, x1, y0 + t, z1, col)
            self.box(x0, y1 - t, z0, x1, y1, z1, col)
        else:
            self.box(x0, y0, z0, x0 + t, y1, z1, col)
            self.box(x1 - t, y0, z0, x1, y1, z1, col)
        return self

    def mirror_y(self):
        ny = self.size[1]
        g = np.zeros_like(self.grid)
        g[:, :ny] = self.grid[:, :ny][:, ::-1, :]
        out = Model(self.name + "_mir")
        out.grid = g
        out.ports = list(self.ports)
        out.meta = dict(self.meta)
        return out

    # -- metadata ---------------------------------------------------------
    def port(self, name, pos, direction, kind="item", note=""):
        fine = [int(round(float(v) * RES)) for v in pos]
        self.ports.append({
            "name": name,
            "pos": [round(v * VOXEL, 4) for v in fine],
            "pos_voxels": fine,
            "dir": [int(d) for d in direction],
            "type": kind,
            "note": note,
        })
        return self

    def info(self, **kw):
        self.meta.update(_norm_meta(kw))
        return self

    # -- output -----------------------------------------------------------
    def mesh(self):
        from .mesh import EMPTY, greedy_mesh
        if self.grid.size == 0 or not self.grid.any():
            return EMPTY
        nx, ny, nz = self.size
        return greedy_mesh(self.grid[:nx, :ny, :nz], palette_array())


class Rig:
    """An articulated model: named parts, each with a pivot in world units.

    Parts are authored in a shared space, so pivots are simply where the joint
    sits.  The exporter turns this into a glTF node hierarchy so an engine can
    rotate `parts[].name` around its own origin and get correct kinematics.
    """

    def __init__(self, name):
        self.name = name
        self.parts = []
        self.ports = []
        self.meta = {}

    def part(self, name, model, pivot, parent=None, axis="z", limits=None, note="",
             mode="rotate"):
        """Add an articulated part.

        `mode` is "rotate" (limits in degrees about `axis`) or "slide" (limits
        in metres along `axis`, measured from the authored position).
        """
        self.parts.append({
            "name": name,
            "model": model,
            "pivot": [float(v) * RES for v in pivot],
            "parent": parent,
            "axis": axis,
            "limits": limits,
            "mode": mode,
            "note": note,
        })
        return model

    def port(self, name, pos, direction, kind="item", note=""):
        fine = [int(round(float(v) * RES)) for v in pos]
        self.ports.append({
            "name": name,
            "pos": [round(v * VOXEL, 4) for v in fine],
            "pos_voxels": fine,
            "dir": [int(d) for d in direction],
            "type": kind,
            "note": note,
        })
        return self

    def info(self, **kw):
        self.meta.update(_norm_meta(kw))
        return self

    def size(self):
        g = None
        for p in self.parts:
            arr = p["model"].grid
            if g is None:
                g = arr
                continue
            shp = tuple(max(a, b) for a, b in zip(g.shape, arr.shape))
            gg = np.zeros(shp, np.int16)
            gg[:g.shape[0], :g.shape[1], :g.shape[2]] = g
            gg[:arr.shape[0], :arr.shape[1], :arr.shape[2]] |= arr
            g = gg
        if g is None or not g.any():
            return (0, 0, 0)
        nx = int(np.argwhere(g.any(axis=(1, 2))).max()) + 1
        ny = int(np.argwhere(g.any(axis=(0, 2))).max()) + 1
        nz = int(np.argwhere(g.any(axis=(0, 1))).max()) + 1
        return (nx, ny, nz)
