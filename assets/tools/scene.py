#!/usr/bin/env python3
"""Compose the asset set into one diorama to check scale, tiling and colours.

    python3 assets/tools/scene.py

Writes assets/scene_showcase.png.  This is a presentation render only -- the
engine places its own models, but it proves the modules line up on the 2 m grid.
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import models.conveyors as conveyors  # noqa: E402
import models.machines as machines  # noqa: E402
import models.pipes as pipes  # noqa: E402
import models.props as props  # noqa: E402
import models.robotics as robotics  # noqa: E402
import models.structures as structures  # noqa: E402
import models.tanks as tanks  # noqa: E402
from voxelgen.gltf import model_origin  # noqa: E402
from voxelgen.model import VOXEL  # noqa: E402
from voxelgen.render import Scene, camera_basis, write_png  # noqa: E402

MODULES = [conveyors, machines, pipes, tanks, robotics, structures, props]
BUILDERS = {fn.__name__: fn for mod in MODULES for fn in mod.BUILDERS}

# (asset id, x m, y m, rotation about Z in degrees).  +y is "into" the scene.
LAYOUT = [
    # belt line from the west, ending at a stop chute
    ("conveyor_straight", -5.0, 0.0, 0),
    ("conveyor_straight", -3.0, 0.0, 0),
    ("conveyor_endstop", -1.5, 0.0, 0),
    # robot picking off the belt
    ("robot_arm", -3.4, 2.0, 0),
    # smelting cell fed by the belt
    ("smelter_furnace", 0.9, 2.9, 0),
    ("control_cabinet", 1.9, 5.0, 0),
    # fluids: tank + pump + pipe run
    ("water_tank", 4.0, 4.4, 0),
    ("pump", 1.2, -2.6, 0),
    ("pipe_straight", 3.3, -2.6, 0),
    ("valve", 5.4, -2.6, 0),
    # storage and handling
    ("storage_rack", 6.0, 1.6, 0),
    ("agv", -1.2, -2.4, 90),
    ("pallet", -5.9, -2.4, 0),
    ("cardboard_boxes", -5.9, -2.4, 0),
    ("crate", -3.6, -1.9, 0),
    # plant services
    ("power_transformer", 7.0, -3.4, 0),
    ("cooling_chiller", 4.8, 7.4, 0),
    ("motor", 0.2, -4.6, 0),
    ("safety_fence", -6.2, 3.8, 0),
    ("barrel", 2.2, -4.0, 0),
]

PITCH = int(round(2.0 / VOXEL))  # voxels per 2 m tile


def rot_z(deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def merged_meshes(obj):
    if hasattr(obj, "parts"):
        pose = obj.meta.get("preview_pose") or {}
        from voxelgen.render import _posed_part_meshes
        return _posed_part_meshes(obj, pose)
    return [obj.mesh()]


def build_scene():
    meshes = []
    for name, x, y, rot in LAYOUT:
        obj = BUILDERS[name]()
        origin = model_origin(obj)
        r = rot_z(rot)
        off = np.array([x / VOXEL, y / VOXEL, 0.0])
        parts = merged_meshes(obj)
        for m in parts:
            if len(m.positions) == 0:
                continue
            rel = m.positions - origin
            m.positions = rel @ r.T + off
            m.normals = m.normals @ r.T
            meshes.append(m)
        print("  placed %-20s at (%5.2f, %5.2f) rot %3d" % (name, x, y, rot))
    return meshes


def main():
    meshes = build_scene()
    allpos = np.vstack([m.positions for m in meshes])
    lo, hi = allpos.min(axis=0), allpos.max(axis=0)
    bounds_center = (lo + hi) * 0.5

    # frame the content itself: centre on the projected bounding box and pick
    # the scale that fits it, instead of guessing from the world extent
    az, el = 147.0, 30.0
    _, right, up = camera_basis(az, el)
    rel = allpos - bounds_center
    px, py = rel @ right, rel @ up
    center = (bounds_center + right * (px.min() + px.max()) * 0.5
              + up * (py.min() + py.max()) * 0.5)
    scene = Scene(1500, 950, center, 1.0, azimuth=az, elevation=el, ssaa=2,
                  bg=(0.905, 0.918, 0.928))
    scene.scale = min(scene.W * 0.93 / (px.max() - px.min()),
                      scene.H * 0.90 / (py.max() - py.min()))
    scene.add_floor(max(hi[0] - lo[0], hi[1] - lo[1]) * 1.4, step=PITCH)
    for m in meshes:
        scene.add_shadow(m)
    for m in meshes:
        scene.add_mesh(m)
    img = scene.finish()
    out = os.path.join(os.path.dirname(HERE), "scene_showcase.png")
    write_png(out, img)
    print("scene -> %s  (%dx%d, %d meshes)" % (out, img.shape[1], img.shape[0], len(meshes)))


if __name__ == "__main__":
    main()
