"""Wavefront OBJ + MTL writer (fallback for engines without glTF).

OBJ has no portable vertex colours, so faces are grouped per palette colour and
each group gets a material with a diffuse colour.  Normals are emitted so flat
shading survives.  Coordinates are already y-up (see voxelgen.gltf.to_gltf).
"""

import os

import numpy as np

from .gltf import normals_to_gltf, to_gltf
from .model import PALETTE
from .palette import hex_to_rgb


def build_obj(meshes, names, out_obj, origin):
    """meshes: list of Mesh in voxel space; origin: voxel offset to subtract."""
    base = os.path.splitext(out_obj)[0]
    mtl_path = base + ".mtl"
    mtl_name = os.path.basename(mtl_path)

    used = {}
    for m in meshes:
        if len(m.colors) == 0:
            continue
        for key in {tuple(np.round(c, 4)) for c in m.colors}:
            used.setdefault(key, "mat_%02d" % len(used))

    lines = [
        "# voxel factory asset set",
        "# units: metres | Y up | front = +Z | origin = bottom centre",
        "mtllib %s" % mtl_name,
    ]
    vcount = 0
    ncount = 0
    for mesh, name in zip(meshes, names):
        if len(mesh.positions) == 0:
            continue
        lines.append("o %s" % name)
        pos = to_gltf(mesh.positions - origin)
        nrm = normals_to_gltf(mesh.normals)
        for p in pos:
            lines.append("v %.5f %.5f %.5f" % (p[0], p[1], p[2]))
        for n in nrm:
            lines.append("vn %.4f %.4f %.4f" % (n[0], n[1], n[2]))
        current = None
        for t in mesh.indices:
            mat = used[tuple(np.round(mesh.colors[t[0]], 4))]
            if mat != current:
                lines.append("usemtl %s" % mat)
                current = mat
            a, b, c = (int(i) + 1 + vcount for i in t)
            na, nb, nc = (int(i) + 1 + ncount for i in t)
            lines.append("f %d//%d %d//%d %d//%d" % (a, na, b, nb, c, nc))
        vcount += len(pos)
        ncount += len(nrm)

    with open(out_obj, "w") as f:
        f.write("\n".join(lines) + "\n")

    named = {tuple(round(v, 4) for v in hex_to_rgb(h)): k for k, h in PALETTE.items()}
    ml = ["# generated materials", ""]
    for col, mat in sorted(used.items(), key=lambda kv: kv[1]):
        label = named.get(col)
        if label:
            ml.append("# %s" % label)
        ml += [
            "newmtl %s" % mat,
            "Kd %.4f %.4f %.4f" % col,
            "Ka 0.0 0.0 0.0",
            "Ks 0.04 0.04 0.04",
            "Ns 40.0",
            "d 1.0",
            "illum 2",
            "",
        ]
    with open(mtl_path, "w") as f:
        f.write("\n".join(ml))
    return used
