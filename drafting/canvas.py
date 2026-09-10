"""A tiny SVG canvas in sheet millimetres, with Y pointing up.

SVG's own Y axis points down, which is the opposite of every drawing
convention, so the flip happens once here at emit time and every caller gets to
work in ordinary drawing coordinates: origin at the bottom-left of the sheet,
X right, Y up, units millimetres.
"""

from __future__ import annotations

import html
import math
from dataclasses import dataclass, field

from . import style


def fmt(v: float) -> str:
    """Format a coordinate: enough precision to be exact, no trailing noise."""
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


@dataclass
class Canvas:
    width: float
    height: float
    parts: list[str] = field(default_factory=list)
    defs: list[str] = field(default_factory=list)

    # -- coordinate flip ----------------------------------------------------

    def _y(self, y: float) -> float:
        return self.height - y

    # -- primitives ---------------------------------------------------------

    def line(self, x1, y1, x2, y2, *, w=style.W_THIN, colour=style.C_LINE,
             dash: str | None = None, cap="round", opacity: float | None = None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        extra += f' opacity="{fmt(opacity)}"' if opacity is not None else ""
        self.parts.append(
            f'<line x1="{fmt(x1)}" y1="{fmt(self._y(y1))}" x2="{fmt(x2)}" '
            f'y2="{fmt(self._y(y2))}" stroke="{colour}" stroke-width="{fmt(w)}" '
            f'stroke-linecap="{cap}"{extra}/>')

    def polyline(self, pts, *, w=style.W_THIN, colour=style.C_LINE,
                 dash=None, close=False, fill="none"):
        d = " ".join(f"{fmt(x)},{fmt(self._y(y))}" for x, y in pts)
        tag = "polygon" if close else "polyline"
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<{tag} points="{d}" fill="{fill}" stroke="{colour}" '
            f'stroke-width="{fmt(w)}" stroke-linejoin="round"{extra}/>')

    def path(self, d: str, *, w=style.W_THIN, colour=style.C_LINE, fill="none",
             dash=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<path d="{d}" fill="{fill}" stroke="{colour}" '
            f'stroke-width="{fmt(w)}" stroke-linejoin="round" '
            f'stroke-linecap="round"{extra}/>')

    def rect(self, x, y, w, h, *, weight=style.W_THIN, colour=style.C_LINE,
             fill="none", dash=None, radius=0.0):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        extra += f' rx="{fmt(radius)}" ry="{fmt(radius)}"' if radius else ""
        self.parts.append(
            f'<rect x="{fmt(x)}" y="{fmt(self._y(y + h))}" width="{fmt(w)}" '
            f'height="{fmt(h)}" fill="{fill}" stroke="{colour}" '
            f'stroke-width="{fmt(weight)}"{extra}/>')

    def circle(self, cx, cy, r, *, w=style.W_THIN, colour=style.C_LINE,
               fill="none", dash=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<circle cx="{fmt(cx)}" cy="{fmt(self._y(cy))}" r="{fmt(r)}" '
            f'fill="{fill}" stroke="{colour}" stroke-width="{fmt(w)}"{extra}/>')

    def arc(self, x1, y1, x2, y2, r, *, large=0, sweep=0, w=style.W_THIN,
            colour=style.C_LINE):
        # The Y flip reverses the sense of rotation, so the sweep flag flips too.
        self.path(f"M {fmt(x1)} {fmt(self._y(y1))} A {fmt(r)} {fmt(r)} 0 "
                  f"{large} {1 - sweep} {fmt(x2)} {fmt(self._y(y2))}",
                  w=w, colour=colour)

    def text(self, x, y, s, *, size=style.T_NOTE, colour=style.C_NOTE,
             anchor="start", face="condensed", bold=False, baseline="alphabetic",
             rotate=0.0):
        """Draw *s* with *size* millimetre capitals, per ISO 3098.

        ``size`` is a cap height, not a font size; the conversion to an em
        happens here so that no caller has to think about it.
        ``baseline='middle'`` centres the capitals vertically on *y*.
        """
        if not s:
            return
        dy = 0.0
        if baseline == "middle":
            dy = style.text_height(size) / 2
        elif baseline == "top":
            dy = -style.text_height(size)
        sy = self._y(y + dy)
        transform = ""
        if rotate:
            transform = f' transform="rotate({fmt(-rotate)} {fmt(x)} {fmt(sy)})"'
        weight = ' font-weight="bold"' if bold else ""
        self.parts.append(
            f'<text x="{fmt(x)}" y="{fmt(sy)}" font-family="{style.FONT_FAMILY[face]}" '
            f'font-size="{fmt(style.em(size))}" fill="{colour}" '
            f'text-anchor="{anchor}"{weight}{transform}>{html.escape(s)}</text>')

    def arrow(self, tip_x, tip_y, angle_deg, *, length=style.ARROW_LEN,
              half_width=style.ARROW_HALF_WIDTH, colour=style.C_DIM):
        """Filled arrowhead with its tip at (tip_x, tip_y), pointing at *angle_deg*."""
        a = math.radians(angle_deg)
        bx, by = tip_x - length * math.cos(a), tip_y - length * math.sin(a)
        nx, ny = -math.sin(a), math.cos(a)
        self.polyline(
            [(tip_x, tip_y),
             (bx + nx * half_width, by + ny * half_width),
             (bx - nx * half_width, by - ny * half_width)],
            close=True, fill=colour, colour=colour, w=0.05)

    # -- output -------------------------------------------------------------

    def to_svg(self) -> str:
        defs = ("<defs>" + "".join(self.defs) + "</defs>") if self.defs else ""
        return (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
            f'width="{fmt(self.width)}mm" height="{fmt(self.height)}mm" '
            f'viewBox="0 0 {fmt(self.width)} {fmt(self.height)}">\n'
            f'<rect width="100%" height="100%" fill="#ffffff"/>\n'
            f'{defs}\n' + "\n".join(self.parts) + "\n</svg>\n")

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(self.to_svg())
