#!/usr/bin/env python3
"""Check generated sheets for text collisions and out-of-frame content.

Two failure modes are easy to introduce and easy to miss when a sheet is only
eyeballed at screen size: two pieces of text landing on top of each other, and
something drifting outside the drawing frame.  Both are cheap to test for,
because the SVG carries every text element's position and size, and the font
metrics are the same ones the layout code used.

Reports rather than asserts: some overlaps are deliberate (a dimension value
sitting on its own dimension line, say), so the output is for a human to read.

Run: uv run --no-project --with pillow python scripts/check_sheets.py
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drafting import style  # noqa: E402

TEXT_RE = re.compile(
    r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*?font-size="([\d.]+)"[^>]*?'
    r'text-anchor="(\w+)"([^>]*)>(.*?)</text>')
ROTATE_RE = re.compile(r'rotate\(([-\d.]+) ([-\d.]+) ([-\d.]+)\)')

#: Text this small anywhere on a sheet is a defect: ISO 3098 puts the floor at
#: 2.5 mm and nothing here should go under it.
MIN_TEXT_MM = 2.4

#: Overlaps smaller than this are touching, not colliding.
OVERLAP_TOL = 0.35


def unescape(s: str) -> str:
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&#x27;", "'"))


def boxes(svg: str) -> list[tuple[float, float, float, float, str, float]]:
    out = []
    for m in TEXT_RE.finditer(svg):
        x, y, size = float(m.group(1)), float(m.group(2)), float(m.group(3))
        anchor, rest, text = m.group(4), m.group(5), unescape(m.group(6))
        if not text.strip():
            continue
        bold = "font-weight=" in rest
        w = style.text_width(text, size, bold=bold)
        asc, desc = style.text_height(size), size * 0.22
        x0 = {"start": x, "middle": x - w / 2, "end": x - w}[anchor]
        box = (x0, y - asc, x0 + w, y + desc)
        rot = ROTATE_RE.search(rest)
        if rot:
            ang = math.radians(float(rot.group(1)))
            cx, cy = float(rot.group(2)), float(rot.group(3))
            corners = [(box[0], box[1]), (box[2], box[1]),
                       (box[2], box[3]), (box[0], box[3])]
            pts = []
            for px, py in corners:
                dx, dy = px - cx, py - cy
                pts.append((cx + dx * math.cos(ang) - dy * math.sin(ang),
                            cy + dx * math.sin(ang) + dy * math.cos(ang)))
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            box = (min(xs), min(ys), max(xs), max(ys))
        out.append((*box, text, size))
    return out


def overlap(a, b) -> float:
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return min(dx, dy) if dx > 0 and dy > 0 else 0.0


def main() -> None:
    sheets = sorted((ROOT / "diagrams").rglob("*.svg"))
    if not sheets:
        raise SystemExit("no sheets found; run scripts/generate_diagrams.py")

    total = 0
    for path in sheets:
        svg = path.read_text()
        page_w = float(re.search(r'width="([\d.]+)mm"', svg).group(1))
        page_h = float(re.search(r'height="([\d.]+)mm"', svg).group(1))
        margin = style.SHEET_MARGIN + 5.0
        items = boxes(svg)

        problems: list[str] = []
        for i, a in enumerate(items):
            if a[5] < MIN_TEXT_MM:
                problems.append(f"text {a[4]!r} is {a[5]:.2f} mm, under the "
                                f"{MIN_TEXT_MM} mm floor")
            if a[0] < margin - 6 or a[2] > page_w - margin + 6 \
                    or a[1] < 0 or a[3] > page_h:
                problems.append(f"text {a[4]!r} at ({a[0]:.1f},{a[1]:.1f}) "
                                f"lies outside the drawing frame")
            for b in items[i + 1:]:
                ov = overlap(a, b)
                if ov > OVERLAP_TOL:
                    problems.append(
                        f"text {a[4]!r} and {b[4]!r} overlap by {ov:.2f} mm "
                        f"near ({max(a[0], b[0]):.1f},{max(a[1], b[1]):.1f})")

        name = path.relative_to(ROOT / "diagrams")
        if problems:
            total += len(problems)
            print(f"{name}: {len(problems)} problem(s)")
            for line in problems[:14]:
                print(f"    {line}")
            if len(problems) > 14:
                print(f"    ... and {len(problems) - 14} more")
        else:
            print(f"{name}: clean ({len(items)} text elements)")
    print(f"\n{total} problem(s) across {len(sheets)} sheets")


if __name__ == "__main__":
    main()
