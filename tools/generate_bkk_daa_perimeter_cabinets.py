#!/usr/bin/env python3
"""Place depot barrel rack cabinets side-by-side around the bkk_daa green border ring."""

import math
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORLD_FILE = SCRIPT_DIR.parent / "worlds" / "bkk_daa.sdf"

# World origin at former (2.5, 2.5). Green ring: outer 6x11 at (-0.25, 2.0),
# inner brown 4.5x9 at (-0.25, 2.0).
WEST_X = -2.875
EAST_X = 2.375
NORTH_Y = 7.25
SOUTH_Y = -3.0
Z = 0.0  # model link origin is at floor level (posts/shelves start at z=0)

OUTER_Y_MIN = -3.5
OUTER_Y_MAX = 7.5
INNER_X_MIN = -2.5
INNER_X_MAX = 2.0

CABINET_WIDTH = 1.2
CABINET_HALF = CABINET_WIDTH / 2.0

# Cabinet front faces local -X at yaw=0.


def positions_along(start, end):
    span = end - start
    count = max(1, int(span / CABINET_WIDTH))
    step = span / count
    return [start + step * (i + 0.5) for i in range(count)]


def fixed_positions(start, end, count):
    span = end - start
    step = span / count
    return [start + step * (i + 0.5) for i in range(count)]


def cabinet_include(name, x, y, z, yaw):
    return f"""    <include>
      <uri>model://depot_barrel_rack</uri>
      <name>{name}</name>
      <pose>{x} {y} {z} 0 0 {yaw}</pose>
    </include>"""


def build_perimeter_cabinets():
    includes = []
    idx = 0

    # West strip (face east, +X)
    for y in positions_along(OUTER_Y_MIN + CABINET_HALF, OUTER_Y_MAX - CABINET_HALF):
        includes.append(cabinet_include(f"perimeter_cabinet_{idx:02d}", WEST_X, y, Z, math.pi))
        idx += 1

    # East strip (face west, -X)
    for y in positions_along(OUTER_Y_MIN + CABINET_HALF, OUTER_Y_MAX - CABINET_HALF):
        includes.append(cabinet_include(f"perimeter_cabinet_{idx:02d}", EAST_X, y, Z, 0.0))
        idx += 1

    # North strip between corners (face south, -Y) — 3 cabinets across 4.5 m
    for x in fixed_positions(INNER_X_MIN + CABINET_HALF, INNER_X_MAX - CABINET_HALF, 3):
        includes.append(cabinet_include(
            f"perimeter_cabinet_{idx:02d}", x, NORTH_Y, Z, math.pi / 2.0))
        idx += 1

    # South strip between corners (face north, +Y) — 3 cabinets across 4.5 m
    for x in fixed_positions(INNER_X_MIN + CABINET_HALF, INNER_X_MAX - CABINET_HALF, 3):
        includes.append(cabinet_include(
            f"perimeter_cabinet_{idx:02d}", x, SOUTH_Y, Z, -math.pi / 2.0))
        idx += 1

    return includes


def update_world(includes):
    text = WORLD_FILE.read_text(encoding="utf-8")

    # Remove prior green-ring slam boxes and single cabinet includes.
    text = re.sub(
        r"\n    <!-- SLAM feature objects.*?"
        r"(?=\n    <!-- (?:Depot barrel|Perimeter cabinet|Middle-left row))",
        "\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\n    <!-- Depot barrel rack cabinet.*?</include>",
        "",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\n    <!-- Perimeter cabinets in green border ring.*?"
        r"(?=\n    <!-- Middle-left row block 5)",
        "\n",
        text,
        flags=re.DOTALL,
    )

    block = (
        "    <!-- Perimeter cabinets in green border ring (generated) -->\n"
        + "\n".join(includes)
        + "\n"
    )

    needle = "    <!-- Middle-left row block 5: height 3.0m -->"
    if needle not in text:
        raise RuntimeError("insertion point not found in bkk_daa.sdf")

    text = text.replace(needle, block + needle, 1)
    WORLD_FILE.write_text(text, encoding="utf-8")


def main():
    includes = build_perimeter_cabinets()
    update_world(includes)
    print(f"Placed {len(includes)} perimeter cabinets in {WORLD_FILE}")


if __name__ == "__main__":
    main()
