#!/usr/bin/env python3
"""Shift bkk_daa world-frame poses so former (2.5, 2.5) becomes world (0, 0)."""

import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORLD_FILE = SCRIPT_DIR.parent / "worlds" / "bkk_daa.sdf"

DX = -2.5
DY = -2.5

SHIFT_MODELS = {
    "outer_ground_plane",
    "ground_plane",
    "green_boundary_wall_north",
    "green_boundary_wall_south",
    "green_boundary_wall_east",
    "green_boundary_wall_west",
    "middle_left_5",
    "top_camera",
}

POSE_RE = re.compile(r"(<pose>)([^<]+)(</pose>)")


def shift_pose_values(content: str) -> str:
    parts = content.split()
    if len(parts) >= 2:
        parts[0] = str(float(parts[0]) + DX)
        parts[1] = str(float(parts[1]) + DY)
    return " ".join(parts)


def shift_line(line: str) -> str:
    match = POSE_RE.search(line)
    if not match:
        return line
    shifted = shift_pose_values(match.group(2))
    return line[: match.start()] + f"{match.group(1)}{shifted}{match.group(3)}" + line[match.end() :]


def shift_world(text: str) -> str:
    lines = text.splitlines()
    out = []

    current_model = None
    pending_model_pose = False
    pending_include_pose = False
    pending_gui_camera_pose = False
    link_depth = 0
    in_gui = False

    for line in lines:
        model_match = re.search(r'<model name="([^"]+)"', line)
        if model_match:
            current_model = model_match.group(1)
            pending_model_pose = current_model in SHIFT_MODELS

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

        should_shift = False
        if POSE_RE.search(line):
            if pending_include_pose:
                should_shift = True
                pending_include_pose = False
            elif pending_gui_camera_pose and link_depth == 0:
                should_shift = True
                pending_gui_camera_pose = False
            elif pending_model_pose and link_depth == 0:
                should_shift = True
                pending_model_pose = False

        if "</include>" in line:
            pending_include_pose = False

        out.append(shift_line(line) if should_shift else line)

    return "\n".join(out) + "\n"


def main():
    text = WORLD_FILE.read_text(encoding="utf-8")
    WORLD_FILE.write_text(shift_world(text), encoding="utf-8")
    print(f"Shifted world-frame poses by ({DX}, {DY}) in {WORLD_FILE}")


if __name__ == "__main__":
    main()
