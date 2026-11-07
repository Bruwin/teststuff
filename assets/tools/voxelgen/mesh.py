"""Greedy voxel mesher.

Turns a dense integer voxel grid (0 = empty, n>0 = palette index n) into a
triangle mesh with flat per-face normals and per-vertex colours.

Only exposed faces are emitted, and coplanar faces of the same colour are
merged into the largest possible rectangles (greedy meshing).  That is what
keeps a 40^3 voxel model in the low hundreds of triangles instead of the tens
of thousands you would get from one cube per voxel -- the "low poly" part of
low poly voxel.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class Mesh:
    positions: np.ndarray  # (N, 3) float32, voxel units
    normals: np.ndarray    # (N, 3) float32, axis-aligned unit normals
    colors: np.ndarray     # (N, 3) float32, sRGB 0..1
    indices: np.ndarray    # (M, 3) uint32

    @property
    def tri_count(self):
        return int(len(self.indices))

    @property
    def vert_count(self):
        return int(len(self.positions))

    def bounds(self):
        if len(self.positions) == 0:
            return np.zeros(3), np.zeros(3)
        return self.positions.min(axis=0), self.positions.max(axis=0)

    def merge(self, other):
        offset = len(self.positions)
        self.positions = np.vstack([self.positions, other.positions]).astype(np.float32)
        self.normals = np.vstack([self.normals, other.normals]).astype(np.float32)
        self.colors = np.vstack([self.colors, other.colors]).astype(np.float32)
        self.indices = np.vstack([self.indices, other.indices + offset]).astype(np.uint32)
        return self


EMPTY = Mesh(
    np.zeros((0, 3), np.float32),
    np.zeros((0, 3), np.float32),
    np.zeros((0, 3), np.float32),
    np.zeros((0, 3), np.uint32),
)


def _greedy_rects(mask, colours):
    """Decompose a 2D boolean mask of equal-colour cells into rectangles.

    Returns (u0, u1, v0, v1, colour_id) with half-open ranges.
    """
    nu, nv = mask.shape
    used = np.zeros_like(mask, dtype=bool)
    out = []
    for u in range(nu):
        v = 0
        row_mask = mask[u]
        row_col = colours[u]
        while v < nv:
            if not row_mask[v] or used[u, v]:
                v += 1
                continue
            c = row_col[v]
            # grow along v
            v1 = v
            while v1 < nv and row_mask[v1] and row_col[v1] == c and not used[u, v1]:
                v1 += 1
            # grow along u while the whole row slice matches
            u1 = u + 1
            while u1 < nu:
                seg = mask[u1, v:v1]
                if not seg.all() or not np.all(colours[u1, v:v1] == c) or used[u1, v:v1].any():
                    break
                u1 += 1
            used[u:u1, v:v1] = True
            out.append((u, u1, v, v1, int(c)))
            v = v1
    return out


# Corner order for a positive-direction face, given (axis u, axis v).
# Verified so the winding produces an outward normal for a counter-clockwise
# front face in a right-handed system.
def _quad_corners(axis, plane, u0, u1, v0, v1):
    if axis == 0:  # +X, u = y, v = z
        return [(plane, u0, v0), (plane, u1, v0), (plane, u1, v1), (plane, u0, v1)]
    if axis == 1:  # +Y, u = x, v = z
        return [(u0, plane, v0), (u0, plane, v1), (u1, plane, v1), (u1, plane, v0)]
    # +Z, u = x, v = y
    return [(u0, v0, plane), (u1, v0, plane), (u1, v1, plane), (u0, v1, plane)]


def greedy_mesh(grid, palette_rgb):
    """Build a Mesh from a dense voxel grid.

    grid: (nx, ny, nz) int array, 0 = empty
    palette_rgb: (K, 3) float array indexed by grid value
    """
    grid = np.ascontiguousarray(grid)
    solid = grid > 0
    positions, normals, colors, indices = [], [], [], []

    for axis in range(3):
        n_axis = grid.shape[axis]
        for sign in (1, -1):
            # neighbour[i] = solid[i + sign] along `axis`
            nb = np.zeros_like(solid)
            src = [slice(None)] * 3
            dst = [slice(None)] * 3
            if sign == 1:
                src[axis] = slice(1, None)
                dst[axis] = slice(0, -1)
            else:
                src[axis] = slice(0, -1)
                dst[axis] = slice(1, None)
            nb[tuple(dst)] = solid[tuple(src)]
            faces = solid & ~nb
            if not faces.any():
                continue

            n_face = np.zeros(3, np.float32)
            n_face[axis] = float(sign)

            for i in range(n_axis):
                sl = [slice(None)] * 3
                sl[axis] = i
                fm = faces[tuple(sl)]
                if not fm.any():
                    continue
                cg = grid[tuple(sl)]
                for u0, u1, v0, v1, cid in _greedy_rects(fm, cg):
                    plane = i + (1 if sign == 1 else 0)
                    corners = _quad_corners(axis, plane, u0, u1, v0, v1)
                    if sign < 0:
                        corners = corners[::-1]
                    base = len(positions)
                    rgb = palette_rgb[cid]
                    for c in corners:
                        positions.append(c)
                        normals.append(n_face)
                        colors.append(rgb)
                    indices.append((base, base + 1, base + 2))
                    indices.append((base, base + 2, base + 3))

    if not positions:
        return Mesh(
            np.zeros((0, 3), np.float32),
            np.zeros((0, 3), np.float32),
            np.zeros((0, 3), np.float32),
            np.zeros((0, 3), np.uint32),
        )

    return Mesh(
        np.asarray(positions, np.float32),
        np.asarray(normals, np.float32),
        np.asarray(colors, np.float32),
        np.asarray(indices, np.uint32),
    )
