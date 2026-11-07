"""glTF 2.0 (.glb) writer -- no external dependencies.

One mesh primitive per model (or per articulated part) using POSITION, NORMAL,
COLOR_0 as flat-shaded triangles with a single shared PBR material.  No
textures and no external buffers: a .glb is self-contained, so loading in a
custom engine is "parse the chunks, upload four buffer views".

Origin: every asset is centred on its footprint and sits on z = 0 in voxel
space, which becomes x = 0, y = 0, z = 0 at the bottom centre in glTF.  Placing
a machine is then just `node.position = grid_cell`.
"""

import json
import struct

import numpy as np

from .model import VOXEL


def to_gltf(p):
    """Voxel space (Z-up, front at y=0) -> glTF space (Y-up, front = +Z)."""
    return np.stack([
        p[..., 0] * VOXEL,
        p[..., 2] * VOXEL,
        -p[..., 1] * VOXEL,
    ], axis=-1)


def normals_to_gltf(n):
    """Axis conversion for directions/normals -- rotated, never scaled."""
    return np.stack([n[..., 0], n[..., 2], -n[..., 1]], axis=-1)


def _dir_gltf(d):
    return [float(d[0]), float(d[2]), -float(d[1])]


class _Bin:
    def __init__(self):
        self.data = bytearray()
        self.views = []

    def add(self, arr, target=None):
        arr = np.ascontiguousarray(arr)
        while len(self.data) % 4:
            self.data.append(0)
        offset = len(self.data)
        self.data.extend(arr.tobytes())
        view = {"buffer": 0, "byteOffset": offset, "byteLength": int(arr.nbytes)}
        if target is not None:
            view["target"] = target
        self.views.append(view)
        return len(self.views) - 1


ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963


def model_origin(model):
    """Bottom-centre origin in voxel space, as an array to subtract.

    Modules that declare `tile_voxels` are centred on their *tile* rather than
    on their geometry, so a conveyor corner whose belt only fills part of its
    2 x 2 m tile still snaps to the grid correctly.
    """
    tile = model.meta.get("tile_voxels")
    if tile:
        return np.array([float(tile[0]) * 0.5, float(tile[1]) * 0.5, 0.0], np.float32)
    if hasattr(model, "parts"):
        nx, ny, _ = model.size()
    else:
        nx, ny, _ = model.size
    return np.array([nx * 0.5, ny * 0.5, 0.0], np.float32)


def build_glb(model, out_path, origin=None):
    is_rig = hasattr(model, "parts")
    origin = model_origin(model) if origin is None else np.asarray(origin, np.float32)
    binbuf = _Bin()
    accessors = []
    meshes = []
    nodes = []
    materials = [{
        "name": "voxel_factory",
        "doubleSided": False,
        "pbrMetallicRoughness": {
            "baseColorFactor": [1.0, 1.0, 1.0, 1.0],
            "metallicFactor": 0.12,
            "roughnessFactor": 0.82,
        },
    }]

    def add_mesh(mesh, name):
        pos = to_gltf(mesh.positions).astype(np.float32)
        nrm = normals_to_gltf(mesh.normals).astype(np.float32)
        col = mesh.colors.astype(np.float32)
        idx = mesh.indices.astype(np.uint32).reshape(-1)
        bv = [binbuf.add(pos, ARRAY_BUFFER), binbuf.add(nrm, ARRAY_BUFFER),
              binbuf.add(col, ARRAY_BUFFER), binbuf.add(idx, ELEMENT_ARRAY_BUFFER)]
        a = len(accessors)
        accessors.extend([
            {"bufferView": bv[0], "componentType": 5126, "count": len(pos),
             "type": "VEC3", "min": [float(v) for v in pos.min(axis=0)],
             "max": [float(v) for v in pos.max(axis=0)]},
            {"bufferView": bv[1], "componentType": 5126, "count": len(nrm), "type": "VEC3"},
            {"bufferView": bv[2], "componentType": 5126, "count": len(col), "type": "VEC3"},
            {"bufferView": bv[3], "componentType": 5125, "count": len(idx), "type": "SCALAR"},
        ])
        meshes.append({
            "name": name,
            "primitives": [{
                "attributes": {"POSITION": a, "NORMAL": a + 1, "COLOR_0": a + 2},
                "indices": a + 3,
                "material": 0,
                "mode": 4,
            }],
        })
        return len(meshes) - 1

    extras = {"voxel_size": VOXEL, "origin": "bottom centre of footprint",
              "color_space": "srgb"}
    extras.update(model.meta)
    ports_extras = [
        {
            "name": p["name"],
            "pos": [float(v) for v in to_gltf(np.array(p["pos_voxels"], np.float32) - origin)],
            "dir": _dir_gltf(p["dir"]),
            "type": p["type"],
            "note": p["note"],
        }
        for p in model.ports
    ]

    if not is_rig:
        mesh = model.mesh()
        mesh.positions = mesh.positions - origin
        mi = add_mesh(mesh, model.name)
        node = {"name": model.name, "mesh": mi, "extras": dict(extras)}
        if ports_extras:
            node["extras"]["ports"] = ports_extras
        nodes.append(node)
        root_nodes = [0]
    else:
        index_of = {p["name"]: i for i, p in enumerate(model.parts)}
        for i, part in enumerate(model.parts):
            nodes.append({
                "name": part["name"],
                "translation": [0.0, 0.0, 0.0],
                "rotation": [0.0, 0.0, 0.0, 1.0],
            })
        for i, part in enumerate(model.parts):
            mesh = part["model"].mesh()
            pivot = np.array(part["pivot"], np.float32)
            mesh.positions = mesh.positions - pivot
            mi = add_mesh(mesh, part["name"])
            if part["parent"] is None:
                delta = to_gltf(pivot - origin)
            else:
                parent = model.parts[index_of[part["parent"]]]
                delta = to_gltf(pivot - np.array(parent["pivot"], np.float32))
                nodes[index_of[part["parent"]]].setdefault("children", []).append(i)
            nodes[i]["translation"] = [float(v) for v in delta]
            nodes[i]["mesh"] = mi
            mode = part.get("mode", "rotate")
            extra = {
                "joint_axis": part["axis"],
                "joint_mode": mode,
                "limits_deg": (list(part["limits"])
                               if part["limits"] and mode == "rotate" else None),
                "limits_m": (list(part["limits"])
                             if part["limits"] and mode == "slide" else None),
                "note": part["note"],
                "pivot_world": [float(v) for v in to_gltf(pivot - origin)],
            }
            if part["parent"] is None and ports_extras:
                extra["ports"] = ports_extras
            nodes[i]["extras"] = extra
        root_nodes = [i for i, p in enumerate(model.parts) if p["parent"] is None]

    gltf = {
        "asset": {"version": "2.0", "generator": "voxel-factory-assets 1.0"},
        "scene": 0,
        "scenes": [{"name": model.name, "nodes": root_nodes}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "accessors": accessors,
        "bufferViews": binbuf.views,
        "buffers": [{"byteLength": len(binbuf.data)}],
    }

    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(json_bytes) % 4:
        json_bytes += b" "
    bin_bytes = bytes(binbuf.data)
    while len(bin_bytes) % 4:
        bin_bytes += b"\x00"
    total = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
    with open(out_path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(json_bytes), 0x4E4F534A))
        f.write(json_bytes)
        f.write(struct.pack("<II", len(bin_bytes), 0x004E4942))
        f.write(bin_bytes)
    return total
