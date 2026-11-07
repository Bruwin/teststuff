#!/usr/bin/env python3
"""Structural validation for the generated assets.

Checks the .glb files as an engine loader would see them: chunk sizes, JSON
structure, accessor ranges inside their buffer views, index ranges, unit
normals, colour range, finite numbers, declared bounds, rig hierarchy, and that
every OBJ face references existing vertices.

    python3 tools/validate.py
"""

import json
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
COMPONENT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
SIZEOF = {"b": 1, "B": 1, "h": 2, "H": 2, "I": 4, "f": 4}


def read_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    magic, version, length = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67, "bad magic in %s" % path
    assert version == 2, "bad glTF version in %s" % path
    assert length == len(data), "declared length %d != file size %d" % (length, len(data))
    out = {"json": None, "bin": b""}
    off = 12
    while off < length:
        clen, ctype = struct.unpack_from("<II", data, off)
        chunk = data[off + 8:off + 8 + clen]
        assert len(chunk) == clen, "truncated chunk in %s" % path
        if ctype == 0x4E4F534A:
            out["json"] = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            out["bin"] = chunk
        off += 8 + clen
    assert out["json"] is not None, "no JSON chunk in %s" % path
    return out


def accessor_array(gltf, binbuf, index):
    acc = gltf["accessors"][index]
    view = gltf["bufferViews"][acc["bufferView"]]
    fmt = COMPONENT[acc["componentType"]]
    n = NCOMP[acc["type"]]
    count = acc["count"]
    dtype = np.dtype("<" + fmt)
    itemsize = SIZEOF[fmt]
    stride = view.get("byteStride", itemsize * n)
    start = view["byteOffset"] + acc.get("byteOffset", 0)
    assert start + count * stride <= view["byteOffset"] + view["byteLength"], \
        "accessor %d overruns its buffer view" % index
    raw = np.frombuffer(binbuf, dtype=np.uint8, count=count * stride, offset=start)
    raw = raw.reshape(count, stride)[:, :itemsize * n]
    return raw.reshape(-1).view(dtype).reshape(count, n)


def validate_glb(path, problems):
    doc = read_glb(path)
    gltf, binbuf = doc["json"], doc["bin"]
    tag = os.path.basename(path)

    buf_len = gltf["buffers"][0]["byteLength"]
    if buf_len > len(binbuf):
        problems.append("%s: buffer declares %d bytes, BIN chunk has %d"
                        % (tag, buf_len, len(binbuf)))
    for i, view in enumerate(gltf["bufferViews"]):
        if view["byteOffset"] + view["byteLength"] > len(binbuf):
            problems.append("%s: bufferView %d overruns BIN chunk" % (tag, i))

    total_tris = 0
    for mesh in gltf["meshes"]:
        for prim in mesh["primitives"]:
            attrs = prim["attributes"]
            for need in ("POSITION", "NORMAL", "COLOR_0"):
                if need not in attrs:
                    problems.append("%s: %s missing %s" % (tag, mesh["name"], need))
            pos = accessor_array(gltf, binbuf, attrs["POSITION"])
            nrm = accessor_array(gltf, binbuf, attrs["NORMAL"])
            col = accessor_array(gltf, binbuf, attrs["COLOR_0"])
            idx = accessor_array(gltf, binbuf, prim["indices"]).reshape(-1)

            if len(pos) != len(nrm) or len(pos) != len(col):
                problems.append("%s: %s attribute counts differ" % (tag, mesh["name"]))
            if not np.isfinite(pos).all() or not np.isfinite(nrm).all():
                problems.append("%s: %s has non-finite values" % (tag, mesh["name"]))
            if idx.max() >= len(pos):
                problems.append("%s: %s index out of range (%d >= %d)"
                                % (tag, mesh["name"], idx.max(), len(pos)))
            if len(idx) % 3:
                problems.append("%s: %s index count not a multiple of 3" % (tag, mesh["name"]))
            lengths = np.linalg.norm(nrm, axis=1)
            if not np.allclose(lengths, 1.0, atol=1e-3):
                problems.append("%s: %s normals not unit length (%.3f..%.3f)"
                                % (tag, mesh["name"], lengths.min(), lengths.max()))
            if col.min() < -1e-6 or col.max() > 1 + 1e-6:
                problems.append("%s: %s colour outside 0..1" % (tag, mesh["name"]))
            tris = idx.reshape(-1, 3)
            a, b, c = pos[tris[:, 0]], pos[tris[:, 1]], pos[tris[:, 2]]
            area = np.linalg.norm(np.cross(b - a, c - a), axis=1) * 0.5
            if (area < 1e-9).any():
                problems.append("%s: %s has %d degenerate triangles"
                                % (tag, mesh["name"], int((area < 1e-9).sum())))
            total_tris += len(tris)

            acc = gltf["accessors"][attrs["POSITION"]]
            if "min" in acc and "max" in acc:
                if not np.allclose(acc["min"], pos.min(axis=0), atol=1e-4):
                    problems.append("%s: %s POSITION min mismatch" % (tag, mesh["name"]))
                if not np.allclose(acc["max"], pos.max(axis=0), atol=1e-4):
                    problems.append("%s: %s POSITION max mismatch" % (tag, mesh["name"]))

    # node/scene integrity + rig hierarchy
    roots = gltf["scenes"][0]["nodes"]
    if not roots:
        problems.append("%s: scene has no root nodes" % tag)
    seen = set()

    def walk(i):
        if i in seen:
            problems.append("%s: node %d reachable twice (cycle?)" % (tag, i))
            return
        seen.add(i)
        for c in gltf["nodes"][i].get("children", []):
            walk(c)

    for r in roots:
        walk(r)
    if len(seen) != len(gltf["nodes"]):
        problems.append("%s: %d nodes unreachable from the scene"
                        % (tag, len(gltf["nodes"]) - len(seen)))
    for i, node in enumerate(gltf["nodes"]):
        if "mesh" not in node and not node.get("children"):
            problems.append("%s: node %d has neither mesh nor children" % (tag, i))
    return total_tris


def validate_obj(path, problems):
    verts = 0
    faces = 0
    vert_indices = []
    with open(path) as f:
        for line in f:
            if line.startswith("v "):
                verts += 1
            elif line.startswith("f "):
                faces += 1
                for tok in line.split()[1:]:
                    vert_indices.append(int(tok.split("//")[0]))
    if faces == 0:
        problems.append("%s: no faces" % os.path.basename(path))
    if vert_indices and (max(vert_indices) > verts or min(vert_indices) < 1):
        problems.append("%s: face references out-of-range vertex" % os.path.basename(path))
    mtl = os.path.splitext(path)[0] + ".mtl"
    if not os.path.exists(mtl):
        problems.append("%s: missing .mtl" % os.path.basename(path))
    return verts, faces


def main():
    manifest_path = os.path.join(ASSETS, "manifest.json")
    if not os.path.exists(manifest_path):
        print("manifest.json missing -- run tools/build.py first")
        return 1
    with open(manifest_path) as f:
        manifest = json.load(f)

    problems = []
    tris = 0
    for asset in manifest["assets"]:
        glb = os.path.join(ASSETS, asset["glb"])
        obj = os.path.join(ASSETS, asset["obj"])
        if not os.path.exists(glb):
            problems.append("%s: missing GLB" % asset["id"])
            continue
        n = validate_glb(glb, problems)
        if n != asset["tris"]:
            problems.append("%s: manifest says %d tris, file has %d"
                            % (asset["id"], asset["tris"], n))
        tris += n
        if os.path.exists(obj):
            v, f = validate_obj(obj, problems)
            if f != asset["tris"]:
                problems.append("%s: OBJ has %d faces, GLB has %d tris"
                                % (asset["id"], f, asset["tris"]))
        else:
            problems.append("%s: missing OBJ" % asset["id"])
        if asset["preview"] and not os.path.exists(os.path.join(ASSETS, asset["preview"])):
            problems.append("%s: missing preview" % asset["id"])

    for p in problems:
        print("FAIL", p)
    print("%d assets, %d triangles, %d problems" % (len(manifest["assets"]), tris, len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
