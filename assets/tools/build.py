#!/usr/bin/env python3
"""Build every voxel asset: .glb + .obj/.mtl + preview PNG + manifest.

    python3 assets/tools/build.py              # everything
    python3 assets/tools/build.py motor pump   # just these ids
    python3 assets/tools/build.py --no-render  # geometry only (fast)

Run from the repository root; paths are resolved from this file, not the cwd.
"""

import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.dirname(HERE)  # assets/ this generator lives inside
sys.path.insert(0, HERE)

import models.conveyors as conveyors  # noqa: E402
import models.machines as machines  # noqa: E402
import models.pipes as pipes  # noqa: E402
import models.props as props  # noqa: E402
import models.robotics as robotics  # noqa: E402
import models.structures as structures  # noqa: E402
import models.tanks as tanks  # noqa: E402
from voxelgen.gltf import build_glb, model_origin, to_gltf  # noqa: E402
from voxelgen.model import PALETTE, VOXEL  # noqa: E402
from voxelgen.obj import build_obj  # noqa: E402
from voxelgen.render import contact_sheet, render_model, write_png  # noqa: E402

MODULES = [conveyors, machines, pipes, tanks, robotics, structures, props]
SUBDIRS = ("glb", "obj", "preview", "rigs")
IMAGES = {}


def size_of(obj):
    return obj.size() if hasattr(obj, "parts") else obj.size


def meshes_of(obj):
    if hasattr(obj, "parts"):
        return [p["model"].mesh() for p in obj.parts], [p["name"] for p in obj.parts]
    return [obj.mesh()], [obj.name]


def aabb_gltf(meshes, origin):
    lo = None
    hi = None
    for m in meshes:
        if len(m.positions) == 0:
            continue
        p = to_gltf(m.positions - origin)
        mn, mx = p.min(axis=0), p.max(axis=0)
        lo = mn if lo is None else np_min(lo, mn)
        hi = mx if hi is None else np_max(hi, mx)
    if lo is None:
        return None
    return {"min": [round(float(v), 4) for v in lo],
            "max": [round(float(v), 4) for v in hi]}


def np_min(a, b):
    return [min(x, y) for x, y in zip(a, b)]


def np_max(a, b):
    return [max(x, y) for x, y in zip(a, b)]


def build_asset(obj, do_render=True):
    name = obj.name
    nx, ny, nz = size_of(obj)
    origin = model_origin(obj)
    meshes, names = meshes_of(obj)

    glb_rel = "glb/%s.glb" % name
    glb_size = build_glb(obj, os.path.join(ASSETS, glb_rel), origin)
    obj_rel = "obj/%s.obj" % name
    build_obj(meshes, names, os.path.join(ASSETS, obj_rel), origin)

    tris = sum(m.tri_count for m in meshes)
    verts = sum(m.vert_count for m in meshes)

    preview_rel = None
    if do_render:
        img = render_model(obj, width=520, height=420, azimuth=145, elevation=27,
                           pose=obj.meta.get("preview_pose"))
        preview_rel = "preview/%s.png" % name
        write_png(os.path.join(ASSETS, preview_rel), img)
        IMAGES[name] = img

    ports = []
    for p in obj.ports:
        # same origin the GLB uses: the tile centre when the asset declares one,
        # otherwise the geometry bounding box centre
        px, py, pz = [float(v) for v in p["pos_voxels"]]
        ox, oy = float(origin[0]), float(origin[1])
        ports.append({
            "name": p["name"],
            "pos": [round((px - ox) * VOXEL, 4), round(pz * VOXEL, 4),
                    round(-(py - oy) * VOXEL, 4)],
            "dir": [p["dir"][0], p["dir"][2], -p["dir"][1]],
            "type": p["type"],
            "note": p["note"],
        })

    entry = {
        "id": name,
        "category": obj.meta.get("category", "misc"),
        "glb": glb_rel,
        "obj": obj_rel,
        "preview": preview_rel,
        "size_voxels": [nx, ny, nz],
        "size_m": [round(nx * VOXEL, 4), round(nz * VOXEL, 4), round(ny * VOXEL, 4)],
        "footprint_m": [round(nx * VOXEL, 4), round(ny * VOXEL, 4)],
        "height_m": round(nz * VOXEL, 4),
        "tris": tris,
        "verts": verts,
        "aabb": aabb_gltf(meshes, origin),
        "ports": ports,
        "meta": obj.meta,
        "bytes": glb_size,
    }

    if hasattr(obj, "parts"):
        rig_rel = "rigs/%s.json" % name
        entry["rig"] = rig_rel
        entry["parts"] = [p["name"] for p in obj.parts]
        rig = {
            "asset": name,
            "units": "metres",
            "forward": "+Z",
            "up": "+Y",
            "note": ("glTF node hierarchy mirrors this rig: rotate each part node "
                     "about its joint axis. Pivots are in model space."),
            "parts": [],
        }
        for p in obj.parts:
            pv = to_gltf(np.array(p["pivot"], np.float32) - origin)
            mode = p.get("mode", "rotate")
            rig["parts"].append({
                "name": p["name"],
                "parent": p["parent"],
                "pivot": [round(float(v), 4) for v in pv],
                "axis": p["axis"],
                "mode": mode,
                "limits_deg": (list(p["limits"])
                               if p["limits"] and mode == "rotate" else None),
                "limits_m": (list(p["limits"])
                             if p["limits"] and mode == "slide" else None),
                "note": p["note"],
            })
        with open(os.path.join(ASSETS, rig_rel), "w") as f:
            json.dump(rig, f, indent=2)
    return entry


def gallery_html(entries):
    cards = []
    for e in entries:
        ports = "".join(
            '<span class="port">%s</span>' % p["name"] for p in e["ports"]
        )
        rig = ('<span class="tag rig">rigged</span>' if e.get("rig") else "")
        cards.append("""
    <article class="card" data-cat="{cat}">
      <div class="thumb"><img src="{img}" alt="{id}" loading="lazy"></div>
      <div class="body">
        <h3>{id}</h3>
        <p class="specs">{w:.2f} &times; {d:.2f} &times; {h:.2f} m &middot; {tris} tris</p>
        <p class="ports">{ports}{rig}</p>
      </div>
    </article>""".format(
            cat=e["category"], img=e["preview"] or "", id=e["id"],
            w=e["size_m"][0], d=e["size_m"][2], h=e["height_m"],
            tris=e["tris"], ports=ports, rig=rig,
        ))
    cats = sorted({e["category"] for e in entries})
    nav = "".join('<a href="#%s">%s</a>' % (c, c) for c in cats)
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Voxel Factory - asset gallery</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#14171b; color:#dfe4ea;
         font:14px/1.5 ui-sans-serif,system-ui,"Segoe UI",Roboto,sans-serif; }}
  header {{ padding:28px 32px 12px; border-bottom:1px solid #262b32; }}
  h1 {{ margin:0 0 4px; font-size:20px; letter-spacing:.2px; }}
  header p {{ margin:0; color:#8d97a3; }}
  nav {{ display:flex; gap:14px; padding:10px 32px 16px; flex-wrap:wrap; }}
  nav a {{ color:#8d97a3; text-decoration:none; font-size:12px;
           text-transform:uppercase; letter-spacing:.08em; }}
  nav a:hover {{ color:#e7b437; }}
  main {{ padding:8px 24px 56px; display:grid; gap:16px;
          grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); }}
  .card {{ background:#1b1f25; border:1px solid #262b32; border-radius:10px;
           overflow:hidden; }}
  .thumb {{ background:#e8eaec; aspect-ratio:520/420; }}
  .thumb img {{ width:100%; height:100%; display:block; }}
  .body {{ padding:10px 12px 12px; }}
  h3 {{ margin:0; font-size:13px; font-weight:600; letter-spacing:.01em; }}
  .specs {{ margin:3px 0 8px; color:#8d97a3; font-size:11.5px;
            font-variant-numeric:tabular-nums; }}
  .ports {{ display:flex; flex-wrap:wrap; gap:4px; margin:0; }}
  .port {{ font-size:10px; padding:1px 5px; border-radius:4px;
           background:#232a33; color:#9fb0c0; }}
  .tag.rig {{ font-size:10px; padding:1px 5px; border-radius:4px;
              background:#3a2f18; color:#e7b437; }}
</style></head>
<body>
<header>
  <h1>Voxel factory &mdash; asset gallery</h1>
  <p>{n} models &middot; 1 voxel = 6.25 cm &middot; 2 m tile grid &middot; glTF + OBJ</p>
</header>
<nav>{nav}</nav>
<main>{cards}
</main>
</body></html>
""".format(n=len(entries), nav=nav, cards="".join(cards))


def main():
    argv = [a for a in sys.argv[1:]]
    do_render = "--no-render" not in argv
    only = [a for a in argv if not a.startswith("-")]
    for d in SUBDIRS:
        os.makedirs(os.path.join(ASSETS, d), exist_ok=True)

    entries = []
    t0 = time.time()
    for mod in MODULES:
        for fn in mod.BUILDERS:
            name = fn.__name__
            if only and name not in only:
                continue
            t1 = time.time()
            obj = fn()
            entry = build_asset(obj, do_render)
            entries.append(entry)
            print("%-20s %5d tris %6.1f kB  %4.0f ms" % (
                entry["id"], entry["tris"], entry["bytes"] / 1024.0,
                (time.time() - t1) * 1000))
    if not entries:
        print("nothing selected")
        return

    if not only:
        manifest_path = os.path.join(ASSETS, "manifest.json")
        manifest = {
            "asset_set": "voxel-factory",
            "version": 1,
            "units": "metres",
            "voxel_size": VOXEL,
            "up": "+Y",
            "forward": "+Z",
            "origin": "bottom centre of the footprint, y = 0 on the floor",
            "grid": {"tile_voxels": 32, "tile_m": 2.0},
            "conventions": {
                "vertex_colors": "COLOR_0, sRGB floats, flat per-face normals",
                "material": "single shared PBR material, no textures",
                "ports": "pos/dir in metres, model space, dir points outward",
            },
            "palette": PALETTE,
            "assets": entries,
        }
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        with open(os.path.join(ASSETS, "gallery.html"), "w") as f:
            f.write(gallery_html(entries))

        with open(os.path.join(ASSETS, "inventory.md"), "w") as f:
            f.write("# Asset inventory\n\n")
            f.write("| id | category | size W x H x D (m) | tris | ports |\n")
            f.write("|---|---|---|---|---|\n")
            for e in sorted(entries, key=lambda a: (a["category"], a["id"])):
                w, h, d = e["size_m"]
                ports = ", ".join("`%s`" % p["name"] for p in e["ports"]) or "-"
                f.write("| `%s` | %s | %.2f x %.2f x %.2f | %d | %s |\n" % (
                    e["id"], e["category"], w, h, d, e["tris"], ports))
            f.write("\nTotal: %d assets, %d triangles, %.1f MB of GLB.\n" % (
                len(entries), sum(e["tris"] for e in entries),
                sum(e["bytes"] for e in entries) / 1048576.0))

        if IMAGES:
            sheet = contact_sheet(
                [(e["id"], IMAGES[e["id"]]) for e in entries if e["id"] in IMAGES],
                cols=4, scale=2)
            write_png(os.path.join(ASSETS, "contact_sheet.png"), sheet)

        print("\n%d assets -> %s" % (len(entries), ASSETS))
        print("total tris: %d, total GLB: %.1f kB, %.1fs" % (
            sum(e["tris"] for e in entries),
            sum(e["bytes"] for e in entries) / 1024.0, time.time() - t0))


if __name__ == "__main__":
    main()
