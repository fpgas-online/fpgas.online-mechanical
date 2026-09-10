"""Sheet furniture: frame, zone markings, title block, note blocks and tables."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import style
from .canvas import Canvas


@dataclass
class TitleBlock:
    title: str
    subtitle: str = ""
    drawing_no: str = ""
    rev: str = ""
    scale: str = "1:1"
    sheet: str = "1 OF 1"
    date: str = ""
    drawn_by: str = ""
    material: str = ""
    units: str = "mm"


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def x1(self) -> float:
        return self.x + self.w

    @property
    def y1(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def inset(self, d: float) -> "Rect":
        return Rect(self.x + d, self.y + d, self.w - 2 * d, self.h - 2 * d)


class Sheet:
    """An ISO-A sheet with a frame, zone markings and a title block.

    The usable area is split into a wide drawing area on the left and a
    narrower annotation column on the right, with the title block beneath the
    column.  Keeping tables and notes out of the drawing area is what stops
    them colliding with dimension lines.
    """

    COLUMN_WIDTH = 162.0
    TITLE_HEIGHT = 42.0

    def __init__(self, size: str = "A3", title: TitleBlock | None = None,
                 column_width: float | None = None):
        self.w, self.h = style.SHEET_SIZES[size]
        self.size_name = size
        self.canvas = Canvas(self.w, self.h)
        self.title = title or TitleBlock(title="")
        # Two borders, ISO 5457 style: a trim line near the paper edge and the
        # drawing frame inside it.  The strip between them carries the zone
        # markings, which is what keeps them clear of the drawing content.
        m = style.SHEET_MARGIN
        self.trim = Rect(m / 2, m / 2, self.w - m, self.h - m)
        self.frame = Rect(m + 5, m + 5, self.w - 2 * (m + 5), self.h - 2 * (m + 5))
        cw = self.COLUMN_WIDTH if column_width is None else column_width
        self.title_rect = Rect(self.frame.x1 - cw, self.frame.y, cw,
                               self.TITLE_HEIGHT)
        self.column = Rect(self.frame.x1 - cw, self.title_rect.y1 + 4.0,
                           cw, self.frame.y1 - self.title_rect.y1 - 4.0)
        self.area = Rect(self.frame.x, self.frame.y,
                         self.frame.w - cw - 6.0, self.frame.h)
        self._column_cursor = self.column.y1

    # -- furniture ----------------------------------------------------------

    def draw_frame(self) -> None:
        c = self.canvas
        c.rect(self.trim.x, self.trim.y, self.trim.w, self.trim.h,
               weight=style.W_THIN, colour="#888888")
        f = self.frame
        c.rect(f.x, f.y, f.w, f.h, weight=style.W_FRAME)
        self._draw_zones()

    def _draw_zones(self) -> None:
        """Zone letters down the sides and numbers along top and bottom."""
        c, f = self.canvas, self.frame
        t = self.trim
        strip = f.y - t.y
        cols = max(2, round(f.w / 70))
        rows = max(2, round(f.h / 70))
        letters = "ABCDEFGH"
        for i in range(cols):
            x0 = f.x + f.w * i / cols
            x1 = f.x + f.w * (i + 1) / cols
            if i:
                c.line(x0, t.y, x0, f.y, w=style.W_THIN, colour="#888888")
                c.line(x0, f.y1, x0, t.y1, w=style.W_THIN, colour="#888888")
            for y in (t.y + strip / 2, t.y1 - strip / 2):
                c.text((x0 + x1) / 2, y, str(cols - i), size=style.T_TINY,
                       anchor="middle", baseline="middle", colour="#666666")
        for j in range(rows):
            y0 = f.y + f.h * j / rows
            y1 = f.y + f.h * (j + 1) / rows
            if j:
                c.line(t.x, y0, f.x, y0, w=style.W_THIN, colour="#888888")
                c.line(f.x1, y0, t.x1, y0, w=style.W_THIN, colour="#888888")
            for x in (t.x + strip / 2, t.x1 - strip / 2):
                c.text(x, (y0 + y1) / 2, letters[rows - 1 - j],
                       size=style.T_TINY, anchor="middle", baseline="middle",
                       colour="#666666")

    def draw_title_block(self) -> None:
        c, r, t = self.canvas, self.title_rect, self.title
        c.rect(r.x, r.y, r.w, r.h, weight=style.W_FRAME)

        band = 13.0
        c.line(r.x, r.y1 - band, r.x1, r.y1 - band, w=style.W_TABLE_HEAVY)
        c.text(r.x + 2.5, r.y1 - band + 4.6, t.title, size=style.T_TITLE,
               face="sans", bold=True)
        if t.subtitle:
            c.text(r.x + 2.5, r.y1 - band + 1.2, t.subtitle,
                   size=style.T_LABEL, colour="#333333")

        cells = [
            ("DRAWN", t.drawn_by), ("DATE", t.date), ("UNITS", t.units),
            ("SCALE", t.scale), ("SIZE", self.size_name), ("SHEET", t.sheet),
            ("DRAWING NO", t.drawing_no), ("REV", t.rev),
        ]
        rows, cols = 2, 4
        ch = (r.h - band) / rows
        cw = r.w / cols
        for i, (label, value) in enumerate(cells):
            col, row = i % cols, i // cols
            x = r.x + col * cw
            y = r.y1 - band - (row + 1) * ch
            if col:
                c.line(x, y, x, y + ch, w=style.W_TABLE)
            if row:
                c.line(x, y + ch, x + cw, y + ch, w=style.W_TABLE)
            c.text(x + 1.6, y + ch - 3.2, label, size=style.T_TINY,
                   colour="#666666")
            c.text(x + 1.6, y + 1.6, value or "-", size=style.T_LABEL,
                   bold=True)

    def projection_symbol(self, x: float, y: float, scale: float = 1.0) -> None:
        """First-angle projection symbol (ISO 128), drawn as a truncated cone."""
        c = self.canvas
        s = scale
        c.text(x, y + 7.2 * s, "FIRST ANGLE PROJECTION", size=style.T_TINY,
               anchor="middle", colour="#666666")
        c.line(x - 11 * s, y + 3 * s, x + 11 * s, y + 3 * s,
               w=style.W_CENTRE, colour="#666666", dash="3,1.2,0.6,1.2")
        c.polyline([(x - 9 * s, y + 5.4 * s), (x - 1 * s, y + 4.2 * s),
                    (x - 1 * s, y + 1.8 * s), (x - 9 * s, y + 0.6 * s)],
                   close=True, w=style.W_OUTLINE)
        c.circle(x + 5.4 * s, y + 3 * s, 2.4 * s, w=style.W_OUTLINE)
        c.circle(x + 5.4 * s, y + 3 * s, 1.2 * s, w=style.W_OUTLINE)

    # -- annotation column --------------------------------------------------

    def column_block(self, height: float) -> Rect:
        """Reserve *height* mm at the top of the remaining annotation column."""
        top = self._column_cursor
        self._column_cursor = top - height - 4.0
        return Rect(self.column.x, top - height, self.column.w, height)

    @property
    def column_remaining(self) -> float:
        return self._column_cursor - self.column.y

    def heading(self, rect: Rect, text: str) -> float:
        """Draw a section heading at the top of *rect*; return the y below it."""
        c = self.canvas
        c.text(rect.x, rect.y1 - style.T_SUBHEAD, text, size=style.T_SUBHEAD,
               face="sans", bold=True)
        y = rect.y1 - style.T_SUBHEAD - 1.4
        c.line(rect.x, y, rect.x1, y, w=style.W_TABLE_HEAVY)
        return y - 2.2

    def notes(self, rect: Rect, title: str, lines: list[str],
              size: float = style.T_NOTE, numbered: bool = True) -> float:
        """Draw a numbered note block, wrapping to the column width."""
        c = self.canvas
        y = self.heading(rect, title) if title else rect.y1
        indent = 5.0 if numbered else 0.0
        for i, line in enumerate(lines, 1):
            wrapped = wrap(line, rect.w - indent, size)
            if numbered:
                c.text(rect.x, y - size, f"{i}.", size=size)
            for j, part in enumerate(wrapped):
                c.text(rect.x + indent, y - size, part, size=size)
                y -= size * 1.32
            y -= 1.0
        return y

    def table(self, rect: Rect, title: str, headers: list[str],
              rows: list[list[str]], aligns: list[str] | None = None,
              size: float = style.T_TABLE) -> float:
        """Draw a bordered table; return the y coordinate of its bottom edge."""
        c = self.canvas
        y = self.heading(rect, title) if title else rect.y1
        ncol = len(headers)
        aligns = aligns or ["start"] * ncol
        pad = 1.8
        widths = []
        for i in range(ncol):
            cells = [headers[i]] + [r[i] for r in rows]
            widths.append(max(style.text_width(t, size, bold=(t is headers[i]))
                              for t in cells) + 2 * pad)
        total = sum(widths)
        if total > rect.w:
            widths = [w * rect.w / total for w in widths]
            total = rect.w

        rh = size * 1.75
        top = y
        c.rect(rect.x, y - rh, total, rh, weight=style.W_TABLE,
               fill=style.C_FILL_TABLE_HEAD)
        x = rect.x
        for i, head in enumerate(headers):
            c.text(_cell_x(x, widths[i], pad, aligns[i]), y - rh + rh * 0.32,
                   head, size=size, bold=True, anchor=_anchor(aligns[i]))
            x += widths[i]
        y -= rh

        for row in rows:
            c.rect(rect.x, y - rh, total, rh, weight=style.W_TABLE)
            x = rect.x
            for i, cell in enumerate(row):
                c.text(_cell_x(x, widths[i], pad, aligns[i]), y - rh + rh * 0.32,
                       cell, size=size, anchor=_anchor(aligns[i]))
                x += widths[i]
            y -= rh
        x = rect.x
        for wdt in widths[:-1]:
            x += wdt
            c.line(x, top, x, y, w=style.W_TABLE)
        return y


def _anchor(align: str) -> str:
    return {"start": "start", "end": "end", "middle": "middle"}[align]


def _cell_x(x: float, w: float, pad: float, align: str) -> float:
    return {"start": x + pad, "end": x + w - pad, "middle": x + w / 2}[align]


def wrap(text: str, width: float, size: float) -> list[str]:
    """Greedy word wrap to *width* millimetres, using real font metrics."""
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if style.text_width(trial, size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]
