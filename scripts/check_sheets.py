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

#: Cap height below which text on a sheet is a defect.  ISO 3098 puts the floor
#: at 2.5 mm; the slack is for floating point, not for smaller text.
MIN_TEXT_MM = 2.45

#: Overlaps smaller than this are touching, not colliding.
OVERLAP_TOL = 0.35


def unescape(s: str) -> str:
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&#x27;", "'"))


def boxes(svg: str) -> list[tuple[float, float, float, float, str, float]]:
    out = []
    for m in TEXT_RE.finditer(svg):
        x, y = float(m.group(1)), float(m.group(2))
        # The SVG carries an em; the layout works in cap heights.
        size = float(m.group(3)) * style.CAP_RATIO
        anchor, rest, text = m.group(4), m.group(5), unescape(m.group(6))
        if not text.strip():
            continue
        bold = "font-weight=" in rest
        w = style.text_width(text, size, bold=bold)
        asc, desc = style.text_height(size), style.descender(size)
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


LINE_RE = re.compile(
    r'<line x1="([-\d.]+)" y1="([-\d.]+)" x2="([-\d.]+)" y2="([-\d.]+)" '
    r'stroke="([#\w]+)"')

#: Lines a label must not sit on.  Table rules and heading underlines are drawn
#: deliberately close to their text, so only annotation and geometry lines are
#: checked: dimension and leader lines, feature outlines, and phantom parts.
CHECKED_STROKES = {style.C_DIM, style.C_HIGHLIGHT, style.C_PHANTOM,
                   style.C_COMPONENT}


def lines(svg: str):
    for m in LINE_RE.finditer(svg):
        x1, y1, x2, y2 = (float(v) for v in m.groups()[:4])
        if m.group(5) in CHECKED_STROKES:
            yield x1, y1, x2, y2


def box_hits_line(box, seg, tol: float) -> float:
    """How far a segment reaches inside a text box, 0 if it stays clear."""
    x0, y0, x1, y1 = box[0] + tol, box[1] + tol, box[2] - tol, box[3] - tol
    if x1 <= x0 or y1 <= y0:
        return 0.0
    ax, ay, bx, by = seg
    # Sample rather than clip: a few points is enough to say whether a line
    # runs through a word, and the maths stays obvious.
    inside = 0
    steps = 40
    for i in range(steps + 1):
        t = i / steps
        px, py = ax + (bx - ax) * t, ay + (by - ay) * t
        if x0 <= px <= x1 and y0 <= py <= y1:
            inside += 1
    if not inside:
        return 0.0
    return math.hypot(bx - ax, by - ay) * inside / steps


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
        # The zone markings live in the strip between the trim line and the
        # drawing frame, by design, so the bound is the trim line.
        trim = style.SHEET_MARGIN / 2
        items = boxes(svg)
        svg_lines = list(lines(svg))

        problems: list[str] = []
        for i, a in enumerate(items):
            if a[5] < MIN_TEXT_MM:
                problems.append(f"text {a[4]!r} is {a[5]:.2f} mm, under the "
                                f"{MIN_TEXT_MM} mm floor")
            if a[0] < trim or a[2] > page_w - trim \
                    or a[1] < trim or a[3] > page_h - trim:
                problems.append(f"text {a[4]!r} at ({a[0]:.1f},{a[1]:.1f}) "
                                f"lies outside the drawing frame")
            for b in items[i + 1:]:
                ov = overlap(a, b)
                if ov > OVERLAP_TOL:
                    problems.append(
                        f"text {a[4]!r} and {b[4]!r} overlap by {ov:.2f} mm "
                        f"near ({max(a[0], b[0]):.1f},{max(a[1], b[1]):.1f})")
        for a in items:
            for seg in svg_lines:
                run = box_hits_line(a[:4], seg, tol=0.5)
                if run > 1.0:
                    problems.append(
                        f"a line runs {run:.2f} mm through the text {a[4]!r} "
                        f"at ({a[0]:.1f},{a[1]:.1f})")
                    break

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
