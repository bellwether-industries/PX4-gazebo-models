#!/usr/bin/env python3
"""Rigidly rotate the bkk_daa world by -90 degrees about the world origin.

Both position ((x, y) -> (y, -x)) and yaw (yaw -> yaw - pi/2) are rotated for
every world-frame pose, so rectangular objects (walls, ground planes) keep
their correct footprint after the turn; z, roll, and pitch are left
unchanged. Applies to top-level <model> poses, <include> poses, and the GUI
camera pose -- the same set of world-frame poses handled by
shift_bkk_daa_world_origin.py -- while leaving nested <link>/<visual>/<collision>
poses (which are relative to their parent, and rotate along with it) untouched.
"""

import math
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORLD_FILE = SCRIPT_DIR.parent / "worlds" / "bkk_daa.sdf"

POSE_RE = re.compile(r"(<pose>)([^<]+)(</pose>)")


def rotate_pose_values(content: str) -> str:
    parts = content.split()
    if len(parts) >= 2:
        x, y = float(parts[0]), float(parts[1])
        parts[0] = str(y)
        parts[1] = str(-x)
    if len(parts) >= 6:
        parts[5] = str(float(parts[5]) - math.pi / 2)
    return " ".join(parts)


def rotate_line(line: str) -> str:
    match = POSE_RE.search(line)
    if not match:
        return line
    rotated = rotate_pose_values(match.group(2))
    return line[: match.start()] + f"{match.group(1)}{rotated}{match.group(3)}" + line[match.end() :]


def rotate_world(text: str) -> str:
    lines = text.splitlines()
    out = []

    pending_model_pose = False
    pending_include_pose = False
    pending_gui_camera_pose = False
    link_depth = 0
    in_gui = False

    for line in lines:
        if re.search(r'<model name="([^"]+)"', line):
            pending_model_pose = True

        if "<gui>" in line:
            in_gui = True
        if "</gui>" in line:
            in_gui = False
        if in_gui and "<camera" in line:
            pending_gui_camera_pose = True

        if "<include>" in line:
            pending_include_pose = True

        if "<link" in line:
            link_depth += line.count("<link")
        if "</link>" in line:
            link_depth -= line.count("</link>")

        should_rotate = False
        if POSE_RE.search(line):
            if pending_include_pose:
                should_rotate = True
                pending_include_pose = False
            elif pending_gui_camera_pose and link_depth == 0:
                should_rotate = True
                pending_gui_camera_pose = False
            elif pending_model_pose and link_depth == 0:
                should_rotate = True
                pending_model_pose = False

        if "</include>" in line:
            pending_include_pose = False

        out.append(rotate_line(line) if should_rotate else line)

    return "\n".join(out) + "\n"


def main():
    text = WORLD_FILE.read_text(encoding="utf-8")
    WORLD_FILE.write_text(rotate_world(text), encoding="utf-8")
    print(f"Rotated world-frame object positions by -90 degrees about the origin in {WORLD_FILE}")


if __name__ == "__main__":
    main()
