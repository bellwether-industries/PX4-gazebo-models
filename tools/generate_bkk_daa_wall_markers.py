#!/usr/bin/env python3
"""Generate ArUco DICT_4X4_50 textures and wall marker layout for bkk_daa.sdf."""

import os
import sys

# Prefer system OpenCV/numpy (avoids broken user-site numpy 2.x installs).
sys.path = ["/usr/lib/python3/dist-packages"] + [p for p in sys.path if "/usr/local" not in p]

import cv2

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "..", "models", "wall_aruco_textures")
WORLD_FILE = os.path.join(SCRIPT_DIR, "..", "worlds", "bkk_daa.sdf")

MARKER_COUNT = 50
MARKER_SIZE = 0.4
WALL_OFFSET = 0.051


def generate_textures():
    os.makedirs(MODEL_DIR, exist_ok=True)
    dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)

    for marker_id in range(MARKER_COUNT):
        img = cv2.aruco.drawMarker(dictionary, marker_id, 400)
        padded = cv2.copyMakeBorder(img, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=255)
        cv2.imwrite(os.path.join(MODEL_DIR, f"marker_{marker_id:02d}.png"), padded)


def marker_visual(name, lx, ly, lz, nx, ny, nz, tex):
    return f"""        <visual name="{name}">
          <pose>{lx} {ly} {lz} 0 0 0</pose>
          <geometry>
            <plane>
              <normal>{nx} {ny} {nz}</normal>
              <size>{MARKER_SIZE} {MARKER_SIZE}</size>
            </plane>
          </geometry>
          <material>
            <diffuse>1 1 1 1</diffuse>
            <specular>0.1 0.1 0.1 1</specular>
            <pbr>
              <metal>
                <albedo_map>model://wall_aruco_textures/{tex}</albedo_map>
              </metal>
            </pbr>
          </material>
        </visual>"""


def build_wall_markers():
    chunks = {}
    marker_id = 0

    xs = [-2.0, -1.0, 0.0, 1.0, 2.0]
    zs = [-0.75, 0.75]

    # North wall interior faces south (-Y).
    lines = []
    for z in zs:
        for x in xs:
            lines.append(marker_visual(
                f"aruco_{marker_id:02d}", x, -WALL_OFFSET, z, 0, -1, 0,
                f"marker_{marker_id:02d}.png"))
            marker_id += 1
    chunks["north"] = "\n".join(lines)

    # South wall interior faces north (+Y).
    lines = []
    for z in zs:
        for x in xs:
            lines.append(marker_visual(
                f"aruco_{marker_id:02d}", x, WALL_OFFSET, z, 0, 1, 0,
                f"marker_{marker_id:02d}.png"))
            marker_id += 1
    chunks["south"] = "\n".join(lines)

    ys = [-4.0, -2.0, 0.0, 2.0, 4.0]
    zs3 = [-0.85, 0.0, 0.85]

    # East wall interior faces west (-X).
    lines = []
    for z in zs3:
        for y in ys:
            lines.append(marker_visual(
                f"aruco_{marker_id:02d}", -WALL_OFFSET, y, z, -1, 0, 0,
                f"marker_{marker_id:02d}.png"))
            marker_id += 1
    chunks["east"] = "\n".join(lines)

    # West wall interior faces east (+X).
    lines = []
    for z in zs3:
        for y in ys:
            lines.append(marker_visual(
                f"aruco_{marker_id:02d}", WALL_OFFSET, y, z, 1, 0, 0,
                f"marker_{marker_id:02d}.png"))
            marker_id += 1
    chunks["west"] = "\n".join(lines)

    return chunks


def update_world(chunks):
    import re

    with open(WORLD_FILE, "r", encoding="utf-8") as f:
        sdf = f.read()

    replacements = {
        "green_boundary_wall_north": chunks["north"],
        "green_boundary_wall_south": chunks["south"],
        "green_boundary_wall_east": chunks["east"],
        "green_boundary_wall_west": chunks["west"],
    }

    for model, markers in replacements.items():
        needle = f'    <model name="{model}">'
        start = sdf.find(needle)
        if start < 0:
            raise RuntimeError(f"model not found: {model}")

        end = sdf.find("    </model>", start)
        block = sdf[start:end]
        block = re.sub(
            r"\n        <visual name=\"aruco_\d+\">.*?</visual>",
            "",
            block,
            flags=re.DOTALL,
        )
        insert_at = block.rfind("      </link>")
        new_block = block[:insert_at] + markers + "\n" + block[insert_at:]
        sdf = sdf[:start] + new_block + sdf[end:]

    with open(WORLD_FILE, "w", encoding="utf-8") as f:
        f.write(sdf)


def main():
    generate_textures()
    update_world(build_wall_markers())
    print(f"Updated {WORLD_FILE} with {MARKER_COUNT} wall ArUco markers")


if __name__ == "__main__":
    main()
