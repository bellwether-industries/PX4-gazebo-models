#!/usr/bin/env python3
"""Generate static feature objects in the green border ring of bkk_daa for SLAM."""

import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORLD_FILE = SCRIPT_DIR.parent / "worlds" / "bkk_daa.sdf"

# Outer green: 6x11 m at (-0.25, 2.0)  -> x [-3.25, 2.75], y [-3.5, 7.5]
# Inner brown: 4.5x9 m at (-0.25, 2.0) -> x [-2.5, 2.0], y [-2.5, 6.5]
# Green ring = outer minus inner (0.75 m side strips, 1 m north/south strips)

COLORS = [
    (0.60, 0.40, 0.20),
    (0.70, 0.20, 0.20),
    (0.20, 0.30, 0.70),
    (0.20, 0.60, 0.30),
    (0.50, 0.50, 0.50),
    (0.80, 0.50, 0.10),
    (0.50, 0.20, 0.60),
    (0.20, 0.50, 0.50),
    (0.35, 0.35, 0.40),
    (0.75, 0.35, 0.35),
]

HEIGHTS = [1.0, 1.5, 2.0, 2.5, 1.2, 1.8, 2.2, 0.8, 1.6, 2.4, 1.4]


def ring_objects():
    """Place boxes only in the green border ring, not the inner brown area."""
    objects = []
    idx = 0

    def add(name, x, y, sx, sy, sz):
        nonlocal idx
        objects.append((name, x, y, sx, sy, sz))
        idx += 1

    # Left green strip (x in [-3.25, -2.5])
    left_x = -2.90
    for i, y in enumerate([-3.0, -2.25, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.25, 7.0]):
        h = HEIGHTS[i % len(HEIGHTS)]
        add(f"slam_ring_left_{i + 1}", left_x, y, 0.35, 0.35, h)

    # Right green strip (x in [2.0, 2.75])
    right_x = 2.40
    for i, y in enumerate([-3.0, -2.25, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.25, 7.0]):
        h = HEIGHTS[(i + 3) % len(HEIGHTS)]
        add(f"slam_ring_right_{i + 1}", right_x, y, 0.35, 0.35, h)

    # South green strip (y in [-3.5, -2.5], x in [-2.5, 2.0])
    south_y = -3.0
    for i, x in enumerate([-2.15, -1.65, -1.15, -0.65, -0.15, 0.35, 0.85, 1.35, 1.65]):
        h = HEIGHTS[(i + 5) % len(HEIGHTS)]
        add(f"slam_ring_south_{i + 1}", x, south_y, 0.35, 0.35, h)

    # North green strip (y in [6.5, 7.5], x in [-2.5, 2.0])
    north_y = 7.0
    for i, x in enumerate([-2.15, -1.65, -1.15, -0.65, -0.15, 0.35, 0.85, 1.35, 1.65]):
        h = HEIGHTS[(i + 7) % len(HEIGHTS)]
        add(f"slam_ring_north_{i + 1}", x, north_y, 0.35, 0.35, h)

    return objects


OBJECTS = ring_objects()


def box_model(name, x, y, sx, sy, sz, color):
    ar, ag, ab = color
    dr = min(ar + 0.1, 1.0)
    dg = min(ag + 0.1, 1.0)
    db = min(ab + 0.1, 1.0)
    z = sz / 2.0
    return f"""    <model name="{name}">
      <static>true</static>
      <pose>{x} {y} {z} 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry>
            <box>
              <size>{sx} {sy} {sz}</size>
            </box>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <box>
              <size>{sx} {sy} {sz}</size>
            </box>
          </geometry>
          <material>
            <ambient>{ar:.4f} {ag:.4f} {ab:.4f} 1</ambient>
            <diffuse>{dr:.4f} {dg:.4f} {db:.4f} 1</diffuse>
            <specular>0.1 0.1 0.1 1</specular>
          </material>
        </visual>
      </link>
    </model>"""


def build_features_xml():
    lines = [
        "    <!-- SLAM feature objects in green border ring only (generated) -->",
    ]
    for idx, (name, x, y, sx, sy, sz) in enumerate(OBJECTS):
        color = COLORS[idx % len(COLORS)]
        lines.append(box_model(name, x, y, sx, sy, sz, color))
    return "\n".join(lines) + "\n"


def update_world(features_xml):
    text = WORLD_FILE.read_text(encoding="utf-8")
    text = re.sub(
        r"\n    <!-- SLAM feature objects.*?"
        r"(?=\n    <!-- Middle-left row block 5)",
        "\n",
        text,
        flags=re.DOTALL,
    )
    needle = "    <!-- Middle-left row block 5: height 3.0m -->"
    if needle not in text:
        raise RuntimeError("insertion point not found in bkk_daa.sdf")
    text = text.replace(needle, features_xml + needle, 1)
    WORLD_FILE.write_text(text, encoding="utf-8")


def main():
    update_world(build_features_xml())
    print(f"Added {len(OBJECTS)} SLAM objects in green border ring to {WORLD_FILE}")


if __name__ == "__main__":
    main()
